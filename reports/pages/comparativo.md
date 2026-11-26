---
title: Comparativo Multi-Perfil — GringoLake
---

```sql resumo_comparativo
SELECT COUNT(DISTINCT investor_type_code) AS total_perfis
FROM gringolake.fct_ibov_investor_flow_daily
```

<div class="page-hero">
  <p class="page-eyebrow">GRINGOLAKE · COMPARATIVO</p>

  <div class="page-head-row">
    <div class="page-title-group">
      <h1 class="page-title">Comparativo Multi-Perfil</h1>
      <p class="page-subtitle">Compare o comportamento de cada categoria oficial da B3, quem faz a contraparte e quem domina o giro</p>
    </div>

    <div class="controls-right">
      <ButtonGroup name=perfil_foco>
        <ButtonGroupItem valueLabel="Pessoa Física" value="pessoa_fisica" default />
        <ButtonGroupItem valueLabel="Institucional" value="institucional" />
        <ButtonGroupItem valueLabel="Estrangeiro" value="estrangeiro" />
        <ButtonGroupItem valueLabel="Inst. Financeiras" value="instituicoes_financeiras" />
        <ButtonGroupItem valueLabel="Outros" value="outros" />
      </ButtonGroup>

      <CounterBadge data={resumo_comparativo} value="total_perfis" label="Perfis B3" decimals={0} />
    </div>
  </div>
</div>

```sql serie_perfil
SELECT
    trading_date,
    investor_type_name_pt,
    ibov_close,
    ibov_label_points,
    daily_net_flow_bi_brl,
    mtd_net_flow_bi_brl,
    cum_net_flow_bi_brl,
    cum_net_flow_ma21_bi_brl,
    ma21_window_obs_count,
    purchase_share_pct,
    flow_vs_ma21_signal,
    investor_type_short_pt
FROM gringolake.fct_ibov_investor_flow_daily
WHERE investor_type_code = '${inputs.perfil_foco}'
ORDER BY trading_date
```

```sql todos_perfis_wide
SELECT
    trading_date,
    estrang_cum_bi_brl,
    instit_cum_bi_brl,
    pf_cum_bi_brl
FROM gringolake.mart_ibov_vs_investors_wide
ORDER BY trading_date
```

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <TerminalDualAxisChart
      data={serie_perfil}
      panelIndex="01"
      panelTitle="Como evolui o fluxo do perfil selecionado frente ao Ibovespa?"
      panelSubtitle="Acumulado contínuo em R$ bi (âmbar) e MM21 vs. fechamento oficial do Ibovespa (grafite)"
      flowCol="cum_net_flow_bi_brl"
      flowName="Fluxo Acumulado"
      maCol="cum_net_flow_ma21_bi_brl"
      maObsCol="ma21_window_obs_count"
      maName="MM 21d"
      ibovCol="ibov_close"
      ibovName="IBOV (pts)"
      focal={true}
      height="360px"
      zoom={true}
    />
  </section>
</div>

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <TerminalLineChart
      data={todos_perfis_wide}
      panelIndex="02"
      panelTitle="Quem compra na contraparte de quem está vendendo?"
      panelSubtitle="Evolução acumulada dos 3 maiores grupos da B3 (Estrangeiro, Pessoa Física e Institucional) em R$ bi"
      x="trading_date"
      y={['estrang_cum_bi_brl', 'pf_cum_bi_brl', 'instit_cum_bi_brl']}
      names={['Estrangeiro', 'Pessoa Física', 'Institucional']}
      colors={['#f2b94b', '#e5e5e5', '#767676']}
      prefix="R$ "
      suffix=" bi"
      decimals={2}
      signed={true}
      axisCompact={true}
      height="295px"
    />
  </section>
</div>

```sql dispersao_estrang_ibov
SELECT
    trading_date,
    ROUND(daily_net_flow_k_brl / 1000.0, 1) AS estrang_mi,
    ibov_return_1d_pct
FROM gringolake.fct_ibov_investor_flow_daily
WHERE investor_type_code = 'estrangeiro'
  AND ibov_return_1d_pct IS NOT NULL
ORDER BY trading_date
```

