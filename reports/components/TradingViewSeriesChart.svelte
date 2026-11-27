<script>
  import { onMount, onDestroy, tick } from 'svelte';
  import TradingViewRangeSlider from './TradingViewRangeSlider.svelte';
  import { formatDateBR, formatFlowBrl, toArray, toIsoDate } from './formatters.js';

  export let data = [];
  export let panelTitle = '';
  export let panelSubtitle = '';
  export let x = 'trading_date';
  export let y = '';
  export let names = [];
  export let colors = [];
  export let prefix = '';
  export let suffix = '';
  export let decimals = 1;
  export let signed = false;
  export let chartType = 'line';
  export let axisCompact = false;
  export let autoScaleUnit = false;
  export let highlightAboveAvg = false;
  export let zeroLine = true;
  export let defaultZoomPoints = 60;
  export let height = 240;

  const DEFAULT_LINE_PALETTE = ['#f2b94b', '#e5e5e5', '#7c7c86'];
  const AMBER_HEX = '#f2b94b';
  const GRAY_HEX = '#7c7c86';
  const BAR_POS_RGBA = 'rgba(242, 185, 75, 0.86)';
  const BAR_NEG_RGBA = 'rgba(124, 124, 134, 0.62)';
  const BAR_SPIKE_RGBA = 'rgba(242, 185, 75, 0.90)';
  const BAR_BASE_RGBA = 'rgba(110, 110, 120, 0.62)';

  let chartContainer;
  let lcModule = null;
  let chart = null;
  let resizeObserver = null;
  let seriesApis = [];
  let priceLineRefs = [];
  let lastChartModeKey = '';
  let isApplyingRange = false;

  let visibleMap = {};
  let hoveredTime = null;
  let visibleStartIdx = 0;
  let visibleEndIdx = 0;

  function formatValue(val, useCompactAxis = false) {
    const num = Number(val);
    if (!Number.isFinite(num)) return '—';
    const trimmedSuffix = (suffix || '').trim();
    const canAutoUnit = autoScaleUnit && (trimmedSuffix === 'mi' || trimmedSuffix === 'bi');

    if (canAutoUnit) {
      return formatFlowBrl(num, {
        inputUnit: trimmedSuffix,
        signed,
        prefix: prefix || '',
        compactAxis: useCompactAxis,
      });
    }

    const d = Number.isFinite(Number(decimals)) ? Number(decimals) : 1;
    const epsilon = 0.5 * Math.pow(10, -Math.max(0, d));
    const cleanNum = Math.abs(num) < epsilon ? 0 : num;

    if (cleanNum === 0 && useCompactAxis && axisCompact) {
      return `${prefix || ''}0${trimmedSuffix === '%' ? '%' : ''}`;
    }

    const useCompactFormat = useCompactAxis && axisCompact;
    const absFormatted = new Intl.NumberFormat('pt-BR', {
      minimumFractionDigits: useCompactFormat ? 0 : d,
      maximumFractionDigits: d
    }).format(Math.abs(cleanNum));

    let signChar = '';
    if (cleanNum < 0) signChar = '-';
    else if (signed && cleanNum > 0) signChar = '+';

    return `${signChar}${prefix || ''}${absFormatted}${suffix || ''}`;
  }

  $: numericHeight = (() => {
    const parsed = typeof height === 'number' ? height : parseInt(String(height || '240'), 10);
    return Number.isFinite(parsed) && parsed >= 140 ? parsed : 240;
  })();

  $: yFields = Array.isArray(y) ? y.filter(Boolean) : (y ? [y] : []);

  $: seriesMeta = yFields.map((field, idx) => {
    const labelList = Array.isArray(names) ? names : (names ? [names] : []);
    const colorList = Array.isArray(colors) ? colors : (colors ? [colors] : []);
    return {
      field,
      name: labelList[idx] || field,
      color: colorList[idx] || DEFAULT_LINE_PALETTE[idx % DEFAULT_LINE_PALETTE.length]
    };
  });

  $: {
    const nextMap = { ...visibleMap };
    let changed = false;
    seriesMeta.forEach((_, idx) => {
      if (typeof nextMap[idx] !== 'boolean') {
        nextMap[idx] = true;
        changed = true;
      }
    });
    if (changed) visibleMap = nextMap;
  }

  $: alignedData = (() => {
    const raw = toArray(data);
    const byDate = new Map();
    for (const row of raw) {
      if (!row) continue;
      const iso = toIsoDate(row[x]);
      if (!iso) continue;
      const entry = { time: iso, values: {} };
      let hasAnyFinite = false;
      for (const s of seriesMeta) {
        const rawVal = row[s.field];
        if (rawVal === null || rawVal === undefined || rawVal === '') {
          entry.values[s.field] = null;
          continue;
        }
        const num = Number(rawVal);
        if (Number.isFinite(num)) {
          entry.values[s.field] = num;
          hasAnyFinite = true;
        } else {
          entry.values[s.field] = null;
        }
      }
      if (hasAnyFinite) {
        byDate.set(iso, entry);
      }
    }
    return Array.from(byDate.values()).sort((a, b) =>
      a.time < b.time ? -1 : a.time > b.time ? 1 : 0
    );
  })();

  $: barStats = (() => {
    if (chartType !== 'bar' || seriesMeta.length === 0 || alignedData.length === 0) {
      return { avg: null, spikeThreshold: null };
    }
    const field = seriesMeta[0].field;
    const nums = alignedData
      .map((r) => r.values[field])
      .filter((v) => typeof v === 'number' && Number.isFinite(v));
    if (nums.length === 0) return { avg: null, spikeThreshold: null };
    const avg = nums.reduce((acc, v) => acc + v, 0) / nums.length;
    return {
      avg,
      spikeThreshold: avg > 0 ? avg * 1.4 : null
    };
  })();

  $: rowByTime = new Map(alignedData.map((r) => [r.time, r]));

  $: activeRow = (() => {
    if (alignedData.length === 0) return null;
    if (hoveredTime && rowByTime.has(hoveredTime)) {
      return rowByTime.get(hoveredTime);
    }
    return alignedData[alignedData.length - 1];
  })();

  $: hasData = alignedData.length > 0 && seriesMeta.length > 0;
  $: startLabel = alignedData[visibleStartIdx] ? formatDateBR(alignedData[visibleStartIdx].time) : '';
  $: endLabel = alignedData[visibleEndIdx] ? formatDateBR(alignedData[visibleEndIdx].time) : '';

  function clearPriceLines() {
    if (!seriesApis.length || !priceLineRefs.length) {
      priceLineRefs = [];
      return;
    }
    for (const ref of priceLineRefs) {
      try {
        ref.api.removePriceLine(ref.line);
      } catch {
        // Ignore if series was replaced
      }
    }
    priceLineRefs = [];
  }

  function clearAllSeries() {
    clearPriceLines();
    if (!chart || !seriesApis.length) {
      seriesApis = [];
      return;
    }
    for (const api of seriesApis) {
      try {
        chart.removeSeries(api);
      } catch {
        // Ignore stale series
      }
    }
    seriesApis = [];
  }

  function applyInitialRange() {
    if (!chart || alignedData.length === 0) {
      visibleStartIdx = 0;
      visibleEndIdx = 0;
      return;
    }
    const total = alignedData.length;
    const zoomCount = Number(defaultZoomPoints) || 0;
    isApplyingRange = true;
    try {
      if (zoomCount > 0 && total > zoomCount) {
        const from = total - zoomCount;
        const to = total - 1;
        visibleStartIdx = from;
        visibleEndIdx = to;
        chart.timeScale().setVisibleLogicalRange({ from, to });
      } else {
        visibleStartIdx = 0;
        visibleEndIdx = total - 1;
        chart.timeScale().fitContent();
      }
    } finally {
      isApplyingRange = false;
    }
  }

  function syncChartData() {
    if (!chart || !lcModule) return;
    const lc = lcModule;

    chart.applyOptions({
      height: numericHeight,
      localization: {
        locale: 'pt-BR',
        dateFormat: 'dd/MM/yyyy',
        priceFormatter: (price) => formatValue(price, true)
      }
    });

    const modeKey = `${chartType}|${autoScaleUnit}|${seriesMeta.map((s) => `${s.field}:${s.color}`).join(',')}`;
    const needsRebuild = modeKey !== lastChartModeKey || seriesApis.length !== seriesMeta.length;

    if (needsRebuild) {
      clearAllSeries();
      lastChartModeKey = modeKey;

      seriesApis = seriesMeta.map((meta, idx) => {
        if (chartType === 'bar') {
          return chart.addSeries(lc.HistogramSeries, {
            base: 0,
            color: AMBER_HEX,
            priceLineVisible: false,
            lastValueVisible: true,
            visible: visibleMap[idx] !== false,
            priceFormat: {
              type: 'custom',
              formatter: (p) => formatValue(p, true)
            }
          });
        }

        return chart.addSeries(lc.LineSeries, {
          color: meta.color,
          lineWidth: idx === 0 ? 2 : 1.75,
          priceLineVisible: false,
          lastValueVisible: true,
          crosshairMarkerVisible: true,
          crosshairMarkerRadius: 4,
          visible: visibleMap[idx] !== false,
          priceFormat: {
            type: 'custom',
            formatter: (p) => formatValue(p, true)
          }
        });
      });
    } else {
      clearPriceLines();
    }

    seriesMeta.forEach((meta, idx) => {
      const api = seriesApis[idx];
      if (!api) return;

      if (chartType === 'bar') {
        const points = [];
        for (const row of alignedData) {
          const val = row.values[meta.field];
          if (val === null || !Number.isFinite(val)) continue;
          let barColor;
          if (highlightAboveAvg) {
            const isSpike = barStats.spikeThreshold !== null && val >= barStats.spikeThreshold;
            barColor = isSpike ? BAR_SPIKE_RGBA : BAR_BASE_RGBA;
          } else {
            barColor = val >= 0 ? BAR_POS_RGBA : BAR_NEG_RGBA;
          }
          points.push({ time: row.time, value: val, color: barColor });
        }
        api.setData(points);
        const lastPt = points[points.length - 1];
        if (lastPt) {
          api.applyOptions({
            color: highlightAboveAvg
              ? (barStats.spikeThreshold !== null && lastPt.value >= barStats.spikeThreshold
                  ? AMBER_HEX
                  : GRAY_HEX)
              : (lastPt.value >= 0 ? AMBER_HEX : GRAY_HEX)
          });
        }
      } else {
        const points = [];
        for (const row of alignedData) {
          const val = row.values[meta.field];
          if (val === null || !Number.isFinite(val)) continue;
          points.push({ time: row.time, value: val });
        }
        api.setData(points);
      }

      api.applyOptions({ visible: visibleMap[idx] !== false });
    });

    const primaryApi = seriesApis[0];
    if (primaryApi && alignedData.length > 0) {
      if (zeroLine) {
        const line = primaryApi.createPriceLine({
          price: 0,
          color: 'rgba(255, 255, 255, 0.16)',
          lineWidth: 1,
          lineStyle: lc.LineStyle.Solid,
          axisLabelVisible: false,
          title: ''
        });
        priceLineRefs.push({ api: primaryApi, line });
      }
      if (chartType === 'bar' && highlightAboveAvg && barStats.avg !== null) {
        const avgLine = primaryApi.createPriceLine({
          price: barStats.avg,
          color: 'rgba(242, 185, 75, 0.45)',
          lineWidth: 1,
          lineStyle: lc.LineStyle.Dashed,
          axisLabelVisible: true,
          title: 'Média'
        });
        priceLineRefs.push({ api: primaryApi, line: avgLine });
      }
    }

    hoveredTime = null;
    applyInitialRange();
  }

  function applyLogicalRange(from, to) {
    if (!chart || alignedData.length === 0) return;
    const maxIdx = alignedData.length - 1;
    const minSpan = Math.min(5, alignedData.length);
    let f = Math.max(0, Math.min(maxIdx, Math.round(from)));
    let t = Math.max(f, Math.min(maxIdx, Math.round(to)));
    if (t - f + 1 < minSpan && alignedData.length >= minSpan) {
      if (f + minSpan - 1 <= maxIdx) t = f + minSpan - 1;
      else f = Math.max(0, t - minSpan + 1);
    }
    isApplyingRange = true;
    try {
      visibleStartIdx = f;
      visibleEndIdx = t;
      chart.timeScale().setVisibleLogicalRange({ from: f, to: t });
    } finally {
      isApplyingRange = false;
    }
  }

  function handleSliderChange(e) {
    if (!e?.detail) return;
    applyLogicalRange(e.detail.from, e.detail.to);
  }

  function zoomBy(factor) {
    if (!chart || alignedData.length === 0) return;
    const maxIdx = alignedData.length - 1;
    const curSpan = Math.max(1, visibleEndIdx - visibleStartIdx + 1);
    const minSpan = Math.min(5, alignedData.length);
    const nextSpan = Math.max(minSpan, Math.min(alignedData.length, Math.round(curSpan * factor)));
    const pinnedRight = visibleEndIdx >= maxIdx - 1;
    if (pinnedRight) {
      applyLogicalRange(maxIdx - nextSpan + 1, maxIdx);
    } else {
      const center = (visibleStartIdx + visibleEndIdx) / 2;
      const half = nextSpan / 2;
      let f = Math.round(center - half);
      let t = f + nextSpan - 1;
      if (f < 0) {
        f = 0;
        t = Math.min(maxIdx, nextSpan - 1);
      } else if (t > maxIdx) {
        t = maxIdx;
        f = Math.max(0, maxIdx - nextSpan + 1);
      }
      applyLogicalRange(f, t);
    }
  }

  function resetZoom() {
    if (!chart || alignedData.length === 0) return;
    isApplyingRange = true;
    try {
      visibleStartIdx = 0;
      visibleEndIdx = alignedData.length - 1;
      chart.timeScale().fitContent();
    } finally {
      isApplyingRange = false;
    }
  }

  function toggleSeriesVisibility(idx) {
    const nextVal = !(visibleMap[idx] !== false);
    visibleMap = { ...visibleMap, [idx]: nextVal };
    if (seriesApis[idx]) {
      seriesApis[idx].applyOptions({ visible: nextVal });
    }
  }

  function getPointPillColor(row, meta, idx) {
    if (!row) return meta.color;
    const val = row.values[meta.field];
    if (chartType === 'bar') {
      if (highlightAboveAvg) {
        return barStats.spikeThreshold !== null && val !== null && val >= barStats.spikeThreshold
          ? AMBER_HEX
          : GRAY_HEX;
      }
      return val !== null && val >= 0 ? AMBER_HEX : GRAY_HEX;
    }
    return meta.color;
  }

  onMount(async () => {
    if (!chartContainer) return;
    const lc = await import('lightweight-charts');
    lcModule = lc;
    await tick();
    if (!chartContainer) return;

    const initialWidth = chartContainer.clientWidth || 600;

    chart = lc.createChart(chartContainer, {
      width: initialWidth,
      height: numericHeight,
      layout: {
        attributionLogo: false,
        background: { type: lc.ColorType.Solid, color: 'transparent' },
        textColor: '#8e8e98',
        fontSize: 11,
        fontFamily: 'JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, monospace'
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { visible: false }
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.08)',
        scaleMargins: {
          top: 0.14,
          bottom: 0.12
        }
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.08)',
        timeVisible: false,
        rightOffset: 0.5,
        minBarSpacing: 3,
        fixLeftEdge: true,
        fixRightEdge: true
      },
      crosshair: {
        mode: lc.CrosshairMode.Normal,
        vertLine: {
          color: 'rgba(245, 245, 245, 0.22)',
          width: 1,
          style: lc.LineStyle.Dashed,
          labelBackgroundColor: '#363636'
        },
        horzLine: {
          color: 'rgba(245, 245, 245, 0.22)',
          width: 1,
          style: lc.LineStyle.Dashed,
          labelBackgroundColor: '#363636'
        }
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: false
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true
      },
      localization: {
        locale: 'pt-BR',
        dateFormat: 'dd/MM/yyyy',
        priceFormatter: (price) => formatValue(price, true)
      }
    });

    chart.subscribeCrosshairMove((param) => {
      if (!param || !param.time) {
        hoveredTime = null;
        return;
      }
      hoveredTime = typeof param.time === 'string' ? param.time : null;
    });

    chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (isApplyingRange || !range || alignedData.length === 0) return;
      const maxIdx = alignedData.length - 1;
      const f = Math.max(0, Math.min(maxIdx, Math.round(range.from)));
      const t = Math.max(f, Math.min(maxIdx, Math.round(range.to)));
      visibleStartIdx = f;
      visibleEndIdx = t;
    });

    resizeObserver = new ResizeObserver((entries) => {
      if (!chart || !entries.length) return;
      const w = Math.floor(entries[0].contentRect.width);
      if (w > 0) {
        chart.applyOptions({ width: w });
      }
    });
    resizeObserver.observe(chartContainer);

    syncChartData();
  });

  $: if (chart && lcModule) {
    alignedData;
    chartType;
    highlightAboveAvg;
    zeroLine;
    defaultZoomPoints;
    decimals;
    signed;
    prefix;
    suffix;
    axisCompact;
    autoScaleUnit;
    numericHeight;
    syncChartData();
  }

  onDestroy(() => {
    if (resizeObserver) {
      resizeObserver.disconnect();
      resizeObserver = null;
    }
    if (chart) {
      clearAllSeries();
      chart.remove();
      chart = null;
    }
  });
