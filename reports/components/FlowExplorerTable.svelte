<script>
  export let data = [];
  export let title = 'Explorador Executivo — Fluxo por Perfil de Investidor (B3)';
  export let subtitle = 'Último pregão disponível na camada Gold · Destaque tipográfico apenas nos desvios em relação à MM21';

  let query = '';

  $: rawRows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  $: filteredRows = query.trim()
    ? rawRows.filter((r) => {
        const q = query.trim().toLowerCase();
        return (
          String(r.investor_type_name_pt ?? '').toLowerCase().includes(q) ||
          String(r.investor_type_short_pt ?? '').toLowerCase().includes(q) ||
          String(r.flow_vs_ma21_signal ?? '').toLowerCase().includes(q) ||
          String(r.trading_date ?? '').toLowerCase().includes(q)
        );
      })
    : rawRows;

  function formatDate(d) {
    if (!d) return '—';
    if (d instanceof Date) return d.toISOString().slice(0, 10);
    return String(d).slice(0, 10);
  }

  function formatBi(v, signed = true) {
    if (v === null || v === undefined) return '—';
    const num = Number(v);
    if (Number.isNaN(num)) return String(v);
    const sign = num < 0 ? '-' : signed && num > 0 ? '+' : '';
    return `${sign}R$ ${Math.abs(num).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })} bi`;
  }

  function formatPct(v) {
    if (v === null || v === undefined) return '—';
    const num = Number(v);
    if (Number.isNaN(num)) return String(v);
    return `${num.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
  }

  function formatSignal(sig) {
    if (sig === 'acima_mm21') return 'Acima MM21';
    if (sig === 'abaixo_mm21') return 'Abaixo MM21';
    return sig ?? '—';
  }

  function exportCsv() {
    if (!filteredRows.length) return;
    const headers = [
      'trading_date',
      'investor_type_short_pt',
      'investor_type_name_pt',
      'daily_net_flow_bi_brl',
      'mtd_net_flow_bi_brl',
      'cum_net_flow_bi_brl',
      'cum_net_flow_ma21_bi_brl',
      'flow_vs_ma21_signal',
    ];
    const lines = [headers.join(',')];
    for (const r of filteredRows) {
      const vals = headers.map((h) => {
        const raw = h === 'trading_date' ? formatDate(r[h]) : r[h] ?? '';
        return `"${String(raw).replace(/"/g, '""')}"`;
      });
      lines.push(vals.join(','));
    }
    const blob = new Blob([`\uFEFF${lines.join('\n')}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'gringolake_b3_investor_flow.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
</script>

<section class="terminal-panel exec-explorer" aria-labelledby="exec-explorer-title">
  <div class="exec-head">
    <div>
      <h2 id="exec-explorer-title" class="terminal-panel-title">{title}</h2>
      <p class="terminal-panel-sub" style="margin-block-end: 0;">{subtitle}</p>
    </div>

    <div class="exec-actions">
      <input
        type="search"
        class="exec-search"
        bind:value={query}
        placeholder="Buscar perfil ou data..."
        aria-label="Buscar perfil ou data"
      />
      <button type="button" class="exec-export" on:click={exportCsv}>Exportar CSV</button>
    </div>
  </div>

  <div class="exec-table-scroll" role="region" tabindex="0" aria-labelledby="exec-explorer-title">
    <table class="exec-table">
      <thead>
        <tr>
          <th scope="col">Sigla</th>
          <th scope="col">Perfil B3</th>
          <th scope="col">Pregão</th>
          <th scope="col" class="num">Saldo Dia</th>
          <th scope="col" class="num">Saldo MTD</th>
          <th scope="col" class="num">Acumulado</th>
          <th scope="col" class="num">MM21</th>
          <th scope="col" class="num">Part. Compra</th>
          <th scope="col" class="num">Sinal MM21</th>
        </tr>
      </thead>
      <tbody>
        {#each filteredRows as row}
          <tr>
            <td class="mono muted">{row.investor_type_short_pt}</td>
            <td class="ind">{row.investor_type_name_pt}</td>
            <td class="mono muted">{formatDate(row.trading_date)}</td>
            <td class="mono num">{formatBi(row.daily_net_flow_bi_brl)}</td>
            <td class="mono num muted">{formatBi(row.mtd_net_flow_bi_brl)}</td>
            <td class="mono num val">{formatBi(row.cum_net_flow_bi_brl)}</td>
            <td class="mono num muted">{formatBi(row.cum_net_flow_ma21_bi_brl)}</td>
            <td class="mono num muted">{formatPct(row.purchase_share_pct)}</td>
            <td class="num status" class:is-alert={row.flow_vs_ma21_signal === 'acima_mm21'}>
              {formatSignal(row.flow_vs_ma21_signal)}
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

  <div class="exec-foot">
    <span>Mostrando {filteredRows.length} de {rawRows.length} registros oficiais B3 (Gold)</span>
  </div>
</section>

<style>
  .exec-explorer {
    margin-block-end: 18px;
  }

  .exec-head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px 16px;
    margin-block-end: 14px;
  }

  .exec-actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }

  .exec-search {
    min-block-size: max(34px, var(--target-size));
    inline-size: min(240px, 100%);
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid #e4e4e7;
    background: #fafafa;
    color: #18181b;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 12px;
  }

  .exec-search::placeholder {
    color: #a1a1aa;
  }

  .exec-search:focus-visible,
  .exec-export:focus-visible,
  .exec-table-scroll:focus-visible {
    outline: 2px solid #d97706;
    outline-offset: 2px;
  }

  .exec-export {
    min-block-size: max(34px, var(--target-size));
    padding: 6px 14px;
    border-radius: 6px;
    border: 1px solid #e4e4e7;
    background: #ffffff;
    color: #18181b;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    white-space: nowrap;
  }

  .exec-export:hover {
    background: #f4f4f5;
  }

  .exec-table-scroll {
    max-inline-size: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .exec-table {
    inline-size: 100%;
    min-inline-size: 780px;
    border-collapse: collapse;
  }

  .exec-table thead th {
    text-align: left;
    padding: 9px 10px;
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #71717a;
    border-block-end: 1px solid #e4e4e7;
    background: #ffffff;
    position: sticky;
    inset-block-start: 0;
  }

  .exec-table tbody td {
    padding: 10px 10px;
    font-size: 12px;
    color: #27272a;
    border-block-end: 1px solid #f4f4f5;
    white-space: nowrap;
  }

  .exec-table tbody tr:last-child td {
    border-block-end: 0;
  }

  .exec-table .ind {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-weight: 500;
    color: #18181b;
  }

  .exec-table .mono {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  .exec-table .muted {
    color: #71717a;
  }

  .exec-table .num {
    text-align: right;
  }

  .exec-table .val {
    font-weight: 600;
    color: #18181b;
  }

  .exec-table tbody td.status {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 11.5px;
    font-weight: 400;
    color: #71717a;
  }

  .exec-table tbody td.status.is-alert {
    font-weight: 600 !important;
    color: #b45309 !important;
  }

  .exec-foot {
    margin-block-start: 12px;
    padding-block-start: 10px;
    border-block-start: 1px solid #f4f4f5;
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 11px;
    color: #71717a;
  }

  @media (max-width: 640px) {
    .exec-actions {
      inline-size: 100%;
    }
    .exec-search {
      flex: 1 1 160px;
    }
  }
</style>
