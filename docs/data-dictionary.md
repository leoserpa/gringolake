# Dicionário de Dados — Arquitetura Medalhão (B3)

Referência de grão, chaves primárias, unidades e colunas das camadas **Bronze**, **Silver** e **Gold**.
Todas as tabelas Silver e Gold existem de forma espelhada em `data/warehouse/gringolandia.duckdb` e em `data/{silver,gold}/<tabela>.parquet` (compressão ZSTD).

---

## Camada Bronze (`data/bronze/`)

### `bronze/b3_ibov_daily`
- **Caminho:** `data/bronze/b3_ibov_daily/year=YYYY/part-0.parquet` (+ `raw_json/year=YYYY.json`)
- **Grão:** 1 linha por pregão (`trading_date`)
- **Fonte:** `GET sistemaswebb3-listados.b3.com.br/indexStatisticsProxy/IndexCall/GetPortfolioDay/{b64}`

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `trading_date` | `DATE` | Data oficial do pregão na B3 |
| `index_code` | `STRING` | Código do índice (`IBOV`) |
| `ibov_close_raw` | `STRING` | Valor bruto original formatado pela B3 (ex.: `"100.774,57"`) |
| `ibov_close` | `DOUBLE` | Fechamento oficial do Ibovespa em pontos |
| `year` | `INT32` | Ano calendário (chave de partição Hive) |
| `_source_system` | `STRING` | Identificador da fonte (`b3_index_statistics_api`) |
| `_source_url` | `STRING` | URL exata requisitada |
| `_payload_hash` | `STRING` | Hash SHA-256 do payload JSON bruto |
| `_ingested_at` | `TIMESTAMPTZ` | Timestamp UTC da ingestão |

### `bronze/b3_investor_flow_mtd`
- **Caminho:** `data/bronze/b3_investor_flow_mtd/publication_date=YYYY-MM-DD/part-0.parquet` (+ `raw_json/`)
- **Grão:** 1 linha por `(publication_date, investor_type_raw)`
- **Fonte:** `POST arquivos.b3.com.br/bdi/table/SharesInvesVolum/{YYYY-MM-DD}/{YYYY-MM-DD}/1/50` (ou `b3_official_backfill`)

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `publication_date` | `DATE` | Data de publicação do BDI na B3 (chave de partição Hive; lag D+2) |
| `reference_date` | `DATE` | Data real do pregão extraída da nota oficial em `source_note_pt` |
| `investor_type_raw` | `STRING` | Perfil oficial B3 (`Investidor Estrangeiro`, `Institucionais`, `Investidores Individuais`, `Instituições Financeiras`, `Outros`) |
| `mtd_purchases_k_brl` | `DOUBLE` | Compras acumuladas no mês (MTD) em **R$ mil** |
| `purchase_share_pct` | `DOUBLE` | Participação percentual do perfil no volume de compras |
| `mtd_sales_k_brl` | `DOUBLE` | Vendas acumuladas no mês (MTD) em **R$ mil** |
| `sale_share_pct` | `DOUBLE` | Participação percentual do perfil no volume de vendas |
| `source_note_pt` | `STRING` | Nota oficial em português retornada no payload do BDI |
| `bdi_limit_date` | `STRING` | Metadado de retenção reportado pela B3 (`D-21` ou `BACKFILL`) |
| `_source_system` | `STRING` | `b3_bdi_api` ou `b3_official_backfill` |
| `_source_url` / `_payload_hash` / `_ingested_at` | `STRING` / `TIMESTAMPTZ` | Metadados de linhagem e auditoria |

---

## Camada Silver (`silver.*` / `data/silver/*.parquet`)

### `silver.stg_b3_ibov_daily`
- **Chave primária:** `trading_date`
- **Papel:** Série limpa do IBOV + calendário oficial de pregões da B3 (`trading_month`, `trading_year`, `prev_trading_date`, `prev_ibov_close`, `ibov_return_1d_pct`, `trading_day_num_in_month`, `is_first_trading_day_of_month`).

### `silver.stg_b3_investor_flow_mtd`
- **Chave primária:** `investor_flow_mtd_sk` (`<reference_date>_<investor_type_code>`)
- **Papel:** Deduplica snapshots por `(reference_date, investor_type_code)` priorizando `b3_bdi_api`, mapeia nomes oficiais para `investor_type_code` canônico e calcula `mtd_net_flow_k_brl` e `mtd_net_flow_bi_brl` (`k_brl / 1_000_000`).

### `silver.int_b3_investor_flow_daily`
- **Chave primária:** `investor_flow_daily_sk` (`<trading_date>_<investor_type_code>`)
- **Papel:** Desacumula o MTD mensal para fluxo diário real usando o calendário de `stg_b3_ibov_daily` (veja [ADR-003](decisions/003-mtd-deaccumulation-using-ibov-calendar.md)).

