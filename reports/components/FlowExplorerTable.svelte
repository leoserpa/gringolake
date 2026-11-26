<script>
  export let data = [];
  export let panelIndex = '';
  export let title = 'Perfis Oficiais B3';
  export let subtitle = 'Saldos diário, mensal (MTD) e acumulado contínuo em R$ bi no último pregão · MM21 ativa a partir de 21 pregões completos';

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
    if (sig === 'em_formacao') return 'Em formação';
    return sig ?? '—';
  }

  function signClass(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return 'muted';
    const num = Number(v);
    if (num > 0) return 'pos';
    if (num < 0) return 'neg';
    return 'muted';
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
      <h2 id="exec-explorer-title" class="terminal-panel-title" style="margin: 0 0 4px 0;">
        {#if panelIndex}
          <span class="panel-index">{panelIndex}</span>
        {/if}
        <span>{title}</span>
      </h2>
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
            <th scope="row" class="mono code-col">{row.investor_type_short_pt}</th>
            <td class="ind">{row.investor_type_name_pt}</td>
            <td class="mono muted">{formatDate(row.trading_date)}</td>
            <td class={`mono num ${signClass(row.daily_net_flow_bi_brl)}`}>{formatBi(row.daily_net_flow_bi_brl)}</td>
            <td class={`mono num ${signClass(row.mtd_net_flow_bi_brl)}`}>{formatBi(row.mtd_net_flow_bi_brl)}</td>
            <td class={`mono num val ${signClass(row.cum_net_flow_bi_brl)}`}>{formatBi(row.cum_net_flow_bi_brl)}</td>
            <td class="mono num muted">{formatBi(row.cum_net_flow_ma21_bi_brl)}</td>
            <td class="mono num muted">{formatPct(row.purchase_share_pct)}</td>
            <td class="num status-cell">
              <span class="signal-pill" class:is-focal={row.flow_vs_ma21_signal === 'acima_mm21'}>
                {formatSignal(row.flow_vs_ma21_signal)}
              </span>
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
    margin-block-end: 20px;
  }

  .exec-head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px 16px;
    margin-block-end: 18px;
  }

  .exec-head > div:first-child {
    flex: 1 1 320px;
    min-inline-size: 0;
  }

  .exec-actions {
    display: flex;
    flex-wrap: nowrap;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .exec-search {
    min-block-size: max(36px, var(--target-size));
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

  .exec-search::placeholder {
    color: #767676;
  }

  .exec-search:focus-visible,
  .exec-export:focus-visible,
  .exec-table-scroll:focus-visible {
    outline: 2px solid #f2b94b;
    outline-offset: 2px;
  }

  .exec-export {
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

  .exec-export:hover {
    background: #3e3e42;
    border-color: #5a5a60;
  }

  .exec-table-scroll {
    max-inline-size: 100%;
    max-block-size: 460px;
    overflow: auto;
    -webkit-overflow-scrolling: touch;
    container-type: inline-size;
  }

  .exec-table {
    inline-size: 100%;
    min-inline-size: 820px;
    border-collapse: separate;
    border-spacing: 0;
    --label-2: 'Perfil B3';
    --label-3: 'Pregão';
    --label-4: 'Saldo Dia';
    --label-5: 'Saldo MTD';
    --label-6: 'Acumulado';
    --label-7: 'MM21';
    --label-8: 'Part. Compra';
    --label-9: 'Sinal MM21';
  }

  .exec-table thead th {
    text-align: left;
    padding: 10px 10px;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #767676;
    border-block-end: 1px solid #3a3a3f;
    background: #2b2b2b;
    position: sticky;
    inset-block-start: 0;
    z-index: 2;
  }

  .exec-table thead th:first-child {
    padding-inline-start: 0;
  }

  .exec-table thead th:last-child {
    padding-inline-end: 0;
  }

  .exec-table tbody th,
  .exec-table tbody td {
    padding: 12px 10px;
    font-size: 12px;
    color: #e5e5e5;
    border-block-end: 1px solid #343438;
    white-space: nowrap;
    background: #2b2b2b;
  }

  .exec-table tbody th.code-col {
    position: sticky;
    inset-inline-start: 0;
    z-index: 1;
    text-align: left;
    padding-inline-start: 0;
    font-weight: 600;
    color: #a3a3a3;
  }

  .exec-table tbody td:last-child {
    padding-inline-end: 0;
  }

  .exec-table tbody tr:hover th,
  .exec-table tbody tr:hover td {
    background: #323236;
  }

  .exec-table tbody tr:last-child th,
  .exec-table tbody tr:last-child td {
    border-block-end: 0;
  }

  .exec-table .ind {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-weight: 500;
    color: #f8f8f8;
  }

  .exec-table .mono {
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  .exec-table .muted {
    color: #8a8a91;
  }

  .exec-table .num {
    text-align: right;
  }

  .exec-table .val {
    font-weight: 700;
  }

  /* Strict Knaflic single-accent rule */
  .exec-table .pos {
    color: #f2b94b;
  }

  .exec-table .neg {
    color: #e5e5e5;
  }

  .signal-pill {
    display: inline-flex;
    align-items: center;
    padding: 3px 10px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.05);
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 11px;
    font-weight: 500;
    color: #8a8a91;
    line-height: 1.3;
  }

  .signal-pill.is-focal {
    background: rgba(242, 185, 75, 0.14);
    color: #f2b94b;
    font-weight: 600;
  }

  .exec-foot {
    margin-block-start: 14px;
    padding-block-start: 12px;
    border-block-start: 1px solid #343438;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 11.5px;
    color: #767676;
  }

  @container (width < 600px) {
    .exec-table,
    .exec-table tbody,
    .exec-table tr {
      display: block;
      min-inline-size: 0;
      inline-size: 100%;
    }

    .exec-table thead {
      display: none;
    }

    .exec-table tr {
      border: 1px solid #363636;
      border-radius: 18px;
      overflow: hidden;
      background: #262626;
      margin-block-end: 12px;
    }

    .exec-table tr:last-child {
      margin-block-end: 0;
    }

    .exec-table tbody th.code-col {
      position: sticky;
      inset-block-start: 0;
      z-index: 1;
      display: block;
      padding: 10px 14px;
      background: #303034;
      border-block-end: 1px solid #3a3a3f;
      font-size: 12px;
      color: #f8f8f8;
    }

    .exec-table tbody td {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 9px 14px;
      font-size: 12px;
      background: #262626;
      border-block-end: 1px solid #323236;
      text-align: right;
    }

    .exec-table tbody td:last-child {
      padding-inline-end: 14px;
      border-block-end: 0;
    }

    .exec-table tbody td::before {
      font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
      font-size: 11.5px;
      font-weight: 500;
      color: #a3a3a3;
      text-align: left;
    }

    .exec-table tbody td:nth-child(2)::before { content: var(--label-2); }
    .exec-table tbody td:nth-child(3)::before { content: var(--label-3); }
    .exec-table tbody td:nth-child(4)::before { content: var(--label-4); }
    .exec-table tbody td:nth-child(5)::before { content: var(--label-5); }
    .exec-table tbody td:nth-child(6)::before { content: var(--label-6); }
    .exec-table tbody td:nth-child(7)::before { content: var(--label-7); }
    .exec-table tbody td:nth-child(8)::before { content: var(--label-8); }
    .exec-table tbody td:nth-child(9)::before { content: var(--label-9); }
  }

  @media (max-width: 640px) {
    .exec-table-scroll {
      max-block-size: none;
      overflow: visible;
    }
    .exec-actions {
      inline-size: 100%;
      flex-wrap: wrap;
    }
    .exec-search {
      flex: 1 1 160px;
      inline-size: auto;
    }
  }
</style>
