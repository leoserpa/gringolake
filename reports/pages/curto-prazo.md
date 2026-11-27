---
title: Curto Prazo (IBOV × P.F.) — GringoLake
---

```sql pf_kpis
WITH agg AS (
    SELECT COUNT(*) AS total_pregoes
    FROM gringolake.mart_ibov_vs_pf_short_term
),
ultimo AS (
    SELECT
        trading_date,
        ibov_close,
        daily_net_flow_bi_brl,
        pf_cum_short_term_bi_brl,
        pf_cum_short_term_ma21_bi_brl,
        ma21_window_obs_count,
        CASE WHEN is_pf_below_ma21 THEN 1 ELSE 0 END AS alerta_mm21
    FROM gringolake.mart_ibov_vs_pf_short_term
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
  <p class="page-eyebrow">GRINGOLAKE · CURTO PRAZO</p>

  <div class="page-head-row">
    <div class="page-title-group">
      <h1 class="page-title">IBOV × Pessoa Física</h1>
      <p class="page-subtitle">Fluxo acumulado da Pessoa Física em R$ bilhões contra a MM21 estrita (21 pregões completos) e o Ibovespa</p>
    </div>

    <div class="controls-right">
      <ButtonGroup name=janela_curto_prazo>
        <ButtonGroupItem valueLabel="60d" value="60" default />
        <ButtonGroupItem valueLabel="160d" value="160" />
        <ButtonGroupItem valueLabel="Máx" value="9999" />
      </ButtonGroup>

      <CounterBadge data={pf_kpis} value="total_pregoes" label="Pregões" decimals={0} />
    </div>
  </div>
</div>

<div class="kpi-grid-4">
  <KPITerminalCard data={pf_kpis} value="ibov_close" dateCol="trading_date" code="IBOV" title="Ibovespa Fechamento" suffix=" pts" decimals={0} subtitle="Último pregão B3" />
  <KPITerminalCard data={pf_kpis} value="pf_cum_short_term_bi_brl" dateCol="trading_date" code="PF CUM" title="Acumulado P.F. (Janela)" prefix="R$ " suffix=" bi" decimals={2} signed={true} subtitle="Base = 0 no início" focalWhenPositive={true} />
  <KPITerminalCard data={pf_kpis} value="pf_cum_short_term_ma21_bi_brl" dateCol="trading_date" code="MM21" title="Média Móvel 21d (P.F.)" prefix="R$ " suffix=" bi" decimals={2} signed={true} alertCol="alerta_mm21" subtitle="Ativa com 21 pregões (ADR-006)" />
  <KPITerminalCard data={pf_kpis} value="daily_net_flow_bi_brl" dateCol="trading_date" code="PF DIA" title="Saldo Diário P.F." prefix="R$ " suffix=" bi" decimals={2} signed={true} subtitle="Compras − Vendas" focalWhenPositive={true} />
</div>

```sql pf_serie_completa
WITH janela AS (
    SELECT trading_date
    FROM gringolake.mart_ibov_vs_pf_short_term
    ORDER BY trading_date DESC
    LIMIT CAST('${inputs.janela_curto_prazo}' AS INTEGER)
)
SELECT
    m.trading_date,
    m.ibov_close,
    m.ibov_label_points,
    m.daily_net_flow_bi_brl,
    m.pf_cum_short_term_bi_brl,
    m.pf_cum_short_term_ma21_bi_brl,
    m.ma21_window_obs_count
FROM gringolake.mart_ibov_vs_pf_short_term m
INNER JOIN janela j ON m.trading_date = j.trading_date
ORDER BY m.trading_date ASC
```

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <TradingViewDualAxisChart
      data={pf_serie_completa}
      panelTitle="A Pessoa Física está acelerando ou perdendo força no curto prazo?"
      panelSubtitle="Terminal interativo TradingView · Fluxo acumulado P.F. (âmbar, R$ mi / bi) vs. MM21 e Ibovespa (prata) · Role para zoom ou use + / −"
      flowCol="pf_cum_short_term_bi_brl"
      flowName="Acum. P.F."
      maCol="pf_cum_short_term_ma21_bi_brl"
      maObsCol="ma21_window_obs_count"
      maName="MM 21d"
      ibovCol="ibov_close"
      ibovName="IBOV (pts)"
      focal={true}
      defaultZoomPoints={90}
      height={300}
    />
  </section>
</div>

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <TradingViewSeriesChart
      data={pf_serie_completa}
      panelTitle="Quanto a Pessoa Física comprou ou vendeu em cada pregão?"
      panelSubtitle="Saldo líquido diário da Pessoa Física (R$ mi / bi) · Âmbar = compra líquida, grafite = saída líquida (desacumulação MTD)"
      x="trading_date"
      y="daily_net_flow_bi_brl"
      names={['Saldo Diário P.F.']}
      prefix="R$ "
      suffix=" bi"
      decimals={2}
      signed={true}
      chartType="bar"
      axisCompact={true}
      autoScaleUnit={true}
      defaultZoomPoints={60}
      height={240}
    />
  </section>
</div>
