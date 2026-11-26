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
      <p class="page-subtitle">Inspeção detalhada por categoria oficial B3 em R$ bilhões e contraparte entre os três maiores grupos</p>
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
      panelTitle="IBOV × Fluxo Acumulado e MM21 do Perfil Selecionado"
      panelSubtitle="Acumulado contínuo em R$ bi (âmbar) vs. fechamento oficial do IBOV (grafite)"
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
      panelTitle="Contraparte de Mercado · Estrangeiro × Pessoa Física × Institucional"
      panelSubtitle="Evolução acumulada conjunta dos 3 maiores grupos da B3 no horizonte disponível (R$ bi)"
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
)
SELECT
    f.investor_type_name_pt,
    ROUND(f.purchase_share_pct + f.sale_share_pct, 2) AS mtd_share_pct,
    ROUND((f.daily_purchases_k_brl + f.daily_sales_k_brl) / t.total_2sided_k * 100.0, 2) AS daily_share_pct
FROM gringolake.fct_ibov_investor_flow_daily f
INNER JOIN ultimo u ON f.trading_date = u.max_dt
INNER JOIN total_dia t ON f.trading_date = t.trading_date
ORDER BY mtd_share_pct DESC
```

<div class="terminal-grid-2">
  <section class="terminal-panel">
    <FlowScatterChart
      data={dispersao_estrang_ibov}
      panelIndex="03"
      panelTitle="Dispersão · Estrangeiro × Retorno IBOV"
      panelSubtitle="Eixo X: fluxo diário estrangeiro (R$ mi) · Eixo Y: variação diária do Ibovespa (%)"
      height="290px"
    />
  </section>

  <section class="terminal-panel">
    <MarketShareBarChart
      data={participacao_volume_b3}
      panelIndex="04"
      panelTitle="Participação no Volume da B3 (%)"
      panelSubtitle="Fatia oficial no mês (BDI) e no último pregão por categoria de investidor"
    />
  </section>
</div>

```sql serie_perfil_desc
SELECT * FROM ${serie_perfil} ORDER BY trading_date DESC
```

<FlowExplorerTable
  data={serie_perfil_desc}
  panelIndex="05"
  title="Histórico Diário do Perfil Selecionado"
  subtitle="Pregões em ordem decrescente com saldo diário, MTD e acumulado em R$ bi · MM21 ativa com 21 pregões completos"
/>
