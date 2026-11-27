# Architecture Decision Records (ADRs)

Este diretório registra as decisões arquiteturais relevantes do projeto **GringoLake**. Cada ADR documenta o contexto, a decisão tomada, as alternativas descartadas e as consequências conhecidas.

## Ciclo de Vida

```text
Proposed -> Accepted -> (Superseded by ADR-XXX | Deprecated)
```

- ADRs antigos não são apagados; quando uma decisão muda, cria-se um novo ADR referenciando e substituindo o anterior.

## Índice de Decisões

| ID | Título | Status | Data |
| --- | --- | --- | --- |
| [ADR-001](001-local-modern-data-stack-medallion.md) | Adotar Modern Data Stack local (Dagster + Polars + DuckDB + dbt) em arquitetura Medalhão | Accepted | 2026-11-25 |
| [ADR-002](002-official-b3-data-sources-only.md) | Consumir exclusivamente fontes oficiais da B3 para IBOV e Participação dos Investidores | Accepted | 2026-11-25 |
| [ADR-003](003-mtd-deaccumulation-using-ibov-calendar.md) | Desacumular o fluxo MTD do BDI usando o calendário oficial de pregões do Ibovespa | Accepted | 2026-11-25 |
| [ADR-004](004-dual-storage-duckdb-and-zstd-parquet.md) | Materialização dupla em DuckDB e Parquet ZSTD com resolução absoluta de caminhos no Dagster | Accepted | 2026-11-25 |
| [ADR-005](005-multi-layer-data-quality-and-zero-sum-invariant.md) | Estratégia de qualidade em três camadas com invariante contábil de soma zero da B3 | Accepted | 2026-11-25 |
| [ADR-006](006-strict-ma21-full-window-and-unified-brl-billions.md) | Rigor estatístico na MM21 (janela cheia obrigatória) e padronização monetária em R$ bilhões | Accepted (Decisão #2 substituída pelo ADR-007) | 2026-11-26 |
| [ADR-007](007-adaptive-brl-scale-and-tradingview-ui.md) | Escala monetária adaptativa (`R$ mi` / `R$ bi`) no frontend e gráficos interativos TradingView | Accepted | 2026-11-27 |
