# Changelog

Todas as mudanças relevantes deste projeto são documentadas neste arquivo.
Ao registrar novas alterações ou correções de documentação, **adicione uma nova entrada datada** — nunca reescreva ou compacte entradas anteriores.

## [Unreleased]

### Added (2026-11-27)
- **Novos componentes interativos do dashboard (`reports/components/`):**
  - `TradingViewSeriesChart.svelte`, `TradingViewFlowReturnChart.svelte` e `TradingViewRangeSlider.svelte`: séries temporais e comparativo fluxo estrangeiro × retorno IBOV com **TradingView Lightweight Charts** (zoom, crosshair, legenda interativa e slider sincronizado).
  - `DailyFlowTable.svelte`: tabela diária completa dos 5 perfis em `Fluxo Diário` com busca por perfil/data, cabeçalho fixo, rolagem vertical (`380px`) e exportação CSV.
  - `AnnualIbovTable.svelte`: tabela anual do Ibovespa (2020–2026) em `Ibovespa` com 7 colunas limpas, formatação condicional única em âmbar (`#f2b94b`) para anos positivos, coluna `Ano` fixa no mobile e exportação CSV.
  - `ProfileMenuControl.svelte`: seletor de perfil responsivo no `Comparativo` que mantém a barra de 5 abas no desktop (`> 900px`) e recolhe em um botão/dropdown compacto (`PERFIL | Pessoa Física ⌄`) no mobile (`<= 900px`), com navegação completa por teclado (`Arrow*`/`Home`/`End`/`Escape`) e restauração de foco.
  - `reports/components/formatters.js` e `reports/tests/formatters.test.mjs`: módulo compartilhado de formatação monetária `mi`/`bi`, datas `pt-BR`, pontos, sinais e exportação CSV com testes unitários nativos em `node --test`.
- **Qualidade de frontend no CI (`.github/workflows/ci.yml`):** novo job `frontend-quality` executando testes unitários dos formatadores e build estático estrito do Evidence.dev (`npm run sources:strict && npm run build:strict`) sobre os snapshots Bronze da branch `data-bronze`, além de resumo automático de diagnóstico em caso de falha em `.github/workflows/deploy-pages.yml`.

### Changed (2026-11-27)
- **Escala monetária unificada (`R$ mi` ↔ `R$ bi`) no frontend ([ADR-007](docs/decisions/007-adaptive-brl-scale-and-tradingview-ui.md)):** valores abaixo de `R$ 999,95 mi` são exibidos em `R$ mi` e valores a partir de `R$ 1,00 bi` em `R$ bi` (com `R$ 0` no zero) em KPIs, gráficos TradingView e tabelas (`KPITerminalCard`, `TradingViewDualAxisChart`, `TradingViewSeriesChart`, `MonthlyFlowTable`, `DailyFlowTable`, `FlowExplorerTable`).
- **Refinamento editorial do tema Atelier Graphite (`+layout.svelte` e páginas):** removida numeração `01`–`06` dos títulos dos painéis, redesenhado `CounterBadge` em pílula horizontal inline (`42px`), atualizado rodapé para formato editorial plano sem caixa arredondada, unificado o indicador de procedência no topo (`B3 Oficial | D+2` no desktop, `B3 | D+2` no mobile) e restaurado o `<BarChart>` nativo do Evidence para participação de volume em `Comparativo` (removido `FlowScatterChart.svelte`).
- **Documentação sincronizada:** atualizados `README.md`, `AGENTS.md` e `scripts/check_docs_drift.sh` (incluindo `ADR-006`, contagem atualizada de 45 data tests + 3 unit tests dbt e mapa do frontend `reports/`).

### Changed (2026-11-26)
- **Novos painéis analíticos oficiais da B3 no dashboard:** gráfico de **Volume Financeiro Total da B3 (R$ bi)** com média móvel e destaque de picos em `Fluxo Diário`; **Dispersão (Estrangeiro × Retorno IBOV)** (`FlowScatterChart.svelte`) e **Participação no Volume da B3 (%)** (`MarketShareBarChart.svelte`) em `Comparativo`; **Drawdown Histórico (%)** e **Matriz de Retornos Mensais (2020–2026)** (`IbovMonthlyMatrix.svelte`) em `Ibovespa`.
- **Rigor estatístico da MM21 ([ADR-006](docs/decisions/006-strict-ma21-full-window-and-unified-brl-billions.md)):** `fct_ibov_investor_flow_daily` e `mart_ibov_vs_pf_short_term` passam a retornar `NULL` nas colunas de MM21, `flow_vs_ma21_signal = 'em_formacao'` e `is_pf_below_ma21 = false` enquanto `ma21_window_obs_count < 21`, impedindo sinais direcionais fabricados por médias parciais. Adicionados `ma21_window_obs_count` na camada Gold, o teste singular `assert_ma21_window_integrity` e testes unitários dbt de aquecimento + janela deslizante de 21/22 pregões.
- **Padronização monetária de mesa bancária no dashboard ([ADR-006](docs/decisions/006-strict-ma21-full-window-and-unified-brl-billions.md)):** acumulados e consolidado mensal (`Panorama`, `Curto Prazo`, `Comparativo` e `MonthlyFlowTable`) 100% em **`R$ bi`** (2 casas decimais); fluxo diário isolado (`Fluxo Diário` — KPIs, gráficos, eixos Y e tabela diária) 100% em **`R$ mi`** (1 casa decimal), sem mistura de unidades no mesmo gráfico ou tabela; auditoria soma-zero explicitamente em **`R$ mil`**.
- **Identidade visual Atelier Graphite no Evidence.dev (`reports/`):** fundo grafite fosco `#222222`, cards arredondados `#2B2B2B` (`28px`/`24px`), acento focal único `#F2B94B` (Tufte/Knaflic), tipografia `Plus Jakarta Sans` + `JetBrains Mono`, barra de navegação fixa de ponta a ponta com trilho central de pílulas e menu hambúrguer mobile, ícones SVG semânticos nos KPIs, tabelas únicas com rolagem horizontal no mobile, `CounterBadge` dinâmico e gráficos interativos limpos sem rótulos flutuantes sobre as curvas.

