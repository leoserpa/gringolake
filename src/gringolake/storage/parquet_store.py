"""Atomic, schema-enforced Bronze storage writers using Polars LazyFrames."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

BRONZE_IBOV_SCHEMA: dict[str, pl.DataType] = {
    "trading_date": pl.Date,
    "index_code": pl.String,
    "ibov_close_raw": pl.String,
    "ibov_close": pl.Float64,
    "year": pl.Int32,
    "_source_system": pl.String,
    "_source_url": pl.String,
    "_payload_hash": pl.String,
    "_ingested_at": pl.Datetime("us", "UTC"),
}

BRONZE_INVESTOR_FLOW_SCHEMA: dict[str, pl.DataType] = {
    "publication_date": pl.Date,
    "reference_date": pl.Date,
    "investor_type_raw": pl.String,
    "mtd_purchases_k_brl": pl.Float64,
    "purchase_share_pct": pl.Float64,
    "mtd_sales_k_brl": pl.Float64,
    "sale_share_pct": pl.Float64,
    "source_note_pt": pl.String,
    "bdi_limit_date": pl.String,
    "_source_system": pl.String,
    "_source_url": pl.String,
    "_payload_hash": pl.String,
    "_ingested_at": pl.Datetime("us", "UTC"),
}


def write_json_atomic(target_path: Path, payload: dict[str, Any]) -> Path:
    """Write a raw JSON payload atomically to preserve an immutable Bronze audit trail.

    Args:
        target_path: Final destination path for the JSON artifact.
        payload: Deserialized API payload to persist as UTF-8 JSON.

    Returns:
        The written `target_path`.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=target_path.parent, suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        os.replace(tmp_name, target_path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
    return target_path


def write_parquet_partition_atomic(
    records: list[dict[str, Any]],
    schema: dict[str, pl.DataType],
    target_path: Path,
    sort_by: list[str] | None = None,
) -> int:
    """Write a schema-validated ZSTD Parquet file atomically via Polars lazy API.

    Args:
        records: Row dictionaries matching `schema`.
        schema: Explicit Polars schema enforced before materialization.
        target_path: Final `.parquet` file destination.
        sort_by: Optional columns used to deterministically sort rows before write.

    Returns:
        Number of rows written to `target_path`.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    lf = pl.DataFrame(records, schema=schema).lazy()
    if sort_by:
        lf = lf.sort(sort_by)
    df = lf.collect()

    fd, tmp_name = tempfile.mkstemp(dir=target_path.parent, suffix=".parquet.tmp")
    os.close(fd)
    try:
        df.write_parquet(tmp_name, compression="zstd", statistics=True)
        os.replace(tmp_name, target_path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
    return df.height


def load_optional_investor_backfill(backfill_dir: Path) -> pl.DataFrame:
    """Load optional official B3 historical backfill files (CSV/Parquet) from landing.

    Because B3's public BDI API retains only D-21 trading days (see ADR-002),
    historical official exports placed in `backfill_dir` are normalized to the
    exact Bronze schema and deduplicated downstream in Silver.

    Args:
        backfill_dir: Directory scanned for `.csv` and `.parquet` files.

    Returns:
        Polars DataFrame conforming to `BRONZE_INVESTOR_FLOW_SCHEMA` (empty if no files).

    Raises:
        ValueError: If any file misses required columns (`reference_date`,
            `investor_type_raw`, `mtd_purchases_k_brl`, `mtd_sales_k_brl`).
    """
    if not backfill_dir.exists():
        return pl.DataFrame(schema=BRONZE_INVESTOR_FLOW_SCHEMA)

    files = sorted(
        p
        for p in backfill_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".csv", ".parquet"}
    )
    if not files:
        return pl.DataFrame(schema=BRONZE_INVESTOR_FLOW_SCHEMA)

    ingested_at = datetime.now(UTC)
    csv_numeric_overrides: dict[str, pl.DataType] = {
        "mtd_purchases_k_brl": pl.Float64,
        "mtd_sales_k_brl": pl.Float64,
        "purchase_share_pct": pl.Float64,
        "sale_share_pct": pl.Float64,
    }
    frames: list[pl.LazyFrame] = []
    for file_path in files:
        lf = (
            pl.scan_parquet(file_path)
            if file_path.suffix.lower() == ".parquet"
            else pl.scan_csv(
                file_path,
                try_parse_dates=True,
                schema_overrides=csv_numeric_overrides,
            )
        )
        cols = set(lf.collect_schema().names())
        required = {
            "reference_date",
            "investor_type_raw",
            "mtd_purchases_k_brl",
            "mtd_sales_k_brl",
        }
        missing = required - cols
        if missing:
            raise ValueError(
                f"Backfill file {file_path.name} missing required columns: {sorted(missing)}"
            )

        exprs: list[pl.Expr] = [
            (
                pl.col("publication_date").cast(pl.Date)
                if "publication_date" in cols
                else pl.col("reference_date").cast(pl.Date)
            ).alias("publication_date"),
            pl.col("reference_date").cast(pl.Date).alias("reference_date"),
            pl.col("investor_type_raw").cast(pl.String).str.strip_chars().alias("investor_type_raw"),
            pl.col("mtd_purchases_k_brl").cast(pl.Float64).alias("mtd_purchases_k_brl"),
            (
                pl.col("purchase_share_pct").cast(pl.Float64)
                if "purchase_share_pct" in cols
                else pl.lit(None, dtype=pl.Float64)
            ).alias("purchase_share_pct"),
            pl.col("mtd_sales_k_brl").cast(pl.Float64).alias("mtd_sales_k_brl"),
            (
                pl.col("sale_share_pct").cast(pl.Float64)
                if "sale_share_pct" in cols
                else pl.lit(None, dtype=pl.Float64)
            ).alias("sale_share_pct"),
            pl.lit("Backfill oficial B3 importado da camada landing").alias("source_note_pt"),
            pl.lit("BACKFILL").alias("bdi_limit_date"),
            pl.lit("b3_official_backfill").alias("_source_system"),
            pl.lit(str(file_path)).alias("_source_url"),
            pl.lit(file_path.name).alias("_payload_hash"),
            pl.lit(ingested_at).cast(pl.Datetime("us", "UTC")).alias("_ingested_at"),
        ]
        frames.append(lf.select(exprs))

    return pl.concat(frames, how="vertical").collect()
