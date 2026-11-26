"""Centralized path and pipeline configuration for the GringoLake Medallion Lakehouse."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def resolve_project_root() -> Path:
    """Resolve the repository root directory."""
    env_root = os.getenv("GRINGOLAKE_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class LakehousePaths:
    """Standard Medallion directory layout on local filesystem."""

    root: Path
    landing_dir: Path
    bronze_dir: Path
    silver_dir: Path
    gold_dir: Path
    warehouse_dir: Path
    dbt_project_dir: Path

    @property
    def duckdb_path(self) -> Path:
        return self.warehouse_dir / "gringolake.duckdb"

    @property
    def bronze_ibov_dir(self) -> Path:
        return self.bronze_dir / "b3_ibov_daily"

    @property
    def bronze_investor_flow_dir(self) -> Path:
        return self.bronze_dir / "b3_investor_flow_mtd"

    @property
    def landing_investor_backfill_dir(self) -> Path:
        return self.landing_dir / "b3_investor_flow_backfill"

    def ensure_dirs(self) -> None:
        for path in (
            self.landing_investor_backfill_dir,
            self.bronze_ibov_dir,
            self.bronze_investor_flow_dir,
            self.silver_dir,
            self.gold_dir,
            self.warehouse_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


def get_lakehouse_paths() -> LakehousePaths:
    root = resolve_project_root()
    data_dir = Path(os.getenv("GRINGOLAKE_DATA_DIR", root / "data")).resolve()
    return LakehousePaths(
        root=root,
        landing_dir=data_dir / "landing",
        bronze_dir=data_dir / "bronze",
        silver_dir=data_dir / "silver",
        gold_dir=data_dir / "gold",
        warehouse_dir=data_dir / "warehouse",
        dbt_project_dir=root / "dbt_gringolake",
    )