</script>

<div class="tvs-wrap">
  {#if panelTitle || panelSubtitle}
    <div class="terminal-panel-header">
      <div class="terminal-panel-heading">
        <div class="terminal-panel-title">
          {panelTitle}
        </div>
        {#if panelSubtitle}
          <div class="terminal-panel-sub">{panelSubtitle}</div>
        {/if}
      </div>
    </div>
  {/if}

  {#if hasData}
    <div class="tvs-hud">
      <div class="tvs-readout">
        <span class="tvs-date">{activeRow ? formatDateBR(activeRow.time) : '—'}</span>
        {#each seriesMeta as meta, idx}
          {#if visibleMap[idx] !== false}
            {@const dotColor = getPointPillColor(activeRow, meta, idx)}
            <span class="tvs-item">
              <span class="tvs-dot" style={`background:${dotColor};`}></span>
              <span class="tvs-label">{meta.name}</span>
              <span
                class="tvs-val"
                class:is-amber={dotColor === AMBER_HEX}
              >
                {activeRow && activeRow.values[meta.field] !== null
                  ? formatValue(activeRow.values[meta.field], false)
                  : '—'}
              </span>
            </span>
          {/if}
        {/each}
        {#if chartType === 'bar' && highlightAboveAvg && barStats.avg !== null}
          <span class="tvs-item tvs-avg-badge">
            <span class="tvs-label">Média</span>
            <span class="tvs-val">{formatValue(barStats.avg, false)}</span>
          </span>
        {/if}
      </div>

      <div class="tvs-controls">
        {#if seriesMeta.length > 1}
          <div class="tvs-series-pills">
            {#each seriesMeta as meta, idx}
              {@const active = visibleMap[idx] !== false}
              <button
                type="button"
                class="tvs-pill"
                class:is-off={!active}
                on:click={() => toggleSeriesVisibility(idx)}
                aria-pressed={active}
                title={`Alternar série ${meta.name}`}
              >
                <span class="tvs-dot" style={`background:${meta.color};`}></span>
                <span>{meta.name}</span>
              </button>
            {/each}
          </div>
        {/if}

        <div class="tvs-zoom-group" aria-label="Controles de zoom do gráfico">
          <button
            type="button"
            class="tvs-btn"
            on:click={() => zoomBy(0.65)}
            aria-label="Aproximar zoom"
            title="Aproximar zoom"
          >
            +
          </button>
          <button
            type="button"
            class="tvs-btn"
            on:click={() => zoomBy(1.45)}
            aria-label="Afastar zoom"
            title="Afastar zoom"
          >
            −
          </button>
          <button
            type="button"
            class="tvs-btn tvs-btn-reset"
            on:click={resetZoom}
            title="Ajustar toda a série"
          >
            Ajustar
          </button>
        </div>
      </div>
    </div>

    <div
      class="tvs-canvas"
      bind:this={chartContainer}
      style={`height:${numericHeight}px;`}
    ></div>

    <TradingViewRangeSlider
      total={alignedData.length}
      startIdx={visibleStartIdx}
      endIdx={visibleEndIdx}
      {startLabel}
      {endLabel}
      on:change={handleSliderChange}
    />
  {:else}
    <div class="tvs-empty" style={`height:${numericHeight}px;`}>
      Sem dados disponíveis na janela selecionada.
    </div>
  {/if}
</div>

<style>
  .tvs-wrap {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    min-width: 0;
  }

  .tvs-hud {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 8px 12px;
    margin-bottom: 8px;
  }

  .tvs-readout {
    display: inline-flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px 12px;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(34, 34, 34, 0.72);
    border: 1px solid rgba(255, 255, 255, 0.07);
    font-size: 0.72rem;
    line-height: 1.3;
    font-variant-numeric: tabular-nums;
    min-width: 0;
  }

  .tvs-date {
    color: #9e9ea9;
    font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
    font-size: 0.69rem;
  }

  .tvs-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }

  .tvs-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .tvs-label {
    color: #b8b8c2;
    font-weight: 500;
  }

  .tvs-val {
    color: #f5f5f5;
    font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
    font-weight: 600;
  }

  .tvs-val.is-amber {
    color: #f2b94b;
  }

  .tvs-avg-badge {
    padding-left: 8px;
    border-left: 1px solid rgba(255, 255, 255, 0.1);
  }

  .tvs-controls {
    display: inline-flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    margin-left: auto;
  }

  .tvs-series-pills {
    display: inline-flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 5px;
  }

  .tvs-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 9px;
    border-radius: 999px;
    background: rgba(34, 34, 34, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #e4e4e7;
    font-size: 0.69rem;
    font-weight: 500;
    cursor: pointer;
    transition: border-color 0.15s ease, opacity 0.15s ease, background 0.15s ease;
  }

  .tvs-pill:hover {
    border-color: rgba(242, 185, 75, 0.55);
  }

  .tvs-pill.is-off {
    opacity: 0.42;
    background: transparent;
  }

  .tvs-zoom-group {
    display: inline-flex;
    align-items: center;
    border-radius: 7px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(34, 34, 34, 0.72);
  }

  .tvs-btn {
    padding: 3px 8px;
    background: transparent;
    border: none;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    color: #c8c8d2;
    font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
    font-size: 0.72rem;
    cursor: pointer;
    transition: background 0.14s ease, color 0.14s ease;
  }

  .tvs-btn:last-child {
    border-right: none;
  }

  .tvs-btn:hover {
    background: rgba(255, 255, 255, 0.07);
    color: #f5f5f5;
  }

  .tvs-btn-reset {
    font-family: inherit;
    font-size: 0.69rem;
    padding: 3px 9px;
  }

  .tvs-canvas {
    width: 100%;
    min-width: 0;
    position: relative;
    margin-top: auto;
  }

  .tvs-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    color: #7c7c86;
    font-size: 0.82rem;
    border: 1px dashed rgba(255, 255, 255, 0.08);
    border-radius: 8px;
  }
</style>
