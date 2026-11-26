# ADR-005: Estratégia de qualidade em três camadas com invariante contábil de soma zero da B3

## Status
Accepted

## Date
2026-11-25

## Context
Erros em pipelines financeiros raramente quebram por exceção de sintaxe; eles se manifestam silenciosamente como unidades trocadas (`R$ mil` vs. `R$ bilhões`), desalinhamento de pregões, perda de uma categoria de investidor ou duplicação de registros que corrompem somas acumuladas.

## Decision
Implementar defesa em profundidade com três camadas complementares de validação:
1. **Camada de Código (Python / `pytest`):** testes determinísticos offline para parsing de números no padrão BR (`100.774,57`), extração de `reference_date`, escrita atômica Parquet/JSON sem arquivos `.tmp` residuais e validação de schema de backfill.
2. **Camada Bronze (Dagster Asset Checks):** validação imediata pós-ingestão verificando unicidade de pregões do IBOV, faixa plausível (`> 10.000` pts), presença simultânea das 5 categorias oficiais B3, ausência de volumes negativos e fechamento da participação percentual (`compras + vendas`) em `100% ± 1%`.
3. **Camadas Silver & Gold (dbt Unit Tests + Data Tests + Invariante Contábil):**
   - **2 dbt Unit Tests** executados em CI/dev (excluídos da execução de produção via `--exclude-resource-type unit_test` em `defs.yaml` para evitar compute redundante) validando a lógica SQL de desacumulação MTD, reset mensal, soma acumulada e MM21.
   - **38 dbt Data Tests** (mapeados automaticamente como Dagster Asset Checks via `enable_asset_checks: true`), incluindo o teste singular **`assert_b3_daily_flow_zero_sum`**, que garante que em todo pregão da Gold existam exatamente as 5 categorias de investidores e que a soma dos saldos líquidos diários de todas elas feche em zero dentro da tolerância de arredondamento da B3 (`|SUM(daily_net_flow_k_brl)| <= 20 R$ mil`).

## Alternatives Considered

### Validar apenas com testes genéricos `unique` e `not_null` no dbt
- Pros: Rápido de configurar.
- Cons: Não detecta erro de sinal na desacumulação MTD, troca de colunas entre compra e venda ou perda silenciosa de uma categoria no BDI.
- Rejected: A invariante contábil de soma zero (`assert_b3_daily_flow_zero_sum`) detecta imediatamente qualquer erro de parsing, filtro ou subtração MTD em dados reais.

### Adicionar Great Expectations ou Soda como framework separado de qualidade
- Pros: Catálogo amplo de expectativas prontas e relatórios HTML dedicados.
- Cons: Duplica responsabilidades já cobertas nativamente por Dagster Asset Checks + dbt Data/Unit Tests, aumentando dependências e tempo de manutenção.
- Rejected: Manter qualidade nativa em Dagster + dbt mantém todos os alertas centralizados na mesma UI e no mesmo DAG.

## Consequences
- Total de **55 verificações automatizadas** (`15 pytest` + `2 Bronze Asset Checks` + `38 dbt Data Tests` + `2 dbt Unit Tests`, com os 38 data tests visíveis também no Dagster como Asset Checks).
- Nos dados reais atuais da B3 (`19` pregões diários válidos), o resíduo máximo observado no teste de soma zero foi de `3,00 R$ mil` (bem abaixo do limite de `20 R$ mil`).
- Caso a B3 crie uma 6ª categoria oficial de investidores no futuro, o check `check_bronze_investor_flow_completeness`, o teste `accepted_values` na Silver e `assert_b3_daily_flow_zero_sum` acusarão imediatamente a mudança para atualização controlada da dimensão.
