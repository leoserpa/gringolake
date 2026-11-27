<script>
  import { onMount, onDestroy, tick } from 'svelte';
  import TradingViewRangeSlider from './TradingViewRangeSlider.svelte';

  export let data = [];
  export let x = 'trading_date';
  export let flowCol = 'estrang_mi';
  export let returnCol = 'ibov_return_1d_pct';
  export let panelTitle = '';
  export let panelSubtitle = '';
  export let defaultZoomPoints = 60;
  export let height = 235;

  const AMBER_HEX = '#f2b94b';
  const GRAY_HEX = '#7c7c86';
  const SILVER_HEX = '#e5e5e5';
  const BAR_POS_RGBA = 'rgba(242, 185, 75, 0.86)';
  const BAR_NEG_RGBA = 'rgba(124, 124, 134, 0.62)';

  let chartContainer;
  let lcModule = null;
  let chart = null;
  let resizeObserver = null;
  let flowSeries = null;
  let returnSeries = null;
  let zeroLineRef = null;
  let isApplyingRange = false;

  let showFlow = true;
  let showReturn = true;
  let hoveredTime = null;
  let visibleStartIdx = 0;
  let visibleEndIdx = 0;

  function toArray(input) {
    if (!input) return [];
    if (Array.isArray(input)) return input;
    if (typeof input.toArray === 'function') return input.toArray();
    if (typeof input[Symbol.iterator] === 'function') return Array.from(input);
    return [];
  }

  function toIsoDate(val) {
    if (val === null || val === undefined) return null;
    if (typeof val === 'string') {
      const match = val.match(/^(\d{4}-\d{2}-\d{2})/);
      if (match) return match[1];
      const parsed = new Date(val);
      return Number.isNaN(parsed.getTime()) ? null : parsed.toISOString().slice(0, 10);
    }
    if (val instanceof Date) {
      return Number.isNaN(val.getTime()) ? null : val.toISOString().slice(0, 10);
    }
    if (typeof val === 'number' && Number.isFinite(val)) {
      const parsed = new Date(val);
      return Number.isNaN(parsed.getTime()) ? null : parsed.toISOString().slice(0, 10);
    }
    return null;
  }

  function formatDateBR(iso) {
    if (!iso || typeof iso !== 'string') return '';
    const parts = iso.split('-');
    if (parts.length !== 3) return iso;
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
  }

  function formatFlow(val, useCompactAxis = false) {
    const num = Number(val);
    if (!Number.isFinite(num)) return '—';
    if (Math.abs(num) < 0.05) return useCompactAxis ? '0' : 'R$ 0';
    const sign = num < 0 ? '-' : '+';
    const abs = Math.abs(num);
    if (abs >= 999.95) {
      const absBi = abs / 1000;
      const formatted = absBi.toLocaleString(
        'pt-BR',
        useCompactAxis
          ? { minimumFractionDigits: 0, maximumFractionDigits: 2 }
          : { minimumFractionDigits: 2, maximumFractionDigits: 2 }
      );
      return useCompactAxis ? `${sign}${formatted} bi` : `${sign}R$ ${formatted} bi`;
    }
    const formatted = abs.toLocaleString(
      'pt-BR',
      useCompactAxis
        ? { minimumFractionDigits: 0, maximumFractionDigits: abs >= 100 ? 0 : 1 }
        : { minimumFractionDigits: 1, maximumFractionDigits: 1 }
    );
    return useCompactAxis ? `${sign}${formatted} mi` : `${sign}R$ ${formatted} mi`;
  }

  function formatPct(val, useCompactAxis = false) {
    const num = Number(val);
    if (!Number.isFinite(num)) return '—';
    const cleanNum = Math.abs(num) < 0.005 ? 0 : num;
    if (cleanNum === 0 && useCompactAxis) return '0%';
    const sign = cleanNum < 0 ? '-' : cleanNum > 0 ? '+' : '';
    const formatted = Math.abs(cleanNum).toLocaleString(
      'pt-BR',
      useCompactAxis
        ? { minimumFractionDigits: 0, maximumFractionDigits: 2 }
        : { minimumFractionDigits: 2, maximumFractionDigits: 2 }
    );
    return `${sign}${formatted}%`;
  }

  $: numericHeight = (() => {
    const parsed = typeof height === 'number' ? height : parseInt(String(height || '235'), 10);
    return Number.isFinite(parsed) && parsed >= 140 ? parsed : 235;
  })();

  $: alignedData = (() => {
    const raw = toArray(data);
    const byDate = new Map();
    for (const row of raw) {
      if (!row) continue;
      const iso = toIsoDate(row[x]);
      if (!iso) continue;
      const fRaw = row[flowCol];
      const rRaw = row[returnCol];
      const fVal = fRaw === null || fRaw === undefined || fRaw === '' ? null : Number(fRaw);
      const rVal = rRaw === null || rRaw === undefined || rRaw === '' ? null : Number(rRaw);
      const hasFlow = fVal !== null && Number.isFinite(fVal);
      const hasRet = rVal !== null && Number.isFinite(rVal);
      if (!hasFlow && !hasRet) continue;
      byDate.set(iso, {
        time: iso,
        flow: hasFlow ? fVal : null,
        ret: hasRet ? rVal : null
      });
    }
    return Array.from(byDate.values()).sort((a, b) =>
      a.time < b.time ? -1 : a.time > b.time ? 1 : 0
    );
  })();

  $: alignmentStats = (() => {
    let aligned = 0;
    let total = 0;
    for (const r of alignedData) {
      if (r.flow === null || r.ret === null) continue;
      total += 1;
      if ((r.flow >= 0 && r.ret >= 0) || (r.flow < 0 && r.ret < 0)) {
        aligned += 1;
      }
    }
    return {
      aligned,
      total,
      pct: total > 0 ? Math.round((aligned / total) * 100) : 0
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

  $: hasData = alignedData.length > 0;
  $: startLabel = alignedData[visibleStartIdx] ? formatDateBR(alignedData[visibleStartIdx].time) : '';
  $: endLabel = alignedData[visibleEndIdx] ? formatDateBR(alignedData[visibleEndIdx].time) : '';

  function clearZeroLine() {
    if (flowSeries && zeroLineRef) {
      try {
        flowSeries.removePriceLine(zeroLineRef);
      } catch {
        // Ignore stale price line
      }
    }
    zeroLineRef = null;
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
    if (!chart || !lcModule || !flowSeries || !returnSeries) return;
    const lc = lcModule;

    chart.applyOptions({ height: numericHeight });
    clearZeroLine();

    const flowPoints = [];
    const retPoints = [];

    for (const r of alignedData) {
      if (r.flow !== null && Number.isFinite(r.flow)) {
        flowPoints.push({
          time: r.time,
          value: r.flow,
          color: r.flow >= 0 ? BAR_POS_RGBA : BAR_NEG_RGBA
        });
      }
      if (r.ret !== null && Number.isFinite(r.ret)) {
        retPoints.push({
          time: r.time,
          value: r.ret
        });
      }
    }

    flowSeries.setData(flowPoints);
    const lastFlowPt = flowPoints[flowPoints.length - 1];
    if (lastFlowPt) {
      flowSeries.applyOptions({ color: lastFlowPt.value >= 0 ? AMBER_HEX : GRAY_HEX });
    }
    flowSeries.applyOptions({ visible: showFlow });

    returnSeries.setData(retPoints);
    returnSeries.applyOptions({ visible: showReturn });

    if (flowPoints.length > 0) {
      zeroLineRef = flowSeries.createPriceLine({
        price: 0,
        color: 'rgba(255, 255, 255, 0.16)',
        lineWidth: 1,
        lineStyle: lc.LineStyle.Solid,
        axisLabelVisible: false,
        title: ''
      });
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

  function toggleFlow() {
    showFlow = !showFlow;
    if (flowSeries) flowSeries.applyOptions({ visible: showFlow });
  }

  function toggleReturn() {
    showReturn = !showReturn;
    if (returnSeries) returnSeries.applyOptions({ visible: showReturn });
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
      leftPriceScale: {
        visible: true,
        borderColor: 'rgba(255, 255, 255, 0.08)',
        scaleMargins: {
          top: 0.14,
          bottom: 0.12
        }
      },
      rightPriceScale: {
        visible: true,
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
        dateFormat: 'dd/MM/yyyy'
      }
    });

    flowSeries = chart.addSeries(lc.HistogramSeries, {
      priceScaleId: 'left',
      base: 0,
      color: AMBER_HEX,
      priceLineVisible: false,
      lastValueVisible: true,
      priceFormat: {
        type: 'custom',
        formatter: (p) => formatFlow(p, true)
      }
    });

    returnSeries = chart.addSeries(lc.LineSeries, {
      priceScaleId: 'right',
      color: SILVER_HEX,
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 4,
      priceFormat: {
        type: 'custom',
        formatter: (p) => formatPct(p, true)
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

  $: if (chart && lcModule && flowSeries && returnSeries) {
    alignedData;
    defaultZoomPoints;
    numericHeight;
    syncChartData();
  }

  onDestroy(() => {
    clearZeroLine();
    if (resizeObserver) {
      resizeObserver.disconnect();
      resizeObserver = null;
    }
    if (chart) {
      chart.remove();
      chart = null;
    }
  });
</script>

<div class="tvfr-wrap">
  {#if panelTitle || panelSubtitle}
    <div class="terminal-panel-header">
      <div class="terminal-panel-heading">
        <div class="terminal-panel-title">{panelTitle}</div>
        {#if panelSubtitle}
          <div class="terminal-panel-sub">{panelSubtitle}</div>
        {/if}
      </div>
    </div>
  {/if}

  {#if hasData}
    <div class="tvfr-hud">
      <div class="tvfr-readout">
        <span class="tvfr-date">{activeRow ? formatDateBR(activeRow.time) : '—'}</span>
        {#if showFlow}
          <span class="tvfr-item">
            <span
              class="tvfr-dot"
              style={`background:${activeRow && activeRow.flow !== null && activeRow.flow >= 0 ? AMBER_HEX : GRAY_HEX};`}
            ></span>
            <span class="tvfr-label">Estrangeiro</span>
            <span
              class="tvfr-val"
              class:is-amber={activeRow && activeRow.flow !== null && activeRow.flow >= 0}
            >
              {activeRow && activeRow.flow !== null ? formatFlow(activeRow.flow, false) : '—'}
            </span>
          </span>
        {/if}
        {#if showReturn}
          <span class="tvfr-item">
            <span class="tvfr-dot" style={`background:${SILVER_HEX};`}></span>
            <span class="tvfr-label">IBOV</span>
            <span class="tvfr-val">
              {activeRow && activeRow.ret !== null ? formatPct(activeRow.ret, false) : '—'}
            </span>
          </span>
        {/if}
        {#if alignmentStats.total > 0}
          <span class="tvfr-item tvfr-align-badge">
            <span class="tvfr-label">Alinhados</span>
            <span class="tvfr-val is-amber">{alignmentStats.pct}%</span>
            <span class="tvfr-date">· {alignmentStats.aligned}/{alignmentStats.total}</span>
          </span>
        {/if}
      </div>

      <div class="tvfr-controls">
        <div class="tvfr-pills">
          <button
            type="button"
            class="tvfr-pill"
            class:is-off={!showFlow}
            aria-pressed={showFlow}
            on:click={toggleFlow}
          >
            <span class="tvfr-dot" style={`background:${AMBER_HEX};`}></span>
            <span>Estrangeiro</span>
          </button>
          <button
            type="button"
            class="tvfr-pill"
            class:is-off={!showReturn}
            aria-pressed={showReturn}
            on:click={toggleReturn}
          >
            <span class="tvfr-dot" style={`background:${SILVER_HEX};`}></span>
            <span>IBOV %</span>
          </button>
        </div>

        <div class="tvfr-zoom-group" aria-label="Controles de zoom do gráfico">
          <button type="button" class="tvfr-btn" on:click={() => zoomBy(0.65)} aria-label="Aproximar zoom">+</button>
          <button type="button" class="tvfr-btn" on:click={() => zoomBy(1.45)} aria-label="Afastar zoom">−</button>
          <button type="button" class="tvfr-btn tvfr-btn-reset" on:click={resetZoom}>Ajustar</button>
        </div>
      </div>
    </div>

    <div
      class="tvfr-canvas"
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
    <div class="tvfr-empty" style={`height:${numericHeight}px;`}>
      Sem dados disponíveis na janela selecionada.
    </div>
  {/if}
</div>

<style>
  .tvfr-wrap {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    min-width: 0;
  }

  .tvfr-hud {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 8px 12px;
    margin-bottom: 8px;
  }

  .tvfr-readout {
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

  .tvfr-date {
    color: #9e9ea9;
    font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
    font-size: 0.69rem;
  }

  .tvfr-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }

  .tvfr-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .tvfr-label {
    color: #b8b8c2;
    font-weight: 500;
  }

  .tvfr-val {
    color: #f5f5f5;
    font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
    font-weight: 600;
  }

  .tvfr-val.is-amber {
    color: #f2b94b;
  }

  .tvfr-align-badge {
    padding-left: 8px;
    border-left: 1px solid rgba(255, 255, 255, 0.1);
  }

  .tvfr-controls {
    display: inline-flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    margin-left: auto;
  }

  .tvfr-pills {
    display: inline-flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 5px;
  }

  .tvfr-pill {
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

  .tvfr-pill:hover {
    border-color: rgba(242, 185, 75, 0.55);
  }

  .tvfr-pill.is-off {
    opacity: 0.42;
    background: transparent;
  }

  .tvfr-zoom-group {
    display: inline-flex;
    align-items: center;
    border-radius: 7px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(34, 34, 34, 0.72);
  }

  .tvfr-btn {
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

  .tvfr-btn:last-child {
    border-right: none;
  }

  .tvfr-btn:hover {
    background: rgba(255, 255, 255, 0.07);
    color: #f5f5f5;
  }

  .tvfr-btn-reset {
    font-family: inherit;
    font-size: 0.69rem;
    padding: 3px 9px;
  }

  .tvfr-canvas {
    width: 100%;
    min-width: 0;
    position: relative;
    margin-top: auto;
  }

  .tvfr-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    color: #7c7c86;
    font-size: 0.82rem;
    border: 1px dashed rgba(255, 255, 255, 0.08);
    border-radius: 8px;
  }
</style>
