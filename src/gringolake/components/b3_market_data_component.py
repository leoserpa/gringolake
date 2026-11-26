"""Custom Dagster Component for official B3 Bronze layer ingestion.

IMPORTANT: Do NOT add `from __future__ import annotations` to this module.
Because `@dg.asset` functions live inside `build_defs()`, deferred PEP 563
string annotations prevent Dagster from resolving `dg.Config` subclasses at
definition-load time. Keep native Python 3.12 runtime union annotations.

See docs/decisions/002-official-b3-data-sources-only.md for source constraints
(B3 D+2 lag, D-21 rolling retention, and immutable Bronze snapshot strategy).
"""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import dagster as dg
import polars as pl

from gringolake.clients import B3Client
from gringolake.config import get_lakehouse_paths
from gringolake.storage import (
    BRONZE_IBOV_SCHEMA,
    BRONZE_INVESTOR_FLOW_SCHEMA,
    load_optional_investor_backfill,
    write_json_atomic,
    write_parquet_partition_atomic,
)

B3_TIMEZONE = ZoneInfo("America/Sao_Paulo")
FINALIZED_MARKER_NAME = ".finalized"

OFFICIAL_B3_INVESTOR_TYPES = {
    "Investidor Estrangeiro",
    "Institucionais",
    "Investidores Individuais",
    "Instituições Financeiras",
    "Outros",
}


def b3_today() -> date:
    """Return the current calendar date in B3's local timezone (America/Sao_Paulo).

    Avoids premature date/year rollover when executing in UTC containers after 21:00 BRT.
    """
    return datetime.now(B3_TIMEZONE).date()


def resolve_lookback_days(override: int | None, default: int) -> int:
    """Resolve investor flow lookback window while preserving an explicit 0-day override."""
    return override if override is not None else default


def should_skip_cached_year(
    year: int,
    current_year: int,
    partition_file: Path,
    force_refresh_past_years: bool,
) -> bool:
    """Return True only when a past year has both cached Parquet data and a `.finalized` marker.

    Prevents permanently skipping an unfinished year after New Year rollover if its last
    ingestion happened before the final trading day of December.
    """
    if force_refresh_past_years or year >= current_year:
        return False
    finalized_marker = partition_file.parent / FINALIZED_MARKER_NAME
    return partition_file.exists() and finalized_marker.exists()


class IbovBronzeConfig(dg.Config):
    start_year: int | None = None
    end_year: int | None = None
    force_refresh_past_years: bool = False


class InvestorFlowBronzeConfig(dg.Config):
    lookback_calendar_days: int | None = None
    force_refresh_recent_days: int = 5


