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
    MAX(CASE WHEN f.investor_type_code = 'estrangeiro' THEN f.daily_net_flow_k_brl / 1000.0 END) AS estrang_mi,
    MAX(CASE WHEN f.investor_type_code = 'pessoa_fisica' THEN f.daily_net_flow_k_brl / 1000.0 END) AS pf_mi,
    MAX(CASE WHEN f.investor_type_code = 'institucional' THEN f.daily_net_flow_k_brl / 1000.0 END) AS instit_mi,
    MAX(CASE WHEN f.investor_type_code = 'instituicoes_financeiras' THEN f.daily_net_flow_k_brl / 1000.0 END) AS inst_fin_mi,
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
      <p class="page-subtitle">Quanto cada grupo comprou ou vendeu isoladamente por pregão (R$ mi / bi · desacumulação MTD · ADR-003)</p>
    </div>

    <div class="controls-right">
      <ButtonGroup name=janela_pregoes>
        <ButtonGroupItem valueLabel="20d" value="20" />
        <ButtonGroupItem valueLabel="60d" value="60" default />
        <ButtonGroupItem valueLabel="Máx" value="9999" />
      </ButtonGroup>

      <CounterBadge
        data={kpis_dia_recente}
        value="max_residuo_k"
        label="Resíduo"
        prefix="R$ "
        suffix=" mil"
        decimals={2}
        hint="Resíduo máximo diário da auditoria soma-zero B3 (tolerância ≤ R$ 20 mil)"
      />
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
    MAX(CASE WHEN f.investor_type_code = 'estrangeiro' THEN f.daily_net_flow_k_brl / 1000.0 END) AS estrang_mi,
    MAX(CASE WHEN f.investor_type_code = 'pessoa_fisica' THEN f.daily_net_flow_k_brl / 1000.0 END) AS pf_mi,
    MAX(CASE WHEN f.investor_type_code = 'institucional' THEN f.daily_net_flow_k_brl / 1000.0 END) AS instit_mi,
    MAX(CASE WHEN f.investor_type_code = 'instituicoes_financeiras' THEN f.daily_net_flow_k_brl / 1000.0 END) AS inst_fin_mi,
    MAX(CASE WHEN f.investor_type_code = 'outros' THEN f.daily_net_flow_k_brl / 1000.0 END) AS outros_mi,
    SUM(f.daily_purchases_k_brl) / 1000000.0 AS volume_total_bi
FROM gringolake.fct_ibov_investor_flow_daily f
INNER JOIN datas_janela d ON f.trading_date = d.trading_date
GROUP BY f.trading_date
ORDER BY f.trading_date ASC
```

<div class="terminal-grid-2">
  <section class="terminal-panel">
    <TradingViewSeriesChart
      data={fluxo_diario_4_perfis}
      panelTitle="Quanto o estrangeiro movimentou por dia?"
      panelSubtitle="Saldo líquido diário (R$ mi / bi) · Âmbar = compra, grafite = saída"
      x="trading_date"
      y="estrang_mi"
      names={['Estrangeiro']}
      prefix="R$ "
      suffix=" mi"
      decimals={1}
      signed={true}
      chartType="bar"
      axisCompact={true}
      autoScaleUnit={true}
      defaultZoomPoints={60}
      height={220}
    />
  </section>

  <section class="terminal-panel">
    <TradingViewSeriesChart
      data={fluxo_diario_4_perfis}
      panelTitle="Quando a Pessoa Física entrou comprando?"
      panelSubtitle="Saldo líquido diário (R$ mi / bi) · Âmbar = compra, grafite = saída"
      x="trading_date"
      y="pf_mi"
      names={['Pessoa Física']}
      prefix="R$ "
      suffix=" mi"
      decimals={1}
      signed={true}
      chartType="bar"
      axisCompact={true}
      autoScaleUnit={true}
      defaultZoomPoints={60}
      height={220}
    />
  </section>
</div>

<div class="terminal-grid-2">
  <section class="terminal-panel">
    <TradingViewSeriesChart
      data={fluxo_diario_4_perfis}
      panelTitle="Qual foi o fluxo diário do institucional?"
      panelSubtitle="Saldo líquido diário (R$ mi / bi) · Âmbar = compra, grafite = saída"
      x="trading_date"
      y="instit_mi"
      names={['Institucional']}
      prefix="R$ "
      suffix=" mi"
      decimals={1}
      signed={true}
      chartType="bar"
      axisCompact={true}
      autoScaleUnit={true}
      defaultZoomPoints={60}
      height={220}
    />
  </section>

  <section class="terminal-panel">
    <TradingViewSeriesChart
      data={fluxo_diario_4_perfis}
      panelTitle="Como atuaram as Inst. Financeiras por dia?"
      panelSubtitle="Saldo líquido diário (R$ mi / bi) · Âmbar = compra, grafite = saída"
      x="trading_date"
      y="inst_fin_mi"
      names={['Inst. Financeira']}
      prefix="R$ "
      suffix=" mi"
      decimals={1}
      signed={true}
      chartType="bar"
      axisCompact={true}
      autoScaleUnit={true}
      defaultZoomPoints={60}
      height={220}
    />
  </section>
</div>

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <TradingViewSeriesChart
      data={fluxo_diario_4_perfis}
      panelTitle="Quais pregões concentraram o maior volume financeiro na B3?"
      panelSubtitle="Giro financeiro diário total em R$ bi (1 ponta, 5 perfis BDI) · Âmbar = pregões ≥ 1,4× média da janela"
      x="trading_date"
      y="volume_total_bi"
      names={['Volume Total B3']}
      prefix="R$ "
      suffix=" bi"
      decimals={2}
      chartType="bar"
      axisCompact={true}
      highlightAboveAvg={true}
      zeroLine={false}
      defaultZoomPoints={60}
      height={240}
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
  <DailyFlowTable data={tabela_fluxo_diario} />
</div>
