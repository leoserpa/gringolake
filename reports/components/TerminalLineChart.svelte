<script>
  import { ECharts } from '@evidence-dev/core-components';

  export let data = [];
  export let x = 'trading_date';
  export let y = [];
  export let names = [];
  export let colors = ['#d97706', '#475569', '#9ca3af', '#cbd5e1'];
  export let dashed = [];
  export let prefix = '';
  export let suffix = '';
  export let decimals = 2;
  export let signed = false;
  export let height = '255px';
  export let showEndLabel = true;
  export let chartType = 'line';
  export let axisCompact = false;
  export let positiveColor = '#d97706';
  export let negativeColor = '#94a3b8';

  $: isBar = chartType === 'bar';

  $: rows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  $: yList = Array.isArray(y) ? y : [y];

  function toIsoDate(val) {
    if (val === null || val === undefined || val === '') return '';
    if (val instanceof Date) return val.toISOString().slice(0, 10);
    if (typeof val === 'number' && !Number.isNaN(val)) {
      return new Date(val).toISOString().slice(0, 10);
    }
    const str = String(val);
    if (/^\d{10,13}$/.test(str)) {
      const ms = str.length === 10 ? Number(str) * 1000 : Number(str);
      return new Date(ms).toISOString().slice(0, 10);
    }
    return str.slice(0, 10);
  }

  function formatAxisDate(val) {
    const iso = toIsoDate(val);
    if (!iso || iso.length < 10) return iso;
    return rows.length > 260 ? iso.slice(0, 4) : `${iso.slice(8, 10)}/${iso.slice(5, 7)}`;
  }

  function formatTooltipDate(val) {
    const iso = toIsoDate(val);
    if (!iso || iso.length < 10) return iso;
    return `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}`;
  }

  function formatVal(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '—';
    const num = Number(v);
    const sign = num < 0 ? '-' : signed && num > 0 ? '+' : '';
    const formatted = Math.abs(num).toLocaleString('pt-BR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
    return `${sign}${prefix}${formatted}${suffix}`;
  }

  function formatAxisVal(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '';
    const num = Number(v);
    if (axisCompact && suffix.trim() === 'mi') {
      const sign = num < 0 ? '-' : '';
      const formatted = Math.abs(num).toLocaleString('pt-BR', {
        maximumFractionDigits: 0,
      });
      return `${sign}${formatted}M`;
    }
    return formatVal(v);
  }

  $: barCategories = isBar
    ? Array.from(new Set(rows.map((r) => toIsoDate(r[x])).filter(Boolean)))
    : [];

  $: seriesMeta = yList
    .map((col, idx) => {
      const pts = [];
      let lastPt = null;
      const barMap = new Map();

      for (const r of rows) {
        const dt = toIsoDate(r[x]);
        const raw = r[col];
        if (!dt || raw === null || raw === undefined) continue;
        const val = Number(raw);
        if (Number.isNaN(val)) continue;
        if (isBar) {
          barMap.set(dt, val);
        } else {
          pts.push([dt, val]);
        }
        lastPt = { x: dt, val };
      }

      if (isBar) {
        for (const dt of barCategories) {
          if (!barMap.has(dt)) {
            pts.push(null);
            continue;
          }
          const val = barMap.get(dt);
          const isPos = val >= 0;
          pts.push({
            value: val,
            itemStyle: {
              color: isPos ? positiveColor : negativeColor,
              borderRadius: isPos ? [3, 3, 0, 0] : [0, 0, 3, 3],
            },
          });
        }
      }

      if (!lastPt) return null;

      const isPrimary = idx === 0;
      const color = colors[idx] || '#737373';
      const name = names[idx] || col;
      const isDashed = Boolean(dashed[idx]);
      const endText = lastPt ? formatVal(lastPt.val) : '';
      const showSeriesEnd = showEndLabel && !isBar && Boolean(lastPt);

      return {
        endText,
        series: {
          name,
          type: chartType,
          data: pts,
          showSymbol: false,
          smooth: false,
          connectNulls: true,
          barMaxWidth: 18,
          barCategoryGap: '28%',
          lineStyle: !isBar
            ? {
                color,
                width: isPrimary ? 2 : 1.35,
                type: isDashed ? 'dashed' : 'solid',
              }
            : undefined,
          itemStyle: !isBar ? { color } : undefined,
          markLine: isBar
            ? {
                silent: true,
                symbol: ['none', 'none'],
                label: { show: false },
                lineStyle: { color: '#d4d4d8', width: 1, type: 'solid' },
                data: [{ yAxis: 0 }],
              }
            : undefined,
          endLabel: showSeriesEnd
            ? {
                show: true,
                distance: 10,
                verticalAlign: 'middle',
                formatter: () => endText,
                color: isPrimary ? color : '#52525b',
                fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
                fontWeight: isPrimary ? 700 : 500,
                fontSize: isPrimary ? 11 : 10,
              }
            : { show: false },
          labelLayout: showSeriesEnd ? { moveOverlap: 'shiftY' } : undefined,
          markPoint: showSeriesEnd
            ? {
                symbol: 'circle',
                symbolSize: isPrimary ? 8 : 5,
                silent: true,
                label: { show: false },
                itemStyle: {
                  color,
                  borderColor: '#ffffff',
                  borderWidth: isPrimary ? 2 : 1.5,
                },
                data: [{ coord: [lastPt.x, lastPt.val] }],
              }
            : undefined,
        },
      };
    })
    .filter(Boolean);

  $: builtSeries = seriesMeta.map((m) => m.series);
  $: hasLegend = builtSeries.length > 1;
  $: maxEndChars = seriesMeta.reduce((acc, m) => Math.max(acc, m.endText.length), 6);
  $: rightPad = showEndLabel && !isBar ? Math.max(66, maxEndChars * 8 + 18) : 14;

  $: config = {
    backgroundColor: 'transparent',
    animationDuration: 300,
    grid: {
      top: hasLegend ? 36 : 16,
      right: rightPad,
      bottom: 24,
      left: 8,
      containLabel: true,
    },
    legend: hasLegend
      ? {
          show: true,
          top: 0,
          left: 'center',
          icon: 'circle',
          itemWidth: 8,
          itemHeight: 8,
          itemGap: 14,
          textStyle: {
            color: '#52525b',
            fontFamily: 'IBM Plex Sans, system-ui, sans-serif',
            fontSize: 11,
            padding: [0, 0, 0, 3],
          },
        }
      : { show: false },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#ffffff',
      borderColor: '#e4e4e7',
      borderWidth: 1,
      extraCssText: 'box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);',
      textStyle: {
        color: '#18181b',
        fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
        fontSize: 11,
      },
      axisPointer: {
        type: 'line',
        lineStyle: { color: '#d4d4d8', width: 1, type: 'dashed' },
      },
      formatter: (params) => {
        if (!Array.isArray(params) || !params.length) return '';
        const rawX = isBar ? params[0].axisValue : params[0].value?.[0] || params[0].axisValueLabel;
        const dateStr = formatTooltipDate(rawX);
        const lines = [`<div style="color:#71717a;margin-bottom:4px;">${dateStr}</div>`];
        for (const p of params) {
          const v = Array.isArray(p.value)
            ? p.value[1]
            : p.value && typeof p.value === 'object'
              ? p.value.value
              : p.value;
          if (v === null || v === undefined) continue;
          const dotColor = isBar ? (Number(v) >= 0 ? positiveColor : negativeColor) : p.color;
          lines.push(
            `<div style="display:flex;justify-content:space-between;gap:14px;">` +
              `<span style="color:#52525b;"><span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:${dotColor};margin-right:6px;"></span>${p.seriesName}</span>` +
              `<strong style="color:#18181b;">${formatVal(v)}</strong>` +
            `</div>`
          );
        }
        return lines.join('');
      },
    },
    xAxis: isBar
      ? {
          type: 'category',
          data: barCategories,
          boundaryGap: true,
          axisLine: { onZero: false, lineStyle: { color: '#e4e4e7' } },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: {
            color: '#71717a',
            fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
            fontSize: 10.5,
            hideOverlap: true,
            formatter: (val) => formatAxisDate(val),
          },
        }
      : {
          type: 'time',
          boundaryGap: false,
          axisLine: { lineStyle: { color: '#e4e4e7' } },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: {
            color: '#71717a',
            fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
            fontSize: 10.5,
            hideOverlap: true,
            formatter: (val) => formatAxisDate(val),
          },
        },
    yAxis: {
      type: 'value',
      scale: !isBar,
      boundaryGap: ['8%', '12%'],
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#f4f4f5' } },
      axisLabel: {
        color: '#71717a',
        fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
        fontSize: 10.5,
        formatter: (val) => formatAxisVal(val),
      },
    },
    series: builtSeries,
  };
</script>

<div class="terminal-line-wrap">
  <ECharts {data} {config} {height} />
</div>

<style>
  .terminal-line-wrap {
    inline-size: 100%;
    min-inline-size: 0;
  }
</style>
