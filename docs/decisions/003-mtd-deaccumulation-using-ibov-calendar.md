# ADR-003: Desacumular o fluxo MTD do BDI usando o calendário oficial de pregões do Ibovespa

## Status
Accepted

## Date
2026-11-25

## Context
A tabela oficial `SharesInvesVolum` do BDI da B3 **não** publica o fluxo isolado de cada dia; ela publica o volume **acumulado desde o início do mês (MTD — Month-To-Date)** em `R$ mil`, junto com uma nota em português no campo `table.texts[0].textPt`:

> `Dados acumulados do início do mês até o dia 23/11/2026.`

Ao inspecionar a transição real entre outubro e novembro de 2026 na API da B3, observou-se dois riscos severos para cálculos acumulados e médias móveis:
1. **Desalinhamento de data (lag D+2):** na data de publicação `2026-11-03` (novembro), o BDI ainda reporta o MTD referente ao pregão `2026-10-29` (outubro). Usar `publication_date` no join com o IBOV deslocaria todas as séries em 2 pregões e quebraria o fechamento mensal.
2. **Início truncado no meio do mês (`D-21`):** o registro mais antigo disponível na janela móvel (ex.: `2026-10-23`) traz o acumulado de todo o mês até aquele dia. Tratá-lo como se fosse o fluxo de um único pregão injetaria um pico artificial de ~17 dias na série acumulada e na MM21.

## Decision
1. Extrair na Bronze a `reference_date` oficial via regex (`DD/MM/YYYY`) sobre `source_note_pt` e deduplicar na Silver (`stg_b3_investor_flow_mtd`) por `(reference_date, investor_type_code)`, priorizando `b3_bdi_api` sobre backfill.
2. Utilizar `stg_b3_ibov_daily` como **calendário oficial de pregões da B3**, derivando `prev_trading_date` e `is_first_trading_day_of_month`.
3. Em `int_b3_investor_flow_daily`, calcular o fluxo diário real com três classificações explícitas em `daily_derivation_method`:
   - `month_start_exact`: quando `is_first_trading_day_of_month = true` → `daily = mtd`.
   - `mtd_diff_exact`: quando o pregão anterior do mês na tabela MTD coincide exatamente com `cal.prev_trading_date` → `daily = mtd[t] - mtd[t-1]`.
   - `missing_prior_trading_day`: quando falta o pregão anterior no meio do mês (ex.: início de janela truncada ou lacuna de coleta) → `daily_* = NULL`.
4. Na Gold (`fct_ibov_investor_flow_daily`), filtrar `daily_net_flow_k_brl IS NOT NULL` antes de computar o acumulado contínuo e a Média Móvel de 21 pregões (`ROWS BETWEEN 20 PRECEDING AND CURRENT ROW`).

## Alternatives Considered

### Usar `publication_date` diretamente e resetar MTD quando o valor diminuir
- Pros: Não depende de regex sobre `textPt` nem de join com calendário do IBOV.
- Cons: Erra o alinhamento temporal com o IBOV em 2 pregões; pode confundir um dia com saldo negativo com reset mensal (ou falhar quando compras MTD crescem em dia 1 de mês muito movimentado).
- Rejected: Matematicamente incorreto e suscetível a erros silenciosos.

### Tratar o primeiro registro disponível de cada mês como fluxo diário
- Pros: Aproveita 100% das linhas da janela `D-21` na Gold sem descartar o primeiro pregão.
- Cons: Contamina a curva acumulada com o saldo de 2 a 3 semanas anteriores concentrado em um único dia.
- Rejected: Preferível perder 1 pregão no bootstrap inicial do que distorcer toda a série acumulada subsequente.

## Consequences
- Os valores diários em `gold.fct_ibov_investor_flow_daily` têm origem auditável e exata, verificada tanto por teste unitário dbt (`test_int_b3_investor_flow_daily_mtd_deaccumulation_and_month_reset`) quanto pela invariante contábil de soma zero.
- O primeiro pregão de um mês incompleto permanece disponível na Silver (`int_b3_investor_flow_daily`) com seus campos `mtd_*` intactos e `daily_derivation_method = 'missing_prior_trading_day'`, garantindo auditabilidade sem poluir a Gold.
- Se houver falha de execução por mais de 21 pregões consecutivos e se abrir uma lacuna no meio de um mês, o primeiro dia após a lacuna será marcado como `missing_prior_trading_day` (comportamento seguro por padrão).
- Depende da continuidade do formato de data `DD/MM/YYYY` no campo `textPt` do BDI; caso a B3 altere esse texto, `reference_date` ficará nulo e falhará nos checks de qualidade.
