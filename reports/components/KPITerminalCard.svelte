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
  export let liveDot = false;
  export let focal = false;
  export let focalWhenPositive = false;
  export let badge = '';

  $: row = data && data.length > 0 ? data[0] : null;
  $: rawVal = row && value ? row[value] : null;
  $: rawDate = row && dateCol ? row[dateCol] : '';
  $: numVal = rawVal !== null && rawVal !== undefined && !Number.isNaN(Number(rawVal)) ? Number(rawVal) : null;
  $: isAlert = Boolean(row && alertCol && Number(row[alertCol]) === 1);
  $: isFocal = focal || isAlert || (focalWhenPositive && numVal !== null && numVal > 0);

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
    const iso = d instanceof Date ? d.toISOString().slice(0, 10) : String(d).slice(0, 10);
    if (iso.length < 10) return iso;
    return `${iso.slice(8, 10)}/${iso.slice(5, 7)}`;
  }

  $: formattedDate = rawDate ? formatDate(rawDate) : '';
</script>

<div class="kpi-card" class:is-focal-card={isFocal && badge} data-code={code || undefined} data-icon={icon || undefined}>
  <div class="kpi-head">
    <span class="kpi-label">
      {#if liveDot}
        <span class="kpi-live-dot" aria-hidden="true"></span>
      {/if}
      <span>{title}</span>
    </span>
    {#if badge}
      <span class="kpi-pill-badge">{badge}</span>
    {:else if formattedDate}
      <span class="kpi-date">{formattedDate}</span>
    {/if}
  </div>

  <div class="kpi-value" class:is-focal={isFocal}>{formatValue(rawVal)}</div>

  {#if subtitle || (badge && formattedDate)}
    <div class="kpi-sub">
      {#if subtitle}
        <span>{subtitle}</span>
      {/if}
      {#if badge && formattedDate}
        <span class="kpi-date">{formattedDate}</span>
      {/if}
    </div>
  {/if}
</div>

<style>
  .kpi-card {
    background: #2b2b2b;
    border: 1px solid #363636;
    border-radius: 24px;
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.18);
    padding: 20px 22px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 10px;
    min-block-size: 118px;
    min-inline-size: 0;
    box-sizing: border-box;
    transition: border-color 0.18s ease, background-color 0.18s ease;
  }

  .kpi-card:hover {
    border-color: #45454a;
  }

  .kpi-card.is-focal-card {
    border-color: rgba(242, 185, 75, 0.34);
  }

  .kpi-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .kpi-label {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #a3a3a3;
    line-height: 1.25;
  }

  .kpi-live-dot {
    inline-size: 6px;
    block-size: 6px;
    border-radius: 50%;
    background: #f8f8f8;
    flex-shrink: 0;
  }

  .kpi-pill-badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 9px;
    border-radius: 999px;
    background: rgba(242, 185, 75, 0.14);
    color: #f2b94b;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 10.5px;
    font-weight: 600;
    line-height: 1.3;
    white-space: nowrap;
  }

  .kpi-value {
    font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
    font-size: clamp(22px, 2vw, 28px);
    font-weight: 700;
    color: #f8f8f8;
    line-height: 1.12;
    letter-spacing: -0.03em;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  .kpi-value.is-focal {
    color: #f2b94b;
  }

  .kpi-sub {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 2px 8px;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 12px;
    color: #767676;
    line-height: 1.35;
  }

  .kpi-date {
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 11px;
    color: #767676;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
  }

  @media (max-width: 640px) {
    .kpi-card {
      border-radius: 20px;
      padding: 15px 16px;
      min-block-size: 98px;
      gap: 7px;
    }

    .kpi-label {
      font-size: 10px;
      letter-spacing: 0.05em;
    }

    .kpi-value {
      font-size: clamp(17px, 4.7vw, 22px);
    }

    .kpi-sub {
      font-size: 11px;
    }

    .kpi-date {
      font-size: 10px;
    }
  }
</style>
