"""Dagster Definitions entrypoint for the GringoLake Medallion Lakehouse."""

import os
from pathlib import Path

from dagster import definitions, load_from_defs_folder

from gringolake.config import get_lakehouse_paths


@definitions
def defs():
    """Load all Dagster definitions from `src/gringolake/defs/`.

    IMPORTANT: DbtProjectComponent copies the dbt project into
    `src/gringolake/defs/.local_defs_state/...` during execution. Injecting
    absolute paths via `os.environ.setdefault` ensures DuckDB and Parquet I/O
    always target the repository's `data/` directory rather than `.local_defs_state`.
    See docs/decisions/004-dual-storage-duckdb-and-zstd-parquet.md.
    """
    paths = get_lakehouse_paths()
    paths.ensure_dirs()
    os.environ.setdefault("GRINGOLAKE_DATA_DIR", str(paths.bronze_dir.parent))
    os.environ.setdefault("GRINGOLAKE_DUCKDB_PATH", str(paths.duckdb_path))
    return load_from_defs_folder(path_within_project=Path(__file__).parent)
