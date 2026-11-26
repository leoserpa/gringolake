"""Unit tests for atomic Bronze Parquet storage and backfill loader."""

from datetime import UTC, date, datetime

import polars as pl
import pytest

from gringolandia.storage.parquet_store import (
    BRONZE_IBOV_SCHEMA,
    load_optional_investor_backfill,
    write_json_atomic,
    write_parquet_partition_atomic,
)


def test_write_parquet_partition_atomic_is_idempotent(tmp_path):
    target = tmp_path / "year=2026" / "part-0.parquet"
    records = [
        {
            "trading_date": date(2026, 11, 4),
            "index_code": "IBOV",
            "ibov_close_raw": "167.563,47",
            "ibov_close": 167563.47,
            "year": 2026,
            "_source_system": "b3_index_statistics_api",
            "_source_url": "https://example.b3.com.br",
            "_payload_hash": "abc",
            "_ingested_at": datetime(2026, 11, 5, tzinfo=UTC),
        },
        {
            "trading_date": date(2026, 11, 3),
            "index_code": "IBOV",
            "ibov_close_raw": "165.528,92",
            "ibov_close": 165528.92,
            "year": 2026,
            "_source_system": "b3_index_statistics_api",
            "_source_url": "https://example.b3.com.br",
            "_payload_hash": "abc",
            "_ingested_at": datetime(2026, 11, 5, tzinfo=UTC),
        },
    ]

    count = write_parquet_partition_atomic(
        records=records,
        schema=BRONZE_IBOV_SCHEMA,
        target_path=target,
        sort_by=["trading_date"],
    )
    assert count == 2
    assert target.exists()
    assert list(target.parent.glob("*.tmp")) == []

    df = pl.scan_parquet(target).collect()
    assert df["trading_date"].to_list() == [date(2026, 11, 3), date(2026, 11, 4)]


def test_write_json_atomic_preserves_utf8(tmp_path):
    target = tmp_path / "raw.json"
    write_json_atomic(target, {"perfil": "Instituições Financeiras"})
    assert "Instituições Financeiras" in target.read_text(encoding="utf-8")


def test_load_optional_investor_backfill_csv_and_validation(tmp_path):
    empty_df = load_optional_investor_backfill(tmp_path)
    assert empty_df.height == 0

    csv_file = tmp_path / "b3_2021.csv"
    csv_file.write_text(
        "reference_date,investor_type_raw,mtd_purchases_k_brl,mtd_sales_k_brl\n"
        "2021-06-01,Investidores Individuais,4000000,3500000\n",
        encoding="utf-8",
    )
    df = load_optional_investor_backfill(tmp_path)
    assert df.height == 1
    assert df["reference_date"][0] == date(2021, 6, 1)
    assert df["_source_system"][0] == "b3_official_backfill"

    bad_dir = tmp_path / "bad"
    bad_dir.mkdir()
    (bad_dir / "broken.csv").write_text("reference_date,foo\n2021-06-01,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required columns"):
        load_optional_investor_backfill(bad_dir)
