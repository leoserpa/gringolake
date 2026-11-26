# ADR-002: Consumir exclusivamente fontes oficiais da B3 para IBOV e Participação dos Investidores

## Status
Accepted

## Date
2026-11-25

## Context
Os gráficos-alvo cruzam o fechamento diário do Ibovespa (`IBOV`) com o fluxo acumulado de investidores (Estrangeiro, Institucional, Pessoa Física, Instituições Financeiras e Outros) em `R$ mil` e `R$ bilhões`.

Requisito explícito de negócio:
- Utilizar apenas fontes oficiais da **B3**, descartando agregadores não oficiais de terceiros (como Dados de Mercado ou Yahoo Finance).

Restrições descobertas ao inspecionar as APIs públicas oficiais da B3:
1. `GET https://sistemaswebb3-listados.b3.com.br/indexStatisticsProxy/IndexCall/GetPortfolioDay/{base64}` retorna o histórico oficial diário completo do IBOV ano a ano (validado de `2020` a `2026`, coincidindo exatamente com os pontos exibidos nos gráficos de referência, ex.: `01/12/2021 = 100.774,57`).
2. `POST https://arquivos.b3.com.br/bdi/table/SharesInvesVolum/{YYYY-MM-DD}/{YYYY-MM-DD}/1/50` retorna a tabela oficial do Boletim Diário de Informações (BDI), porém possui três características críticas:
   - Retenção deslizante de **`limitDate: D-21`** (aproximadamente 20–21 pregões disponíveis online por vez).
   - Defasagem padrão **D+2** entre `publication_date` e a data do pregão de referência (`reference_date`).
   - SLA oficial de divulgação às **`20:00:00` BRT** (informado no campo `configuration.SLA` do payload).

## Decision
1. Extrair **IBOV** diretamente de `GetPortfolioDay` (cacheando anos encerrados em Parquet na Bronze e atualizando o ano corrente) e **Participação dos Investidores** diretamente de `SharesInvesVolum`.
2. Persistir cada snapshot diário na Bronze particionado por `publication_date=YYYY-MM-DD/` sem apagar partições antigas, acumulando histórico próprio permanente para superar a janela `D-21` da B3.
3. Manter a pasta `data/landing/b3_investor_flow_backfill/` para ingestão opcional de arquivos históricos oficiais do BDI em CSV/Parquet, marcados com `_source_system = 'b3_official_backfill'`.
4. Agendar a atualização diária em `0 21 * * 1-5` (`America/Sao_Paulo`), 1 hora após o SLA oficial das 20h da B3.

## Alternatives Considered

### API / scraping de agregadores terceiros (Dados de Mercado + Yahoo Finance)
- Pros: Histórico longo pronto em uma única chamada HTTP sem necessidade de desacumulação MTD.
- Cons: Não é fonte primária oficial da B3; risco de divergência metodológica, quebra de HTML ou cobrança por token.
- Rejected: Requisito explícito de consumir exclusivamente fontes oficiais da B3.

### Scraping com navegador headless (Playwright/Selenium) nas páginas institucionais da B3
- Pros: Emula navegação humana quando não há API estruturada.
- Cons: Frágil a mudanças de DOM, lento e exige binários de navegador instalados.
- Rejected: Os endpoints JSON oficiais (`GetPortfolioDay` e `bdi/table/SharesInvesVolum`) respondem diretamente via HTTPS com validação TLS padrão (`httpx`).

## Consequences
- Fidelidade 100% às publicações oficiais da B3, com trilha de auditoria preservada em JSON bruto (`raw_json/*.json`) + hash SHA-256 do payload na camada Bronze.
- Na primeira execução sem arquivos na pasta de backfill, o histórico de fluxo de investidores começa limitado à janela `D-21` online da B3 (~19 pregões diários válidos) e cresce a cada pregão executado; para reconstruir anos anteriores (ex.: 2020–2025), é necessário fornecer arquivos oficiais do BDI na pasta de landing.
- Como os endpoints são proxies internos usados pelo portal público da B3 (sem contrato OpenAPI versionado), mudanças de formato são detectadas rapidamente pelos testes de contrato e pelos Asset Checks da Bronze.
