<script>
  export let data = [];
  export let title = 'Como o Ibovespa fechou em cada ano desde 2020?';
  export let subtitle =
    'Contagem oficial de pregões, abertura, mínima, máxima e variação percentual por ano calendário · Anos positivos destacados em âmbar';

  $: rows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  function toNumber(value) {
    if (value === null || value === undefined || value === '') return null;
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
  }

  function signClass(value) {
    const num = toNumber(value);
    if (num === null) return 'neutral';
    const normalized = Math.abs(num) < 0.005 ? 0 : num;
    if (normalized > 0) return 'pos';
    if (normalized < 0) return 'neg';
    return 'neutral';
  }

  function formatYear(value) {
    if (value === null || value === undefined || value === '') return '—';
    return String(value);
  }

  function formatInt(value) {
    const num = toNumber(value);
    if (num === null) return '—';
    return Math.round(num).toLocaleString('pt-BR');
  }

  function formatPts(value) {
    const num = toNumber(value);
    if (num === null) return '—';
    return `${Math.round(num).toLocaleString('pt-BR')} pts`;
  }

  function formatPctSigned(value) {
    const num = toNumber(value);
    if (num === null) return '—';
    const normalized = Math.abs(num) < 0.005 ? 0 : num;
    const sign = normalized > 0 ? '+' : normalized < 0 ? '-' : '';
    const absFormatted = Math.abs(normalized).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
    return `${sign}${absFormatted}%`;
  }

  function csvEscape(value) {
    const str = value === null || value === undefined ? '' : String(value);
    if (/[",;\n\r]/.test(str)) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  }

  function exportCsv() {
    if (!rows.length) return;
    const headers = [
      'ano',
      'pregoes',
      'abertura_pts',
      'fechamento_pts',
      'minima_pts',
      'maxima_pts',
      'variacao_pct'
    ];
    const lines = [
      headers.join(','),
      ...rows.map((row) =>
        [
          row.ano,
          row.pregoes,
          row.primeiro_fechamento,
          row.ultimo_fechamento,
          row.minima,
          row.maxima,
          row.retorno_anual_pct
        ]
          .map(csvEscape)
          .join(',')
      )
    ];
    const blob = new Blob([`\uFEFF${lines.join('\n')}`], {
      type: 'text/csv;charset=utf-8;'
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'gringolake_ibovespa_anual_b3.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
</script>

<section class="terminal-panel annual-ibov-panel" aria-labelledby="annual-ibov-title">
  <div class="annual-head">
    <div class="annual-title-block">
      <h2 id="annual-ibov-title" class="terminal-panel-title" style="margin: 0 0 4px 0;">
        {title}
      </h2>
      {#if subtitle}
        <p class="terminal-panel-sub" style="margin: 0;">{subtitle}</p>
      {/if}
    </div>
    <div class="annual-actions">
      <button type="button" class="export-btn" on:click={exportCsv} disabled={!rows.length}>
        Exportar CSV
      </button>
    </div>
  </div>

  <div class="annual-root">
    <div class="table-wrap">
      <table class="annual-table">
        <thead>
          <tr>
            <th scope="col" class="col-ano sticky-col">Ano</th>
            <th scope="col" class="num">Pregões</th>
            <th scope="col" class="num">Abertura</th>
            <th scope="col" class="num">Fechamento</th>
            <th scope="col" class="num">Mínima</th>
            <th scope="col" class="num">Máxima</th>
            <th scope="col" class="num col-var">Variação</th>
          </tr>
        </thead>
        <tbody>
          {#if rows.length === 0}
            <tr>
              <td colspan="7" class="empty-cell">Sem dados anuais disponíveis.</td>
            </tr>
          {:else}
            {#each rows as row (row.ano)}
              <tr>
                <th scope="row" class="col-ano sticky-col">{formatYear(row.ano)}</th>
                <td class="num muted">{formatInt(row.pregoes)}</td>
                <td class="num pts">{formatPts(row.primeiro_fechamento)}</td>
                <td class="num pts strong">{formatPts(row.ultimo_fechamento)}</td>
                <td class="num pts">{formatPts(row.minima)}</td>
                <td class="num pts">{formatPts(row.maxima)}</td>
                <td class="num var {signClass(row.retorno_anual_pct)}">
                  {formatPctSigned(row.retorno_anual_pct)}
                </td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
    <p class="scroll-hint">Deslize a tabela para o lado →</p>
  </div>
</section>

<style>
  .annual-head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px 16px;
    margin-block-end: 18px;
  }

  .annual-title-block {
    min-inline-size: 0;
    flex: 1 1 320px;
  }

  .annual-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .export-btn {
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

  .export-btn:hover:not(:disabled) {
    background: #3e3e42;
    border-color: #5a5a60;
  }

  .export-btn:focus-visible,
  .table-wrap:focus-visible {
    outline: 2px solid #f2b94b;
    outline-offset: 2px;
  }

  .export-btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .annual-root {
    container-type: inline-size;
    inline-size: 100%;
    min-inline-size: 0;
  }

  .table-wrap {
    max-inline-size: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    --scrollbar-thumb: #7a7a85;
    --scrollbar-track: #222222;
    scrollbar-width: thin;
    scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);
  }

  @supports not (scrollbar-color: auto) {
    .table-wrap::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }

    .table-wrap::-webkit-scrollbar-track {
      background: var(--scrollbar-track);
      border-radius: 9999px;
    }

    .table-wrap::-webkit-scrollbar-thumb {
      background: var(--scrollbar-thumb);
      border-radius: 9999px;
    }
  }

  .annual-table {
    inline-size: 100%;
    min-inline-size: 680px;
    border-collapse: separate;
    border-spacing: 0;
  }

  .annual-table thead th {
    padding: 10px 12px;
    border-block-end: 1px solid #3a3a3f;
    background: #2b2b2b;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #767676;
    text-align: left;
    white-space: nowrap;
  }

  .annual-table thead th.num {
    text-align: right;
  }

  .annual-table thead th:first-child {
    padding-inline-start: 0;
  }

  .annual-table thead th:last-child {
    padding-inline-end: 0;
  }

  .annual-table tbody th,
  .annual-table tbody td {
    padding: 14px 12px;
    font-size: 12.5px;
    border-block-end: 1px solid #343438;
    background: #2b2b2b;
    white-space: nowrap;
    vertical-align: middle;
  }

  .annual-table tbody tr:last-child th,
  .annual-table tbody tr:last-child td {
    border-block-end: 0;
  }

  .annual-table tbody tr:hover th,
  .annual-table tbody tr:hover td {
    background: #323236;
  }

  .col-ano {
    font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
    font-variant-numeric: tabular-nums;
    font-weight: 600;
    color: #f8f8f8;
    text-align: left;
  }

  .sticky-col {
    position: sticky;
    inset-inline-start: 0;
    z-index: 2;
    padding-inline-start: 0;
    background: #2b2b2b;
  }

  .annual-table thead th.sticky-col {
    z-index: 3;
  }

  .annual-table tbody tr:hover th.sticky-col {
    background: #323236;
  }

  .annual-table tbody td:last-child {
    padding-inline-end: 0;
  }

  .num {
    text-align: right;
    font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
    font-variant-numeric: tabular-nums;
  }

  .muted {
    color: #8a8a91;
    font-size: 12px;
  }

  .pts {
    color: #c7c7cc;
    font-weight: 500;
  }

  .pts.strong {
    color: #f8f8f8;
    font-weight: 600;
  }

  .var {
    font-weight: 700;
  }

  .pos {
    color: #f2b94b;
  }

  .neg {
    color: #e5e5e5;
  }

  .neutral {
    color: #767676;
  }

  .empty-cell {
    padding: 24px 12px;
    text-align: center;
    color: #8a8a91;
  }

  .scroll-hint {
    display: none;
    margin: 10px 0 0;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 10.5px;
    color: #f2b94b;
    text-align: right;
  }

  @container (width < 800px) {
    .annual-table thead th,
    .annual-table tbody th,
    .annual-table tbody td {
      padding: 11px 10px;
      font-size: 11.5px;
    }

    .annual-table thead th.sticky-col,
    .annual-table tbody th.sticky-col {
      padding-inline: 0 12px;
      border-inline-end: 1px solid #363636;
    }

    .scroll-hint {
      display: block;
    }
  }

  @media (max-width: 640px) {
    .annual-actions,
    .export-btn {
      inline-size: 100%;
    }
  }
</style>
