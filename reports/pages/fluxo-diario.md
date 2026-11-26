---
title: Fluxo Diário — GringoLake
---

```sql kpis_dia_recente
WITH ultimo AS (
    SELECT MAX(trading_date) AS max_dt
    FROM gringolake.fct_ibov_investor_flow_daily
),
zero_sum AS (
    SELECT MAX(ABS(daily_sum)) AS max_residuo_k
    FROM (
        SELECT trading_date, SUM(daily_net_flow_k_brl) AS daily_sum
        FROM gringolake.fct_ibov_investor_flow_daily
        GROUP BY trading_date
    )
)
SELECT
    f.trading_date,
    MAX(CASE WHEN f.investor_type_code = 'estrangeiro' THEN round(f.daily_net_flow_k_brl / 1000.0, 2) END) AS estrang_mi,
    MAX(CASE WHEN f.investor_type_code = 'pessoa_fisica' THEN round(f.daily_net_flow_k_brl / 1000.0, 2) END) AS pf_mi,
    MAX(CASE WHEN f.investor_type_code = 'institucional' THEN round(f.daily_net_flow_k_brl / 1000.0, 2) END) AS instit_mi,
    MAX(CASE WHEN f.investor_type_code = 'instituicoes_financeiras' THEN round(f.daily_net_flow_k_brl / 1000.0, 2) END) AS inst_fin_mi,
    MAX(z.max_residuo_k) AS max_residuo_k
FROM gringolake.fct_ibov_investor_flow_daily f
INNER JOIN ultimo u ON f.trading_date = u.max_dt
CROSS JOIN zero_sum z
GROUP BY f.trading_date
```

<div class="page-hero">
  <p class="page-eyebrow">GRINGOLAKE · FLUXO DIÁRIO AUDITADO</p>

  <div class="page-head-row">
    <div class="page-title-group">
      <h1 class="page-title">Entradas e Saídas Diárias na B3</h1>
      <p class="page-subtitle">Saldo líquido isolado por pregão em R$ milhões derivado por desacumulação oficial MTD (ADR-003)</p>
    </div>

    <div class="controls-right">
      <ButtonGroup name=janela_pregoes>
        <ButtonGroupItem valueLabel="20d" value="20" />
        <ButtonGroupItem valueLabel="60d" value="60" default />
        <ButtonGroupItem valueLabel="Máx" value="9999" />
      </ButtonGroup>

      <CounterBadge data={kpis_dia_recente} value="max_residuo_k" label="Resíduo (R$ mil)" decimals={1} />
    </div>
  </div>
</div>

<div class="kpi-grid-4">
  <KPITerminalCard data={kpis_dia_recente} value="estrang_mi" dateCol="trading_date" code="ESTRANG" title="Estrangeiro" prefix="R$ " suffix=" mi" decimals={1} signed={true} subtitle="Saldo líquido diário" focalWhenPositive={true} />
  <KPITerminalCard data={kpis_dia_recente} value="pf_mi" dateCol="trading_date" code="PF" title="Pessoa Física" prefix="R$ " suffix=" mi" decimals={1} signed={true} subtitle="Saldo líquido diário" focalWhenPositive={true} />
  <KPITerminalCard data={kpis_dia_recente} value="instit_mi" dateCol="trading_date" code="INSTIT" title="Institucional" prefix="R$ " suffix=" mi" decimals={1} signed={true} subtitle="Saldo líquido diário" focalWhenPositive={true} />
  <KPITerminalCard data={kpis_dia_recente} value="inst_fin_mi" dateCol="trading_date" code="INST FIN" title="Inst. Financeira" prefix="R$ " suffix=" mi" decimals={1} signed={true} subtitle="Saldo líquido diário" focalWhenPositive={true} />
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
    MAX(CASE WHEN f.investor_type_code = 'outros' THEN round(f.daily_net_flow_k_brl / 1000.0, 2) END) AS outros_mi,
    ROUND(SUM(f.daily_purchases_k_brl) / 1000000.0, 2) AS volume_total_bi
FROM gringolake.fct_ibov_investor_flow_daily f
INNER JOIN datas_janela d ON f.trading_date = d.trading_date
GROUP BY f.trading_date
ORDER BY f.trading_date ASC
```

<div class="terminal-grid-2">
  <section class="terminal-panel">
    <TerminalLineChart
      data={fluxo_diario_4_perfis}
      panelIndex="01"
      panelTitle="Estrangeiro"
      panelSubtitle="Âmbar = compra líquida · Grafite = saída líquida (R$ mi)"
      x="trading_date"
      y="estrang_mi"
      names={['Estrangeiro']}
      prefix="R$ "
      suffix=" mi"
      decimals={1}
      signed={true}
      chartType="bar"
      axisCompact={true}
      height="275px"
      showEndLabel={false}
    />
  </section>

  <section class="terminal-panel">
    <TerminalLineChart
      data={fluxo_diario_4_perfis}
      panelIndex="02"
      panelTitle="Pessoa Física"
      panelSubtitle="Âmbar = compra líquida · Grafite = saída líquida (R$ mi)"
      x="trading_date"
      y="pf_mi"
      names={['Pessoa Física']}
      prefix="R$ "
      suffix=" mi"
      decimals={1}
      signed={true}
      chartType="bar"
      axisCompact={true}
      height="275px"
      showEndLabel={false}
    />
  </section>
</div>

<div class="terminal-grid-2">
  <section class="terminal-panel">
    <TerminalLineChart
      data={fluxo_diario_4_perfis}
      panelIndex="03"
      panelTitle="Institucional"
      panelSubtitle="Âmbar = compra líquida · Grafite = saída líquida (R$ mi)"
      x="trading_date"
      y="instit_mi"
      names={['Institucional']}
      prefix="R$ "
      suffix=" mi"
      decimals={1}
      signed={true}
      chartType="bar"
      axisCompact={true}
      height="275px"
      showEndLabel={false}
    />
  </section>

  <section class="terminal-panel">
    <TerminalLineChart
      data={fluxo_diario_4_perfis}
      panelIndex="04"
      panelTitle="Inst. Financeira"
      panelSubtitle="Âmbar = compra líquida · Grafite = saída líquida (R$ mi)"
      x="trading_date"
      y="inst_fin_mi"
      names={['Inst. Financeira']}
      prefix="R$ "
      suffix=" mi"
      decimals={1}
      signed={true}
      chartType="bar"
      axisCompact={true}
      height="275px"
      showEndLabel={false}
    />
  </section>
</div>

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <TerminalLineChart
      data={fluxo_diario_4_perfis}
      panelIndex="05"
      panelTitle="Volume Financeiro Total da B3 (R$ bi)"
      panelSubtitle="Giro financeiro diário somando os 5 perfis (1 ponta, BDI) · Âmbar = pregões ≥ 1,4× média da janela"
      x="trading_date"
      y="volume_total_bi"
      names={['Volume Total B3']}
      prefix="R$ "
      suffix=" bi"
      decimals={1}
      chartType="bar"
      axisCompact={true}
      highlightAboveAvg={true}
      height="250px"
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
    <h2 class="terminal-panel-title"><span class="panel-index">06</span><span>Histórico Diário por Perfil (R$ milhões)</span></h2>
    <p class="terminal-panel-sub">Soma das 5 categorias oficiais da B3 fecha em zero a cada pregão (tolerância ≤ R$ 20 mil) · Atualização às 21h BRT</p>
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
