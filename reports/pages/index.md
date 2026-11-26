---
title: Panorama — GringoLake
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Panorama de Fluxo na B3 — IBOV × Investidores</h1>
    <p class="page-subtitle">Ibovespa oficial · Participação dos Investidores (BDI SharesInvesVolum) · Acumulado e Média Móvel de 21 pregões</p>
  </div>

  <div class="controls-bar">
    <div class="controls-left">
      <ButtonGroup name=janela_panorama>
        <ButtonGroupItem valueLabel="30 dias" value="30" />
        <ButtonGroupItem valueLabel="Curto Prazo (160d)" value="240" default />
        <ButtonGroupItem valueLabel="Máx" value="36500" />
      </ButtonGroup>

      <ButtonGroup name=exibir_extremos>
        <ButtonGroupItem valueLabel="Com topos/fundos" value="1" default />
        <ButtonGroupItem valueLabel="Limpo" value="0" />
      </ButtonGroup>
    </div>

    <div class="controls-right">
      <span class="status-chip"><span class="status-chip-accent">Atualização útil</span> · 21:00 BRT (pós-SLA B3)</span>
    </div>
  </div>
</div>

```sql kpi_latest
SELECT
    trading_date,
    ibov_close,
    ibov_return_1d_pct,
    estrang_cum_bi_brl,
    instit_cum_bi_brl,
    pf_cum_bi_brl,
    pf_cum_ma21_bi_brl,
    round(pf_cum_bi_brl - pf_cum_ma21_bi_brl, 2) AS pf_spread_mm21,
    CASE WHEN pf_cum_bi_brl < pf_cum_ma21_bi_brl THEN 1 ELSE 0 END AS pf_abaixo_mm21
FROM gringolake.mart_ibov_vs_investors_wide
ORDER BY trading_date DESC
LIMIT 1
```

<div class="kpi-grid-5">
  <KPITerminalCard data={kpi_latest} value="ibov_close" dateCol="trading_date" code="IBOV" title="Ibovespa Fechamento" suffix=" pts" decimals={0} subtitle="B3 GetPortfolioDay" icon="trend" />
  <KPITerminalCard data={kpi_latest} value="estrang_cum_bi_brl" dateCol="trading_date" code="ESTRANG" title="Estrangeiro Acum." prefix="R$ " suffix=" bi" decimals={2} signed={true} subtitle="BDI SharesInvesVolum" icon="globe" />
  <KPITerminalCard data={kpi_latest} value="instit_cum_bi_brl" dateCol="trading_date" code="INSTIT" title="Institucional Acum." prefix="R$ " suffix=" bi" decimals={2} signed={true} subtitle="Fundos e previdência" icon="bank" />
  <KPITerminalCard data={kpi_latest} value="pf_cum_bi_brl" dateCol="trading_date" code="PF" title="Pessoa Física Acum." prefix="R$ " suffix=" bi" decimals={2} signed={true} subtitle="Investidores individuais" icon="users" />
  <KPITerminalCard data={kpi_latest} value="pf_spread_mm21" dateCol="trading_date" code="MM21" title="Spread P.F. vs MM21" prefix="R$ " suffix=" bi" decimals={2} signed={true} alertCol="pf_abaixo_mm21" subtitle="Acumulado menos MM21" icon="activity" />
</div>

```sql serie_curto_prazo
WITH limite AS (
    SELECT MAX(trading_date) AS max_dt FROM gringolake.mart_ibov_vs_pf_short_term
)
SELECT
    m.trading_date,
    m.ibov_close,
    CASE WHEN '${inputs.exibir_extremos}' = '1' THEN m.ibov_label_points ELSE NULL END AS ibov_label_points,
    m.pf_cum_short_term_bi_brl,
    m.pf_cum_short_term_ma21_bi_brl,
    m.is_pf_below_ma21
FROM gringolake.mart_ibov_vs_pf_short_term m
CROSS JOIN limite l
WHERE date_diff('day', m.trading_date, l.max_dt) <= CAST('${inputs.janela_panorama}' AS INTEGER)
ORDER BY m.trading_date
```

```sql serie_comparativa
WITH limite AS (
    SELECT MAX(trading_date) AS max_dt FROM gringolake.mart_ibov_vs_investors_wide
)
SELECT
    w.trading_date,
    w.ibov_close,
    CASE WHEN '${inputs.exibir_extremos}' = '1' THEN w.ibov_label_points ELSE NULL END AS ibov_label_points,
    w.pf_cum_bi_brl,
    w.pf_cum_ma21_bi_brl,
    w.instit_cum_bi_brl,
    w.instit_cum_ma21_bi_brl,
    w.estrang_cum_bi_brl,
    w.estrang_cum_ma21_bi_brl
FROM gringolake.mart_ibov_vs_investors_wide w
CROSS JOIN limite l
WHERE date_diff('day', w.trading_date, l.max_dt) <= CAST('${inputs.janela_panorama}' AS INTEGER)
ORDER BY w.trading_date
```

