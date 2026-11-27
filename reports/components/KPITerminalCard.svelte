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
  export let autoScaleUnit = true;
  export let icon = '';
  export let alertCol = null;
  export let focal = false;
  export let focalWhenPositive = false;

  const CODE_ICON_MAP = {
    IBOV: 'trend',
    ESTRANG: 'globe',
    PF: 'user',
    'PF CUM': 'user',
    'PF DIA': 'user',
    INSTIT: 'building',
    'INST FIN': 'bank',
    MM21: 'wave',
    '1D': 'delta',
    MAX: 'up',
    MIN: 'down',
    GOLD: 'layers',
    'ZERO-SUM': 'shield',
    DIM: 'users',
  };

  $: resolvedIcon = icon || CODE_ICON_MAP[code] || 'trend';
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
    const trimmedSuffix = (suffix || '').trim();
    const canAutoUnit = autoScaleUnit && (trimmedSuffix === 'mi' || trimmedSuffix === 'bi');

    if (canAutoUnit) {
      const inMi = trimmedSuffix === 'bi' ? num * 1000 : num;
      if (Math.abs(inMi) < 0.05) {
        return `${prefix}0`;
      }
      const sign = inMi < 0 ? '-' : signed ? '+' : '';
      const absMi = Math.abs(inMi);
      if (absMi >= 999.95) {
        const formatted = (absMi / 1000).toLocaleString('pt-BR', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
        return `${sign}${prefix}${formatted} bi`;
      }
      const formatted = absMi.toLocaleString('pt-BR', {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
      });
      return `${sign}${prefix}${formatted} mi`;
    }

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

<div class="kpi-card" data-code={code || undefined} data-icon={resolvedIcon}>
  <div class="kpi-head">
    <span class="kpi-label">
      <svg
        class="kpi-icon"
        class:is-focal={isFocal}
        width="15"
        height="15"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        {#if resolvedIcon === 'globe'}
          <circle cx="12" cy="12" r="9" />
          <path d="M3 12h18" />
          <path d="M12 3a13.5 13.5 0 0 1 0 18" />
          <path d="M12 3a13.5 13.5 0 0 0 0 18" />
        {:else if resolvedIcon === 'user'}
          <circle cx="12" cy="8" r="4" />
          <path d="M5 20a7 7 0 0 1 14 0" />
        {:else if resolvedIcon === 'building'}
          <rect x="4" y="3" width="16" height="18" rx="2" />
          <path d="M9 8h1M14 8h1M9 12h1M14 12h1M9 16h1M14 16h1" />
        {:else if resolvedIcon === 'bank'}
          <path d="M3 10h18" />
          <path d="M5 10v8M10 10v8M14 10v8M19 10v8" />
          <path d="M3 20h18" />
          <path d="M12 3l9 5H3l9-5z" />
        {:else if resolvedIcon === 'wave'}
          <path d="M3 12h4l3-7 4 14 3-7h4" />
        {:else if resolvedIcon === 'delta'}
          <path d="M7 17V7m0 0-3 3m3-3 3 3" />
          <path d="M17 7v10m0 0-3-3m3 3 3-3" />
        {:else if resolvedIcon === 'up'}
          <path d="M4 17l6-6 4 4 6-7" />
          <path d="M15 8h5v5" />
        {:else if resolvedIcon === 'down'}
          <path d="M4 7l6 6 4-4 6 7" />
          <path d="M15 16h5v-5" />
        {:else if resolvedIcon === 'layers'}
          <path d="M12 3l9 4.5-9 4.5-9-4.5L12 3z" />
          <path d="M3 12l9 4.5 9-4.5" />
          <path d="M3 16.5l9 4.5 9-4.5" />
        {:else if resolvedIcon === 'shield'}
          <path d="M12 3l7 3v5c0 4.5-3 8.2-7 10-4-1.8-7-5.5-7-10V6l7-3z" />
          <path d="M9 12l2 2 4-4" />
        {:else if resolvedIcon === 'users'}
          <circle cx="9" cy="8" r="3.5" />
          <path d="M3 19a6 6 0 0 1 12 0" />
          <circle cx="17" cy="9" r="2.5" />
          <path d="M17 14a4.5 4.5 0 0 1 4 4.5" />
        {:else}
          <path d="M3 17l5.5-5.5 4 3.5L21 6.5" />
          <circle cx="21" cy="6.5" r="1.5" fill="currentColor" stroke="none" />
        {/if}
      </svg>
      <span>{title}</span>
    </span>
    {#if formattedDate}
      <span class="kpi-date">{formattedDate}</span>
    {/if}
  </div>

  <div class="kpi-value" class:is-focal={isFocal}>{formatValue(rawVal)}</div>

  {#if subtitle}
    <div class="kpi-sub">
      <span>{subtitle}</span>
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
    min-inline-size: 0;
  }

  .kpi-icon {
    color: #8a8a91;
    flex-shrink: 0;
  }

  .kpi-icon.is-focal {
    color: #f2b94b;
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
      gap: 5px;
    }

    .kpi-icon {
      inline-size: 13px;
      block-size: 13px;
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
