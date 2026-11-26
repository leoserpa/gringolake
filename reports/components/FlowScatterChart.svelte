<script>
  import { ECharts } from '@evidence-dev/core-components';

  export let data = [];
  export let xCol = 'estrang_mi';
  export let yCol = 'ibov_return_1d_pct';
  export let dateCol = 'trading_date';
  export let panelIndex = '';
  export let panelTitle = '';
  export let panelSubtitle = '';
  export let height = '290px';

  let chartWidth = 0;
  $: isCompact = chartWidth > 0 && chartWidth < 460;
  $: resolvedHeight = isCompact ? '245px' : height;

  $: rows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  function toIsoDate(val) {
    if (!val) return '';
    if (val instanceof Date) return val.toISOString().slice(0, 10);
    return String(val).slice(0, 10);
  }

  function formatBrDate(iso) {
    if (!iso || iso.length < 10) return iso;
    return `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}`;
  }

  function formatMi(v) {
    const num = Number(v);
    if (Number.isNaN(num)) return '—';
    const sign = num < 0 ? '-' : num > 0 ? '+' : '';
    return `${sign}R$ ${Math.abs(num).toLocaleString('pt-BR', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    })} mi`;
  }

  function formatPct(v) {
    const num = Number(v);
    if (Number.isNaN(num)) return '—';
    const sign = num < 0 ? '-' : num > 0 ? '+' : '';
    return `${sign}${Math.abs(num).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}%`;
  }

  $: parsed = rows
    .map((r) => {
      const x = r[xCol] === null || r[xCol] === undefined ? null : Number(r[xCol]);
      const y = r[yCol] === null || r[yCol] === undefined ? null : Number(r[yCol]);
      if (x === null || y === null || Number.isNaN(x) || Number.isNaN(y)) return null;
      const aligned = (x >= 0 && y >= 0) || (x < 0 && y < 0);
      return { date: toIsoDate(r[dateCol]), x, y, aligned };
    })
    .filter(Boolean);

  $: alignedPoints = parsed.filter((p) => p.aligned).map((p) => ({ value: [p.x, p.y], date: p.date }));
  $: divergentPoints = parsed.filter((p) => !p.aligned).map((p) => ({ value: [p.x, p.y], date: p.date }));
  $: alignedPct = parsed.length > 0 ? Math.round((alignedPoints.length / parsed.length) * 100) : 0;

  $: config = {
    backgroundColor: 'transparent',
    animationDuration: 300,
    grid: {
      top: isCompact ? 34 : 38,
      right: isCompact ? 22 : 30,
      bottom: 30,
      left: isCompact ? 6 : 10,
      containLabel: true,
    },
    legend: {
      show: true,
      top: 0,
      left: 0,
      icon: 'circle',
      itemWidth: 8,
      itemHeight: 8,
      itemGap: isCompact ? 10 : 16,
      textStyle: {
        color: '#a3a3a3',
        fontFamily: 'Plus Jakarta Sans, system-ui, sans-serif',
        fontSize: isCompact ? 10 : 11,
      },
    },
    tooltip: {
      trigger: 'item',
      confine: true,
      backgroundColor: '#222222',
      borderColor: '#45454a',
      borderWidth: 1,
      extraCssText: 'border-radius: 16px; padding: 10px 14px; box-shadow: 0 14px 36px rgba(0, 0, 0, 0.48);',
      textStyle: {
        color: '#f8f8f8',
        fontFamily: 'JetBrains Mono, ui-monospace, monospace',
        fontSize: 11,
      },
      formatter: (p) => {
        const dt = formatBrDate(p.data?.date || '');
        const xVal = p.data?.value?.[0];
        const yVal = p.data?.value?.[1];
        return (
          `<div style="color:#a3a3a3;margin-bottom:6px;font-family:Plus Jakarta Sans,sans-serif;font-weight:600;font-size:11px;">${dt} · ${p.seriesName}</div>` +
          `<div style="display:flex;justify-content:space-between;gap:14px;line-height:1.55;">` +
            `<span style="color:#a3a3a3;font-family:Plus Jakarta Sans,sans-serif;">Estrangeiro</span>` +
            `<strong style="color:#f8f8f8;">${formatMi(xVal)}</strong>` +
          `</div>` +
          `<div style="display:flex;justify-content:space-between;gap:14px;line-height:1.55;">` +
            `<span style="color:#a3a3a3;font-family:Plus Jakarta Sans,sans-serif;">Retorno IBOV</span>` +
            `<strong style="color:${p.color};">${formatPct(yVal)}</strong>` +
          `</div>`
        );
      },
    },
    xAxis: {
      type: 'value',
      scale: true,
      axisLine: { onZero: true, lineStyle: { color: '#424248' } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: {
        color: '#767676',
        fontFamily: 'JetBrains Mono, ui-monospace, monospace',
        fontSize: isCompact ? 9 : 10,
        formatter: (v) => (Math.abs(v) < 0.5 ? '0' : `${Math.round(v).toLocaleString('pt-BR')} mi`),
      },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLine: { onZero: true, lineStyle: { color: '#424248' } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: {
        color: '#767676',
        fontFamily: 'JetBrains Mono, ui-monospace, monospace',
        fontSize: isCompact ? 9 : 10,
        formatter: (v) => (Math.abs(v) < 0.05 ? '0%' : `${v > 0 ? '+' : ''}${Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`),
      },
    },
    series: [
      {
        name: 'Mesma direção',
        type: 'scatter',
        symbolSize: isCompact ? 9 : 11,
        data: alignedPoints,
        itemStyle: {
          color: '#f2b94b',
          borderColor: '#2b2b2b',
          borderWidth: 1.5,
        },
      },
      {
        name: 'Divergente',
        type: 'scatter',
        symbolSize: isCompact ? 8 : 10,
        data: divergentPoints,
        itemStyle: {
          color: '#9a9aa0',
          borderColor: '#2b2b2b',
          borderWidth: 1.5,
        },
      },
    ],
  };
</script>

<div class="scatter-wrap">
  {#if panelTitle}
    <div class="scatter-head-row">
      <h2 class="terminal-panel-title" style="margin: 0;">
        {#if panelIndex}
          <span class="panel-index">{panelIndex}</span>
        {/if}
        <span>{panelTitle}</span>
      </h2>
      {#if parsed.length > 0}
        <span class="scatter-readout">{alignedPoints.length}/{parsed.length} alinhados ({alignedPct}%)</span>
      {/if}
    </div>
    {#if panelSubtitle}
      <p class="terminal-panel-sub">{panelSubtitle}</p>
    {/if}
  {/if}
  <div class="scatter-box" bind:clientWidth={chartWidth}>
    {#if chartWidth > 0}
      <ECharts {data} {config} height={resolvedHeight} width="100%" />
    {/if}
  </div>
</div>

<style>
  .scatter-wrap {
    inline-size: 100%;
    max-inline-size: 100%;
    min-inline-size: 0;
  }

  .scatter-box {
    inline-size: 100%;
    max-inline-size: 100%;
    overflow: hidden;
  }

  .scatter-head-row {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 4px 12px;
    margin-block-end: 4px;
  }

  .scatter-readout {
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 12.5px;
    font-weight: 600;
    color: #f2b94b;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
</style>
