---
title: Fluxo Diário — GringoLake
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Entradas e Saídas Diárias na B3 — Fluxo por Perfil</h1>
    <p class="page-subtitle">Saldo líquido diário (Compras − Vendas) em R$ milhões derivado por desacumulação MTD oficial da B3 (SharesInvesVolum D+2)</p>
  </div>

  <div class="controls-bar">
    <div class="controls-left">
      <ButtonGroup name=janela_pregoes>
        <ButtonGroupItem valueLabel="Últimos 20 pregões" value="20" />
        <ButtonGroupItem valueLabel="Últimos 60 pregões" value="60" default />
        <ButtonGroupItem valueLabel="Máx" value="9999" />
      </ButtonGroup>
    </div>

    <div class="controls-right">
      <span class="status-chip"><span class="status-chip-accent">Base Gold</span> · fct_ibov_investor_flow_daily (R$ mi)</span>
    </div>
  </div>
</div>

```sql kpis_dia_recente
WITH ultimo AS (
    SELECT MAX(trading_date) AS max_dt
    FROM gringolake.fct_ibov_investor_flow_daily
)
SELECT
    f.trading_date,
    MAX(CASE WHEN f.investor_type_code = 'estrangeiro' THEN round(f.daily_net_flow_k_brl / 1000.0, 2) END) AS estrang_mi,
    MAX(CASE WHEN f.investor_type_code = 'pessoa_fisica' THEN round(f.daily_net_flow_k_brl / 1000.0, 2) END) AS pf_mi,
    MAX(CASE WHEN f.investor_type_code = 'institucional' THEN round(f.daily_net_flow_k_brl / 1000.0, 2) END) AS instit_mi,
    MAX(CASE WHEN f.investor_type_code = 'instituicoes_financeiras' THEN round(f.daily_net_flow_k_brl / 1000.0, 2) END) AS inst_fin_mi
FROM gringolake.fct_ibov_investor_flow_daily f
INNER JOIN ultimo u ON f.trading_date = u.max_dt
GROUP BY f.trading_date
```

<div class="kpi-grid-4">
  <KPITerminalCard data={kpis_dia_recente} value="estrang_mi" dateCol="trading_date" code="ESTRANG" title="Estrangeiro (Gringo)" prefix="R$ " suffix=" mi" decimals={1} signed={true} subtitle="Saldo diário · último pregão" icon="globe" />
  <KPITerminalCard data={kpis_dia_recente} value="pf_mi" dateCol="trading_date" code="PF" title="Pessoa Física (PF)" prefix="R$ " suffix=" mi" decimals={1} signed={true} subtitle="Saldo diário · último pregão" icon="users" />
  <KPITerminalCard data={kpis_dia_recente} value="instit_mi" dateCol="trading_date" code="INSTIT" title="Institucional (Fundos)" prefix="R$ " suffix=" mi" decimals={1} signed={true} subtitle="Saldo diário · último pregão" icon="bank" />
  <KPITerminalCard data={kpis_dia_recente} value="inst_fin_mi" dateCol="trading_date" code="INST FIN" title="Inst. Financeira" prefix="R$ " suffix=" mi" decimals={1} signed={true} subtitle="Saldo diário · último pregão" icon="flow" />
</div>

```sql fluxo_diario_4_perfis
WITH datas_janela AS (
    SELECT DISTINCT trading_date
    FROM gringolake.fct_ibov_investor_flow_daily
    ORDER BY trading_date DESC
    LIMIT CAST('${inputs.janela_pregoes}' AS INTEGER)
)
SELECT
    f.trading_date,
    MAX(f.ibov_close) AS ibov_close,
    MAX(CASE WHEN f.investor_type_code = 'estrangeiro' THEN round(f.daily_net_flow_k_brl / 1000.0, 2) END) AS estrang_mi,
    MAX(CASE WHEN f.investor_type_code = 'pessoa_fisica' THEN round(f.daily_net_flow_k_brl / 1000.0, 2) END) AS pf_mi,
    MAX(CASE WHEN f.investor_type_code = 'institucional' THEN round(f.daily_net_flow_k_brl / 1000.0, 2) END) AS instit_mi,
    MAX(CASE WHEN f.investor_type_code = 'instituicoes_financeiras' THEN round(f.daily_net_flow_k_brl / 1000.0, 2) END) AS inst_fin_mi,
    MAX(CASE WHEN f.investor_type_code = 'outros' THEN round(f.daily_net_flow_k_brl / 1000.0, 2) END) AS outros_mi
FROM gringolake.fct_ibov_investor_flow_daily f
INNER JOIN datas_janela d ON f.trading_date = d.trading_date
GROUP BY f.trading_date
ORDER BY f.trading_date ASC
```