```sql participacao_volume_b3
WITH ultimo AS (
    SELECT MAX(trading_date) AS max_dt
    FROM gringolake.fct_ibov_investor_flow_daily
),
total_dia AS (
    SELECT
        f.trading_date,
        SUM(f.daily_purchases_k_brl + f.daily_sales_k_brl) AS total_2sided_k
    FROM gringolake.fct_ibov_investor_flow_daily f
    INNER JOIN ultimo u ON f.trading_date = u.max_dt
    GROUP BY f.trading_date
),
base AS (
    SELECT
        CASE f.investor_type_code
            WHEN 'estrangeiro' THEN 'Estrangeiro'
            WHEN 'instituicoes_financeiras' THEN 'Inst. Financeira'
            ELSE f.investor_type_name_pt
        END AS perfil,
        ROUND((f.purchase_share_pct + f.sale_share_pct) / 100.0, 4) AS mtd_share,
        ROUND((f.daily_purchases_k_brl + f.daily_sales_k_brl) / t.total_2sided_k, 4) AS daily_share
    FROM gringolake.fct_ibov_investor_flow_daily f
    INNER JOIN ultimo u ON f.trading_date = u.max_dt
    INNER JOIN total_dia t ON f.trading_date = t.trading_date
)
SELECT perfil, 'Mês (BDI)' AS periodo, mtd_share AS participacao_pct, mtd_share AS sort_key
FROM base
UNION ALL
SELECT perfil, 'Último Pregão' AS periodo, daily_share AS participacao_pct, mtd_share AS sort_key
FROM base
ORDER BY sort_key DESC, periodo ASC
```

<div class="terminal-grid-2">
  <section class="terminal-panel">
    <FlowScatterChart
      data={dispersao_estrang_ibov}
      panelIndex="03"
      panelTitle="Quando o estrangeiro entra, o IBOV sobe?"
      panelSubtitle="Dispersão diária: fluxo estrangeiro (R$ mi, X) × variação do Ibovespa (%, Y)"
      height="290px"
    />
  </section>

  <section class="terminal-panel">
    <h2 class="terminal-panel-title"><span class="panel-index">04</span><span>Qual perfil domina o volume na B3?</span></h2>
    <p class="terminal-panel-sub">Participação oficial no giro do mês (BDI) e no último pregão (%) · Clique na legenda ou passe o mouse</p>
    <BarChart
      data={participacao_volume_b3}
      x=perfil
      y=participacao_pct
      series=periodo
      type=grouped
      swapXY=true
      sort=false
      yFmt=pct1
      labels=true
      labelSize=11
      chartAreaHeight=240
      seriesOrder={['Mês (BDI)', 'Último Pregão']}
      seriesColors={{ 'Mês (BDI)': '#f2b94b', 'Último Pregão': '#8a8a93' }}
      seriesOptions={{
        itemStyle: { borderRadius: [0, 5, 5, 0] },
        label: {
          color: '#e5e5e5',
          fontFamily: 'JetBrains Mono, ui-monospace, monospace',
          fontSize: 11,
          distance: 6
        }
      }}
      echartsOptions={{
        backgroundColor: 'transparent',
        grid: {
          left: 8,
          right: 46,
          containLabel: true
        },
        tooltip: {
          backgroundColor: '#222222',
          borderColor: '#45454a',
          textStyle: { color: '#f8f8f8' }
        },
        legend: {
          textStyle: { color: '#a3a3a3' }
        },
        xAxis: {
          splitLine: { lineStyle: { color: '#333338' } },
          axisLabel: { color: '#8a8a93' }
        },
        yAxis: {
          axisLabel: { color: '#e5e5e5', fontSize: 12 }
        }
      }}
    />
  </section>
</div>

```sql serie_perfil_desc
SELECT * FROM ${serie_perfil} ORDER BY trading_date DESC
```

<FlowExplorerTable
  data={serie_perfil_desc}
  panelIndex="05"
  title="Qual o histórico diário detalhado do perfil selecionado?"
  subtitle="Pregões em ordem decrescente com saldo diário, MTD e acumulado em R$ bi · MM21 ativa com 21 pregões completos"
/>
