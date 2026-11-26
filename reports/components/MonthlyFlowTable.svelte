<script>
  export let data = [];
  export let title = 'Fluxo Mensal Consolidado por Tipo de Investidor × Retorno do Ibovespa';
  export let subtitle =
    'Como ler: compare quem comprou e quem vendeu em cada mês (saldo oficial MTD da B3) lado a lado com a alta ou queda do Ibovespa';

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
    const numK = Number(kVal);
    const absK = Math.abs(numK);
    const sign = numK < 0 ? '-' : numK > 0 ? '+' : '';

    if (absK >= 1_000_000) {
      const bi = absK / 1_000_000;
      return `${sign}R$ ${bi.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })} bi`;
    }

    const mi = absK / 1_000;
    return `${sign}R$ ${mi.toLocaleString('pt-BR', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    })} mi`;
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

<section class="terminal-panel monthly-panel" aria-label={title}>
  <div class="monthly-head">
    <div>
      <h2 class="terminal-panel-title">{title}</h2>
      <p class="terminal-panel-sub" style="margin-block-end: 0;">{subtitle}</p>
    </div>

    <button type="button" class="monthly-export" on:click={exportCsv}>Exportar CSV</button>
  </div>

  <div class="monthly-scroll" role="region" tabindex="0" aria-label={title}>
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
            <td class="mono mes-col">{row.mes}</td>
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
    <span>Base oficial B3 (último saldo MTD disponível em cada mês · retorno IBOV calculado fechamento/fechamento mensal)</span>
    <span>{rows.length} {rows.length === 1 ? 'mês' : 'meses'} disponíveis</span>
  </div>
</section>

<style>
  .monthly-panel {
    margin-block-end: 18px;
  }

  .monthly-head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px 16px;
    margin-block-end: 14px;
  }

  .monthly-export {
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

  .monthly-export:hover {
    background: #f4f4f5;
  }

  .monthly-export:focus-visible,
  .monthly-scroll:focus-visible {
    outline: 2px solid #d97706;
    outline-offset: 2px;
  }

  .monthly-scroll {
    max-inline-size: 100%;
    max-block-size: 420px;
    overflow: auto;
    -webkit-overflow-scrolling: touch;
  }

  .monthly-table {
    inline-size: 100%;
    min-inline-size: 720px;
    border-collapse: collapse;
  }

  .monthly-table thead th {
    position: sticky;
    inset-block-start: 0;
    z-index: 1;
    background: #ffffff;
    text-align: left;
    padding: 10px 12px;
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #71717a;
    border-block-end: 1px solid #e4e4e7;
    white-space: nowrap;
  }

  .monthly-table tbody td {
    padding: 11px 12px;
    font-size: 12.5px;
    border-block-end: 1px solid #f4f4f5;
    white-space: nowrap;
  }

  .monthly-table tbody tr:hover td {
    background: #fafaf9;
  }

  .monthly-table tbody tr:last-child td {
    border-block-end: 0;
  }

  .monthly-table .mono {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  .monthly-table .mes-col {
    font-weight: 600;
    color: #18181b;
  }

  .monthly-table .muted {
    color: #71717a;
    font-size: 11.5px;
  }

  .monthly-table .num {
    text-align: right;
    font-weight: 600;
  }

  .monthly-table .pos {
    color: #15803d;
  }

  .monthly-table .neg {
    color: #b91c1c;
  }

  .monthly-table .neutral {
    color: #71717a;
  }

  .monthly-table .ibov-col {
    font-weight: 700;
  }

  .monthly-foot {
    margin-block-start: 12px;
    padding-block-start: 10px;
    border-block-start: 1px solid #f4f4f5;
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 8px 16px;
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 11px;
    color: #71717a;
  }
</style>
