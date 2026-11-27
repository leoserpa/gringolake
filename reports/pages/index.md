---
title: Panorama — GringoLake
---

```sql kpi_latest
WITH agg AS (
    SELECT COUNT(*) AS total_pregoes
    FROM gringolake.mart_ibov_vs_investors_wide
),
ultimo AS (
    SELECT
        trading_date,
        ibov_close,
        ibov_return_1d_pct,
        estrang_cum_bi_brl,
        pf_cum_bi_brl,
        instit_cum_bi_brl,
        inst_fin_cum_bi_brl
    FROM gringolake.mart_ibov_vs_investors_wide
    ORDER BY trading_date DESC
    LIMIT 1
)
SELECT
    u.*,
    a.total_pregoes
FROM ultimo u
CROSS JOIN agg a
```

<div class="page-hero">
  <p class="page-eyebrow">GRINGOLAKE · B3 OFICIAL</p>

  <div class="page-head-row">
    <div class="page-title-group">
      <h1 class="page-title">Fluxo de Capital na B3</h1>
      <p class="page-subtitle">Quem está comprando e vendendo na bolsa · Acumulado oficial B3 (BDI D+2) em R$ bi vs. Ibovespa</p>
    </div>

    <div class="controls-right">
      <ButtonGroup name=janela_panorama>
        <ButtonGroupItem valueLabel="30 pregões" value="45" />
        <ButtonGroupItem valueLabel="160 pregões" value="240" default />
        <ButtonGroupItem valueLabel="Máx" value="36500" />
      </ButtonGroup>

      <CounterBadge data={kpi_latest} value="total_pregoes" label="Pregões" decimals={0} />
    </div>
  </div>
</div>

<div class="kpi-grid-4">
  <KPITerminalCard data={kpi_latest} value="ibov_close" dateCol="trading_date" code="IBOV" title="Ibovespa" suffix=" pts" decimals={0} subtitle="Fechamento oficial B3" />
  <KPITerminalCard data={kpi_latest} value="estrang_cum_bi_brl" dateCol="trading_date" code="ESTRANG" title="Estrangeiro Acum." prefix="R$ " suffix=" bi" decimals={2} signed={true} subtitle="Acumulado na série (BDI)" focalWhenPositive={true} />
  <KPITerminalCard data={kpi_latest} value="pf_cum_bi_brl" dateCol="trading_date" code="PF" title="Pessoa Física Acum." prefix="R$ " suffix=" bi" decimals={2} signed={true} subtitle="Acumulado na série (BDI)" focalWhenPositive={true} />
  <KPITerminalCard data={kpi_latest} value="instit_cum_bi_brl" dateCol="trading_date" code="INSTIT" title="Institucional Acum." prefix="R$ " suffix=" bi" decimals={2} signed={true} subtitle="Acumulado na série (BDI)" focalWhenPositive={true} />
</div>

```sql serie_comparativa
WITH limite AS (
    SELECT MAX(trading_date) AS max_dt FROM gringolake.mart_ibov_vs_investors_wide
)
SELECT
    w.trading_date,
    w.ibov_close,
    w.ma21_window_obs_count,
    w.estrang_cum_bi_brl,
    w.estrang_cum_ma21_bi_brl,
    w.pf_cum_bi_brl,
    w.pf_cum_ma21_bi_brl,
    w.instit_cum_bi_brl,
    w.instit_cum_ma21_bi_brl,
    w.inst_fin_cum_bi_brl,
    w.inst_fin_cum_ma21_bi_brl
FROM gringolake.mart_ibov_vs_investors_wide w
CROSS JOIN limite l
WHERE date_diff('day', w.trading_date, l.max_dt) <= CAST('${inputs.janela_panorama}' AS INTEGER)
ORDER BY w.trading_date
```

<div class="terminal-grid-2">
  <section class="terminal-panel">
    <TradingViewDualAxisChart
      data={serie_comparativa}
      panelIndex="01"
      panelTitle="Os estrangeiros estão comprando ou vendendo?"
      panelSubtitle="Fluxo estrangeiro acumulado (âmbar, R$ bi) vs. Ibovespa (prata) · Role para zoom"
      flowCol="estrang_cum_bi_brl"
      flowName="Estrangeiro"
      maCol="estrang_cum_ma21_bi_brl"
      maObsCol="ma21_window_obs_count"
      maName="MM 21d"
      ibovCol="ibov_close"
      ibovName="IBOV (pts)"
      focal={true}
      height={220}
    />
  </section>

  <section class="terminal-panel">
    <TradingViewDualAxisChart
      data={serie_comparativa}
      panelIndex="02"
      panelTitle="Como a Pessoa Física está posicionada na B3?"
      panelSubtitle="Fluxo acumulado da Pessoa Física (âmbar, R$ bi) vs. Ibovespa (prata) · Role para zoom"
      flowCol="pf_cum_bi_brl"
      flowName="Pessoa Física"
      maCol="pf_cum_ma21_bi_brl"
      maObsCol="ma21_window_obs_count"
      maName="MM 21d"
      ibovCol="ibov_close"
      ibovName="IBOV (pts)"
      height={220}
    />
  </section>
