# GringoLake — `data-bronze` Automated Snapshot Branch

This orphan branch is managed automatically by `.github/workflows/deploy-pages.yml`.
It stores compact ZSTD Parquet snapshots of official B3 Bronze partitions (`b3_ibov_daily` and `b3_investor_flow_mtd`) so daily runs retain full history beyond B3 BDI's rolling 21-session API retention window.
