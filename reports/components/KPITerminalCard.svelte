<script>
  export let data = [];
  export let value = null;
  export let dateCol = null;
  export let code = '';
  export let title = '';
  export let subtitle = '';
  export let prefix = '';
  export let suffix = '';
  export let decimals = 2;
  export let signed = false;
  export let icon = 'trend';
  export let alertCol = null;

  $: row = data && data.length > 0 ? data[0] : null;
  $: rawVal = row && value ? row[value] : null;
  $: rawDate = row && dateCol ? row[dateCol] : '';
  $: isAlert = Boolean(row && alertCol && Number(row[alertCol]) === 1);

  function formatValue(v) {
    if (v === null || v === undefined) return '—';
    if (v instanceof Date) return v.toISOString().slice(0, 10);
    if (typeof v === 'string') return `${prefix}${v}${suffix}`;
    const num = Number(v);
    if (Number.isNaN(num)) return String(v);
    const epsilon = 0.5 * Math.pow(10, -decimals);
    const normalized = Math.abs(num) < epsilon ? 0 : num;
    const sign = normalized < 0 ? '-' : signed && normalized > 0 ? '+' : '';
    const formatted = Math.abs(normalized).toLocaleString('pt-BR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
    return `${sign}${prefix}${formatted}${suffix}`;
  }

  function formatDate(d) {
    if (!d) return '';
    if (d instanceof Date) return d.toISOString().slice(0, 10);
    return String(d).slice(0, 10);
  }

  $: formattedDate = rawDate ? formatDate(rawDate) : '';
</script>

<div class="kpi-card" data-code={code || undefined}>
  <div class="kpi-head">
    <span class="kpi-label">{title}</span>
    <span class="kpi-icon" aria-hidden="true">
      {#if icon === 'dollar'}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" stroke="#737373" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      {:else if icon === 'activity'}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2" stroke="#737373" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      {:else if icon === 'bank'}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3" stroke="#737373" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      {:else if icon === 'globe'}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="9.5" stroke="#737373" stroke-width="1.6" />
          <path d="M2.5 12h19M12 2.5a14 14 0 0 1 3.8 9.5 14 14 0 0 1-3.8 9.5 14 14 0 0 1-3.8-9.5 14 14 0 0 1 3.8-9.5z" stroke="#737373" stroke-width="1.6" />
        </svg>
      {:else if icon === 'flow'}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <path d="M7 16V4m0 0-4 4m4-4 4 4M17 8v12m0 0 4-4m-4 4-4-4" stroke="#737373" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      {:else if icon === 'users'}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke="#737373" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      {:else}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <path d="M3 3v18h18" stroke="#737373" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
          <path d="m19 9-5 5-4-4-3 3" stroke="#737373" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      {/if}
    </span>
  </div>

  <div class="kpi-value" class:is-alert={isAlert}>{formatValue(rawVal)}</div>

  {#if subtitle || formattedDate}
    <div class="kpi-sub">
      {#if subtitle}
        <span>{subtitle}</span>
      {/if}
      {#if formattedDate}
        <span class="kpi-date">{formattedDate}</span>
      {/if}
    </div>
  {/if}
</div>

<style>
  .kpi-card {
    background: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 10px;
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 8px;
    min-block-size: 104px;
    min-inline-size: 0;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
  }

  .kpi-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .kpi-label {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 12px;
    font-weight: 500;
    color: #52525b;
    line-height: 1.25;
  }

  .kpi-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .kpi-value {
    font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
    font-size: clamp(20px, 1.9vw, 25px);
    font-weight: 700;
    color: #18181b;
    line-height: 1.15;
    letter-spacing: -0.025em;
    font-variant-numeric: tabular-nums;
  }

  .kpi-value.is-alert {
    color: #b45309;
  }

  .kpi-sub {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 2px 8px;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 11px;
    color: #71717a;
    line-height: 1.35;
  }

  .kpi-date {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 10.5px;
    color: #a1a1aa;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
  }

  @media (max-width: 640px) {
    .kpi-card {
      padding: 13px 14px;
      min-block-size: 92px;
    }
  }
</style>
