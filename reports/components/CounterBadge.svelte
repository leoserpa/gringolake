<script>
  export let data = [];
  export let value = null;
  export let label = '';
  export let suffix = '';
  export let decimals = 0;

  $: rows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  $: row = rows.length > 0 ? rows[0] : null;
  $: rawVal = row && value ? row[value] : null;

  function formatValue(v) {
    if (v === null || v === undefined) return '—';
    if (typeof v === 'string') return `${v}${suffix}`;
    const num = Number(v);
    if (Number.isNaN(num)) return String(v);
    const epsilon = 0.5 * Math.pow(10, -decimals);
    const normalized = Math.abs(num) < epsilon ? 0 : num;
    const sign = normalized < 0 ? '-' : '';
    const formatted = Math.abs(normalized).toLocaleString('pt-BR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
    return `${sign}${formatted}${suffix}`;
  }
</script>

<div class="ag-counter-badge">
  {#if label}
    <span class="ag-counter-label">{label}</span>
  {/if}
  <span class="ag-counter-value">{formatValue(rawVal)}</span>
</div>

<style>
  .ag-counter-badge {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    min-inline-size: 74px;
    min-block-size: 46px;
    padding: 6px 14px;
    border-radius: 14px;
    background: #222222;
    border: 1px solid #555555;
    box-sizing: border-box;
    flex-shrink: 0;
  }

  .ag-counter-label {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 10.5px;
    font-weight: 500;
    color: #a3a3a3;
    line-height: 1.2;
    white-space: nowrap;
  }

  .ag-counter-value {
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 15px;
    font-weight: 700;
    color: #f8f8f8;
    line-height: 1.15;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  @media (max-width: 640px) {
    .ag-counter-badge {
      flex-direction: row;
      justify-content: space-between;
      inline-size: 100%;
      min-block-size: 40px;
      padding: 8px 14px;
    }
  }
</style>
