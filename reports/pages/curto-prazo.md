---
title: Curto Prazo (IBOV × P.F.) — GringoLake Terminal
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Relação: IBOV × Pessoa Física (Curto Prazo)</h1>
    <p class="page-subtitle">Janela móvel rebased em Pessoa Física com Média Móvel de 21 pregões, cruzamentos destacados e saldo líquido diário</p>
  </div>

  <div class="controls-bar">
    <div class="controls-left">
      <ButtonGroup name=exibir_faixas>
        <ButtonGroupItem valueLabel="Com faixas P.F. < MM21" value="1" default />
        <ButtonGroupItem valueLabel="Sem faixas" value="0" />
      </ButtonGroup>
    </div>

    <div class="controls-right">
      <span class="status-chip"><span class="status-chip-accent">Mart Gold</span> · mart_ibov_vs_pf_short_term</span>
    </div>
  </div>
</div>

```sql pf_kpis
SELECT
    trading_date,
    ibov_close,
    daily_net_flow_bi_brl,
    pf_cum_short_term_bi_brl,
    pf_cum_short_term_ma21_bi_brl,
    CASE WHEN is_pf_below_ma21 THEN 1 ELSE 0 END AS alerta_mm21
FROM gringolake.mart_ibov_vs_pf_short_term
ORDER BY trading_date DESC
LIMIT 1
```

<div class="kpi-grid-4">
  <KPITerminalCard data={pf_kpis} value="ibov_close" dateCol="trading_date" code="IBOV" title="Ibovespa Fechamento" suffix=" pts" decimals={0} subtitle="Último pregão" icon="trend" />
  <KPITerminalCard data={pf_kpis} value="pf_cum_short_term_bi_brl" dateCol="trading_date" code="PF CUM" title="Acumulado P.F. (Janela)" prefix="R$ " suffix=" bi" decimals={2} signed={true} subtitle="Base = 0 no início" icon="users" />
  <KPITerminalCard data={pf_kpis} value="pf_cum_short_term_ma21_bi_brl" dateCol="trading_date" code="MM21" title="Média Móvel 21d (P.F.)" prefix="R$ " suffix=" bi" decimals={2} signed={true} alertCol="alerta_mm21" subtitle="Tendência curto prazo" icon="activity" />
  <KPITerminalCard data={pf_kpis} value="daily_net_flow_bi_brl" dateCol="trading_date" code="PF DIA" title="Saldo Diário P.F." prefix="R$ " suffix=" bi" decimals={2} signed={true} subtitle="Compras − Vendas" icon="flow" />
</div>

```sql pf_serie_completa
SELECT
    trading_date,
    ibov_close,
    ibov_label_points,
    daily_net_flow_bi_brl,
    pf_cum_short_term_bi_brl,
    pf_cum_short_term_ma21_bi_brl,
    CASE WHEN '${inputs.exibir_faixas}' = '1' THEN is_pf_below_ma21 ELSE FALSE END AS shade_flag
FROM gringolake.mart_ibov_vs_pf_short_term
ORDER BY trading_date
```

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <h2 class="terminal-panel-title">IBOV × Acumulado Pessoa Física e MM21 — Visão Expandida com Zoom</h2>
    <p class="terminal-panel-sub">Use o slider ou scroll para dar zoom nos pregões · Caixas sobre o IBOV destacam extremos locais (topos/fundos ±10 pregões)</p>
    <TerminalDualAxisChart
      data={pf_serie_completa}
      flowCol="pf_cum_short_term_bi_brl"
      flowName="Acum. P.F."
      maCol="pf_cum_short_term_ma21_bi_brl"
      maName="MM 21 (P.F.)"
      ibovCol="ibov_close"
      ibovName="IBOV (pts)"
      extremaCol="ibov_label_points"
      shadeCol="shade_flag"
      height="360px"
      zoom={true}
    />
  </section>
</div>

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <h2 class="terminal-panel-title">Saldo Líquido Diário de Pessoa Física na B3 (R$ bi)</h2>
    <p class="terminal-panel-sub">Entradas líquidas diárias (amarelo) vs. saídas líquidas diárias (cinza) derivadas por desacumulação MTD</p>
    <TerminalLineChart
      data={pf_serie_completa}
      x="trading_date"
      y="daily_net_flow_bi_brl"
      names={['Saldo Diário P.F.']}
      prefix="R$ "
      suffix=" bi"
      decimals={2}
      signed={true}
      chartType="bar"
      height="220px"
      showEndLabel={false}
    />
  </section>
</div>
