---
title: Linhagem e Qualidade — GringoLake
---

```sql kpi_qualidade
WITH ibov_stats AS (
    SELECT COUNT(*) AS total_pregoes_ibov, MAX(trading_date) AS max_ibov_date
    FROM gringolake.stg_b3_ibov_daily
),
gold_stats AS (
    SELECT COUNT(DISTINCT trading_date) AS pregoes_fluxo_validos, MAX(trading_date) AS max_flow_date
    FROM gringolake.fct_ibov_investor_flow_daily
),
zero_sum AS (
    SELECT MAX(ABS(daily_sum)) AS max_residuo_k_brl
    FROM (
        SELECT trading_date, SUM(daily_net_flow_k_brl) AS daily_sum
        FROM gringolake.fct_ibov_investor_flow_daily
        GROUP BY trading_date
    )
),
perfis AS (
    SELECT COUNT(*) AS total_perfis FROM gringolake.dim_investor_type
)
SELECT
    i.total_pregoes_ibov,
    i.max_ibov_date,
    g.pregoes_fluxo_validos,
    g.max_flow_date,
    z.max_residuo_k_brl,
    p.total_perfis
FROM ibov_stats i
CROSS JOIN gold_stats g
CROSS JOIN zero_sum z
CROSS JOIN perfis p
```

<div class="page-hero">
  <p class="page-eyebrow">GRINGOLAKE · LINHAGEM &amp; QUALIDADE</p>

  <div class="page-head-row">
    <div class="page-title-group">
      <h1 class="page-title">Qualidade &amp; Linhagem Medalhão</h1>
      <p class="page-subtitle">Auditoria do pipeline Dagster + Polars + DuckDB + dbt · Execução diária Seg–Sex às 21h BRT</p>
    </div>

    <div class="controls-right">
      <CounterBadge data={kpi_qualidade} value="max_residuo_k_brl" label="Resíduo (R$ mil)" decimals={1} />
    </div>
  </div>
</div>

<div class="kpi-grid-4">
  <KPITerminalCard data={kpi_qualidade} value="total_pregoes_ibov" dateCol="max_ibov_date" code="IBOV" title="Pregões IBOV (Silver)" decimals={0} subtitle="Calendário oficial B3" liveDot={true} />
  <KPITerminalCard data={kpi_qualidade} value="pregoes_fluxo_validos" dateCol="max_flow_date" code="GOLD" title="Pregões Fluxo (Gold)" decimals={0} subtitle="Diário desacumulado" focal={true} />
  <KPITerminalCard data={kpi_qualidade} value="max_residuo_k_brl" code="ZERO-SUM" title="Resíduo Máx. Soma-Zero" prefix="R$ " suffix=" mil" decimals={2} subtitle="Tolerância ≤ R$ 20 mil" />
  <KPITerminalCard data={kpi_qualidade} value="total_perfis" code="DIM" title="Perfis Oficiais B3" decimals={0} subtitle="dim_investor_type" />
</div>

```sql auditoria_derivacao
SELECT
    daily_derivation_method AS metodo_derivacao,
    COUNT(DISTINCT trading_date) AS pregoes,
    COUNT(*) AS registros,
    MIN(trading_date) AS primeira_data,
    MAX(trading_date) AS ultima_data
FROM gringolake.int_b3_investor_flow_daily
GROUP BY daily_derivation_method
ORDER BY pregoes DESC
```

```sql auditoria_soma_zero
SELECT
    trading_date AS pregao,
    COUNT(DISTINCT investor_type_code) AS perfis,
    ROUND(SUM(daily_purchases_k_brl) / 1000000.0, 3) AS total_compras_bi,
    ROUND(SUM(daily_sales_k_brl) / 1000000.0, 3) AS total_vendas_bi,
    ROUND(SUM(daily_net_flow_k_brl), 2) AS residuo_k_brl
FROM gringolake.fct_ibov_investor_flow_daily
GROUP BY trading_date
ORDER BY trading_date DESC
```

<div class="terminal-grid-1">
  <section class="terminal-panel">
    <h2 class="terminal-panel-title"><span class="panel-index">01</span><span>Como cada pregão foi desacumulado do MTD para diário?</span></h2>
    <p class="terminal-panel-sub">Distribuição dos métodos oficiais em int_b3_investor_flow_daily conforme ADR-003</p>
    <DataTable data={auditoria_derivacao} rows=10>
      <Column id=metodo_derivacao title="Método" />
      <Column id=pregoes title="Pregões" fmt=num0 />
      <Column id=registros title="Linhas" fmt=num0 />
      <Column id=primeira_data title="Início" />
      <Column id=ultima_data title="Fim" />
    </DataTable>
  </section>

  <section class="terminal-panel">
    <h2 class="terminal-panel-title"><span class="panel-index">02</span><span>As compras e vendas da B3 fecham em soma-zero todo dia?</span></h2>
    <p class="terminal-panel-sub">Auditoria contábil diária das 5 categorias oficiais (resíduo esperado ≤ R$ 20 mil)</p>
    <DataTable data={auditoria_soma_zero} rows=10>
      <Column id=pregao title="Pregão" />
      <Column id=perfis title="Perfis" fmt=num0 />
      <Column id=total_compras_bi title="Compras (R$ bi)" fmt=num2 />
      <Column id=total_vendas_bi title="Vendas (R$ bi)" fmt=num2 />
      <Column id=residuo_k_brl title="Resíduo (R$ mil)" fmt=num2 />
    </DataTable>
  </section>
</div>
