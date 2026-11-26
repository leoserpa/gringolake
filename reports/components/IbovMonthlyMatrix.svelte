<script>
  export let data = [];
  export let panelIndex = '03';
  export let title = 'Matriz de Retornos Mensais do Ibovespa';
  export let subtitle = 'Variação percentual fechamento/fechamento por mês e acumulado anual oficial da B3 (2020–2026)';

  const MONTHS = [
    { key: 'm01', label: 'Jan' },
    { key: 'm02', label: 'Fev' },
    { key: 'm03', label: 'Mar' },
    { key: 'm04', label: 'Abr' },
    { key: 'm05', label: 'Mai' },
    { key: 'm06', label: 'Jun' },
    { key: 'm07', label: 'Jul' },
    { key: 'm08', label: 'Ago' },
    { key: 'm09', label: 'Set' },
    { key: 'm10', label: 'Out' },
    { key: 'm11', label: 'Nov' },
    { key: 'm12', label: 'Dez' },
  ];

  $: rows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  function formatPct(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '—';
    const num = Number(v);
    const normalized = Math.abs(num) < 0.005 ? 0 : num;
    const sign = normalized < 0 ? '-' : normalized > 0 ? '+' : '';
    return `${sign}${Math.abs(normalized).toLocaleString('pt-BR', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    })}%`;
  }

  function cellTone(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return 'empty';
    const num = Number(v);
    if (num >= 5) return 'pos-strong';
    if (num > 0) return 'pos';
    if (num <= -5) return 'neg-strong';
    if (num < 0) return 'neg';
    return 'empty';
  }

  function exportCsv() {
    if (!rows.length) return;
    const headers = ['ano', ...MONTHS.map((m) => m.key), 'ano_pct'];
    const lines = [headers.join(',')];
    for (const r of rows) {
      lines.push(headers.map((h) => `"${r[h] ?? ''}"`).join(','));
    }
    const blob = new Blob([`\uFEFF${lines.join('\n')}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'gringolake_ibov_retornos_mensais.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
</script>

<section class="terminal-panel matrix-panel" aria-labelledby="ibov-matrix-title">
  <div class="matrix-head">
    <div class="matrix-title-block">
      <h2 id="ibov-matrix-title" class="terminal-panel-title" style="margin: 0 0 4px 0;">
        {#if panelIndex}
          <span class="panel-index">{panelIndex}</span>
        {/if}
        <span>{title}</span>
      </h2>
      {#if subtitle}
        <p class="terminal-panel-sub" style="margin: 0;">{subtitle}</p>
      {/if}
    </div>

    <div class="matrix-actions">
      <button type="button" class="matrix-export" on:click={exportCsv}>Exportar CSV</button>
    </div>
  </div>

  <div class="matrix-scroll" role="region" tabindex="0" aria-labelledby="ibov-matrix-title">
    <table class="matrix-table">
      <thead>
        <tr>
          <th scope="col">Ano</th>
          {#each MONTHS as m}
            <th scope="col" class="num">{m.label}</th>
          {/each}
          <th scope="col" class="num year-col">Ano</th>
        </tr>
      </thead>
      <tbody>
        {#each rows as row}
          <tr>
            <th scope="row" class="mono ano-col">{row.ano}</th>
            {#each MONTHS as m}
              <td class={`mono num ${cellTone(row[m.key])}`}>{formatPct(row[m.key])}</td>
            {/each}
            <td class={`mono num year-col ${cellTone(row.ano_pct)}`}>{formatPct(row.ano_pct)}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

  <div class="matrix-foot">
    <span>Meses positivos em âmbar · Altas ≥ +5% com destaque suave · Série oficial B3 GetPortfolioDay</span>
    <span class="scroll-hint">Deslize na tabela →</span>
  </div>
</section>

<style>
  .matrix-panel {
    margin-block-end: 20px;
  }

  .matrix-head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px 16px;
    margin-block-end: 18px;
  }

  .matrix-title-block {
    min-inline-size: 0;
    flex: 1 1 280px;
  }

  .matrix-actions {
    flex-shrink: 0;
  }

  .matrix-export {
    min-block-size: max(36px, var(--target-size));
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

  .matrix-export:hover {
    background: #3e3e42;
    border-color: #5a5a60;
  }

  .matrix-export:focus-visible,
  .matrix-scroll:focus-visible {
    outline: 2px solid #f2b94b;
    outline-offset: 2px;
  }

  .matrix-scroll {
    max-inline-size: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .matrix-table {
    inline-size: 100%;
    min-inline-size: 860px;
    border-collapse: separate;
    border-spacing: 0;
  }

  .matrix-table thead th {
    position: sticky;
    inset-block-start: 0;
    z-index: 2;
    background: #2b2b2b;
    text-align: left;
    padding: 10px 8px;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #767676;
    border-block-end: 1px solid #3a3a3f;
    white-space: nowrap;
  }

  .matrix-table thead th:first-child {
    position: sticky;
    inset-inline-start: 0;
    z-index: 3;
    padding-inline: 0 12px;
  }

  .matrix-table thead th:last-child {
    padding-inline-end: 0;
  }

  .matrix-table tbody th,
  .matrix-table tbody td {
    padding: 11px 8px;
    font-size: 12px;
    border-block-end: 1px solid #343438;
    white-space: nowrap;
    background: #2b2b2b;
  }

  .matrix-table tbody th.ano-col {
    position: sticky;
    inset-inline-start: 0;
    z-index: 1;
    text-align: left;
    padding-inline: 0 12px;
    font-weight: 700;
    color: #f8f8f8;
  }

  .matrix-table tbody td:last-child {
    padding-inline-end: 0;
  }

  .matrix-table tbody tr:last-child th,
  .matrix-table tbody tr:last-child td {
    border-block-end: 0;
  }

  .matrix-table .mono {
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  .matrix-table .num {
    text-align: right;
  }

  .matrix-table .pos {
    color: #f2b94b;
    font-weight: 600;
  }

  .matrix-table .pos-strong {
    color: #f2b94b;
    font-weight: 700;
    background: rgba(242, 185, 75, 0.11);
  }

  .matrix-table .neg {
    color: #d4d4d8;
    font-weight: 500;
  }

  .matrix-table .neg-strong {
    color: #f8f8f8;
    font-weight: 600;
    background: rgba(255, 255, 255, 0.04);
  }

  .matrix-table .empty {
    color: #5c5c62;
  }

  .matrix-table .year-col {
    font-weight: 700;
    border-inline-start: 1px solid #3a3a3f;
    padding-inline-start: 12px;
  }

  .matrix-foot {
    margin-block-start: 14px;
    padding-block-start: 12px;
    border-block-start: 1px solid #343438;
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 8px 16px;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 11.5px;
    color: #767676;
  }

  .scroll-hint {
    display: none;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 10.5px;
    color: #f2b94b;
  }

  @media (max-width: 900px) {
    .matrix-table thead th:first-child,
    .matrix-table tbody th.ano-col {
      border-inline-end: 1px solid #363636;
    }

    .scroll-hint {
      display: inline;
    }
  }

  @media (max-width: 640px) {
    .matrix-actions,
    .matrix-export {
      inline-size: 100%;
    }
  }
</style>