</div>

<div class="terminal-grid-2">
  <section class="terminal-panel">
    <TradingViewDualAxisChart
      data={serie_comparativa}
      panelIndex="03"
      panelTitle="O institucional está entrando ou saindo?"
      panelSubtitle="Fluxo institucional acumulado (âmbar, R$ bi) vs. Ibovespa (prata) · Role para zoom"
      flowCol="instit_cum_bi_brl"
      flowName="Institucional"
      maCol="instit_cum_ma21_bi_brl"
      maObsCol="ma21_window_obs_count"
      maName="MM 21d"
      ibovCol="ibov_close"
      ibovName="IBOV (pts)"
      height={220}
    />
  </section>

  <section class="terminal-panel">
    <TradingViewDualAxisChart
      data={serie_comparativa}
      panelIndex="04"
      panelTitle="Como atuam as Instituições Financeiras?"
      panelSubtitle="Fluxo acumulado de Inst. Financeiras (âmbar, R$ bi) vs. Ibovespa (prata) · Role para zoom"
      flowCol="inst_fin_cum_bi_brl"
      flowName="Inst. Financeira"
      maCol="inst_fin_cum_ma21_bi_brl"
      maObsCol="ma21_window_obs_count"
      maName="MM 21d"
      ibovCol="ibov_close"
      ibovName="IBOV (pts)"
      height={220}
    />
  </section>
</div>

```sql fluxo_mensal_ibov
WITH last_flow AS (
    SELECT
        strftime(trading_date, '%Y-%m') AS mes,
        investor_type_code,
        LAST(mtd_net_flow_k_brl ORDER BY trading_date) AS mtd_k_brl,
        MAX(trading_date) AS max_dt
    FROM gringolake.int_b3_investor_flow_daily
    GROUP BY 1, 2
),
ibov_m AS (
    SELECT
        strftime(trading_date, '%Y-%m') AS mes,
        LAST(ibov_close ORDER BY trading_date) AS close_end
    FROM gringolake.stg_b3_ibov_daily
    GROUP BY 1
),
ibov_ret AS (
    SELECT
        mes,
        ROUND(((close_end / LAG(close_end) OVER (ORDER BY mes)) - 1.0) * 100.0, 2) AS ibov_month_pct
    FROM ibov_m
)
SELECT
    f.mes,
    MAX(f.max_dt) AS ate_pregao,
    MAX(CASE WHEN f.investor_type_code = 'estrangeiro' THEN f.mtd_k_brl END) AS estrang_k_brl,
    MAX(CASE WHEN f.investor_type_code = 'institucional' THEN f.mtd_k_brl END) AS instit_k_brl,
    MAX(CASE WHEN f.investor_type_code = 'pessoa_fisica' THEN f.mtd_k_brl END) AS pf_k_brl,
    MAX(CASE WHEN f.investor_type_code = 'instituicoes_financeiras' THEN f.mtd_k_brl END) AS inst_fin_k_brl,
    MAX(i.ibov_month_pct) AS ibov_month_pct
FROM last_flow f
LEFT JOIN ibov_ret i ON f.mes = i.mes
GROUP BY f.mes
ORDER BY f.mes DESC
```

<MonthlyFlowTable data={fluxo_mensal_ibov} panelIndex="05" />

```sql explorador_perfis
WITH ultimo_pregao AS (
    SELECT MAX(trading_date) AS max_dt FROM gringolake.fct_ibov_investor_flow_daily
)
SELECT
    f.trading_date,
    f.investor_type_short_pt,
    f.investor_type_name_pt,
    f.daily_net_flow_bi_brl,
    f.mtd_net_flow_bi_brl,
    f.cum_net_flow_bi_brl,
    f.cum_net_flow_ma21_bi_brl,
    f.purchase_share_pct,
    f.flow_vs_ma21_signal
FROM gringolake.fct_ibov_investor_flow_daily f
INNER JOIN ultimo_pregao u ON f.trading_date = u.max_dt
ORDER BY f.display_order
```

<FlowExplorerTable
  data={explorador_perfis}
  panelIndex="06"
  title="Qual a posição atual de cada perfil no último pregão?"
  subtitle="Saldos diário, mensal (MTD) e acumulado em R$ bi por categoria B3 · MM21 ativa com 21 pregões completos"
/>
