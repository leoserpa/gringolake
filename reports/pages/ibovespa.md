---
title: Ibovespa Histórico — GringoLake
---

```sql ibov_filtrado
WITH limite AS (
    SELECT MAX(trading_date) AS max_dt FROM gringolake.stg_b3_ibov_daily
),
janela AS (
    SELECT
        s.trading_date,
        s.trading_year,
        s.ibov_close,
        s.ibov_return_1d_pct
    FROM gringolake.stg_b3_ibov_daily s
    CROSS JOIN limite l
    WHERE date_diff('day', s.trading_date, l.max_dt) <= CAST('${inputs.horizonte_ibov}' AS INTEGER)
)
SELECT
    trading_date,
    trading_year,
    ibov_close,
    ibov_return_1d_pct,
    ROUND(
        ((ibov_close / MAX(ibov_close) OVER (ORDER BY trading_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)) - 1.0) * 100.0,
        2
    ) AS drawdown_pct
FROM janela
ORDER BY trading_date
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
      <p class="page-subtitle">Tendência, quedas a partir do topo e sazonalidade mensal do índice oficial da B3 (GetPortfolioDay)</p>
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
  <KPITerminalCard data={ibov_kpis} value="fechamento_atual" dateCol="ultima_data" code="IBOV" title="Fechamento Atual" suffix=" pts" decimals={0} subtitle="Último pregão B3" focal={true} />
  <KPITerminalCard data={ibov_kpis} value="retorno_1d" dateCol="ultima_data" code="1D" title="Variação Diária" suffix="%" decimals={2} signed={true} subtitle="Retorno 1 pregão" focalWhenPositive={true} />
  <KPITerminalCard data={ibov_kpis} value="maxima_periodo" code="MAX" title="Máxima na Janela" suffix=" pts" decimals={0} subtitle="Fechamento mais alto" />
  <KPITerminalCard data={ibov_kpis} value="minima_periodo" code="MIN" title="Mínima na Janela" suffix=" pts" decimals={0} subtitle="Fechamento mais baixo" />
</div>

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <TerminalLineChart
      data={ibov_filtrado}
      panelIndex="01"
      panelTitle="Qual a trajetória do Ibovespa no horizonte selecionado?"
      panelSubtitle="Fechamento oficial diário da B3 em pontos (stg_b3_ibov_daily)"
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

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <TerminalLineChart
      data={ibov_filtrado}
      panelIndex="02"
      panelTitle="Quanto o Ibovespa já caiu desde a máxima do período?"
      panelSubtitle="Drawdown percentual a partir do topo acumulado na janela selecionada (0% = máxima da janela)"
      x="trading_date"
      y="drawdown_pct"
      names={['Drawdown IBOV']}
      colors={['#f2b94b']}
      suffix="%"
      decimals={2}
      signed={true}
      height="250px"
    />
  </section>
</div>

```sql matriz_mensal_ibov
WITH mensal AS (
    SELECT
        CAST(EXTRACT(YEAR FROM trading_date) AS INTEGER) AS ano_num,
        CAST(EXTRACT(MONTH FROM trading_date) AS INTEGER) AS mes_num,
        strftime(trading_date, '%Y-%m') AS ym,
        FIRST(ibov_close ORDER BY trading_date) AS first_close,
        LAST(ibov_close ORDER BY trading_date) AS close_end
    FROM gringolake.stg_b3_ibov_daily
    GROUP BY 1, 2, 3
),
retornos_m AS (
    SELECT
        ano_num,
        mes_num,
        ROUND((close_end / COALESCE(LAG(close_end) OVER (ORDER BY ym), first_close)) - 1.0, 4) AS retorno
    FROM mensal
)
SELECT
    CAST(ano_num AS VARCHAR) AS ano,
    ano_num,
    mes_num,
    CASE mes_num
        WHEN 1 THEN 'Jan'
        WHEN 2 THEN 'Fev'
        WHEN 3 THEN 'Mar'
        WHEN 4 THEN 'Abr'
        WHEN 5 THEN 'Mai'
        WHEN 6 THEN 'Jun'
        WHEN 7 THEN 'Jul'
        WHEN 8 THEN 'Ago'
        WHEN 9 THEN 'Set'
        WHEN 10 THEN 'Out'
        WHEN 11 THEN 'Nov'
        WHEN 12 THEN 'Dez'
    END AS mes,
    retorno
FROM retornos_m
WHERE retorno IS NOT NULL
ORDER BY ano_num DESC, mes_num ASC
```

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <h2 class="terminal-panel-title"><span class="panel-index">03</span><span>Quais meses historicamente rendem mais ou menos no Ibovespa?</span></h2>
    <p class="terminal-panel-sub">Mapa de calor (Heatmap) dos retornos mensais oficiais da B3 (Jan/2020 a Nov/2026 · Dez/2026 ainda não iniciado)</p>
    <Heatmap
      data={matriz_mensal_ibov}
      x=mes
      y=ano
      xSort=mes_num
      xSortOrder=asc
      ySort=ano_num
      ySortOrder=desc
      value=retorno
      valueFmt=pct1
      nullsZero=false
      zeroDisplay="0.0%"
      cellHeight=40
      leftPadding=48
      rightPadding=12
      mobileValueLabels=false
      seriesOptions={{
        itemStyle: {
          borderColor: '#2b2b2b',
          borderWidth: 3,
          borderRadius: 6
        },
        label: {
          color: '#f8f8f8',
          fontFamily: 'JetBrains Mono, ui-monospace, monospace',
          fontSize: 11,
          fontWeight: 600
        }
      }}
      echartsOptions={{
        backgroundColor: 'transparent',
        tooltip: {
          backgroundColor: '#222222',
          borderColor: '#45454a',
          textStyle: { color: '#f8f8f8' }
        },
        xAxis: {
          splitArea: { show: false },
          axisLabel: { color: '#d4d4d8', fontFamily: 'Plus Jakarta Sans, system-ui, sans-serif', fontSize: 11.5, fontWeight: 600 }
        },
        yAxis: {
          splitArea: { show: false },
          axisLabel: { color: '#e5e5e5', fontFamily: 'JetBrains Mono, ui-monospace, monospace', fontSize: 11.5, fontWeight: 600 }
        },
        visualMap: [{
          type: 'piecewise',
          orient: 'horizontal',
          left: 'center',
          bottom: 0,
          itemWidth: 14,
          itemHeight: 10,
          itemGap: 10,
          textStyle: { color: '#a3a3a3', fontSize: 11, fontFamily: 'Plus Jakarta Sans, system-ui, sans-serif' },
          pieces: [
            { max: -0.08, label: '< -8%', color: '#991b1b' },
            { min: -0.08, max: -0.03, label: '-8% a -3%', color: '#c0392b' },
            { min: -0.03, max: -0.005, label: '-3% a 0%', color: '#6b282b' },
            { min: -0.005, max: 0.005, label: 'Neutro', color: '#35353c' },
            { min: 0.005, max: 0.03, label: '0% a +3%', color: '#1b5e44' },
            { min: 0.03, max: 0.08, label: '+3% a +8%', color: '#1c8c5e' },
            { min: 0.08, label: '> +8%', color: '#22b573' }
          ]
        }]
      }}
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

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <h2 class="terminal-panel-title"><span class="panel-index">04</span><span>Como o Ibovespa fechou em cada ano desde 2020?</span></h2>
    <p class="terminal-panel-sub">Contagem oficial de pregões, abertura, mínima, máxima e variação percentual por ano calendário</p>
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
</div>
