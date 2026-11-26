# ADR-004: Materialização dupla em DuckDB e Parquet ZSTD com resolução absoluta de caminhos no Dagster

## Status
Accepted

## Date
2026-11-25

## Context
A camada de consumo (BI, notebooks Python/Polars, Power BI, Metabase ou Evidence) pode se conectar de formas distintas: ferramentas SQL preferem um banco analítico (`gringolake.duckdb`), enquanto pipelines Python/lakehouse e ferramentas de arquivo preferem tabelas colunares portáveis em `data/silver/*.parquet` e `data/gold/*.parquet`.

Além disso, ao integrar o projeto dbt ao Dagster via `DbtProjectComponent` (um `StateBackedComponent`), o Dagster copia o projeto dbt para `src/gringolake/defs/.local_defs_state/DbtProjectComponent__dbt_gringolake__/project/` em tempo de execução. Caminhos relativos como `../data/warehouse/gringolake.duckdb` passam a resolver dentro de `.local_defs_state/` e falham com `IOException: No such file or directory`.

## Decision
1. Materializar todos os modelos Silver e Gold como tabelas no DuckDB (`data/warehouse/gringolake.duckdb`, schemas `silver` e `gold`) e exportar automaticamente cada tabela para Parquet com compressão ZSTD (`data/silver/<model>.parquet` e `data/gold/<model>.parquet`) via post-hook dbt ([export_parquet.sql](../../dbt_gringolake/macros/export_parquet.sql)), restrito a `execute and flags.WHICH in ('run', 'build')`.
2. Configurar caminhos no dbt via variáveis de ambiente com fallback relativo (`GRINGOLAKE_DATA_DIR` e `GRINGOLAKE_DUCKDB_PATH` em `profiles.yml`, `_sources.yml` e `export_parquet.sql`), escapando apóstrofos (`replace("'", "''")`) antes de interpolar caminhos em literais SQL do DuckDB.
3. Em `src/gringolake/definitions.py`, preencher `os.environ.setdefault(...)` com os caminhos absolutos resolvidos por `get_lakehouse_paths()` antes de chamar `load_from_defs_folder()`.

## Alternatives Considered

### Usar apenas tabelas internas no DuckDB (sem Parquet na Silver/Gold)
- Pros: Elimina o macro de post-hook e evita duplicação física em disco.
- Cons: Obriga qualquer consumidor externo a abrir o arquivo DuckDB (que possui lock exclusivo durante escrita) em vez de ler arquivos Parquet imutáveis em paralelo.
- Rejected: Para um volume local de dezenas de kilobytes, o custo de disco do Parquet é desprezível e aumenta muito a interoperabilidade.

### Usar `materialized='external'` no `dbt-duckdb` (apenas Parquet, sem tabelas DuckDB)
- Pros: Um único artefato físico por modelo.
- Cons: Ferramentas de BI conectadas ao arquivo `.duckdb` precisam lidar com views sobre caminhos externos e perdem simplicidade de catálogo SQL nativo.
- Rejected: A materialização dupla entrega o melhor dos dois mundos com overhead inferior a 50ms por execução.

### Hardcodar caminhos absolutos dentro de `profiles.yml` e `_sources.yml`
- Pros: Resolve o problema do `.local_defs_state` imediatamente.
- Cons: Quebra portabilidade entre máquinas diferentes e impede isolamento em CI/testes.
- Rejected: Variáveis de ambiente com `setdefault` em `definitions.py` mantêm o repositório 100% portável.

## Consequences
- O pipeline funciona de forma idêntica tanto via Dagster (`uv run dg launch` / `uv run dg dev`) quanto via dbt standalone (`cd dbt_gringolake && uv run dbt build --profiles-dir .`).
- Os arquivos Parquet em `data/silver/` e `data/gold/` ficam sempre sincronizados com as tabelas do DuckDB após cada `run`/`build`, sem disparar exportação durante `dbt parse` ou `dbt test`.
- A exportação `COPY ... TO` reescreve o arquivo Parquet por completo a cada build — adequado para o volume atual, mas exigiria particionamento incremental caso o volume crescesse para dezenas de milhões de linhas.
