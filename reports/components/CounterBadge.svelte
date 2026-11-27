<script>
  export let data = [];
  export let value = null;
  export let label = '';
  export let prefix = '';
  export let suffix = '';
  export let decimals = 0;
  export let hint = '';

  $: rows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  $: row = rows.length > 0 ? rows[0] : null;
  $: rawVal = row && value ? row[value] : null;

  function formatValue(v) {
    if (v === null || v === undefined) return '—';
    if (typeof v === 'string') return `${prefix}${v}${suffix}`;
    const num = Number(v);
    if (Number.isNaN(num)) return String(v);
    const epsilon = 0.5 * Math.pow(10, -decimals);
    const normalized = Math.abs(num) < epsilon ? 0 : num;
    const sign = normalized < 0 ? '-' : '';
    const formatted = Math.abs(normalized).toLocaleString('pt-BR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
    return `${sign}${prefix}${formatted}${suffix}`;
  }
</script>

<div class="ag-counter-badge" title={hint || undefined}>
  {#if label}
    <span class="ag-counter-label">{label}</span>
    <span class="ag-counter-sep" aria-hidden="true"></span>
  {/if}
  <span class="ag-counter-value">{formatValue(rawVal)}</span>
</div>

<style>
  .ag-counter-badge {
    display: inline-flex;
    flex-direction: row;
    align-items: center;
    gap: 10px;
    min-block-size: max(42px, var(--target-size, 42px));
    padding: 0 16px;
    border-radius: 999px;
    background: #2b2b2b;
    border: 1px solid #363636;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.16);
    box-sizing: border-box;
    flex-shrink: 0;
  }

  .ag-counter-label {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #8a8a91;
    line-height: 1;
    white-space: nowrap;
  }

  .ag-counter-sep {
    inline-size: 1px;
    block-size: 14px;
    background: #3e3e44;
    flex-shrink: 0;
  }

  .ag-counter-value {
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 12.5px;
    font-weight: 600;
    color: #f5f5f5;
    line-height: 1;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  @media (max-width: 640px) {
    .ag-counter-badge {
      min-block-size: 36px;
      padding: 0 13px;
      gap: 8px;
    }
  }
</style>