<div class="terminal-grid-2">
  <section class="terminal-panel">
    <h2 class="terminal-panel-title">Entradas e Saídas Diárias · Estrangeiro (Gringo)</h2>
    <p class="terminal-panel-sub">Como ler: barras amarelas = dia de compra líquida na B3; barras cinzas = dia de saque/venda líquida (em R$ milhões)</p>
    <TerminalLineChart
      data={fluxo_diario_4_perfis}
      x="trading_date"
      y="estrang_mi"
      names={['Estrangeiro']}
      prefix="R$ "
      suffix=" mi"
      decimals={1}
      signed={true}
      chartType="bar"
      axisCompact={true}
      height="255px"
      showEndLabel={false}
    />
  </section>

  <section class="terminal-panel">
    <h2 class="terminal-panel-title">Entradas e Saídas Diárias · Pessoa Física (PF)</h2>
    <p class="terminal-panel-sub">Como ler: barras amarelas = dia de compra líquida na B3; barras cinzas = dia de saque/venda líquida (em R$ milhões)</p>
    <TerminalLineChart
      data={fluxo_diario_4_perfis}
      x="trading_date"
      y="pf_mi"
      names={['Pessoa Física']}
      prefix="R$ "
      suffix=" mi"
      decimals={1}
      signed={true}
      chartType="bar"
      axisCompact={true}
      height="255px"
      showEndLabel={false}
    />
  </section>
</div>

<div class="terminal-grid-2">
  <section class="terminal-panel">
    <h2 class="terminal-panel-title">Entradas e Saídas Diárias · Institucional (Fundos)</h2>
    <p class="terminal-panel-sub">Como ler: barras amarelas = dia de compra líquida na B3; barras cinzas = dia de saque/venda líquida (em R$ milhões)</p>
    <TerminalLineChart
      data={fluxo_diario_4_perfis}
      x="trading_date"
      y="instit_mi"
      names={['Institucional']}
      prefix="R$ "
      suffix=" mi"
      decimals={1}
      signed={true}
      chartType="bar"
      axisCompact={true}
      height="255px"
      showEndLabel={false}
    />
  </section>

  <section class="terminal-panel">
    <h2 class="terminal-panel-title">Entradas e Saídas Diárias · Inst. Financeira</h2>
    <p class="terminal-panel-sub">Como ler: barras amarelas = dia de compra líquida na B3; barras cinzas = dia de saque/venda líquida (em R$ milhões)</p>
    <TerminalLineChart
      data={fluxo_diario_4_perfis}
      x="trading_date"
      y="inst_fin_mi"
      names={['Inst. Financeira']}
      prefix="R$ "
      suffix=" mi"
      decimals={1}
      signed={true}
      chartType="bar"
      axisCompact={true}
      height="255px"
      showEndLabel={false}
    />
  </section>
</div>

```sql tabela_fluxo_diario
SELECT
    strftime(trading_date, '%Y-%m-%d') AS pregao,
    ibov_close,
    estrang_mi,
    pf_mi,
    instit_mi,
    inst_fin_mi,
    outros_mi
FROM ${fluxo_diario_4_perfis}
ORDER BY trading_date DESC
```

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <h2 class="terminal-panel-title">Histórico Diário por Perfil — B3 (R$ milhões)</h2>
    <p class="terminal-panel-sub">Soma das 5 categorias oficiais da B3 fecha em zero a cada pregão (mercado soma-zero) · Histórico cresce automaticamente a cada pregão útil via bot diário</p>
    <DataTable data={tabela_fluxo_diario} rows=15 search=false>
      <Column id=pregao title="Pregão" />
      <Column id=ibov_close title="IBOV (pts)" fmt="#,##0" />
      <Column id=estrang_mi title="Estrangeiro (R$ mi)" fmt="+#,##0.0;-#,##0.0;0.0" />
      <Column id=pf_mi title="Pessoa Física (R$ mi)" fmt="+#,##0.0;-#,##0.0;0.0" />
      <Column id=instit_mi title="Institucional (R$ mi)" fmt="+#,##0.0;-#,##0.0;0.0" />
      <Column id=inst_fin_mi title="Inst. Financeira (R$ mi)" fmt="+#,##0.0;-#,##0.0;0.0" />
      <Column id=outros_mi title="Outros (R$ mi)" fmt="+#,##0.0;-#,##0.0;0.0" />
    </DataTable>
  </section>
</div>
