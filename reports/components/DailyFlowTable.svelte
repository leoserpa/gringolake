<script>
  export let data = [];
  export let title = 'Como ficou o saldo diário detalhado de todos os perfis?';
  export let subtitle =
    'Histórico pregão a pregão (R$ mi / bi) · Soma das 5 categorias oficiais fecha em zero (tolerância ≤ R$ 20 mil) · Atualização às 21h BRT';

  const PAGE_STEP = 100;

  const PROFILE_COLS = [
    { id: 'estrang_mi', label: 'Estrangeiro', phrases: ['estrangeiro', 'estrang', 'gringo'] },
    { id: 'pf_mi', label: 'Pessoa Física', phrases: ['pessoa fisica', 'pessoa', 'fisica', 'pf', 'p.f.'] },
    { id: 'instit_mi', label: 'Institucional', phrases: ['institucional', 'instit'] },
    {
      id: 'inst_fin_mi',
      label: 'Inst. Financeira',
      phrases: ['inst. financeira', 'inst financeira', 'inst fin', 'financeira', 'financeiro', 'banco'],
    },
    { id: 'outros_mi', label: 'Outros', phrases: ['outros', 'outro'] },
  ];

  const MULTI_WORD_PHRASES = [
    { phrase: 'inst. financeira', colId: 'inst_fin_mi' },
    { phrase: 'inst financeira', colId: 'inst_fin_mi' },
    { phrase: 'pessoa fisica', colId: 'pf_mi' },
    { phrase: 'inst fin', colId: 'inst_fin_mi' },
  ];

  let query = '';
  let visibleLimit = PAGE_STEP;

  $: rows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  function normalizeText(str) {
    return String(str ?? '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .trim();
  }

  function formatDateShort(d) {
    if (!d) return '—';
    const iso = d instanceof Date ? d.toISOString().slice(0, 10) : String(d).slice(0, 10);
    if (iso.length < 10) return iso;
    return `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}`;
  }

  function formatIbov(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '—';
    return `${Math.round(Number(v)).toLocaleString('pt-BR')} pts`;
  }

  function formatFlowFromMi(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '—';
    const num = Number(v);
    if (Math.abs(num) < 0.05) return 'R$ 0';
    const sign = num < 0 ? '-' : '+';
    const abs = Math.abs(num);
    if (abs >= 999.95) {
      return `${sign}R$ ${(abs / 1000).toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })} bi`;
    }
    return `${sign}R$ ${abs.toLocaleString('pt-BR', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    })} mi`;
  }

  function signClass(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return 'neutral';
    const num = Number(v);
    if (num > 0.05) return 'pos';
    if (num < -0.05) return 'neg';
    return 'neutral';
  }

  function parseQuery(rawQuery) {
    const qNorm = normalizeText(rawQuery);
    if (!qNorm) {
      return { activeCols: PROFILE_COLS, remainingTokens: [] };
    }

    const matchedIds = new Set();
    let working = qNorm;

    for (const item of MULTI_WORD_PHRASES) {
      if (working.includes(item.phrase)) {
        matchedIds.add(item.colId);
        working = working.split(item.phrase).join(' ');
      }
    }

    const tokens = working.split(/\s+/).filter(Boolean);
    const remainingTokens = [];

    for (const tok of tokens) {
      let tokMatchedProfile = false;
      for (const col of PROFILE_COLS) {
        const hit = col.phrases.some(
          (p) => p === tok || (tok.length >= 3 && p.startsWith(tok))
        );
        if (hit) {
          matchedIds.add(col.id);
          tokMatchedProfile = true;
        }
      }
      if (!tokMatchedProfile) {
        remainingTokens.push(tok);
      }
    }

    const matchedCols = PROFILE_COLS.filter((c) => matchedIds.has(c.id));
    return {
      activeCols: matchedCols.length > 0 ? matchedCols : PROFILE_COLS,
      remainingTokens,
    };
  }

  $: parsedSearch = parseQuery(query);
  $: activeCols = parsedSearch.activeCols;

  $: filteredRows =
    parsedSearch.remainingTokens.length === 0
      ? rows
      : rows.filter((r) => {
          const hayDateBr = normalizeText(formatDateShort(r.pregao));
          const hayDateIso = normalizeText(r.pregao);
          const hayIbov = normalizeText(formatIbov(r.ibov_close));
          return parsedSearch.remainingTokens.every(
            (tok) => hayDateBr.includes(tok) || hayDateIso.includes(tok) || hayIbov.includes(tok)
          );
        });

  $: {
    query;
    rows;
    visibleLimit = PAGE_STEP;
  }

  $: visibleRows = filteredRows.slice(0, visibleLimit);
  $: hasMoreRows = filteredRows.length > visibleLimit;

  function exportCsv() {
    if (!filteredRows.length) return;
    const headers = ['pregao', 'ibov_close', ...activeCols.map((c) => c.id)];
    const lines = [headers.join(',')];
    for (const r of filteredRows) {
      const vals = headers.map((h) => {
        const raw = h === 'pregao' ? formatDateShort(r[h]) : r[h] ?? '';
        return `"${String(raw).replace(/"/g, '""')}"`;
      });
      lines.push(vals.join(','));
    }
    const blob = new Blob([`\uFEFF${lines.join('\n')}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'gringolake_fluxo_diario_b3.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
</script>

<section class="terminal-panel daily-panel" aria-labelledby="daily-flow-title">
  <div class="daily-root">
    <div class="daily-head">
      <div class="daily-title-block">
        <h2 id="daily-flow-title" class="terminal-panel-title" style="margin: 0 0 4px 0;">
          <span>{title}</span>
        </h2>
        {#if subtitle}
          <p class="terminal-panel-sub" style="margin: 0;">{subtitle}</p>
        {/if}
      </div>

      <div class="daily-actions">
        <input
          type="search"
          class="daily-search"
          bind:value={query}
          placeholder="Buscar perfil ou data..."
          aria-label="Buscar perfil ou data"
        />
        <button type="button" class="daily-export" on:click={exportCsv}>Exportar CSV</button>
      </div>
    </div>

    <div class="daily-scroll" role="region" tabindex="0" aria-labelledby="daily-flow-title">
      <table class="daily-table" class:is-filtered={activeCols.length < PROFILE_COLS.length}>
        <thead>
          <tr>
            <th scope="col">Pregão</th>
            <th scope="col" class="num">IBOV</th>
            {#each activeCols as col (col.id)}
              <th scope="col" class="num">{col.label}</th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#if visibleRows.length === 0}
            <tr>
              <td colspan={2 + activeCols.length} class="empty-row">
                Nenhum pregão encontrado para "{query.trim()}".
              </td>
            </tr>
          {:else}
            {#each visibleRows as row}
              <tr>
                <th scope="row" class="mono date-col">{formatDateShort(row.pregao)}</th>
                <td class="mono num ibov-col">{formatIbov(row.ibov_close)}</td>
                {#each activeCols as col (col.id)}
                  <td class={`mono num ${signClass(row[col.id])}`}>
                    {formatFlowFromMi(row[col.id])}
                  </td>
                {/each}
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>

    <div class="daily-foot">
      <span>
        Mostrando {visibleRows.length} de {filteredRows.length}
        {filteredRows.length === 1 ? 'pregão oficial B3' : 'pregões oficiais B3'}
        {#if activeCols.length < PROFILE_COLS.length}
          · Perfil: {activeCols.map((c) => c.label).join(', ')}
        {/if}
      </span>
      <div class="daily-foot-right">
        {#if hasMoreRows}
          <button type="button" class="daily-more" on:click={() => (visibleLimit += PAGE_STEP)}>
            Carregar +{Math.min(PAGE_STEP, filteredRows.length - visibleLimit)}
          </button>
        {/if}
        <span class="scroll-hint">Deslize na tabela →</span>
      </div>
    </div>
  </div>
</section>

<style>
  .daily-panel {
    margin-block-end: 20px;
  }

  .daily-head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px 16px;
    margin-block-end: 18px;
  }

  .daily-title-block {
    min-inline-size: 0;
    flex: 1 1 320px;
  }

  .daily-actions {
    display: flex;
    flex-wrap: nowrap;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .daily-search {
    min-block-size: max(36px, var(--target-size, 36px));
    inline-size: 225px;
    max-inline-size: 100%;
    padding: 6px 14px;
    border-radius: 999px;
    border: 1px solid #3a3a3f;
    background: #222222;
    color: #f8f8f8;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 12px;
    box-sizing: border-box;
  }

  .daily-search::placeholder {
    color: #767676;
  }

  .daily-export,
  .daily-more {
    min-block-size: max(36px, var(--target-size, 36px));
    padding: 6px 16px;
    border-radius: 999px;
    border: 1px solid #45454a;
    background: #343434;
    color: #f8f8f8;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    white-space: nowrap;
    transition: background-color 0.16s ease, border-color 0.16s ease;
  }

  .daily-more {
    min-block-size: max(30px, var(--target-size, 30px));
    padding: 4px 13px;
    font-size: 11.5px;
  }

  .daily-export:hover,
  .daily-more:hover {
    background: #3e3e42;
    border-color: #5a5a60;
  }

  .daily-search:focus-visible,
  .daily-export:focus-visible,
  .daily-more:focus-visible,
  .daily-scroll:focus-visible {
    outline: 2px solid #f2b94b;
    outline-offset: 2px;
  }

  .daily-root {
    container-type: inline-size;
    inline-size: 100%;
    min-inline-size: 0;
  }

  .daily-scroll {
    max-inline-size: 100%;
    max-block-size: 380px;
    overflow: auto;
    scrollbar-gutter: stable;
    -webkit-overflow-scrolling: touch;
    --scrollbar-thumb: #858592;
    --scrollbar-track: #202022;
    scrollbar-width: thin;
    scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);
  }

  @supports not (scrollbar-color: auto) {
    .daily-scroll {
      scrollbar-width: auto;
    }

    .daily-scroll::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }

    .daily-scroll::-webkit-scrollbar-thumb {
      background: var(--scrollbar-thumb);
      border-radius: 999px;
    }

    .daily-scroll::-webkit-scrollbar-track {
      background: var(--scrollbar-track);
      border-radius: 999px;
    }
  }

  .daily-table {
    inline-size: 100%;
    min-inline-size: 740px;
    border-collapse: separate;
    border-spacing: 0;
  }

  .daily-table.is-filtered {
    min-inline-size: 420px;
  }

  .daily-table thead th {
    position: sticky;
    inset-block-start: 0;
    z-index: 2;
    background: #2b2b2b;
    text-align: left;
    padding: 10px 12px;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #767676;
    border-block-end: 1px solid #3a3a3f;
    white-space: nowrap;
  }

  .daily-table thead th:first-child {
    position: sticky;
    inset-inline-start: 0;
    z-index: 3;
    padding-inline-start: 0;
  }

  .daily-table thead th.num {
    text-align: right;
  }

  .daily-table thead th:last-child {
    padding-inline-end: 14px;
  }

  .daily-table tbody th,
  .daily-table tbody td {
    padding: 13px 12px;
    font-size: 12.5px;
    border-block-end: 1px solid #343438;
    white-space: nowrap;
    background: #2b2b2b;
  }

  .daily-table tbody th.date-col {
    position: sticky;
    inset-inline-start: 0;
    z-index: 1;
    text-align: left;
    padding-inline-start: 0;
    font-weight: 600;
    color: #f8f8f8;
  }

  .daily-table tbody td:last-child {
    padding-inline-end: 14px;
  }

  .daily-table tbody tr:hover th,
  .daily-table tbody tr:hover td {
    background: #323236;
  }

  .daily-table tbody tr:last-child th,
  .daily-table tbody tr:last-child td {
    border-block-end: 0;
  }

  .daily-table tbody td.empty-row {
    text-align: center;
    padding: 28px 16px;
    color: #8a8a93;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 12.5px;
  }

  .daily-table .mono {
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  .daily-table .num {
    text-align: right;
    font-weight: 600;
  }

  .daily-table .ibov-col {
    color: #b8b8c2;
    font-weight: 600;
  }

  .daily-table .pos {
    color: #f2b94b;
  }

  .daily-table .neg {
    color: #e5e5e5;
  }

  .daily-table .neutral {
    color: #767676;
  }

  .daily-foot {
    margin-block-start: 14px;
    padding-block-start: 12px;
    border-block-start: 1px solid #343438;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 8px 16px;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 11.5px;
    color: #767676;
  }

  .daily-foot-right {
    display: inline-flex;
    align-items: center;
    gap: 10px;
  }

  .scroll-hint {
    display: none;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 10.5px;
    color: #f2b94b;
  }

  @container (width < 760px) {
    .daily-scroll {
      max-block-size: 360px;
    }

    .daily-table {
      min-inline-size: 680px;
    }

    .daily-table.is-filtered {
      min-inline-size: 360px;
    }

    .daily-table thead th,
    .daily-table tbody th,
    .daily-table tbody td {
      padding: 11px 10px;
      font-size: 11.5px;
    }

    .daily-table thead th:first-child {
      padding-inline: 0 12px;
      border-inline-end: 1px solid #363636;
    }

    .daily-table tbody th.date-col {
      padding-inline: 0 12px;
      border-inline-end: 1px solid #363636;
    }

    .scroll-hint {
      display: inline;
    }
  }

  @container (width < 560px) {
    .daily-actions {
      flex-wrap: wrap;
      inline-size: 100%;
    }

    .daily-search {
      flex: 1 1 180px;
      inline-size: auto;
    }

    .daily-export {
      flex-shrink: 0;
    }
  }
</style>
