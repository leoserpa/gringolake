# AGENTS.md — Guia Operacional para Agentes e Engenheiros

Este arquivo documenta as convenções, comandos verificados, armadilhas conhecidas (*gotchas*) e decisões arquiteturais do repositório **GringoLake**. Consulte os [ADRs](docs/decisions/README.md) antes de propor mudanças estruturais.

## Arquitetura e Mapa do Repositório

```text
src/gringolake/
├── config.py                                  # Resolução centralizada de caminhos do Lakehouse
├── definitions.py                             # Entrypoint Dagster (injeta env vars absolutas p/ dbt)
├── clients/b3_client.py                       # Cliente HTTP oficial B3 (GetPortfolioDay + BDI SharesInvesVolum)
├── storage/parquet_store.py                   # Escrita atômica Parquet ZSTD / JSON + loader de backfill
├── components/b3_market_data_component.py     # Dagster Component da camada Bronze + Asset Checks
└── defs/
    ├── bronze_b3/defs.yaml                    # Instância YAML do B3MarketDataComponent
    ├── dbt_medallion/defs.yaml                # Instância YAML do DbtProjectComponent
    └── schedules.py                           # Jobs e schedule diário pós-SLA B3 (21h BRT)

dbt_gringolake/
├── dbt_project.yml / profiles.yml             # Adapter dbt-duckdb + post-hook de exportação Parquet
├── macros/export_parquet.sql                  # Exporta tabelas Silver/Gold para data/{layer}/*.parquet
├── models/bronze/_sources.yml                 # External Parquet sources ligados aos assets Bronze
├── models/silver/                             # Limpeza, calendário oficial e desacumulação MTD -> Diário
├── models/gold/                               # Dimensão, fato principal e marts prontos para BI
└── tests/assert_b3_daily_flow_zero_sum.sql    # Invariante contábil soma-zero de mercado da B3

docs/
├── decisions/                                 # ADRs numerados (ADR-001 a ADR-005)
└── data-dictionary.md                         # Contratos de schema e grão das camadas Bronze/Silver/Gold
```

## Comandos Verificados

Não assuma que `make` está instalado no host; prefira sempre `uv run`:

| Tarefa | Comando |
| --- | --- |
| Validar componentes e definições Dagster + dbt | `uv run dg check defs` |
| Materializar apenas Bronze | `uv run dg launch --assets bronze/b3_ibov_daily,bronze/b3_investor_flow_mtd` |
| Executar pipeline Medalhão completo (Bronze → Silver → Gold) | `uv run dg launch --job b3_medallion_full_refresh` |
| Executar dbt standalone (build + unit/data tests) | `(cd dbt_gringolake && uv run dbt build --profiles-dir .)` |
| Rodar apenas testes dbt (41 data + 2 unit tests) | `(cd dbt_gringolake && uv run dbt test --profiles-dir .)` |
| Rodar testes unitários Python | `uv run pytest -v` |
| Rodar linter Python | `uv run ruff check src tests` |
| Subir Dagster UI local | `uv run dg dev` |
| Checar drift entre código e documentação | `bash scripts/check_docs_drift.sh` |

## Convenções Obrigatórias

1. **Somente fontes oficiais da B3:** não introduza agregadores terceiros não oficiais (Yahoo Finance, Dados de Mercado, etc.). Veja [ADR-002](docs/decisions/002-official-b3-data-sources-only.md).
2. **Polars sempre em modo lazy:** inicie transformações com `pl.scan_parquet` / `.lazy()` e materialize uma única vez com `.collect()`.
3. **dbt rigoroso:** use `{{ source() }}` e `{{ ref() }}`, aliases explícitos em joins (obrigatório para dbt unit tests) e valide saídas reais com `dbt show` após alterar modelos.
4. **ADRs e Changelog:** qualquer mudança de stack, fonte de dados, regra de desacumulação ou contrato Gold exige um novo ADR (ou superseding) em `docs/decisions/` e entrada datada no topo de `CHANGELOG.md` (nunca reescreva entradas antigas).

## Armadilhas Conhecidas (Known Gotchas)

- **Não adicione `from __future__ import annotations` em `b3_market_data_component.py`:** como `@dg.asset` é definido dentro da closure `build_defs()`, anotações adiadas (PEP 563) fazem o Dagster receber o nome da classe de `dg.Config` como string e falhar com `DagsterInvalidPythonicConfigDefinitionError`. Use sintaxe de união nativa do Python 3.12 (`int | None`) sem future import.
- **Caminhos relativos quebram em `DbtProjectComponent`:** o Dagster copia o projeto dbt para `src/gringolake/defs/.local_defs_state/...` durante execuções. Por isso `definitions.py` injeta `GRINGOLAKE_DATA_DIR` e `GRINGOLAKE_DUCKDB_PATH` absolutos via `os.environ.setdefault()` (veja [ADR-004](docs/decisions/004-dual-storage-duckdb-and-zstd-parquet.md)).
- **Nunca use `publication_date` da B3 no join com o IBOV:** o BDI `SharesInvesVolum` tem lag D+2 e valores acumulados no mês (MTD). A data real do pregão vem da nota oficial em `table.texts[0].textPt` (`reference_date`), e o fluxo diário é derivado apenas em `int_b3_investor_flow_daily` cruzado com `stg_b3_ibov_daily` (veja [ADR-003](docs/decisions/003-mtd-deaccumulation-using-ibov-calendar.md)).
- **Nunca apague partições antigas em `data/bronze/b3_investor_flow_mtd/`:** a API BDI da B3 retém apenas `D-21` pregões online. As partições locais são o histórico permanente do pipeline (veja [ADR-002](docs/decisions/002-official-b3-data-sources-only.md)).
- **Unidades monetárias:** o BDI publica valores em **`R$ mil`** (`*_k_brl`). Para converter para **`R$ bilhões`** (`*_bi_brl`), divida por `1_000_000.0` (`1e6`), não por `1e9`.
