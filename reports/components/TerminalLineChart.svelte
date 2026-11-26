<script>
  import { ECharts } from '@evidence-dev/core-components';

  export let data = [];
  export let x = 'trading_date';
  export let y = [];
  export let names = [];
  export let colors = ['#f2b94b', '#e5e5e5', '#8a8a91', '#5c5c62'];
  export let dashed = [];
  export let prefix = '';
  export let suffix = '';
  export let decimals = 2;
  export let signed = false;
  export let height = '275px';
  export let showEndLabel = true;
  export let chartType = 'line';
  export let axisCompact = false;
  export let positiveColor = '#f2b94b';
  export let negativeColor = '#5c5c62';
  export let highlightAboveAvg = false;
  export let focal = false;
  export let panelIndex = '';
  export let panelTitle = '';
  export let panelSubtitle = '';

  let chartWidth = 0;
  $: isCompact = chartWidth > 0 && chartWidth < 460;
  $: resolvedHeight = isCompact ? '230px' : height;
  $: effectiveEndLabel = showEndLabel && !isCompact;

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
    const epsilon = 0.5 * Math.pow(10, -decimals);
    const normalized = Math.abs(num) < epsilon ? 0 : num;
    const sign = normalized < 0 ? '-' : signed && normalized > 0 ? '+' : '';
    const formatted = Math.abs(normalized).toLocaleString('pt-BR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
    return `${sign}${prefix}${formatted}${suffix}`;
  }

  function formatAxisVal(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '';
    const num = Number(v);
    if (axisCompact && suffix.trim() === 'bi') {
      if (Math.abs(num) < 0.005) return '0';
      const sign = num < 0 ? '-' : '';
      const formatted = Math.abs(num).toLocaleString('pt-BR', {
        minimumFractionDigits: Math.abs(num) < 1 ? 1 : 0,
        maximumFractionDigits: 1,
      });
      return `${sign}${formatted} bi`;
    }
    if (axisCompact && suffix.trim() === 'mi') {
      if (Math.abs(num) < 0.5) return '0';
      const sign = num < 0 ? '-' : '';
      const formatted = Math.abs(num).toLocaleString('pt-BR', {
        maximumFractionDigits: 0,
      });
      return `${sign}${formatted} mi`;
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

      let barAvg = null;
      if (isBar) {
        if (highlightAboveAvg && barMap.size > 0) {
          let sum = 0;
          for (const v of barMap.values()) sum += v;
          barAvg = sum / barMap.size;
        }
        for (const dt of barCategories) {
          if (!barMap.has(dt)) {
            pts.push(null);
            continue;
          }
          const val = barMap.get(dt);
          const isPos = val >= 0;
          const barColor = highlightAboveAvg
            ? val >= barAvg * 1.4
              ? positiveColor
              : negativeColor
            : isPos
              ? positiveColor
              : negativeColor;
          pts.push({
            value: val,
            itemStyle: {
              color: barColor,
              borderRadius: isPos ? [7, 7, 3, 3] : [3, 3, 7, 7],
            },
          });
        }
      }

      if (!lastPt) return null;

      const isPrimary = idx === 0;
      const color = colors[idx] || '#767676';
      const name = names[idx] || col;
      const isDashed = Boolean(dashed[idx]);
      const endText = lastPt ? formatVal(lastPt.val) : '';
      const showSeriesEnd = effectiveEndLabel && !isBar && Boolean(lastPt);

      return {
        lastVal: lastPt.val,
        endText,
        series: {
          name,
          type: chartType,
          data: pts,
          showSymbol: false,
          smooth: isBar ? false : 0.25,
          connectNulls: true,
          barMaxWidth: 22,
          barCategoryGap: '26%',
          lineStyle: !isBar
            ? {
                color,
                width: isPrimary ? 2.4 : 1.5,
                cap: 'round',
                type: isDashed ? 'dashed' : 'solid',
              }
            : undefined,
          itemStyle: !isBar ? { color } : undefined,
          markLine: isBar
            ? {
                silent: true,
                symbol: ['none', 'none'],
                label:
                  highlightAboveAvg && barAvg !== null
                    ? {
                        show: true,
                        position: 'insideEndTop',
                        formatter: () => `Média ${formatVal(barAvg)}`,
                        color: '#a3a3a3',
                        fontFamily: 'JetBrains Mono, ui-monospace, monospace',
                        fontSize: 10,
                      }
                    : { show: false },
                lineStyle: {
                  color: highlightAboveAvg ? '#5c5c62' : '#424248',
                  width: 1,
                  type: highlightAboveAvg ? 'dashed' : 'solid',
                },
                data: [{ yAxis: highlightAboveAvg && barAvg !== null ? barAvg : 0 }],
              }
            : undefined,
          endLabel: showSeriesEnd
            ? {
                show: true,
                distance: 8,
                verticalAlign: 'middle',
                formatter: () => endText,
                color: isPrimary ? color : '#a3a3a3',
                fontFamily: 'JetBrains Mono, ui-monospace, monospace',
                fontWeight: isPrimary ? 600 : 500,
                fontSize: isPrimary ? 10.5 : 10,
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
                  borderColor: '#2b2b2b',
                  borderWidth: isPrimary ? 2 : 1.5,
                },
                data: [{ coord: [lastPt.x, lastPt.val] }],
              }
            : undefined,
        },
      };
    })
    .filter(Boolean);

  $: primaryLastVal = seriesMeta.length === 1 ? seriesMeta[0].lastVal : null;
  $: readoutColor =
    primaryLastVal !== null && signed
      ? focal || primaryLastVal > 0
        ? '#f2b94b'
        : '#e5e5e5'
      : '#f2b94b';

  $: builtSeries = seriesMeta.map((m) => m.series);
  $: hasLegend = builtSeries.length > 1;
  $: maxEndChars = seriesMeta.reduce((acc, m) => Math.max(acc, m.endText.length), 6);
  $: rightPad = effectiveEndLabel && !isBar ? Math.max(68, maxEndChars * 8 + 14) : isCompact ? 14 : 10;

  $: config = {
    backgroundColor: 'transparent',
    animationDuration: 320,
    grid: {
      top: hasLegend ? (isCompact ? 34 : 38) : 20,
      right: rightPad,
      bottom: 24,
      left: isCompact ? 4 : 6,
      containLabel: true,
    },
    legend: hasLegend
      ? {
          show: true,
          top: 0,
          left: 0,
          type: 'scroll',
          icon: 'roundRect',
          itemWidth: 11,
          itemHeight: 3,
          itemGap: 16,
          pageIconColor: '#a3a3a3',
          pageTextStyle: { color: '#767676' },
          textStyle: {
            color: '#a3a3a3',
            fontFamily: 'Plus Jakarta Sans, system-ui, sans-serif',
            fontSize: 11,
            padding: [0, 0, 0, 4],
          },
        }
      : { show: false },
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
        type: isBar ? 'shadow' : 'line',
        lineStyle: { color: '#55555b', width: 1, type: 'dashed' },
        shadowStyle: { color: 'rgba(255, 255, 255, 0.04)' },
      },
      formatter: (params) => {
        if (!Array.isArray(params) || !params.length) return '';
        const rawX = isBar ? params[0].axisValue : params[0].value?.[0] || params[0].axisValueLabel;
        const dateStr = formatTooltipDate(rawX);
        const lines = [
          `<div style="color:#a3a3a3;margin-bottom:6px;font-family:Plus Jakarta Sans,sans-serif;font-weight:600;font-size:11px;">${dateStr}</div>`,
        ];
        for (const p of params) {
          const v = Array.isArray(p.value)
            ? p.value[1]
            : p.value && typeof p.value === 'object'
              ? p.value.value
              : p.value;
          if (v === null || v === undefined) continue;
          const dotColor = isBar ? (Number(v) >= 0 ? positiveColor : negativeColor) : p.color;
          lines.push(
            `<div style="display:flex;justify-content:space-between;align-items:center;gap:16px;line-height:1.55;">` +
              `<span style="color:#a3a3a3;font-family:Plus Jakarta Sans,sans-serif;"><span style="display:inline-block;width:7px;height:7px;border-radius:999px;background:${dotColor};margin-right:7px;"></span>${p.seriesName}</span>` +
              `<strong style="color:#f8f8f8;">${formatVal(v)}</strong>` +
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
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: {
            color: '#767676',
            fontFamily: 'JetBrains Mono, ui-monospace, monospace',
            fontSize: isCompact ? 9 : 10,
            margin: 10,
            hideOverlap: true,
            formatter: (val) => formatAxisDate(val),
          },
        }
      : {
          type: 'time',
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
            formatter: (val) => formatAxisDate(val),
          },
        },
    yAxis: {
      type: 'value',
      scale: !isBar,
      boundaryGap: ['10%', '14%'],
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: {
        color: '#767676',
        fontFamily: 'JetBrains Mono, ui-monospace, monospace',
        fontSize: isCompact ? 9 : 10,
        formatter: (val) => formatAxisVal(val),
      },
    },
    series: builtSeries,
  };
