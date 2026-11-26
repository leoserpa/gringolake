<script>
  export let data = [];
  export let panelIndex = '05';
  export let title = 'Quem liderou o fluxo em cada mês e como fechou o Ibovespa?';
  export let subtitle = 'Último saldo mensal oficial (MTD) em R$ bi por perfil · Entradas líquidas positivas destacadas em âmbar';

  $: rows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  function formatDateShort(d) {
    if (!d) return '—';
    const iso = d instanceof Date ? d.toISOString().slice(0, 10) : String(d).slice(0, 10);
    if (iso.length < 10) return iso;
    return `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}`;
  }

  function formatFlowFromKBrl(kVal) {
    if (kVal === null || kVal === undefined || Number.isNaN(Number(kVal))) return '—';
    const numBi = Number(kVal) / 1_000_000;
    const normalized = Math.abs(numBi) < 0.005 ? 0 : numBi;
    const sign = normalized < 0 ? '-' : normalized > 0 ? '+' : '';
    return `${sign}R$ ${Math.abs(normalized).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })} bi`;
  }

  function formatPct(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '—';
    const num = Number(v);
    const sign = num < 0 ? '-' : num > 0 ? '+' : '';
    return `${sign}${Math.abs(num).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}%`;
  }

  function signClass(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return 'neutral';
    const num = Number(v);
    if (num > 0) return 'pos';
    if (num < 0) return 'neg';
    return 'neutral';
  }

  function exportCsv() {
    if (!rows.length) return;
    const headers = [
      'mes',
      'ate_pregao',
      'estrang_k_brl',
      'instit_k_brl',
      'pf_k_brl',
      'inst_fin_k_brl',
      'ibov_month_pct',
    ];
    const lines = [headers.join(',')];
    for (const r of rows) {
      const vals = headers.map((h) => {
        const raw = h === 'ate_pregao' ? formatDateShort(r[h]) : r[h] ?? '';
        return `"${String(raw).replace(/"/g, '""')}"`;
      });
      lines.push(vals.join(','));
    }
    const blob = new Blob([`\uFEFF${lines.join('\n')}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'gringolake_fluxo_mensal_b3.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
</script>

<section class="terminal-panel monthly-panel" aria-labelledby="monthly-flow-title">
  <div class="monthly-head">
    <div class="monthly-title-block">
      <h2 id="monthly-flow-title" class="terminal-panel-title" style="margin: 0 0 4px 0;">
        {#if panelIndex}
          <span class="panel-index">{panelIndex}</span>
        {/if}
        <span>{title}</span>
      </h2>
      {#if subtitle}
        <p class="terminal-panel-sub" style="margin: 0;">{subtitle}</p>
      {/if}
    </div>

    <div class="monthly-right">
      <button type="button" class="monthly-export" on:click={exportCsv}>Exportar CSV</button>
    </div>
  </div>

  <div class="monthly-scroll" role="region" tabindex="0" aria-labelledby="monthly-flow-title">
    <table class="monthly-table">
      <thead>
        <tr>
          <th scope="col">Mês</th>
          <th scope="col">Até Pregão</th>
          <th scope="col" class="num">Estrangeiro</th>
          <th scope="col" class="num">Institucional</th>
          <th scope="col" class="num">Pessoa Física</th>
          <th scope="col" class="num">Inst. Financeira</th>
          <th scope="col" class="num">Ibovespa Mês</th>
        </tr>
      </thead>
      <tbody>
        {#each rows as row}
          <tr>
            <th scope="row" class="mono mes-col">{row.mes}</th>
            <td class="mono muted">{formatDateShort(row.ate_pregao)}</td>
            <td class={`mono num ${signClass(row.estrang_k_brl)}`}>{formatFlowFromKBrl(row.estrang_k_brl)}</td>
            <td class={`mono num ${signClass(row.instit_k_brl)}`}>{formatFlowFromKBrl(row.instit_k_brl)}</td>
            <td class={`mono num ${signClass(row.pf_k_brl)}`}>{formatFlowFromKBrl(row.pf_k_brl)}</td>
            <td class={`mono num ${signClass(row.inst_fin_k_brl)}`}>{formatFlowFromKBrl(row.inst_fin_k_brl)}</td>
            <td class={`mono num ibov-col ${signClass(row.ibov_month_pct)}`}>{formatPct(row.ibov_month_pct)}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

  <div class="monthly-foot">
    <span>Saldo MTD oficial da B3 no último pregão de cada mês · Histórico ampliado automaticamente às 21h BRT</span>
    <span class="monthly-foot-right">
      <span class="scroll-hint">Deslize na tabela →</span>
      <span>{rows.length} {rows.length === 1 ? 'mês' : 'meses'} disponíveis</span>
    </span>
  </div>
</section>

<style>
  .monthly-panel {
    margin-block-end: 20px;
  }

  .monthly-head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px 16px;
    margin-block-end: 18px;
  }

  .monthly-title-block {
    min-inline-size: 0;
    flex: 1 1 280px;
  }

  .monthly-right {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }

  .monthly-export {
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

  .monthly-export:hover {
    background: #3e3e42;
    border-color: #5a5a60;
  }

  .monthly-export:focus-visible,
  .monthly-scroll:focus-visible {
    outline: 2px solid #f2b94b;
    outline-offset: 2px;
  }

  .monthly-scroll {
    max-inline-size: 100%;
    max-block-size: 460px;
    overflow: auto;
    -webkit-overflow-scrolling: touch;
  }

  .monthly-table {
    inline-size: 100%;
    min-inline-size: 680px;
    border-collapse: separate;
    border-spacing: 0;
  }

  .monthly-table thead th {
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

  .monthly-table thead th:first-child {
    padding-inline-start: 0;
  }

  .monthly-table thead th:last-child {
    padding-inline-end: 0;
  }

  .monthly-table tbody th,
  .monthly-table tbody td {
    padding: 14px 12px;
    font-size: 12.5px;
    border-block-end: 1px solid #343438;
    white-space: nowrap;
    background: #2b2b2b;
  }

  .monthly-table tbody th.mes-col {
    position: sticky;
    inset-inline-start: 0;
    z-index: 1;
    text-align: left;
    padding-inline-start: 0;
    font-weight: 600;
    color: #f8f8f8;
  }

  .monthly-table tbody td:last-child {
    padding-inline-end: 0;
  }

  .monthly-table tbody tr:hover th,
  .monthly-table tbody tr:hover td {
    background: #323236;
  }

  .monthly-table tbody tr:last-child th,
  .monthly-table tbody tr:last-child td {
    border-block-end: 0;
  }

  .monthly-table .mono {
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  .monthly-table .muted {
    color: #8a8a91;
    font-size: 12px;
  }

  .monthly-table .num {
    text-align: right;
    font-weight: 600;
  }

  /* Strict Knaflic single-accent rule: warm amber for positive inflows, calm neutral for outflows */
  .monthly-table .pos {
    color: #f2b94b;
  }

  .monthly-table .neg {
    color: #e5e5e5;
  }

  .monthly-table .neutral {
    color: #767676;
  }

  .monthly-table .ibov-col {
    font-weight: 700;
  }

  .monthly-foot {
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

  .monthly-foot-right {
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

  @media (max-width: 720px) {
    .monthly-scroll {
      overflow-x: auto;
      overflow-y: auto;
      max-block-size: 420px;
    }

    .monthly-table {
      min-inline-size: 620px;
    }

    .monthly-table thead th,
    .monthly-table tbody th,
    .monthly-table tbody td {
      padding: 11px 10px;
      font-size: 11.5px;
    }

    .monthly-table thead th:first-child {
      position: sticky;
      inset-inline-start: 0;
      z-index: 3;
      padding-inline: 0 12px;
      border-inline-end: 1px solid #363636;
    }

    .monthly-table tbody th.mes-col {
      padding-inline: 0 12px;
      border-inline-end: 1px solid #363636;
    }

    .scroll-hint {
      display: inline;
    }
  }

  @media (max-width: 640px) {
    .monthly-right {
      inline-size: 100%;
    }

    .monthly-export {
      inline-size: 100%;
    }
  }
</style>
