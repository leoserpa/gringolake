<script>
  import { ECharts } from '@evidence-dev/core-components';

  export let data = [];
  export let x = 'trading_date';
  export let flowCol = 'pf_cum_bi_brl';
  export let flowName = 'Fluxo Acumulado';
  export let maCol = null;
  export let maName = 'MM 21 pregões';
  export let ibovCol = 'ibov_close';
  export let ibovName = 'IBOV (pts)';
  export let extremaCol = null;
  export let shadeCol = null;
  export let height = '270px';
  export let flowColor = '#facc15';
  export let ibovColor = '#d4d4d4';
  export let maColor = '#737373';
  export let zoom = false;

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
    const sign = num < 0 ? '-' : num > 0 ? '+' : '';
    return `${sign}R$ ${Math.abs(num).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })} bi`;
  }

  function formatBiAxis(v) {
    const num = Number(v);
    if (Number.isNaN(num)) return '';
    const abs = Math.abs(num).toLocaleString('pt-BR', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    });
    return num < 0 ? `(${abs})` : abs;
  }

  function formatPts(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '—';
    return Math.round(Number(v)).toLocaleString('pt-BR');
  }

  $: dates = rows.map((r) => toIsoDate(r[x]));
  $: flowData = rows.map((r) => (r[flowCol] === null || r[flowCol] === undefined ? null : Number(r[flowCol])));
  $: maData = maCol
    ? rows.map((r) => (r[maCol] === null || r[maCol] === undefined ? null : Number(r[maCol])))
    : [];
  $: ibovData = rows.map((r) => (r[ibovCol] === null || r[ibovCol] === undefined ? null : Number(r[ibovCol])));

  // Build shaded crossover intervals where shadeCol is truthy (Chart 1 style)
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

  // Build IBOV local peak/trough callout badges
  $: ibovExtremaPoints = (() => {
    if (!extremaCol || !rows.length) return [];
    const pts = [];
    for (let i = 0; i < rows.length; i++) {
      const labelPts = rows[i][extremaCol];
      if (labelPts !== null && labelPts !== undefined && ibovData[i] !== null) {
        pts.push({
          coord: [dates[i], ibovData[i]],
          value: formatPts(labelPts),
        });
      }
    }
    return pts;
  })();

  $: lastFlowIdx = (() => {
    for (let i = flowData.length - 1; i >= 0; i--) {
      if (flowData[i] !== null) return i;
    }
    return -1;
  })();

  $: series = [
    {
      name: flowName,
      type: 'line',
      yAxisIndex: 0,
      data: flowData,
      showSymbol: false,
      smooth: false,
      connectNulls: true,
      lineStyle: { color: flowColor, width: 2.1 },
      itemStyle: { color: flowColor },
      markPoint:
        lastFlowIdx >= 0
          ? {
              symbol: 'circle',
              symbolSize: 8,
              silent: true,
              label: { show: false },
              itemStyle: { color: flowColor, borderColor: '#161616', borderWidth: 2 },
              data: [{ coord: [dates[lastFlowIdx], flowData[lastFlowIdx]] }],
            }
          : undefined,
      markArea:
        shadeAreas.length > 0
          ? {
              silent: true,
              itemStyle: {
                color: 'rgba(250, 204, 21, 0.065)',
                borderColor: 'rgba(250, 204, 21, 0.22)',
                borderWidth: 1,
              },
              data: shadeAreas,
            }
          : undefined,
    },
    ...(maCol
      ? [
          {
            name: maName,
            type: 'line',
            yAxisIndex: 0,
            data: maData,
            showSymbol: false,
            smooth: false,
            connectNulls: true,
            lineStyle: { color: maColor, width: 1.35, type: 'dashed' },
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
      smooth: false,
      connectNulls: true,
      lineStyle: { color: ibovColor, width: 1.55 },
      itemStyle: { color: ibovColor },
      markPoint:
        ibovExtremaPoints.length > 0
          ? {
              symbol: 'circle',
              symbolSize: 6,
              silent: true,
              itemStyle: { color: '#f5f5f5', borderColor: '#161616', borderWidth: 1.5 },
              label: {
                show: true,
                position: 'top',
                distance: 6,
                formatter: (p) => p.data.value,
                color: '#f5f5f5',
                backgroundColor: '#212121',
                borderColor: '#2a2a2a',
                borderWidth: 1,
                borderRadius: 4,
                padding: [2, 5],
                fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
                fontSize: 9.5,
                fontWeight: 600,
              },
              data: ibovExtremaPoints,
            }
          : undefined,
    },
  ];

  $: config = {
    backgroundColor: 'transparent',
    animationDuration: 300,
    grid: {
      top: 46,
      right: 14,
      bottom: zoom ? 48 : 24,
      left: 12,
      containLabel: true,
    },
    legend: {
      show: true,
      top: 0,
      left: 'center',
      icon: 'circle',
      itemWidth: 8,
      itemHeight: 8,
      itemGap: 14,
      textStyle: {
        color: '#a6a6a6',
        fontFamily: 'IBM Plex Sans, system-ui, sans-serif',
        fontSize: 11,
        padding: [0, 0, 0, 3],
      },
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#212121',
      borderColor: '#2a2a2a',
      borderWidth: 1,
      textStyle: {
        color: '#f5f5f5',
        fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
        fontSize: 11,
      },
      axisPointer: {
        type: 'line',
        lineStyle: { color: '#3f3f46', width: 1, type: 'dashed' },
      },
      formatter: (params) => {
        if (!Array.isArray(params) || !params.length) return '';
        const dateStr = params[0].axisValueLabel || '';
        const lines = [`<div style="color:#a6a6a6;margin-bottom:4px;">${dateStr}</div>`];
        for (const p of params) {
          if (p.value === null || p.value === undefined) continue;
          const formatted = p.seriesName === ibovName ? `${formatPts(p.value)} pts` : formatBi(p.value);
          lines.push(
            `<div style="display:flex;justify-content:space-between;gap:14px;">` +
              `<span><span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:${p.color};margin-right:6px;"></span>${p.seriesName}</span>` +
              `<strong style="color:#f5f5f5;">${formatted}</strong>` +
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
            height: 18,
            bottom: 4,
            borderColor: '#2a2a2a',
            backgroundColor: '#0f0f0f',
            fillerColor: 'rgba(250, 204, 21, 0.14)',
            handleStyle: { color: '#facc15', borderColor: '#facc15' },
            textStyle: { color: '#737373', fontFamily: 'IBM Plex Mono, monospace', fontSize: 10 },
          },
        ]
      : undefined,
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#2a2a2a' } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: {
        color: '#737373',
        fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
        fontSize: 10,
        hideOverlap: true,
        formatter: (v) => formatShortDate(v),
      },
    },
    yAxis: [
      {
        type: 'value',
        name: 'R$ bi',
        nameTextStyle: {
          color: '#737373',
          fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
          fontSize: 10,
          padding: [0, 0, 0, -8],
        },
        scale: true,
        boundaryGap: ['10%', '14%'],
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: '#202020' } },
        axisLabel: {
          color: '#737373',
          fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
          fontSize: 10,
          formatter: (v) => formatBiAxis(v),
        },
      },
      {
        type: 'value',
        scale: true,
        boundaryGap: ['10%', '14%'],
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: {
          color: '#737373',
          fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
          fontSize: 10,
          formatter: (v) => formatPts(v),
        },
      },
    ],
    series,
  };
</script>

<div class="terminal-dual-wrap">
  <ECharts {data} {config} {height} />
</div>

<style>
  .terminal-dual-wrap {
    inline-size: 100%;
    min-inline-size: 0;
  }
</style>
