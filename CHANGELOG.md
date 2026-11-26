# Changelog

Todas as mudanças relevantes deste projeto são documentadas neste arquivo.
Ao registrar novas alterações ou correções de documentação, **adicione uma nova entrada datada** — nunca reescreva ou compacte entradas anteriores.

## [Unreleased]

### Fixed
- **Virada de ano no cache do IBOV:** adicionado marcador `.finalized` em `b3_market_data_component.py` para impedir que um ano encerrado parcialmente em dezembro seja pulado permanentemente após 1º de janeiro.
- **Timezone seguro em ambientes UTC:** substituído `date.today()` por `datetime.now(ZoneInfo("America/Sao_Paulo")).date()` em `b3_market_data_component.py`.
- **Lookback `0` explícito:** `resolve_lookback_days()` preserva `lookback_calendar_days=0` (usando padrão apenas quando `None`).
- **Backfill CSV com decimais tardios:** aplicados `schema_overrides` (`pl.Float64`) no `pl.scan_csv` em `parquet_store.py` para evitar falha de inferência após a janela padrão de 100 linhas do Polars.
- **Escape SQL no DuckDB:** escapados apóstrofos (`'`) em `GRINGOLAKE_DATA_DIR` em `export_parquet.sql` e `models/bronze/_sources.yml`.
- **Detecção de drift Git:** `scripts/check_docs_drift.sh` agora reporta `can't tell` em repositórios shallow e quando há alterações locais não commitadas.

### Added
- Teste dbt `relationships` em `stg_b3_investor_flow_mtd.reference_date` → `stg_b3_ibov_daily.trading_date` impedindo descarte silencioso no `INNER JOIN` do calendário.
- Coluna `has_full_ma21_window` (com teste `not_null`) propagada para `gold.mart_ibov_vs_investors_wide` e `gold.mart_ibov_vs_pf_short_term`.
- Novos testes unitários em `tests/test_b3_component_logic.py` e `tests/test_parquet_store.py`.

### Changed
- Padronizados pacote Python (`src/gringolake`), projeto dbt (`dbt_gringolake`), banco analítico (`data/warehouse/gringolake.duckdb`), variáveis de ambiente (`GRINGOLAKE_*`) e toda a documentação para alinhar 100% com o nome do repositório GitHub (`leoserpa/gringolake`).
- Adicionados metadados de licença (`GPL-3.0`) e autoria em `pyproject.toml`, badges técnicos e seção legível de **Licença e Aviso sobre Dados (B3)** no `README.md` (preservando o arquivo `LICENSE` GPLv3 verbatim).

## [0.1.0] - 2026-11-25

### Added
- Projeto Dagster inicializado via `create-dagster` com gerenciamento de dependências `uv` (`Python 3.12`, `Dagster 1.13`, `Polars 2.2`, `DuckDB 2.0`, `dbt-core 1.12`, `dbt-duckdb 1.11`).
- Cliente HTTP oficial da B3 ([`b3_client.py`](src/gringolake/clients/b3_client.py)) com retry exponencial (`tenacity`) para:
  - `GetPortfolioDay` (`IBOV` diário histórico de 2020 ao ano corrente).
  - `BDI SharesInvesVolum` (Participação dos Investidores MTD com extração da `reference_date` real e tratamento de defasagem D+2).
- Escrita atômica Hive-partitioned em Parquet ZSTD e trilha imutável em JSON bruto ([`parquet_store.py`](src/gringolake/storage/parquet_store.py)), incluindo suporte a backfill histórico oficial em `data/landing/b3_investor_flow_backfill/`.
- Componente Dagster [`B3MarketDataComponent`](src/gringolake/components/b3_market_data_component.py) com 2 assets Bronze e 2 Asset Checks (`check_bronze_ibov_quality` e `check_bronze_investor_flow_completeness`).
- Projeto `dbt_gringolake` integrado ao Dagster via `DbtProjectComponent` contendo:
  - Camada Silver: `stg_b3_ibov_daily`, `stg_b3_investor_flow_mtd` e `int_b3_investor_flow_daily` (desacumulação MTD → Diário).
  - Camada Gold: `dim_investor_type`, `fct_ibov_investor_flow_daily` (acumulado + MM21 + topos/fundos locais do IBOV), `mart_ibov_vs_investors_wide` e `mart_ibov_vs_pf_short_term`.
  - Exportação automática de todas as tabelas Silver e Gold para Parquet ZSTD via post-hook dbt.
- Suíte de qualidade com 15 testes unitários Python (`pytest`), 2 dbt unit tests, 38 dbt data tests e teste singular de invariante contábil de soma zero (`assert_b3_daily_flow_zero_sum`).
- Agenda diária `b3_daily_eod_schedule` (`0 21 * * 1-5`, `America/Sao_Paulo`, pós-SLA oficial das 20h da B3).
- Documentação arquitetural completa: ADRs (`docs/decisions/001` a `005`), dicionário de dados (`docs/data-dictionary.md`), guia para agentes (`AGENTS.md`) e script de detecção de drift (`scripts/check_docs_drift.sh`).

### Fixed
- Resolução de caminhos do DuckDB e Parquet ao executar `DbtProjectComponent` via `.local_defs_state` injetando `GRINGOLAKE_DATA_DIR` e `GRINGOLAKE_DUCKDB_PATH` absolutos em `src/gringolake/definitions.py`.
- Removido `from __future__ import annotations` em `b3_market_data_component.py` para permitir resolução em runtime das classes `dg.Config` dentro de `build_defs()`.
- Atualizado `README.md` para exibir comandos diretos via `uv run` sem exigir `make` instalado no ambiente.