<div class="terminal-grid-2">
  <section class="terminal-panel">
    <h2 class="terminal-panel-title">Relação: IBOV × Pessoa Física (Curto Prazo)</h2>
    <p class="terminal-panel-sub">Acumulado P.F. rebased na janela (amarelo) e MM21 (tracejada) no eixo esquerdo · IBOV (prata) no direito · Faixas indicam P.F. abaixo da MM21</p>
    <TerminalDualAxisChart
      data={serie_curto_prazo}
      flowCol="pf_cum_short_term_bi_brl"
      flowName="Acum. P.F."
      maCol="pf_cum_short_term_ma21_bi_brl"
      maName="MM 21 (P.F.)"
      ibovCol="ibov_close"
      ibovName="IBOV (pts)"
      extremaCol="ibov_label_points"
      shadeCol="is_pf_below_ma21"
      height="265px"
    />
  </section>

  <section class="terminal-panel">
    <h2 class="terminal-panel-title">Comparativo: IBOV × Pessoa Física (R$ bi)</h2>
    <p class="terminal-panel-sub">Fluxo líquido acumulado contínuo de Pessoa Física (amarelo) + MM21 (tracejada) contra fechamento do IBOV (prata)</p>
    <TerminalDualAxisChart
      data={serie_comparativa}
      flowCol="pf_cum_bi_brl"
      flowName="Pessoa Física"
      maCol="pf_cum_ma21_bi_brl"
      maName="MM 21 (P.F.)"
      ibovCol="ibov_close"
      ibovName="IBOV (pts)"
      extremaCol="ibov_label_points"
      height="265px"
    />
  </section>
</div>

<div class="terminal-grid-2">
  <section class="terminal-panel">
    <h2 class="terminal-panel-title">Comparativo: IBOV × Institucional (R$ bi)</h2>
    <p class="terminal-panel-sub">Fluxo líquido acumulado de Investidores Institucionais (amarelo) + MM21 (tracejada) contra fechamento do IBOV (prata)</p>
    <TerminalDualAxisChart
      data={serie_comparativa}
      flowCol="instit_cum_bi_brl"
      flowName="Institucional"
      maCol="instit_cum_ma21_bi_brl"
      maName="MM 21 (Instit.)"
      ibovCol="ibov_close"
      ibovName="IBOV (pts)"
      extremaCol="ibov_label_points"
      height="265px"
    />
  </section>

  <section class="terminal-panel">
    <h2 class="terminal-panel-title">Comparativo: IBOV × Investidor Estrangeiro (R$ bi)</h2>
    <p class="terminal-panel-sub">Fluxo líquido acumulado do capital estrangeiro na B3 (amarelo) + MM21 (tracejada) contra fechamento do IBOV (prata)</p>
    <TerminalDualAxisChart
      data={serie_comparativa}
      flowCol="estrang_cum_bi_brl"
      flowName="Estrangeiro"
      maCol="estrang_cum_ma21_bi_brl"
      maName="MM 21 (Estrang.)"
      ibovCol="ibov_close"
      ibovName="IBOV (pts)"
      extremaCol="ibov_label_points"
      height="265px"
    />
  </section>
</div>

```sql explorador_perfis
WITH ultimo_pregao AS (
    SELECT MAX(trading_date) AS max_dt FROM gringolake.fct_ibov_investor_flow_daily
)
SELECT
    f.trading_date,
    f.investor_type_short_pt,
    f.investor_type_name_pt,
    f.daily_net_flow_bi_brl,
    f.mtd_net_flow_bi_brl,
    f.cum_net_flow_bi_brl,
    f.cum_net_flow_ma21_bi_brl,
    f.purchase_share_pct,
    f.flow_vs_ma21_signal
FROM gringolake.fct_ibov_investor_flow_daily f
INNER JOIN ultimo_pregao u ON f.trading_date = u.max_dt
ORDER BY f.display_order
```

<FlowExplorerTable
  data={explorador_perfis}
  title="Explorador Executivo — Os 5 Perfis Oficiais da B3 no Último Pregão"
  subtitle="Saldos líquidos diário, mensal (MTD) e acumulado em R$ bilhões · Destaque amarelo nos perfis acima da MM21"
/>
