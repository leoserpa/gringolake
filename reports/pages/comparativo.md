---
title: Comparativo Multi-Perfil — GringoLake
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Comparativo: IBOV × Estrangeiro × Institucional × Pessoa Física</h1>
    <p class="page-subtitle">Selecione o perfil de investidor para inspecionar a série acumulada + MM21 contra o Ibovespa em tela cheia</p>
  </div>

  <div class="controls-bar">
    <div class="controls-left">
      <ButtonGroup name=perfil_foco>
        <ButtonGroupItem valueLabel="Pessoa Física" value="pessoa_fisica" default />
        <ButtonGroupItem valueLabel="Institucional" value="institucional" />
        <ButtonGroupItem valueLabel="Estrangeiro" value="estrangeiro" />
        <ButtonGroupItem valueLabel="Inst. Financeiras" value="instituicoes_financeiras" />
        <ButtonGroupItem valueLabel="Outros" value="outros" />
      </ButtonGroup>
    </div>

    <div class="controls-right">
      <span class="status-chip"><span class="status-chip-accent">Fato Gold</span> · fct_ibov_investor_flow_daily</span>
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
    <h2 class="terminal-panel-title">IBOV × Fluxo Acumulado e MM21 — Perfil Selecionado</h2>
    <p class="terminal-panel-sub">Acumulado em R$ bilhões (amarelo) + MM21 (tracejada) no eixo esquerdo · Fechamento oficial do IBOV (prata) no eixo direito</p>
    <TerminalDualAxisChart
      data={serie_perfil}
      flowCol="cum_net_flow_bi_brl"
      flowName="Fluxo Acumulado"
      maCol="cum_net_flow_ma21_bi_brl"
      maName="MM 21 pregões"
      ibovCol="ibov_close"
      ibovName="IBOV (pts)"
      extremaCol="ibov_label_points"
      height="360px"
      zoom={true}
    />
  </section>
</div>

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <h2 class="terminal-panel-title">Contraparte de Mercado — Estrangeiro × Institucional × Pessoa Física (R$ bi)</h2>
    <p class="terminal-panel-sub">Evolução conjunta dos 3 maiores grupos da B3 (destaque amarelo em Estrangeiro, tons neutros em Institucional e Pessoa Física)</p>
    <TerminalLineChart
      data={todos_perfis_wide}
      x="trading_date"
      y={['estrang_cum_bi_brl', 'pf_cum_bi_brl', 'instit_cum_bi_brl']}
      names={['Estrangeiro', 'Pessoa Física', 'Institucional']}
      colors={['#facc15', '#d4d4d4', '#737373']}
      prefix="R$ "
      suffix=" bi"
      decimals={2}
      signed={true}
      height="265px"
    />
  </section>
</div>

```sql serie_perfil_desc
SELECT * FROM ${serie_perfil} ORDER BY trading_date DESC
```

<FlowExplorerTable
  data={serie_perfil_desc}
  title="Histórico Diário do Perfil Selecionado"
  subtitle="Pregões em ordem decrescente com saldo diário, MTD, acumulado e posição frente à MM21"
/>
