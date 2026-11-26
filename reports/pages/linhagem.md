---
title: Linhagem e Qualidade — GringoLake
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Qualidade de Dados e Linhagem Medalhão</h1>
    <p class="page-subtitle">Auditoria da desacumulação MTD → Diário, cobertura de pregões e invariante contábil soma-zero da B3</p>
  </div>

  <div class="controls-bar">
    <div class="controls-left">
      <span class="status-chip"><span class="status-chip-accent">Stack</span> · Dagster + Polars + DuckDB + dbt</span>
      <span class="status-chip"><span class="status-chip-accent">Fontes</span> · 100% B3 Oficial</span>
    </div>
    <div class="controls-right">
      <span class="status-chip"><span class="status-chip-accent">Schedule</span> · Seg–Sex 21:00 BRT</span>
    </div>
  </div>
</div>

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

<div class="kpi-grid-4">
  <KPITerminalCard data={kpi_qualidade} value="total_pregoes_ibov" dateCol="max_ibov_date" code="IBOV" title="Pregões IBOV (Silver)" decimals={0} subtitle="Calendário oficial B3" icon="trend" />
  <KPITerminalCard data={kpi_qualidade} value="pregoes_fluxo_validos" dateCol="max_flow_date" code="GOLD" title="Pregões Fluxo (Gold)" decimals={0} subtitle="Diário desacumulado" icon="flow" />
  <KPITerminalCard data={kpi_qualidade} value="max_residuo_k_brl" code="ZERO-SUM" title="Resíduo Máx. Soma-Zero" prefix="R$ " suffix=" mil" decimals={2} subtitle="Tolerância ≤ R$ 20 mil" icon="activity" />
  <KPITerminalCard data={kpi_qualidade} value="total_perfis" code="DIM" title="Perfis Oficiais B3" decimals={0} subtitle="dim_investor_type" icon="users" />
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
    <h2 class="terminal-panel-title">Métodos de Desacumulação MTD → Diário (Silver)</h2>
    <p class="terminal-panel-sub">Distribuição dos pregões em int_b3_investor_flow_daily conforme ADR-003</p>
    <DataTable data={auditoria_derivacao} rows=10>
      <Column id=metodo_derivacao title="Método" />
      <Column id=pregoes title="Pregões" fmt=num0 />
      <Column id=registros title="Linhas" fmt=num0 />
      <Column id=primeira_data title="Início" />
      <Column id=ultima_data title="Fim" />
    </DataTable>
  </section>

  <section class="terminal-panel">
    <h2 class="terminal-panel-title">Auditoria Diária do Invariante Soma-Zero (B3)</h2>
    <p class="terminal-panel-sub">Soma de compras vs. vendas das 5 categorias em cada pregão (resíduo esperado próximo de zero)</p>
    <DataTable data={auditoria_soma_zero} rows=10>
      <Column id=pregao title="Pregão" />
      <Column id=perfis title="Perfis" fmt=num0 />
      <Column id=total_compras_bi title="Compras (R$ bi)" fmt=num2 />
      <Column id=total_vendas_bi title="Vendas (R$ bi)" fmt=num2 />
      <Column id=residuo_k_brl title="Resíduo (R$ mil)" fmt=num2 />
    </DataTable>
  </section>
</div>
