---
title: Ibovespa Histórico — GringoLake
---

```sql ibov_filtrado
WITH limite AS (
    SELECT MAX(trading_date) AS max_dt FROM gringolake.stg_b3_ibov_daily
),
com_medias AS (
    SELECT
        trading_date,
        trading_year,
        ibov_close,
        ibov_return_1d_pct,
        CASE
            WHEN COUNT(ibov_close) OVER (ORDER BY trading_date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) = 21
            THEN ROUND(AVG(ibov_close) OVER (ORDER BY trading_date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW), 2)
        END AS ibov_ma21,
        CASE
            WHEN COUNT(ibov_close) OVER (ORDER BY trading_date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) = 50
            THEN ROUND(AVG(ibov_close) OVER (ORDER BY trading_date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW), 2)
        END AS ibov_ma50,
        CASE
            WHEN COUNT(ibov_close) OVER (ORDER BY trading_date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) = 200
            THEN ROUND(AVG(ibov_close) OVER (ORDER BY trading_date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW), 2)
        END AS ibov_ma200
    FROM gringolake.stg_b3_ibov_daily
),
janela AS (
    SELECT
        s.trading_date,
        s.trading_year,
        s.ibov_close,
        s.ibov_return_1d_pct,
        s.ibov_ma21,
        s.ibov_ma50,
        s.ibov_ma200
    FROM com_medias s
    CROSS JOIN limite l
    WHERE date_diff('day', s.trading_date, l.max_dt) <= CAST('${inputs.horizonte_ibov}' AS INTEGER)
)
SELECT
    trading_date,
    trading_year,
    ibov_close,
    ibov_return_1d_pct,
    ibov_ma21,
    ibov_ma50,
    ibov_ma200,
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
    <TradingViewIbovChart
      data={ibov_filtrado}
      panelTitle="Qual a trajetória do Ibovespa no horizonte selecionado?"
      panelSubtitle="Gráfico de velas (Candlestick) derivado dos fechamentos oficiais B3 · Tempo gráfico 1D / 1S / 1M + MM21/MM50/MM200"
      height={340}
    />
  </section>
</div>

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <TradingViewSeriesChart
      data={ibov_filtrado}
      panelTitle="Quanto o Ibovespa já caiu desde a máxima do período?"
      panelSubtitle="Drawdown percentual a partir do topo acumulado na janela selecionada (0% = máxima da janela)"
      x="trading_date"
      y="drawdown_pct"
      names={['Drawdown IBOV']}
      colors={['#f2b94b']}
      suffix="%"
      decimals={2}
      signed={true}
      defaultZoomPoints={0}
      height={235}
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
  <MonthlyHeatmap
    data={matriz_mensal_ibov}
    title="Quais meses historicamente rendem mais ou menos no Ibovespa?"
    subtitle="Mapa de calor (Heatmap) dos retornos mensais oficiais da B3 (Jan/2020 a Nov/2026 · Dez/2026 ainda não iniciado)"
  />
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
  <AnnualIbovTable data={resumo_anual_ibov} />
</div>
