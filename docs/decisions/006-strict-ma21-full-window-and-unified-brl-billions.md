# ADR-006: Rigor estatístico na MM21 (janela cheia obrigatória) e padronização monetária em R$ bilhões

## Status
Accepted

## Date
2026-11-26

## Context
Durante a auditoria financeira do dashboard e da camada Gold com dados reais da B3 (`2026-10-23` a `2026-11-23`), foram identificados dois riscos de interpretação analítica inaceitáveis para dados de mercado financeiro:

1. **Média Móvel de 21 pregões (MM21) parcial durante aquecimento (`< 21` pregões):**
   - Como a API BDI da B3 retém `D-21` pregões online (`20` arquivos) e o primeiro pregão da janela truncada é descartado por `missing_prior_trading_day` ([ADR-003](003-mtd-deaccumulation-using-ibov-calendar.md)), o bootstrap inicial produz `19` pregões válidos na Gold até que novos pregões sejam acumulados às 21h BRT.
   - Antes desta decisão, `fct_ibov_investor_flow_daily` e `mart_ibov_vs_pf_short_term` calculavam `avg(cum_net_flow_k_brl) over (rows between 20 preceding and current row)` sem exigir 21 observações, emitindo uma média expansiva parcial (de 1 a 19 pregões) rotulada como `MM21` e disparando sinais `acima_mm21` / `abaixo_mm21` / `is_pf_below_ma21` antes de existir uma janela estatística completa de 21 pregões.
2. **Mistura de unidades monetárias (`R$ mi` e `R$ bi`) na camada de visualização:**
   - Embora a B3 publique valores brutos em `R$ mil` (`*_k_brl`), exibir `R$ mi` em alguns cards/células (`-R$ 1.499,9 mi`, `+R$ 683,6 mi`) lado a lado com `R$ bi` (`-R$ 5,91 bi`, `-R$ 13,92 bi`) — ou converter o eixo Y para `bi` enquanto o cabeçalho do gráfico indica `mi` — induz erro de leitura de ordem de grandeza.

## Decision
1. **MM21 estrita de 21 pregões na camada Gold:**
   - Em `fct_ibov_investor_flow_daily` e `mart_ibov_vs_pf_short_term`, só emitir `cum_net_flow_ma21_*`, `flow_vs_ma21_spread_bi_brl` e `pf_cum_short_term_ma21_*` quando `ma21_window_obs_count = 21` (`has_full_ma21_window = true`).
   - Quando `ma21_window_obs_count < 21`, retornar `NULL` nas colunas numéricas da MM21, `flow_vs_ma21_signal = 'em_formacao'` e `is_pf_below_ma21 = false`.
   - Expor `ma21_window_obs_count` em `fct_ibov_investor_flow_daily`, `mart_ibov_vs_investors_wide` e `mart_ibov_vs_pf_short_term` para que o dashboard informe com precisão o progresso da janela (ex.: `19/21 pregões`).
   - Proteger essa regra com o teste singular dbt `assert_ma21_window_integrity` e testes unitários cobrindo tanto a fase de aquecimento quanto a transição deslizante nos pregões 21 e 22.
2. **Unidade monetária consistente por contexto (padrão de mesa bancária brasileira, sem mistura interna):**
   - **Fluxos acumulados e consolidados mensais (`Panorama`, `Curto Prazo`, `Comparativo` e `MonthlyFlowTable`):** 100% em **`R$ bilhões` (`R$ bi`, 2 casas decimais)** — incluindo categorias menores como `Inst. Financeira` (`+R$ 0,68 bi` em `2026-11`), eliminando qualquer mistura de `mi` e `bi` na mesma tabela ou gráfico.
   - **Fluxo diário isolado por pregão (`Fluxo Diário` — KPIs, gráficos de barras, eixos Y, tooltips e tabela diária):** 100% em **`R$ milhões` (`R$ mi`, 1 casa decimal)**, padrão adotado por mesas institucionais de ações no Brasil para preservar leitura de sensibilidade em pregões de menor giro (`+R$ 31,3 mi`, `-R$ 104,9 mi`, `-R$ 1.499,9 mi`), sem nunca converter o eixo Y para `bi` no mesmo gráfico.
   - **Auditoria contábil soma-zero (`Linhagem` e badge `Resíduo (R$ mil)`):** explicitamente em **`R$ mil`**, onde a tolerância da B3 é `≤ R$ 20 mil`.

## Alternatives Considered

### Manter média expansiva parcial com rótulo "MM21 (parcial)"
- Pros: Mostra uma linha tracejada desde o primeiro dia de coleta sem esperar 21 pregões.
- Cons: Gera sinais direcionais (`acima_mm21` / `abaixo_mm21`) e faixas de alerta matematicamente inválidos para uma janela de 21 pregões; um usuário pode interpretar o sinal como cruzamento real de tendência mensal.
- Rejected: Em finanças quantitativas, um indicador não definido deve ser `NULL` (`em_formacao`), nunca um substituto parcial disfarçado.

### Manter formatação automática `R$ mi` / `R$ bi` por magnitude dentro da mesma tabela ou gráfico
- Pros: Evita zeros à esquerda em categorias menores (`+R$ 0,03 bi` vs. `+R$ 31,3 mi`).
- Cons: Mistura escalas de 1.000× na mesma coluna ou no mesmo gráfico (`+R$ 683,6 mi` ao lado de `-R$ 5,91 bi`), aumentando o risco de erro cognitivo na leitura rápida de fluxo de mercado.
- Rejected: A uniformidade dimensional dentro de cada tela/tabela (`R$ bi` nos acumulados/mensal, `R$ mi` no fluxo diário isolado e `R$ mil` na auditoria) prioriza precisão comparativa sobre estética numérica isolada.

## Consequences
- Durante os primeiros 20 pregões de uma série nova (ou rebased em `mart_ibov_vs_pf_short_term`), as colunas `*_ma21_*` são legitimamente `NULL`; testes `not_null` ingênuos nessas colunas foram substituídos pelo invariante completo `assert_ma21_window_integrity`.
- Assim que o pipeline completar 21 pregões válidos na Gold (automaticamente às 21h BRT), a curva MM21 e os sinais `Acima MM21` / `Abaixo MM21` passam a renderizar automaticamente sem intervenção manual.
- Cada página, gráfico e tabela em `reports/` usa uma única unidade fixa do início ao fim (`R$ bi` nos acumulados e consolidado mensal; `R$ mi` no fluxo diário; `R$ mil` na auditoria contábil soma-zero), eliminando ambiguidade entre eixos, cabeçalhos e células.