class B3MarketDataComponent(dg.Component, dg.Model, dg.Resolvable):
    """Ingests official B3 market data (IBOV daily + BDI SharesInvesVolum) into Bronze Parquet."""

    ibov_start_year: int = 2020
    investor_flow_lookback_days: int = 35
    group_name: str = "bronze"
    request_timeout_seconds: float = 20.0

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        default_start_year = self.ibov_start_year
        default_lookback_days = self.investor_flow_lookback_days
        group_name = self.group_name
        timeout_seconds = self.request_timeout_seconds

        ibov_asset_key = dg.AssetKey(["bronze", "b3_ibov_daily"])
        investor_flow_asset_key = dg.AssetKey(["bronze", "b3_investor_flow_mtd"])

        @dg.asset(
            key=ibov_asset_key,
            group_name=group_name,
            kinds={"python", "polars", "parquet"},
            description=(
                "Série histórica oficial diária do Ibovespa (IBOV) extraída diretamente da API "
                "oficial de estatísticas de índices da B3 (GetPortfolioDay), persistida em "
                "Parquet particionado por ano + JSON bruto imutável."
            ),
            tags={"layer": "bronze", "source": "b3_official", "domain": "equities_index"},
        )
        def b3_ibov_daily(
            context: dg.AssetExecutionContext,
            config: IbovBronzeConfig,
        ) -> dg.MaterializeResult:
            paths = get_lakehouse_paths()
            paths.ensure_dirs()

            current_year = b3_today().year
            start_year = config.start_year if config.start_year is not None else default_start_year
            end_year = config.end_year if config.end_year is not None else current_year

            years_written: list[int] = []
            years_skipped: list[int] = []

            with B3Client(timeout_seconds=timeout_seconds) as client:
                for year in range(start_year, end_year + 1):
                    partition_file = paths.bronze_ibov_dir / f"year={year}" / "part-0.parquet"
                    if should_skip_cached_year(
                        year=year,
                        current_year=current_year,
                        partition_file=partition_file,
                        force_refresh_past_years=config.force_refresh_past_years,
                    ):
                        years_skipped.append(year)
                        continue

                    result = client.fetch_ibov_daily_for_year(year=year, index_code="IBOV")
                    if not result.records:
                        context.log.warning(f"No IBOV records returned by B3 for year={year}")
                        continue

                    raw_json_path = paths.bronze_ibov_dir / "raw_json" / f"year={year}.json"
                    write_json_atomic(raw_json_path, result.raw_payload)
                    rows = write_parquet_partition_atomic(
                        records=result.records,
                        schema=BRONZE_IBOV_SCHEMA,
                        target_path=partition_file,
                        sort_by=["trading_date"],
                    )
                    if year < current_year:
                        write_json_atomic(
                            partition_file.parent / FINALIZED_MARKER_NAME,
                            {
                                "year": year,
                                "row_count": rows,
                                "finalized_at_utc": datetime.now(UTC).isoformat(),
                            },
                        )
                    years_written.append(year)
                    context.log.info(
                        f"Wrote {rows} IBOV trading days for year={year} -> {partition_file}"
                    )

            stats = (
                pl.scan_parquet(str(paths.bronze_ibov_dir / "year=*" / "*.parquet"))
                .select(
                    pl.len().alias("row_count"),
                    pl.col("trading_date").min().alias("min_date"),
                    pl.col("trading_date").max().alias("max_date"),
                    pl.col("ibov_close").sort_by("trading_date").last().alias("latest_close"),
                )
                .collect()
                .row(0, named=True)
            )

            return dg.MaterializeResult(
                metadata={
                    "row_count": dg.MetadataValue.int(int(stats["row_count"])),
                    "min_trading_date": dg.MetadataValue.text(str(stats["min_date"])),
                    "max_trading_date": dg.MetadataValue.text(str(stats["max_date"])),
                    "latest_ibov_close": dg.MetadataValue.float(float(stats["latest_close"])),
                    "years_written": dg.MetadataValue.json(years_written),
                    "years_skipped_cached": dg.MetadataValue.json(years_skipped),
                    "bronze_path": dg.MetadataValue.path(str(paths.bronze_ibov_dir)),
                }
            )

        @dg.asset(
            key=investor_flow_asset_key,
            group_name=group_name,
            kinds={"python", "polars", "parquet"},
            description=(
                "Participação dos Investidores (BDI oficial B3 — SharesInvesVolum) em R$ mil "
                "(acumulado no mês MTD com defasagem D+2). Preserva snapshots diários imutáveis "
                "para superar a janela deslizante D-21 da API oficial e suporta backfill oficial "
                "em data/landing/b3_investor_flow_backfill/."
            ),
            tags={"layer": "bronze", "source": "b3_official", "domain": "investor_flow"},
        )
        def b3_investor_flow_mtd(
            context: dg.AssetExecutionContext,
            config: InvestorFlowBronzeConfig,
        ) -> dg.MaterializeResult:
            paths = get_lakehouse_paths()
            paths.ensure_dirs()

            lookback_days = resolve_lookback_days(
                config.lookback_calendar_days, default_lookback_days
            )
            today = b3_today()
            recent_cutoff = today - timedelta(days=config.force_refresh_recent_days)

            partitions_written: list[str] = []
            partitions_skipped: list[str] = []
            empty_dates_count = 0

            with B3Client(timeout_seconds=timeout_seconds) as client:
                for delta in range(lookback_days, -1, -1):
                    pub_date = today - timedelta(days=delta)
                    iso = pub_date.isoformat()
                    partition_file = (
                        paths.bronze_investor_flow_dir
                        / f"publication_date={iso}"
                        / "part-0.parquet"
                    )

                    if partition_file.exists() and pub_date < recent_cutoff:
                        partitions_skipped.append(iso)
                        continue

                    result = client.fetch_investor_flow_mtd_for_date(publication_date=pub_date)
                    if not result.records:
                        empty_dates_count += 1
                        continue

                    raw_json_path = (
                        paths.bronze_investor_flow_dir / "raw_json" / f"publication_date={iso}.json"
                    )
                    write_json_atomic(raw_json_path, result.raw_payload)
                    write_parquet_partition_atomic(
                        records=result.records,
                        schema=BRONZE_INVESTOR_FLOW_SCHEMA,
                        target_path=partition_file,
                        sort_by=["publication_date", "investor_type_raw"],
                    )
                    partitions_written.append(iso)
                    context.log.info(
                        f"Wrote {len(result.records)} rows for pub={iso} "
                        f"(ref={result.reference_date})"
                    )

            backfill_df = load_optional_investor_backfill(paths.landing_investor_backfill_dir)
            backfill_rows = backfill_df.height
            if backfill_rows > 0:
                for (pub_dt,), part_df in backfill_df.group_by("publication_date", maintain_order=True):
                    iso = pub_dt.isoformat()
                    bf_path = (
                        paths.bronze_investor_flow_dir
                        / f"publication_date={iso}"
                        / "part-backfill.parquet"
                    )
                    write_parquet_partition_atomic(
                        records=part_df.to_dicts(),
                        schema=BRONZE_INVESTOR_FLOW_SCHEMA,
                        target_path=bf_path,
                        sort_by=["publication_date", "investor_type_raw"],
                    )
                context.log.info(f"Ingested {backfill_rows} official backfill rows into Bronze.")

            parquet_glob = str(paths.bronze_investor_flow_dir / "publication_date=*" / "*.parquet")
            stats = (
                pl.scan_parquet(parquet_glob)
                .select(
                    pl.len().alias("row_count"),
                    pl.col("reference_date").n_unique().alias("distinct_reference_dates"),
                    pl.col("reference_date").min().alias("min_reference_date"),
                    pl.col("reference_date").max().alias("max_reference_date"),
                    pl.col("publication_date").max().alias("max_publication_date"),
                )
                .collect()
                .row(0, named=True)
            )

            return dg.MaterializeResult(
                metadata={
                    "total_rows_in_bronze": dg.MetadataValue.int(int(stats["row_count"])),
                    "distinct_reference_dates": dg.MetadataValue.int(
                        int(stats["distinct_reference_dates"])
                    ),
                    "min_reference_date": dg.MetadataValue.text(str(stats["min_reference_date"])),
                    "max_reference_date": dg.MetadataValue.text(str(stats["max_reference_date"])),
                    "max_publication_date": dg.MetadataValue.text(
                        str(stats["max_publication_date"])
                    ),
                    "partitions_written": dg.MetadataValue.int(len(partitions_written)),
                    "partitions_skipped_cached": dg.MetadataValue.int(len(partitions_skipped)),
                    "empty_non_trading_dates": dg.MetadataValue.int(empty_dates_count),
                    "backfill_rows_ingested": dg.MetadataValue.int(backfill_rows),
                    "bronze_path": dg.MetadataValue.path(str(paths.bronze_investor_flow_dir)),
                }
            )

        @dg.asset_check(
            asset=ibov_asset_key,
            name="check_bronze_ibov_quality",
            description="Valida integridade estrutural, unicidade de pregões e faixa plausível do IBOV.",
        )
        def check_bronze_ibov_quality() -> dg.AssetCheckResult:
            paths = get_lakehouse_paths()
            lf = pl.scan_parquet(str(paths.bronze_ibov_dir / "year=*" / "*.parquet"))
            metrics = (
                lf.select(
                    pl.len().alias("row_count"),
                    pl.col("trading_date").n_unique().alias("unique_dates"),
                    pl.col("ibov_close").null_count().alias("null_closes"),
                    pl.col("ibov_close").min().alias("min_close"),
                    pl.col("ibov_close").max().alias("max_close"),
                )
                .collect()
                .row(0, named=True)
            )
            passed = (
                metrics["row_count"] > 0
                and metrics["row_count"] == metrics["unique_dates"]
                and metrics["null_closes"] == 0
                and metrics["min_close"] > 10_000.0
            )
            return dg.AssetCheckResult(
                passed=bool(passed),
                metadata={
                    "row_count": int(metrics["row_count"]),
                    "unique_dates": int(metrics["unique_dates"]),
                    "null_closes": int(metrics["null_closes"]),
                    "min_close": float(metrics["min_close"]),
                    "max_close": float(metrics["max_close"]),
                },
            )

        @dg.asset_check(
            asset=investor_flow_asset_key,
            name="check_bronze_investor_flow_completeness",
            description=(
                "Valida presença dos 5 perfis oficiais B3, ausência de volumes negativos e "
                "fechamento da soma de participações percentuais em ~100% no snapshot mais recente."
            ),
        )
        def check_bronze_investor_flow_completeness() -> dg.AssetCheckResult:
            paths = get_lakehouse_paths()
            lf = pl.scan_parquet(
                str(paths.bronze_investor_flow_dir / "publication_date=*" / "*.parquet")
            )
            latest_df = (
                lf.filter(pl.col("publication_date") == pl.col("publication_date").max())
                .select(
                    "publication_date",
                    "reference_date",
                    "investor_type_raw",
                    "mtd_purchases_k_brl",
                    "mtd_sales_k_brl",
                    "purchase_share_pct",
                    "sale_share_pct",
                )
                .collect()
            )
            found_types = set(latest_df["investor_type_raw"].to_list())
            missing_types = sorted(OFFICIAL_B3_INVESTOR_TYPES - found_types)
            min_purchase = float(latest_df["mtd_purchases_k_brl"].min() or 0.0)
            min_sale = float(latest_df["mtd_sales_k_brl"].min() or 0.0)
            total_share = float(
                (latest_df["purchase_share_pct"].sum() or 0.0)
                + (latest_df["sale_share_pct"].sum() or 0.0)
            )
            passed = (
                latest_df.height >= 5
                and len(missing_types) == 0
                and min_purchase >= 0.0
                and min_sale >= 0.0
                and 99.0 <= total_share <= 101.0
            )
            return dg.AssetCheckResult(
                passed=bool(passed),
                metadata={
                    "latest_publication_date": str(latest_df["publication_date"][0]),
                    "latest_reference_date": str(latest_df["reference_date"][0]),
                    "missing_investor_types": missing_types,
                    "total_buy_plus_sell_share_pct": round(total_share, 4),
                    "min_mtd_purchase_k_brl": min_purchase,
                    "min_mtd_sale_k_brl": min_sale,
                },
            )

        return dg.Definitions(
            assets=[b3_ibov_daily, b3_investor_flow_mtd],
            asset_checks=[check_bronze_ibov_quality, check_bronze_investor_flow_completeness],
        )
