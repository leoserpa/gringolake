---
title: Ibovespa Histórico — GringoLake
---

```sql ibov_filtrado
WITH limite AS (
    SELECT MAX(trading_date) AS max_dt FROM gringolake.stg_b3_ibov_daily
)
SELECT
    s.trading_date,
    s.trading_year,
    s.ibov_close,
    s.ibov_return_1d_pct
FROM gringolake.stg_b3_ibov_daily s
CROSS JOIN limite l
WHERE date_diff('day', s.trading_date, l.max_dt) <= CAST('${inputs.horizonte_ibov}' AS INTEGER)
ORDER BY s.trading_date
```

```sql ibov_kpis
SELECT
    COUNT(*) AS pregoes_janela,
    MAX(trading_date) AS ultima_data,
    LAST(ibov_close ORDER BY trading_date) AS fechamento_atual,
    LAST(ibov_return_1d_pct ORDER BY trading_date) AS retorno_1d,
    MAX(ibov_close) AS maxima_periodo,
    MIN(ibov_close) AS minima_periodo
FROM ${ibov_filtrado}
```

<div class="page-hero">
  <p class="page-eyebrow">GRINGOLAKE · IBOVESPA OFICIAL</p>

  <div class="page-head-row">
    <div class="page-title-group">
      <h1 class="page-title">Ibovespa Histórico</h1>
      <p class="page-subtitle">Fechamento oficial diário da B3 (GetPortfolioDay) utilizado como calendário âncora da desacumulação MTD</p>
    </div>

    <div class="controls-right">
      <ButtonGroup name=horizonte_ibov>
        <ButtonGroupItem valueLabel="1 Ano" value="365" />
        <ButtonGroupItem valueLabel="2 Anos" value="730" />
        <ButtonGroupItem valueLabel="5 Anos" value="1825" default />
        <ButtonGroupItem valueLabel="Máx (2020+)" value="36500" />
      </ButtonGroup>

      <CounterBadge data={ibov_kpis} value="pregoes_janela" label="Pregões" decimals={0} />
    </div>
  </div>
</div>

<div class="kpi-grid-4">
  <KPITerminalCard data={ibov_kpis} value="fechamento_atual" dateCol="ultima_data" code="IBOV" title="Fechamento Atual" suffix=" pts" decimals={0} subtitle="Último pregão B3" liveDot={true} focal={true} />
  <KPITerminalCard data={ibov_kpis} value="retorno_1d" dateCol="ultima_data" code="1D" title="Variação Diária" suffix="%" decimals={2} signed={true} subtitle="Retorno 1 pregão" focalWhenPositive={true} />
  <KPITerminalCard data={ibov_kpis} value="maxima_periodo" code="MAX" title="Máxima na Janela" suffix=" pts" decimals={0} subtitle="Fechamento mais alto" />
  <KPITerminalCard data={ibov_kpis} value="minima_periodo" code="MIN" title="Mínima na Janela" suffix=" pts" decimals={0} subtitle="Fechamento mais baixo" />
</div>

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <TerminalLineChart
      data={ibov_filtrado}
      panelIndex="01"
      panelTitle="Evolução do Ibovespa no Horizonte Selecionado"
      panelSubtitle="Pontos de fechamento oficial diário da B3 (stg_b3_ibov_daily)"
      x="trading_date"
      y="ibov_close"
      names={['Ibovespa']}
      colors={['#f2b94b']}
      suffix=" pts"
      decimals={0}
      height="350px"
    />
  </section>
</div>

```sql resumo_anual_ibov
SELECT
    trading_year AS ano,
    COUNT(*) AS pregoes,
    ROUND(FIRST(ibov_close ORDER BY trading_date), 2) AS primeiro_fechamento,
    ROUND(LAST(ibov_close ORDER BY trading_date), 2) AS ultimo_fechamento,
    ROUND(MIN(ibov_close), 2) AS minima,
    ROUND(MAX(ibov_close), 2) AS maxima,
    ROUND(((LAST(ibov_close ORDER BY trading_date) / FIRST(ibov_close ORDER BY trading_date)) - 1.0) * 100.0, 2) AS retorno_anual_pct
FROM gringolake.stg_b3_ibov_daily
GROUP BY trading_year
ORDER BY trading_year DESC
```

<section class="terminal-panel">
  <h2 class="terminal-panel-title"><span class="panel-index">02</span><span>Resumo Anual do Ibovespa (B3 Oficial)</span></h2>
  <p class="terminal-panel-sub">Contagem oficial de pregões, extremos de fechamento e variação percentual por ano calendário</p>
  <DataTable data={resumo_anual_ibov} rows=10>
    <Column id=ano title="Ano" fmt=id />
    <Column id=pregoes title="Pregões" fmt=num0 />
    <Column id=primeiro_fechamento title="Abertura Ano" fmt=num0 />
    <Column id=ultimo_fechamento title="Último Fech." fmt=num0 />
    <Column id=minima title="Mínima" fmt=num0 />
    <Column id=maxima title="Máxima" fmt=num0 />
    <Column id=retorno_anual_pct title="Variação (%)" fmt=num2 />
  </DataTable>
</section>
