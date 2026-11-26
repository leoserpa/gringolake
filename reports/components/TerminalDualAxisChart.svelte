<script>
  import { ECharts } from '@evidence-dev/core-components';

  export let data = [];
  export let x = 'trading_date';
  export let flowCol = 'pf_cum_bi_brl';
  export let flowName = 'Fluxo Acumulado';
  export let maCol = null;
  export let maObsCol = null;
  export let maName = 'MM 21d';
  export let ibovCol = 'ibov_close';
  export let ibovName = 'IBOV (pts)';
  export let shadeCol = null;
  export let height = '280px';
  export let flowColor = '#f2b94b';
  export let ibovColor = '#9a9aa0';
  export let maColor = '#5c5c62';
  export let zoom = false;
  export let focal = false;
  export let panelIndex = '';
  export let panelTitle = '';
  export let panelSubtitle = '';

  let chartWidth = 0;
  $: isCompact = chartWidth > 0 && chartWidth < 460;
  $: resolvedHeight = isCompact ? '235px' : height;

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

  function formatShortDate(iso) {
    if (!iso || iso.length < 10) return iso;
    return `${iso.slice(8, 10)}/${iso.slice(5, 7)}`;
  }

  function formatBi(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '—';
    const num = Number(v);
    const normalized = Math.abs(num) < 0.005 ? 0 : num;
    const sign = normalized < 0 ? '-' : normalized > 0 ? '+' : '';
    return `${sign}R$ ${Math.abs(normalized).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })} bi`;
  }

  function formatBiAxis(v) {
    const num = Number(v);
    if (Number.isNaN(num)) return '';
    if (Math.abs(num) < 0.05) return '0';
    const sign = num < 0 ? '-' : '';
    const abs = Math.abs(num).toLocaleString('pt-BR', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    });
    return `${sign}${abs} bi`;
  }

  function formatPts(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '—';
    return Math.round(Number(v)).toLocaleString('pt-BR');
  }

  function formatPtsAxis(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '';
    const num = Number(v);
    if (Math.abs(num) >= 1000) {
      return `${Math.round(num / 1000)}k`;
    }
    return String(Math.round(num));
  }

  $: dates = rows.map((r) => toIsoDate(r[x]));
  $: flowData = rows.map((r) => (r[flowCol] === null || r[flowCol] === undefined ? null : Number(r[flowCol])));
  $: maData = maCol
    ? rows.map((r) => (r[maCol] === null || r[maCol] === undefined ? null : Number(r[maCol])))
    : [];
  $: hasValidMa = Boolean(maCol && maData.some((v) => v !== null && !Number.isNaN(v)));
  $: latestMaObs = (() => {
    if (!maObsCol || !rows.length) return null;
    for (let i = rows.length - 1; i >= 0; i--) {
      const val = rows[i][maObsCol];
      if (val !== null && val !== undefined && !Number.isNaN(Number(val))) {
        return Number(val);
      }
    }
    return null;
  })();
  $: ibovData = rows.map((r) => (r[ibovCol] === null || r[ibovCol] === undefined ? null : Number(r[ibovCol])));

  $: lastFlowIdx = (() => {
    for (let i = flowData.length - 1; i >= 0; i--) {
      if (flowData[i] !== null) return i;
    }
    return -1;
  })();

  $: latestFlowVal = lastFlowIdx >= 0 ? flowData[lastFlowIdx] : null;
  $: badgeColor = focal || (latestFlowVal !== null && latestFlowVal > 0) ? '#f2b94b' : '#e5e5e5';

  $: shadeAreas = (() => {
    if (!shadeCol || !rows.length) return [];
    const areas = [];
    let startIdx = null;
    for (let i = 0; i < rows.length; i++) {
      const active = Boolean(rows[i][shadeCol]);
      if (active && startIdx === null) {
        startIdx = i;
      } else if (!active && startIdx !== null) {
        areas.push([{ xAxis: dates[startIdx] }, { xAxis: dates[i - 1] }]);
        startIdx = null;
      }
    }
    if (startIdx !== null) {
      areas.push([{ xAxis: dates[startIdx] }, { xAxis: dates[rows.length - 1] }]);
    }
    return areas;
  })();

  $: series = [
    {
      name: flowName,
      type: 'line',
      yAxisIndex: 0,
      data: flowData,
      showSymbol: false,
      smooth: 0.25,
      connectNulls: true,
      lineStyle: { color: flowColor, width: 2.4, cap: 'round' },
      itemStyle: { color: flowColor },
      markPoint:
        lastFlowIdx >= 0
          ? {
              symbol: 'circle',
              symbolSize: 8,
              silent: true,
              label: { show: false },
              itemStyle: { color: flowColor, borderColor: '#2b2b2b', borderWidth: 2 },
              data: [{ coord: [dates[lastFlowIdx], flowData[lastFlowIdx]] }],
            }
          : undefined,
      markArea:
        shadeAreas.length > 0
          ? {
              silent: true,
              itemStyle: {
                color: 'rgba(242, 185, 75, 0.08)',
                borderColor: 'rgba(242, 185, 75, 0.22)',
                borderWidth: 1,
              },
              data: shadeAreas,
            }
          : undefined,
    },
    ...(hasValidMa
      ? [
          {
            name: maName,
            type: 'line',
            yAxisIndex: 0,
            data: maData,
            showSymbol: false,
            smooth: 0.25,
            connectNulls: true,
            lineStyle: { color: maColor, width: 1.25, type: 'dashed' },
            itemStyle: { color: maColor },
          },
        ]
      : []),
    {
      name: ibovName,
      type: 'line',
      yAxisIndex: 1,
      data: ibovData,
      showSymbol: false,
      smooth: 0.25,
      connectNulls: true,
      lineStyle: { color: ibovColor, width: 1.5, cap: 'round' },
      itemStyle: { color: ibovColor },
    },
  ];

  $: config = {
    backgroundColor: 'transparent',
    animationDuration: 320,
    grid: {
      top: isCompact ? 34 : 38,
      right: isCompact ? 2 : 6,
      bottom: zoom ? 50 : 22,
      left: isCompact ? 2 : 6,
      containLabel: true,
    },
    legend: {
      show: true,
      top: 0,
      left: 0,
      type: 'scroll',
      icon: 'roundRect',
      itemWidth: isCompact ? 9 : 11,
      itemHeight: 3,
      itemGap: isCompact ? 10 : 16,
      pageIconColor: '#a3a3a3',
      pageTextStyle: { color: '#767676' },
      textStyle: {
        color: '#a3a3a3',
        fontFamily: 'Plus Jakarta Sans, system-ui, sans-serif',
        fontSize: isCompact ? 10 : 11,
        padding: [0, 0, 0, 3],
      },
    },
    tooltip: {
      trigger: 'axis',
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
      axisPointer: {
        type: 'line',
        lineStyle: { color: '#55555b', width: 1, type: 'dashed' },
      },
      formatter: (params) => {
        if (!Array.isArray(params) || !params.length) return '';
        const dateStr = params[0].axisValueLabel || '';
        const lines = [
          `<div style="color:#a3a3a3;margin-bottom:6px;font-family:Plus Jakarta Sans,sans-serif;font-weight:600;font-size:11px;">${dateStr}</div>`,
        ];
        for (const p of params) {
          if (p.value === null || p.value === undefined) continue;
          const formatted = p.seriesName === ibovName ? `${formatPts(p.value)} pts` : formatBi(p.value);
          lines.push(
            `<div style="display:flex;justify-content:space-between;align-items:center;gap:16px;line-height:1.55;">` +
              `<span style="color:#a3a3a3;font-family:Plus Jakarta Sans,sans-serif;"><span style="display:inline-block;width:7px;height:7px;border-radius:999px;background:${p.color};margin-right:7px;"></span>${p.seriesName}</span>` +
              `<strong style="color:#f8f8f8;">${formatted}</strong>` +
            `</div>`
          );
        }
        return lines.join('');
      },
    },
    dataZoom: zoom
      ? [
          { type: 'inside', xAxisIndex: 0 },
          {
            type: 'slider',
            xAxisIndex: 0,
            height: 20,
            bottom: 4,
            borderColor: '#363636',
            backgroundColor: '#222222',
            fillerColor: 'rgba(242, 185, 75, 0.16)',
            handleStyle: { color: '#f2b94b', borderColor: '#f2b94b' },
            moveHandleStyle: { color: '#5c5c62' },
            textStyle: { color: '#767676', fontFamily: 'JetBrains Mono, monospace', fontSize: 10 },
          },
        ]
      : undefined,
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#3a3a3f' } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: {
        color: '#767676',
        fontFamily: 'JetBrains Mono, ui-monospace, monospace',
        fontSize: isCompact ? 9 : 10,
        margin: 10,
        hideOverlap: true,
        formatter: (v) => formatShortDate(v),
      },
    },
    yAxis: [
      {
        type: 'value',
        scale: true,
        boundaryGap: ['12%', '16%'],
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: {
          color: '#767676',
          fontFamily: 'JetBrains Mono, ui-monospace, monospace',
          fontSize: isCompact ? 9 : 10,
          formatter: (v) => formatBiAxis(v),
        },
      },
      {
        type: 'value',
        scale: true,
        boundaryGap: ['12%', '16%'],
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: {
          color: '#767676',
          fontFamily: 'JetBrains Mono, ui-monospace, monospace',
          fontSize: isCompact ? 9 : 10,
          formatter: (v) => formatPtsAxis(v),
        },
      },
    ],
    series,
  };
