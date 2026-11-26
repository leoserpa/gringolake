"""Jobs and schedules for the GringoLake B3 Medallion Lakehouse."""

import dagster as dg

b3_medallion_full_job = dg.define_asset_job(
    name="b3_medallion_full_refresh",
    selection=dg.AssetSelection.groups("bronze", "silver", "gold"),
    description=(
        "Executa o pipeline completo Medalhão (Bronze -> Silver -> Gold) com fontes oficiais "
        "da B3 (IBOV diário + BDI Participação dos Investidores) e validações de qualidade."
    ),
)

b3_bronze_ingestion_job = dg.define_asset_job(
    name="b3_bronze_ingestion",
    selection=dg.AssetSelection.groups("bronze"),
    description="Executa apenas a ingestão oficial B3 para a camada Bronze (Parquet + JSON).",
)

# B3 BDI official SLA metadata reports 20:00:00 BRT; schedule runs at 21:00 BRT on business days.
b3_daily_eod_schedule = dg.ScheduleDefinition(
    name="b3_daily_eod_schedule",
    job=b3_medallion_full_job,
    cron_schedule="0 21 * * 1-5",
    execution_timezone="America/Sao_Paulo",
    description=(
        "Atualização diária do pipeline Medalhão B3 (segunda a sexta às 21h BRT, "
        "após o SLA oficial de divulgação do BDI da B3 às 20h)."
    ),
    tags={"domain": "b3_market_data", "sla": "post_bdi_20h_brt"},
)