| Coluna-chave | Tipo | Descrição |
| --- | --- | --- |
| `daily_derivation_method` | `STRING` | `month_start_exact` (1º pregão do mês), `mtd_diff_exact` (`mtd[t] - mtd[t-1]`), ou `missing_prior_trading_day` (início truncado / lacuna → valores diários `NULL`) |
| `daily_purchases_k_brl` / `daily_sales_k_brl` | `DOUBLE` | Compras e vendas isoladas do pregão em **R$ mil** |
| `daily_net_flow_k_brl` / `daily_net_flow_bi_brl` | `DOUBLE` | Saldo líquido diário (`compras - vendas`) em **R$ mil** e **R$ bilhões** |

---

## Camada Gold (`gold.*` / `data/gold/*.parquet`)

### `gold.dim_investor_type`
- **Chave primária:** `investor_type_code`
- **Colunas:** `investor_type_code`, `investor_type_name_pt`, `investor_type_short_pt` (`ESTRANG`, `INSTIT.`, `P.F.`, `INST. FIN.`, `OUTROS`), `display_order`, `suggested_color_hex`, `is_primary_chart_group`.

### `gold.fct_ibov_investor_flow_daily`
- **Chave primária:** `fact_ibov_flow_sk` (`<trading_date>_<investor_type_code>`)
- **Filtro:** considera apenas pregões com `daily_net_flow_k_brl IS NOT NULL` (excluindo dias truncados sem pregão anterior).

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `trading_date` | `DATE` | Data oficial do pregão |
| `investor_type_code` / `investor_type_name_pt` / `investor_type_short_pt` | `STRING` | Identificação do perfil de investidor |
| `ibov_close` / `ibov_return_1d_pct` | `DOUBLE` | Fechamento oficial do IBOV (pts) e variação diária (%) |
| `ibov_local_extrema_type` | `STRING` | `'peak'`, `'trough'` ou `NULL` em janela simétrica de `±10` pregões (`var local_extrema_window_days`) |
| `ibov_label_points` | `BIGINT` | Pontuação inteira arredondada nos extremos locais e no último pregão (pronta para rótulos de gráfico) |
| `daily_net_flow_k_brl` / `daily_net_flow_bi_brl` | `DOUBLE` | Saldo líquido do pregão em R$ mil / R$ bilhões |
| `cum_net_flow_k_brl` / `cum_net_flow_bi_brl` | `DOUBLE` | Saldo líquido acumulado contínuo na série |
| `cum_net_flow_ytd_bi_brl` | `DOUBLE` | Saldo líquido acumulado no ano (YTD) em R$ bilhões |
| `cum_net_flow_ma21_k_brl` / `cum_net_flow_ma21_bi_brl` | `DOUBLE` | Média móvel simples de 21 pregões sobre o acumulado (`ROWS BETWEEN 20 PRECEDING AND CURRENT ROW`) |
| `flow_vs_ma21_spread_bi_brl` | `DOUBLE` | Diferença `cum_net_flow_bi_brl - cum_net_flow_ma21_bi_brl` |
| `flow_vs_ma21_signal` | `STRING` | `'acima_mm21'` ou `'abaixo_mm21'` |
| `has_full_ma21_window` | `BOOLEAN` | `true` quando já existem 21 pregões completos na janela da MM21 |

### `gold.mart_ibov_vs_investors_wide`
- **Chave primária:** `trading_date` (1 linha por pregão)
- **Uso:** Gráficos comparativos **`COMPARATIVO: IBOVESPA X ESTRANG X INSTIT. X P.F. - R$ (mil)`**.
- **Colunas:** `trading_date`, `trading_month`, `trading_year`, `ibov_close`, `ibov_return_1d_pct`, `ibov_local_extrema_type`, `ibov_label_points`, `has_full_ma21_window`, além dos trios `*_daily_bi_brl`, `*_cum_bi_brl` e `*_cum_ma21_bi_brl` para os 5 perfis (`estrang`, `instit`, `pf`, `inst_fin`, `outros`) e `*_cum_k_brl` para os 3 perfis principais.

### `gold.mart_ibov_vs_pf_short_term`
- **Chave primária:** `trading_date` (últimos `160` pregões configuráveis via `var short_term_trading_days`)
- **Uso:** Gráfico **`Relação: IBOV x P.F. (CURTO PRAZO)`**.
- **Colunas:** `trading_date`, `ibov_close`, `ibov_return_1d_pct`, `ibov_local_extrema_type`, `ibov_label_points`, `daily_net_flow_k_brl`, `daily_net_flow_bi_brl`, `pf_cum_short_term_k_brl`, `pf_cum_short_term_bi_brl` (rebased no início da janela), `pf_cum_short_term_ma21_k_brl`, `pf_cum_short_term_ma21_bi_brl`, `is_pf_below_ma21`, `has_full_ma21_window`.