</script>

<div class="terminal-line-wrap">
  {#if panelTitle}
    <div class="line-head-row">
      <h2 class="terminal-panel-title" style="margin: 0;">
        {#if panelIndex}
          <span class="panel-index">{panelIndex}</span>
        {/if}
        <span>{panelTitle}</span>
      </h2>
      {#if primaryLastVal !== null}
        <span class="line-live-readout" style={`color: ${readoutColor};`}>
          {formatVal(primaryLastVal)}
        </span>
      {/if}
    </div>
    {#if panelSubtitle}
      <p class="terminal-panel-sub">{panelSubtitle}</p>
    {/if}
  {/if}
  <div class="line-chart-box" bind:clientWidth={chartWidth}>
    {#if chartWidth > 0}
      <ECharts {data} {config} height={resolvedHeight} width="100%" />
    {/if}
  </div>
</div>

<style>
  .terminal-line-wrap {
    inline-size: 100%;
    max-inline-size: 100%;
    min-inline-size: 0;
  }

  .line-chart-box {
    inline-size: 100%;
    max-inline-size: 100%;
    overflow: hidden;
  }

  .line-head-row {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 4px 12px;
    margin-block-end: 4px;
  }

  .line-live-readout {
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 14px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  @media (max-width: 640px) {
    .line-live-readout {
      font-size: 13px;
    }
  }
</style>