### Fixed
- **Virada de ano no cache do IBOV:** adicionado marcador `.finalized` em `b3_market_data_component.py` para impedir que um ano encerrado parcialmente em dezembro seja pulado permanentemente após 1º de janeiro.
- **Timezone seguro em ambientes UTC:** substituído `date.today()` por `datetime.now(ZoneInfo("America/Sao_Paulo")).date()` em `b3_market_data_component.py`.
- **Lookback `0` explícito:** `resolve_lookback_days()` preserva `lookback_calendar_days=0` (usando padrão apenas quando `None`).
- **Backfill CSV com decimais tardios:** aplicados `schema_overrides` (`pl.Float64`) no `pl.scan_csv` em `parquet_store.py` para evitar falha de inferência após a janela padrão de 100 linhas do Polars.
- **Escape SQL no DuckDB:** escapados apóstrofos (`'`) em `GRINGOLAKE_DATA_DIR` em `export_parquet.sql` e `models/bronze/_sources.yml`.
- **Detecção de drift Git:** `scripts/check_docs_drift.sh` agora reporta `can't tell` em repositórios shallow e quando há alterações locais não commitadas.

### Added
- Componente **`MonthlyFlowTable`** (`reports/components/MonthlyFlowTable.svelte`) exibindo a tabela **Fluxo Mensal Consolidado por Tipo de Investidor × Retorno do Ibovespa** (`Estrangeiro`, `Institucional`, `Pessoa Física`, `Inst. Financeira` via último saldo oficial MTD da B3 no mês + retorno mensal fechamento/fechamento do IBOV, com formatação automática `R$ bi`/`R$ mi` e exportação CSV), integrado nas páginas `Panorama` e `Fluxo Diário`.
- Página **`Fluxo Diário`** (`reports/pages/fluxo-diario.md`) com os 4 gráficos de barras de **Entradas e Saídas Diárias na B3** em `R$ milhões` (**Estrangeiro (Gringo)**, **Pessoa Física (PF)**, **Institucional (Fundos)** e **Inst. Financeira**), KPIs do último pregão, seletor de janela (`20` / `60` / `Máx` pregões) e tabela diária dos 5 perfis oficiais.
- Persistência automática da camada Bronze na branch órfã `data-bronze` pelo bot diário do GitHub Actions ([`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml)), salvando exclusivamente Parquets ZSTD e marcadores `.finalized` (sem `raw_json/` nem `.duckdb`) para acumular histórico além da janela online `D-21` da B3.
- Workflow de publicação automática no **GitHub Pages** ([`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml)) executando o pipeline Medalhão da B3 (com cache cumulativo da camada Bronze) e publicando o dashboard Evidence.dev em `https://leoserpa.github.io/gringolake/` no push e diariamente às 21h BRT (Seg–Sex).
- Dashboard interativo em **Evidence.dev** (`reports/`, **GringoLake Terminal**) com visual dark charcoal (`#0F0F0F` / `#161616`) e acento amarelo (`#FACC15`), lendo diretamente `data/gold/*.parquet` e `data/silver/*.parquet` via DuckDB `:memory:` (sem acoplamento de versão binária do DuckDB e sem lock de escrita). Inclui 5 páginas (`Panorama`, `Curto Prazo`, `Comparativo`, `Ibovespa`, `Linhagem`) e 4 componentes Svelte (`KPITerminalCard`, `TerminalDualAxisChart`, `TerminalLineChart`, `FlowExplorerTable`).
- Workflow de CI automatizado no GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) executando `ruff`, `dg check defs` e `pytest` (incluindo o novo teste E2E offline de toda a cadeia Bronze → Silver → Gold + 41 data tests + 2 dbt unit tests em [`tests/test_medallion_e2e_offline.py`](tests/test_medallion_e2e_offline.py)) a cada push e pull request na branch `main`.
- Teste dbt `relationships` em `stg_b3_investor_flow_mtd.reference_date` → `stg_b3_ibov_daily.trading_date` impedindo descarte silencioso no `INNER JOIN` do calendário.
- Coluna `has_full_ma21_window` (com teste `not_null`) propagada para `gold.mart_ibov_vs_investors_wide` e `gold.mart_ibov_vs_pf_short_term`.
- Novos testes unitários em `tests/test_b3_component_logic.py` e `tests/test_parquet_store.py`.

### Changed
- Migrado o tema do dashboard Evidence.dev para **modo claro editorial** (canvas off-white `#F5F5F4`, cards e gráficos brancos `#FFFFFF`, bordas `#E4E4E7`, tipografia grafite `#18181B` e acento dourado/âmbar `#D97706` com contraste acessível sobre branco).
- Criada marca visual própria em SVG (`reports/static/favicon.svg` e navbar: camadas do lago Medalhão + curva de fluxo dourada) e removida a etiqueta `Terminal` de todos os títulos, cabeçalho, rodapé e badges do dashboard.
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