</script>

<div class="terminal-dual-wrap">
  {#if panelTitle}
    <div class="dual-head-row">
      <h2 class="terminal-panel-title" style="margin: 0;">
        {#if panelIndex}
          <span class="panel-index">{panelIndex}</span>
        {/if}
        <span>{panelTitle}</span>
      </h2>
      {#if latestFlowVal !== null}
        <span class="dual-live-readout" style={`color: ${badgeColor};`}>{formatBi(latestFlowVal)}</span>
      {/if}
    </div>
    {#if panelSubtitle || (maCol && !hasValidMa && latestMaObs !== null)}
      <div class="dual-sub-row">
        {#if panelSubtitle}
          <p class="terminal-panel-sub" style="margin: 0;">{panelSubtitle}</p>
        {/if}
        {#if maCol && !hasValidMa && latestMaObs !== null}
          <span class="ma-warmup-pill">MM21 em formação · {latestMaObs}/21 pregões</span>
        {/if}
      </div>
    {/if}
  {/if}
  <div class="dual-chart-box" bind:clientWidth={chartWidth}>
    {#if chartWidth > 0}
      <ECharts {data} {config} height={resolvedHeight} width="100%" />
    {/if}
  </div>
</div>

<style>
  .terminal-dual-wrap {
    inline-size: 100%;
    max-inline-size: 100%;
    min-inline-size: 0;
  }

  .dual-chart-box {
    inline-size: 100%;
    max-inline-size: 100%;
    overflow: hidden;
  }

  .dual-head-row {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 4px 12px;
    margin-block-end: 4px;
  }

  .dual-live-readout {
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 14px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  .dual-sub-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 6px 12px;
    margin-block-end: 12px;
  }

  .ma-warmup-pill {
    display: inline-flex;
    align-items: center;
    padding: 2px 9px;
    border-radius: 999px;
    background: #262626;
    border: 1px solid #3a3a3f;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 10.5px;
    font-weight: 500;
    color: #a3a3a3;
    white-space: nowrap;
  }

  @media (max-width: 640px) {
    .dual-live-readout {
      font-size: 13px;
    }
  }
</style>
