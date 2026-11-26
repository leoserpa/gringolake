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
      extremaCol="ibov_label_points"
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

```sql serie_perfil_desc
SELECT * FROM ${serie_perfil} ORDER BY trading_date DESC
```

<FlowExplorerTable
  data={serie_perfil_desc}
  panelIndex="03"
  title="Histórico Diário do Perfil Selecionado"
  subtitle="Pregões em ordem decrescente com saldo diário, MTD e acumulado em R$ bi · MM21 ativa com 21 pregões completos"
/>
