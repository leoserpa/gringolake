<script>
  export let data = [];
  export let panelIndex = '03';
  export let title = 'Quais meses historicamente rendem mais ou menos no Ibovespa?';
  export let subtitle = '';

  const MONTH_LABELS = [
    'Jan',
    'Fev',
    'Mar',
    'Abr',
    'Mai',
    'Jun',
    'Jul',
    'Ago',
    'Set',
    'Out',
    'Nov',
    'Dez',
  ];

  const LEGEND_ITEMS = [
    { label: '< -8%', color: '#991b1b' },
    { label: '-8% a -3%', color: '#c0392b' },
    { label: '-3% a 0%', color: '#6b282b' },
    { label: 'Neutro', color: '#35353c' },
    { label: '0% a +3%', color: '#1b5e44' },
    { label: '+3% a +8%', color: '#1c8c5e' },
    { label: '> +8%', color: '#22b573' },
  ];

  let selectedKey = null;

  function toArray(input) {
    if (!input) return [];
    if (Array.isArray(input)) return input;
    if (typeof input.toArray === 'function') return input.toArray();
    if (typeof input[Symbol.iterator] === 'function') return Array.from(input);
    return [];
  }

  function getColorForReturn(val) {
    if (val === null || val === undefined || !Number.isFinite(val)) return 'transparent';
    if (val < -0.08) return '#991b1b';
    if (val < -0.03) return '#c0392b';
    if (val < -0.005) return '#6b282b';
    if (val <= 0.005) return '#35353c';
    if (val <= 0.03) return '#1b5e44';
    if (val <= 0.08) return '#1c8c5e';
    return '#22b573';
  }

  function formatPctBr(val) {
    if (val === null || val === undefined || !Number.isFinite(val)) return '—';
    const rawPct = val * 100;
    const pct = Math.abs(rawPct) < 0.05 ? 0 : rawPct;
    const sign = pct > 0 ? '+' : pct < 0 ? '-' : '';
    const formatted = Math.abs(pct).toLocaleString('pt-BR', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    });
    return `${sign}${formatted}%`;
  }

  $: parsed = (() => {
    const rows = toArray(data);
    const grid = new Map();
    const yearSet = new Set();
    let latestCell = null;
    let maxStamp = -1;

    for (const row of rows) {
      if (!row) continue;
      const anoNum = Number(row.ano_num ?? row.ano);
      const mesNum = Number(row.mes_num);
      const val =
        row.retorno === null || row.retorno === undefined || row.retorno === ''
          ? null
          : Number(row.retorno);
      if (!Number.isInteger(anoNum) || !Number.isInteger(mesNum) || mesNum < 1 || mesNum > 12) {
        continue;
      }
      yearSet.add(anoNum);
      if (val !== null && Number.isFinite(val)) {
        const key = `${anoNum}-${mesNum}`;
        grid.set(key, val);
        const stamp = anoNum * 100 + mesNum;
        if (stamp > maxStamp) {
          maxStamp = stamp;
          latestCell = {
            key,
            year: anoNum,
            mesNum,
            monthLabel: MONTH_LABELS[mesNum - 1],
            value: val,
          };
        }
      }
    }

    const years = Array.from(yearSet).sort((a, b) => b - a);
    return { years, grid, latestCell };
  })();

  $: activeCell = (() => {
    if (selectedKey && parsed.grid.has(selectedKey)) {
      const [yStr, mStr] = selectedKey.split('-');
      const year = Number(yStr);
      const mesNum = Number(mStr);
      return {
        key: selectedKey,
        year,
        mesNum,
        monthLabel: MONTH_LABELS[mesNum - 1],
        value: parsed.grid.get(selectedKey),
      };
    }
    return parsed.latestCell;
  })();

  function selectCell(year, mesNum) {
    const key = `${year}-${mesNum}`;
    if (parsed.grid.has(key)) {
      selectedKey = key;
    }
  }
</script>

