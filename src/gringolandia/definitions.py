"""Dagster Definitions entrypoint for the Gringolândia Medallion Lakehouse."""

import os
from pathlib import Path

from dagster import definitions, load_from_defs_folder

from gringolandia.config import get_lakehouse_paths


@definitions
def defs():
    """Load all Dagster definitions from `src/gringolandia/defs/`.

    IMPORTANT: DbtProjectComponent copies the dbt project into
    `src/gringolandia/defs/.local_defs_state/...` during execution. Injecting
    absolute paths via `os.environ.setdefault` ensures DuckDB and Parquet I/O
    always target the repository's `data/` directory rather than `.local_defs_state`.
    See docs/decisions/004-dual-storage-duckdb-and-zstd-parquet.md.
    """
    paths = get_lakehouse_paths()
    paths.ensure_dirs()
    os.environ.setdefault("GRINGOLANDIA_DATA_DIR", str(paths.bronze_dir.parent))
    os.environ.setdefault("GRINGOLANDIA_DUCKDB_PATH", str(paths.duckdb_path))
    return load_from_defs_folder(path_within_project=Path(__file__).parent)
