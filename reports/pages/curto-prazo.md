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
      <ButtonGroup name=exibir_faixas>
        <ButtonGroupItem valueLabel="Faixas P.F. < MM21" value="1" default />
        <ButtonGroupItem valueLabel="Sem faixas" value="0" />
      </ButtonGroup>

      <CounterBadge data={pf_kpis} value="total_pregoes" label="Pregões" decimals={0} />
    </div>
  </div>
</div>

<div class="kpi-grid-4">
  <KPITerminalCard data={pf_kpis} value="ibov_close" dateCol="trading_date" code="IBOV" title="Ibovespa Fechamento" suffix=" pts" decimals={0} subtitle="Último pregão B3" liveDot={true} />
  <KPITerminalCard data={pf_kpis} value="pf_cum_short_term_bi_brl" dateCol="trading_date" code="PF CUM" title="Acumulado P.F. (Janela)" prefix="R$ " suffix=" bi" decimals={2} signed={true} subtitle="Base = 0 no início" focalWhenPositive={true} />
  <KPITerminalCard data={pf_kpis} value="pf_cum_short_term_ma21_bi_brl" dateCol="trading_date" code="MM21" title="Média Móvel 21d (P.F.)" prefix="R$ " suffix=" bi" decimals={2} signed={true} alertCol="alerta_mm21" subtitle="Ativa com 21 pregões (ADR-006)" />
  <KPITerminalCard data={pf_kpis} value="daily_net_flow_bi_brl" dateCol="trading_date" code="PF DIA" title="Saldo Diário P.F." prefix="R$ " suffix=" bi" decimals={2} signed={true} subtitle="Compras − Vendas" focalWhenPositive={true} />
</div>

```sql pf_serie_completa
SELECT
    trading_date,
    ibov_close,
    ibov_label_points,
    daily_net_flow_bi_brl,
    pf_cum_short_term_bi_brl,
    pf_cum_short_term_ma21_bi_brl,
    ma21_window_obs_count,
    CASE WHEN '${inputs.exibir_faixas}' = '1' THEN is_pf_below_ma21 ELSE FALSE END AS shade_flag
FROM gringolake.mart_ibov_vs_pf_short_term
ORDER BY trading_date
```

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <TerminalDualAxisChart
      data={pf_serie_completa}
      panelIndex="01"
      panelTitle="A Pessoa Física está acelerando ou perdendo força no curto prazo?"
      panelSubtitle="Fluxo acumulado da P.F. (R$ bi) vs. MM21 e Ibovespa · Use a barra inferior ou scroll para dar zoom nos pregões"
      flowCol="pf_cum_short_term_bi_brl"
      flowName="Acum. P.F."
      maCol="pf_cum_short_term_ma21_bi_brl"
      maObsCol="ma21_window_obs_count"
      maName="MM 21d"
      ibovCol="ibov_close"
      ibovName="IBOV (pts)"
      shadeCol="shade_flag"
      focal={true}
      height="360px"
      zoom={true}
    />
  </section>
</div>

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <TerminalLineChart
      data={pf_serie_completa}
      panelIndex="02"
      panelTitle="Quanto a Pessoa Física comprou ou vendeu em cada pregão?"
      panelSubtitle="Saldo líquido diário da Pessoa Física em R$ bi · Âmbar = compra líquida, grafite = saída líquida (desacumulação MTD)"
      x="trading_date"
      y="daily_net_flow_bi_brl"
      names={['Saldo Diário P.F.']}
      prefix="R$ "
      suffix=" bi"
      decimals={2}
      signed={true}
      chartType="bar"
      axisCompact={true}
      height="250px"
      showEndLabel={false}
    />
  </section>
</div>