<section class="terminal-panel heatmap-panel" aria-labelledby="ibov-heatmap-title">
  <div class="hm-header">
    <div class="hm-heading">
      <h2 id="ibov-heatmap-title" class="terminal-panel-title">
        {#if panelIndex}<span class="panel-index">{panelIndex}</span>{/if}
        <span>{title}</span>
      </h2>
      {#if subtitle}
        <p class="terminal-panel-sub hm-sub">{subtitle}</p>
      {/if}
    </div>

    {#if activeCell}
      <div class="hm-active-pill" aria-live="polite">
        <span
          class="hm-active-dot"
          style={`background: ${getColorForReturn(activeCell.value)};`}
          aria-hidden="true"
        ></span>
        <span class="hm-active-period">{activeCell.monthLabel}/{activeCell.year}</span>
        <span class="hm-active-sep" aria-hidden="true">·</span>
        <span class="hm-active-val">{formatPctBr(activeCell.value)}</span>
      </div>
    {/if}
  </div>

  <div class="hm-root">
    <div
      class="hm-scroll"
      role="region"
      tabindex="0"
      aria-labelledby="ibov-heatmap-title"
    >
      <table class="hm-table">
        <colgroup>
          <col class="hm-col-year" />
          {#each MONTH_LABELS as _}
            <col />
          {/each}
        </colgroup>
        <thead>
          <tr>
            <th scope="col" class="hm-corner">Ano</th>
            {#each MONTH_LABELS as mLabel}
              <th scope="col" class="hm-month">{mLabel}</th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each parsed.years as year}
            <tr>
              <th scope="row" class="hm-year">{year}</th>
              {#each MONTH_LABELS as mLabel, idx}
                {@const mesNum = idx + 1}
                {@const cellKey = `${year}-${mesNum}`}
                {@const val = parsed.grid.has(cellKey) ? parsed.grid.get(cellKey) : null}
                <td class="hm-cell">
                  {#if val !== null}
                    <button
                      type="button"
                      class="hm-tile"
                      class:is-active={activeCell && activeCell.key === cellKey}
                      style={`background: ${getColorForReturn(val)};`}
                      aria-label={`${mLabel} de ${year}: ${formatPctBr(val)}`}
                      aria-pressed={activeCell && activeCell.key === cellKey}
                      on:mouseenter={() => selectCell(year, mesNum)}
                      on:focus={() => selectCell(year, mesNum)}
                      on:click={() => selectCell(year, mesNum)}
                    >
                      {formatPctBr(val)}
                    </button>
                  {:else}
                    <span
                      class="hm-empty"
                      aria-label={`${mLabel} de ${year}: sem dados`}
                    >
                      —
                    </span>
                  {/if}
                </td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <p class="hm-hint">Deslize horizontalmente para ver Jan–Dez →</p>

    <div class="hm-legend" aria-label="Legenda de faixas de retorno mensal">
      {#each LEGEND_ITEMS as item}
        <span class="hm-legend-item">
          <span
            class="hm-legend-swatch"
            style={`background: ${item.color};`}
            aria-hidden="true"
          ></span>
          <span class="hm-legend-label">{item.label}</span>
        </span>
      {/each}
    </div>
  </div>
</section>

<style>
  .hm-header {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px 16px;
    margin-block-end: 14px;
  }

  .hm-heading {
    min-inline-size: 0;
    flex: 1 1 280px;
  }

  .hm-sub {
    margin-block-end: 0 !important;
  }

  .hm-active-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 5px 11px;
    border-radius: 999px;
    background: #222222;
    border: 1px solid #3a3a3f;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 11.5px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    color: #f5f5f5;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .hm-active-dot {
    inline-size: 8px;
    block-size: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .hm-active-period {
    color: #c8c8d2;
  }

  .hm-active-sep {
    color: #6e6e78;
  }

  .hm-active-val {
    color: #f8f8f8;
  }

  .hm-root {
    container-type: inline-size;
    inline-size: 100%;
    min-inline-size: 0;
  }

  .hm-scroll {
    overflow-x: auto;
    max-inline-size: 100%;
    -webkit-overflow-scrolling: touch;
    padding-block-end: 8px;
    --scrollbar-thumb: #7a7a85;
    --scrollbar-track: #222222;
    scrollbar-width: thin;
    scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);
  }

  .hm-scroll:focus-visible {
    outline: 2px solid #f2b94b;
    outline-offset: 3px;
    border-radius: 8px;
  }

  @supports not (scrollbar-color: auto) {
    .hm-scroll {
      scrollbar-width: auto;
    }

    .hm-scroll::-webkit-scrollbar {
      height: 8px;
    }

    .hm-scroll::-webkit-scrollbar-thumb {
      background: var(--scrollbar-thumb);
      border-radius: 999px;
    }

    .hm-scroll::-webkit-scrollbar-track {
      background: var(--scrollbar-track);
      border-radius: 999px;
    }
  }

  .hm-table {
    width: 100%;
    min-width: 780px;
    border-collapse: separate;
    border-spacing: 5px;
    table-layout: fixed;
    background: transparent;
  }

  .hm-col-year {
    width: 54px;
  }

  .hm-corner,
  .hm-year {
    position: sticky;
    inset-inline-start: 0;
    z-index: 2;
    background: #2b2b2b;
    padding-inline-end: 8px;
    text-align: right;
    vertical-align: middle;
  }

  .hm-corner {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 10.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #7c7c86;
    padding-block-end: 4px;
  }

  .hm-month {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 11.5px;
    font-weight: 600;
    color: #d4d4d8;
    text-align: center;
    padding: 0 0 4px 0;
    border: 0;
    background: transparent;
  }

  .hm-year {
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 11.5px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    color: #e5e5e5;
    padding-block: 0;
    padding-inline-start: 0;
    border: 0;
  }

  .hm-cell {
    padding: 0;
    border: 0;
    background: transparent;
    vertical-align: middle;
  }

  .hm-tile {
    inline-size: 100%;
    block-size: 38px;
    border: 0;
    border-radius: 7px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 11.5px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    color: #f8f8f8;
    white-space: nowrap;
    cursor: pointer;
    padding: 0 4px;
    transition: transform 0.12s ease, filter 0.12s ease, outline-color 0.12s ease;
  }

  .hm-tile:hover {
    filter: brightness(1.1);
  }

  .hm-tile:focus-visible,
  .hm-tile.is-active {
    outline: 2px solid #f2b94b;
    outline-offset: -2px;
  }

  .hm-empty {
    inline-size: 100%;
    block-size: 38px;
    border-radius: 7px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.025);
    border: 1px dashed rgba(255, 255, 255, 0.08);
    color: #5a5a63;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 11.5px;
  }

  .hm-hint {
    display: none;
    margin: 8px 0 0 0;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 11px;
    color: #8a8a93;
    text-align: right;
  }

  .hm-legend {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px 14px;
    margin-block-start: 12px;
  }

  .hm-legend-item {
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  .hm-legend-swatch {
    inline-size: 12px;
    block-size: 10px;
    border-radius: 3px;
    flex-shrink: 0;
  }

  .hm-legend-label {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 11px;
    color: #a3a3a3;
    white-space: nowrap;
  }

  @container (width < 800px) {
    .hm-corner,
    .hm-year {
      box-shadow: 6px 0 10px -6px rgba(0, 0, 0, 0.6);
    }

    .hm-hint {
      display: block;
    }
  }
</style>
