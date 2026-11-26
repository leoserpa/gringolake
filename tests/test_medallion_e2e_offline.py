"""Offline end-to-end Medallion integration test (Bronze Parquet -> dbt Silver/Gold -> DuckDB + Parquet).

Builds a deterministic, zero-sum 25-trading-day official-schema B3 dataset in `tmp_path`
spanning a month transition (Oct -> Nov) and runs `dbt build` (all 7 models, 41 data tests,
and 2 dbt unit tests) without any network calls.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import duckdb
import polars as pl

from gringolake.storage.parquet_store import (
    BRONZE_IBOV_SCHEMA,
    BRONZE_INVESTOR_FLOW_SCHEMA,
    write_parquet_partition_atomic,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt_gringolake"

INVESTOR_PROFILES = [
    ("Investidor Estrangeiro", -200_000.0, 31.0, 31.5),
    ("Institucionais", -100_000.0, 13.0, 13.2),
    ("Investidores Individuais", 250_000.0, 5.2, 4.5),
    ("Instituições Financeiras", 30_000.0, 0.5, 0.5),
    ("Outros", 20_000.0, 0.3, 0.3),
]


def _business_days(start: date, count: int) -> list[date]:
    days: list[date] = []
    cur = start
    while len(days) < count:
        if cur.weekday() < 5 and cur != date(2026, 11, 2):
            days.append(cur)
        cur += timedelta(days=1)
    return days


def test_medallion_end_to_end_offline_dbt_build(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    for sub in (
        "bronze/b3_ibov_daily",
        "bronze/b3_investor_flow_mtd",
        "silver",
        "gold",
        "warehouse",
    ):
        (data_dir / sub).mkdir(parents=True, exist_ok=True)

    # Full IBOV calendar from Oct 1 (matching real B3 GetPortfolioDay), while investor flow
    # starts mid-month on Oct 27 (matching B3's rolling D-21 window).
    ibov_days = _business_days(date(2026, 10, 1), 45)
    trading_days = [dt for dt in ibov_days if dt >= date(2026, 10, 27)][:25]
    ingested_at = datetime(2026, 11, 30, 21, 0, tzinfo=UTC)

    ibov_records = [
        {
            "trading_date": dt,
            "index_code": "IBOV",
            "ibov_close_raw": f"{160_000 + idx * 500:,.2f}",
            "ibov_close": float(160_000 + idx * 500),
            "year": dt.year,
            "_source_system": "b3_index_statistics_api",
            "_source_url": "https://example.b3.com.br/ibov",
            "_payload_hash": "synthetic",
            "_ingested_at": ingested_at,
        }
        for idx, dt in enumerate(ibov_days)
    ]
    write_parquet_partition_atomic(
        records=ibov_records,
        schema=BRONZE_IBOV_SCHEMA,
        target_path=data_dir / "bronze/b3_ibov_daily/year=2026/part-0.parquet",
        sort_by=["trading_date"],
    )

    # Seed mid-month October MTD balance so 2026-10-27 is detected as missing_prior_trading_day,
    # 2026-10-28..30 are mtd_diff_exact, and 2026-11-03 resets as month_start_exact.
    mtd_purch: dict[str, float] = {name: 50_000_000.0 for name, *_ in INVESTOR_PROFILES}
    mtd_sales: dict[str, float] = {name: 50_000_000.0 for name, *_ in INVESTOR_PROFILES}
    prev_month = trading_days[0].month

    for dt in trading_days:
        if dt.month != prev_month:
            mtd_purch = {name: 0.0 for name, *_ in INVESTOR_PROFILES}
            mtd_sales = {name: 0.0 for name, *_ in INVESTOR_PROFILES}
            prev_month = dt.month

        pub_dt = dt + timedelta(days=2)
        day_records = []
        for name, net_k, buy_pct, sell_pct in INVESTOR_PROFILES:
            base_vol = 5_000_000.0
            daily_buy = base_vol + max(net_k, 0.0)
            daily_sell = base_vol + max(-net_k, 0.0)
            mtd_purch[name] += daily_buy
            mtd_sales[name] += daily_sell
            day_records.append(
                {
                    "publication_date": pub_dt,
                    "reference_date": dt,
                    "investor_type_raw": name,
                    "mtd_purchases_k_brl": mtd_purch[name],
                    "purchase_share_pct": buy_pct,
                    "mtd_sales_k_brl": mtd_sales[name],
                    "sale_share_pct": sell_pct,
                    "source_note_pt": (
                        f"Dados acumulados do início do mês até o dia {dt.strftime('%d/%m/%Y')}."
                    ),
                    "bdi_limit_date": "D-21",
                    "_source_system": "b3_bdi_api",
                    "_source_url": "https://example.b3.com.br/bdi",
                    "_payload_hash": "synthetic",
                    "_ingested_at": ingested_at,
                }
            )

        write_parquet_partition_atomic(
            records=day_records,
            schema=BRONZE_INVESTOR_FLOW_SCHEMA,
            target_path=(
                data_dir
                / "bronze/b3_investor_flow_mtd"
                / f"publication_date={pub_dt.isoformat()}"
                / "part-0.parquet"
            ),
            sort_by=["publication_date", "investor_type_raw"],
        )

    duckdb_path = data_dir / "warehouse/gringolake.duckdb"
    dbt_bin = shutil.which("dbt") or str(Path(sys.executable).parent / "dbt")

    env = os.environ.copy()
    env["GRINGOLAKE_DATA_DIR"] = str(data_dir)
    env["GRINGOLAKE_DUCKDB_PATH"] = str(duckdb_path)

    proc = subprocess.run(
        [dbt_bin, "build", "--profiles-dir", ".", "--target-path", str(tmp_path / "dbt_target")],
        cwd=DBT_PROJECT_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"dbt build failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    # Verify DuckDB & Parquet parity and MA21 warm-up transition
    con = duckdb.connect(str(duckdb_path), read_only=True)
    try:
        # 25 trading days total: day 1 (mid-month Oct) is missing_prior_trading_day -> 24 valid Gold days
        wide_df = pl.scan_parquet(data_dir / "gold/mart_ibov_vs_investors_wide.parquet").sort(
            "trading_date"
        ).collect()
        pf_df = pl.scan_parquet(data_dir / "gold/mart_ibov_vs_pf_short_term.parquet").sort(
            "trading_date"
        ).collect()

        assert wide_df.height == 24
        assert pf_df.height == 24
        assert wide_df["has_full_ma21_window"].to_list()[:20] == [False] * 20
        assert wide_df["has_full_ma21_window"].to_list()[20:] == [True] * 4
        assert pf_df["has_full_ma21_window"].to_list()[:20] == [False] * 20
        assert pf_df["has_full_ma21_window"].to_list()[20:] == [True] * 4

        db_wide_cnt = con.execute("SELECT count(*) FROM gold.mart_ibov_vs_investors_wide").fetchone()[0]
        assert db_wide_cnt == wide_df.height
    finally:
        con.close()
