# ADR-001: Adotar Modern Data Stack local (Dagster + Polars + DuckDB + dbt) em arquitetura Medalhão

## Status
Accepted

## Date
2026-11-25

## Context
O projeto precisa ingerir séries financeiras diárias da B3 (Ibovespa e Participação dos Investidores), aplicar regras de desacumulação mensal e janelas móveis (acumulado e Média Móvel de 21 pregões) e entregar tabelas analíticas confiáveis para construção de gráficos comparativos de curto e longo prazo.

Requisitos e restrições principais:
- Execução local sem custo de infraestrutura em nuvem e sem dependência obrigatória de Docker.
- Separação clara de responsabilidades por camadas (**Bronze / Silver / Gold**) com reprocessamento idempotente.
- Linhagem observável ponta a ponta (da extração HTTP até os marts de BI), agenda diária e validações de qualidade integradas ao grafo de execução.
- Ambiente disponível: Linux com Python 3.12 e `uv`.

## Decision
Utilizar **Dagster** (via `create-dagster`, `B3MarketDataComponent` e `DbtProjectComponent`) para orquestração, **Polars** (API lazy) para ingestão e validação na Bronze, **DuckDB** como engine analítica local e **dbt-duckdb** para modelagem SQL, testes de dados e testes unitários nas camadas Silver e Gold.

## Alternatives Considered

### Python enxuto (Polars + DuckDB sem orquestrador)
- Pros: Menor número de dependências e inicialização mais simples.
- Cons: Exige implementar manualmente linhagem entre camadas, metadados por execução, agenda pós-SLA da B3 e catálogo visual de Asset Checks.
- Rejected: O objetivo exige padrões completos de engenharia de dados (orquestração declarativa, observabilidade e linhagem nativa).

### Airflow + PySpark + Delta Lake (via Docker)
- Pros: Padrão consolidado em ambientes corporativos distribuídos.
- Cons: Alto consumo de memória e complexidade operacional para um volume diário de poucos megabytes (milhares de pregões), além de exigir daemon Docker ativo.
- Rejected: Sobrecarga operacional desproporcional ao volume de dados do domínio.

### Cloud Data Warehouse gerenciado (BigQuery / Databricks / Snowflake)
- Pros: Escalabilidade elástica e governança corporativa gerenciada.
- Cons: Introduz custo recorrente, gestão de credenciais em nuvem e acoplamento a provedor externo antes da validação local dos gráficos.
- Rejected: O design em dbt SQL + Parquet permite migração futura para nuvem com baixo atrito se necessário.

## Consequences
- O grafo completo (`bronze/* -> silver/* -> gold/*`) e os 40 Asset Checks rodam localmente em poucos segundos (~2s na transformação dbt) e podem ser inspecionados via `uv run dg dev`.
- Todas as dependências ficam isoladas e reproduzíveis em `pyproject.toml` e `uv.lock`.
- `DbtProjectComponent` exige atenção à resolução de caminhos relativos ao executar a partir de `.local_defs_state` (tratado na [ADR-004](004-dual-storage-duckdb-and-zstd-parquet.md)).
- A escala fica restrita a máquina única; para volumes de terabytes seria necessário trocar o adapter dbt e o storage Bronze para nuvem/objeto distribuído.
