# ADR-007: Escala monetária adaptativa (`R$ mi` / `R$ bi`) no frontend e gráficos interativos TradingView

## Status
Accepted (substitui parcialmente a Decisão #2 do [ADR-006](006-strict-ma21-full-window-and-unified-brl-billions.md) sobre unidades fixas na camada de apresentação; mantém integralmente a Decisão #1 do ADR-006 sobre rigor estatístico da MM21)

## Date
2026-11-27

## Context
No [ADR-006](006-strict-ma21-full-window-and-unified-brl-billions.md), adotamos unidades fixas separadas por página (`R$ bi` para acumulados e `R$ mi` para fluxo diário). Na prática de uso diário do dashboard Evidence.dev (`reports/`), surgiram dois problemas de legibilidade:

1. **Valores diários acima de `R$ 1 bi` (ex.: `+R$ 1.490,0 mi` ou `-R$ 1.660,0 mi`)** e **valores acumulados abaixo de `R$ 1 bi` (ex.: `R$ 0,03 bi` ou `-R$ 0,45 bi`)** exigiam conversão mental constante entre KPIs, gráficos e tabelas.
2. **Interatividade limitada em gráficos estáticos:** séries temporais longas (IBOV desde 2020, fluxo acumulado, comparativo entre perfis e relação fluxo estrangeiro × retorno IBOV) precisavam de zoom fluido, crosshair sincronizado, slider de janela e leitura clara em telas mobile.

## Decision
1. **Escala monetária adaptativa unificada na camada de apresentação (`reports/`):**
   - Valores absolutos `< R$ 999,95 mi` são exibidos em **`R$ mi`** (1 casa decimal, ex.: `+R$ 449,5 mi`).
   - Valores absolutos `>= R$ 999,95 mi` são exibidos em **`R$ bi`** (2 casas decimais, ex.: `+R$ 1,49 bi`).
   - Zero exato (`< 0,05 mi`) é exibido como **`R$ 0`**.
   - Os contratos das camadas Silver e Gold no DuckDB/Parquet **não mudam** (`*_k_brl` em `R$ mil` e `*_bi_brl` em `R$ bilhões`); apenas a formatação visual no frontend é adaptativa.
   - A auditoria soma-zero em `Linhagem` permanece explicitamente em **`R$ mil`**.
2. **Padronização de séries temporais com TradingView Lightweight Charts (`reports/components/TradingView*.svelte`):**
   - `TradingViewDualAxisChart`, `TradingViewSeriesChart`, `TradingViewIbovChart`, `TradingViewFlowReturnChart` e `TradingViewRangeSlider` passam a renderizar as séries temporais principais do dashboard, preservando o `<BarChart>` nativo do Evidence para gráficos categóricos (como participação no volume da B3).
3. **Tabelas e controles responsivos no tema Atelier Graphite:**
   - Formatação condicional limpa de acento único (`#f2b94b` positivo, `#e5e5e5` negativo, `#767676` neutro) aplicada uniformemente em `MonthlyFlowTable`, `DailyFlowTable`, `FlowExplorerTable` e `AnnualIbovTable`.
   - Controles de filtro com muitas opções (`perfil_foco` no `Comparativo`) usam `ProfileMenuControl.svelte`: barra horizontal no desktop (`> 900px`) e seletor dropdown compacto no mobile (`<= 900px`).

## Alternatives Considered

### Manter unidades fixas por página (ADR-006 original)
- **Prós:** zero ambiguidade de ordem de grandeza em colunas numéricas fixas.
- **Contras:** gera leituras poluídas como `+R$ 1.660,0 mi` em pregões de alto volume e `+R$ 0,03 bi` em perfis menores (`Outros` / `Inst. Financeira`).
- **Rejeitada:** o usuário solicitou expressamente escala única adaptativa entre KPIs, gráficos e tabelas para leitura direta.

### Centralizar a conversão na camada Gold do dbt
- **Prós:** frontend exibiria strings pré-formatadas.
- **Contras:** acoplaria formatação de UI a contratos analíticos numéricos, quebrando ordenação, exportação CSV numérica e consumo externo em BI/Python.
- **Rejeitada:** a camada Gold permanece puramente numérica (`*_bi_brl` / `*_k_brl`) e a formatação adaptativa fica isolada na camada de apresentação.

## Consequences
- **Positivas:** leitura homogênea entre KPIs, gráficos TradingView e tabelas; navegação responsiva em mobile sem quebra de barra de perfis; contratos dbt/DuckDB preservados sem breaking changes; lógica de formatação `mi`/`bi`, datas `pt-BR`, normalização de dados e exportação CSV centralizada em `reports/components/formatters.js` com suíte de testes unitários em `reports/tests/formatters.test.mjs` (`node --test`).
- **Atenções operacionais:** o build estático do Evidence.dev e os testes unitários do frontend passam a rodar também no workflow de CI (`.github/workflows/ci.yml`), evitando regressões em PRs antes do deploy no GitHub Pages.
