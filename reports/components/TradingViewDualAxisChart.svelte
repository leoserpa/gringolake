<script>
  import { onMount, onDestroy } from 'svelte';
  import TradingViewRangeSlider from './TradingViewRangeSlider.svelte';

  export let data = [];
  export let x = 'trading_date';
  export let flowCol = 'pf_cum_bi_brl';
  export let flowName = 'Fluxo Acumulado';
  export let maCol = null;
  export let maObsCol = null;
  export let maName = 'MM 21d';
  export let ibovCol = 'ibov_close';
  export let ibovName = 'IBOV (pts)';
  export let height = 300;
  export let flowColor = '#f2b94b';
  export let ibovColor = '#9a9aa0';
  export let maColor = '#8a8a93';
  export let focal = false;
  export let defaultZoomPoints = 0;
  export let panelIndex = '';
  export let panelTitle = '';
  export let panelSubtitle = '';

  let containerEl;
  let chart = null;
  let flowSeries = null;
  let maSeries = null;
  let ibovSeries = null;
  let resizeObserver = null;
  let mounted = false;

  let showMa = true;
  let showIbov = true;
  let hovered = null;
  let visibleFrom = 0;
  let visibleTo = 0;
  let syncingFromSlider = false;

  function toIsoDate(val) {
    if (!val) return '';
    if (val instanceof Date) return val.toISOString().slice(0, 10);
    return String(val).slice(0, 10);
  }

  function formatBrDate(iso) {
    if (!iso || iso.length < 10) return iso || '—';
    return `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}`;
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
    const normalized = Math.abs(num) < 0.005 ? 0 : num;
    const sign = normalized < 0 ? '-' : normalized > 0 ? '+' : '';
    const abs = Math.abs(normalized).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    return `${sign}${abs} bi`;
  }

  function formatPts(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '—';
    return `${Math.round(Number(v)).toLocaleString('pt-BR')} pts`;
  }

  function formatPtsAxis(v) {
    const num = Number(v);
    if (Number.isNaN(num)) return '';
    return Math.round(num).toLocaleString('pt-BR');
  }

  $: rawRows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  $: parsed = (() => {
    const seen = new Set();
    const out = [];
    for (const r of rawRows) {
      const time = toIsoDate(r[x]);
      if (!time || seen.has(time)) continue;
      const flow = r[flowCol] === null || r[flowCol] === undefined ? null : Number(r[flowCol]);
      const ibov = r[ibovCol] === null || r[ibovCol] === undefined ? null : Number(r[ibovCol]);
      const ma = maCol && r[maCol] !== null && r[maCol] !== undefined ? Number(r[maCol]) : null;
      const maObs = maObsCol && r[maObsCol] !== null && r[maObsCol] !== undefined ? Number(r[maObsCol]) : null;
      if (flow === null && ibov === null) continue;
      seen.add(time);
      out.push({
        time,
        flow: Number.isNaN(flow) ? null : flow,
        ibov: Number.isNaN(ibov) ? null : ibov,
        ma: ma !== null && !Number.isNaN(ma) ? ma : null,
        maObs: maObs !== null && !Number.isNaN(maObs) ? maObs : null,
      });
    }
    out.sort((a, b) => (a.time < b.time ? -1 : a.time > b.time ? 1 : 0));
    return out;
  })();

  $: byDate = new Map(parsed.map((p) => [p.time, p]));
  $: hasValidMa = Boolean(maCol && parsed.some((p) => p.ma !== null));
  $: latest = parsed.length ? parsed[parsed.length - 1] : null;
  $: latestMaObs = (() => {
    if (!maObsCol || !parsed.length) return null;
    for (let i = parsed.length - 1; i >= 0; i--) {
      if (parsed[i].maObs !== null) return parsed[i].maObs;
    }
    return null;
  })();
  $: activePoint = hovered || latest;
  $: sliderStartLabel = parsed.length ? formatBrDate(parsed[Math.max(0, Math.min(Math.round(visibleFrom), parsed.length - 1))]?.time) : '';
  $: sliderEndLabel = parsed.length ? formatBrDate(parsed[Math.max(0, Math.min(Math.round(visibleTo), parsed.length - 1))]?.time) : '';

  function applyInitialRange() {
    if (!chart) return;
    const ts = chart.timeScale();
    if (defaultZoomPoints > 0 && parsed.length > defaultZoomPoints) {
      const from = parsed.length - defaultZoomPoints;
      const to = parsed.length - 1;
      ts.setVisibleLogicalRange({ from, to: to + 2 });
      visibleFrom = from;
      visibleTo = to;
    } else {
      ts.fitContent();
      visibleFrom = 0;
      visibleTo = Math.max(0, parsed.length - 1);
    }
  }

  function syncSeriesData() {
    if (!chart || !flowSeries) return;
    flowSeries.setData(parsed.filter((p) => p.flow !== null).map((p) => ({ time: p.time, value: p.flow })));
    maSeries.setData(parsed.filter((p) => p.ma !== null).map((p) => ({ time: p.time, value: p.ma })));
    ibovSeries.setData(parsed.filter((p) => p.ibov !== null).map((p) => ({ time: p.time, value: p.ibov })));
    applyInitialRange();
  }

  function syncVisibility() {
    if (!chart) return;
    maSeries?.applyOptions({ visible: hasValidMa && showMa });
    ibovSeries?.applyOptions({ visible: showIbov });
    chart.priceScale('right').applyOptions({ visible: showIbov });
  }

  function zoomBy(factor) {
    if (!chart) return;
    const ts = chart.timeScale();
    const range = ts.getVisibleLogicalRange();
    if (!range) return;
    const span = range.to - range.from;
    const newSpan = Math.max(5, span * factor);
    const center = (range.from + range.to) / 2;
    ts.setVisibleLogicalRange({
      from: center - newSpan / 2,
      to: center + newSpan / 2,
    });
  }

  function handleSliderChange(e) {
    if (!chart) return;
    syncingFromSlider = true;
    visibleFrom = e.detail.from;
    visibleTo = e.detail.to;
    chart.timeScale().setVisibleLogicalRange({ from: e.detail.from, to: e.detail.to });
    syncingFromSlider = false;
  }

  function resetFit() {
    chart?.timeScale().fitContent();
    visibleFrom = 0;
    visibleTo = Math.max(0, parsed.length - 1);
  }

  $: if (mounted && chart && parsed) {
    syncSeriesData();
  }

  $: if (mounted && chart) {
    showMa;
    showIbov;
    hasValidMa;
    syncVisibility();
  }

  onMount(async () => {
    mounted = true;
    const {
      createChart,
      LineSeries,
      ColorType,
      CrosshairMode,
      LineStyle,
    } = await import('lightweight-charts');

    if (!containerEl || !mounted) return;

    const initialWidth = Math.max(260, containerEl.clientWidth || 520);
    chart = createChart(containerEl, {
      width: initialWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: '#2b2b2b' },
        textColor: '#8a8a93',
        fontFamily: "'JetBrains Mono', ui-monospace, monospace",
        fontSize: 10.5,
        attributionLogo: false,
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { visible: false },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: '#6b6b73',
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: '#222222',
        },
        horzLine: {
          color: '#6b6b73',
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: '#222222',
        },
      },
      leftPriceScale: {
        visible: true,
        borderColor: '#3a3a3f',
        scaleMargins: { top: 0.14, bottom: 0.12 },
      },
      rightPriceScale: {
        visible: true,
        borderColor: '#3a3a3f',
        scaleMargins: { top: 0.14, bottom: 0.12 },
      },
      timeScale: {
        borderColor: '#3a3a3f',
        timeVisible: false,
        rightOffset: 3,
        minBarSpacing: 2,
      },
      localization: {
        locale: 'pt-BR',
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: false,
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true,
      },
    });

    flowSeries = chart.addSeries(LineSeries, {
      priceScaleId: 'left',
      color: flowColor,
      lineWidth: 2.2,
      priceLineVisible: true,
      priceLineColor: 'rgba(242, 185, 75, 0.45)',
      priceLineStyle: LineStyle.Dashed,
      lastValueVisible: true,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 4.5,
      crosshairMarkerBorderColor: '#2b2b2b',
      crosshairMarkerBackgroundColor: flowColor,
      priceFormat: {
        type: 'custom',
        minMove: 0.01,
        formatter: (v) => formatBiAxis(v),
      },
    });

    maSeries = chart.addSeries(LineSeries, {
      priceScaleId: 'left',
      color: maColor,
      lineWidth: 1.25,
      lineStyle: LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
      priceFormat: {
        type: 'custom',
        minMove: 0.01,
        formatter: (v) => formatBiAxis(v),
      },
    });

    ibovSeries = chart.addSeries(LineSeries, {
      priceScaleId: 'right',
      color: ibovColor,
      lineWidth: 1.6,
      priceLineVisible: false,
      lastValueVisible: true,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 3.5,
      crosshairMarkerBorderColor: '#2b2b2b',
      crosshairMarkerBackgroundColor: ibovColor,
      priceFormat: {
        type: 'custom',
        minMove: 1,
        formatter: (v) => formatPtsAxis(v),
      },
    });

    chart.subscribeCrosshairMove((param) => {
      if (!param || !param.time) {
        hovered = null;
        return;
      }
      const iso = typeof param.time === 'string' ? param.time : '';
      hovered = byDate.get(iso) || null;
    });

    chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (syncingFromSlider || !range || !parsed.length) return;
      visibleFrom = Math.max(0, Math.min(range.from, parsed.length - 1));
      visibleTo = Math.max(visibleFrom, Math.min(range.to, parsed.length - 1));
    });

    syncSeriesData();
    syncVisibility();

    resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const w = Math.floor(entry.contentRect.width);
        if (w > 0 && chart) {
          chart.applyOptions({ width: w });
        }
      }
    });
    resizeObserver.observe(containerEl);
  });

  onDestroy(() => {
    mounted = false;
    resizeObserver?.disconnect();
    resizeObserver = null;
    chart?.remove();
    chart = null;
  });
</script>

<div class="tvd-wrap">
  {#if panelTitle}
    <div class="tvd-head-row">
      <h2 class="terminal-panel-title" style="margin: 0;">
        {#if panelIndex}
          <span class="panel-index">{panelIndex}</span>
        {/if}
        <span>{panelTitle}</span>
      </h2>
    </div>
    {#if panelSubtitle || (maCol && !hasValidMa && latestMaObs !== null)}
      <div class="tvd-sub-row">
        {#if panelSubtitle}
          <p class="terminal-panel-sub" style="margin: 0;">{panelSubtitle}</p>
        {/if}
        {#if maCol && !hasValidMa && latestMaObs !== null}
          <span class="ma-warmup-pill">MM21 em formação · {latestMaObs}/21 pregões</span>
        {/if}
      </div>
    {/if}
  {/if}

  <div class="tvd-toolbar">
    {#if activePoint}
      <div class="tvd-hud" aria-live="polite">
        <span class="hud-date">{formatBrDate(activePoint.time)}</span>
        <span class="hud-item">
          <span class="hud-dot" style={`background: ${flowColor};`}></span>
          <span class="hud-lbl">{flowName}</span>
          <strong class="hud-val is-amber">{formatBi(activePoint.flow)}</strong>
        </span>
        {#if showIbov && activePoint.ibov !== null}
          <span class="hud-item">
            <span class="hud-dot" style={`background: ${ibovColor};`}></span>
            <span class="hud-lbl">IBOV</span>
            <span class="hud-val">{formatPts(activePoint.ibov)}</span>
          </span>
        {/if}
        {#if hasValidMa && showMa && activePoint.ma !== null}
          <span class="hud-item">
            <span class="hud-lbl">{maName}</span>
            <span class="hud-val">{formatBi(activePoint.ma)}</span>
          </span>
        {/if}
      </div>
    {/if}

    <div class="tvd-controls" role="group" aria-label="Controles do gráfico">
      <button type="button" class="tvd-pill" class:is-on={showIbov} on:click={() => (showIbov = !showIbov)}>
        <span class="dot" style={`background: ${ibovColor};`}></span>
        <span>IBOV</span>
      </button>
      {#if hasValidMa}
        <button type="button" class="tvd-pill" class:is-on={showMa} on:click={() => (showMa = !showMa)}>
          <span class="dot" style={`background: ${maColor};`}></span>
          <span>{maName}</span>
        </button>
      {/if}
      <div class="tvd-zoom-group" role="group" aria-label="Controles de zoom">
        <button type="button" class="tvd-zoom-btn" on:click={() => zoomBy(0.72)} title="Aproximar zoom" aria-label="Aproximar zoom">+</button>
        <button type="button" class="tvd-zoom-btn" on:click={() => zoomBy(1.38)} title="Afastar zoom" aria-label="Afastar zoom">−</button>
        <button type="button" class="tvd-zoom-btn tvd-zoom-fit" on:click={resetFit} title="Resetar zoom e enquadramento">Ajustar</button>
      </div>
    </div>
  </div>

  <div class="tvd-canvas" bind:this={containerEl} style={`height: ${height}px;`}></div>

  <TradingViewRangeSlider
    total={parsed.length}
    startIdx={visibleFrom}
    endIdx={visibleTo}
    startLabel={sliderStartLabel}
    endLabel={sliderEndLabel}
    on:change={handleSliderChange}
  />
</div>

<style>
  .tvd-wrap {
    inline-size: 100%;
    max-inline-size: 100%;
    min-inline-size: 0;
  }

  .tvd-head-row {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 4px 12px;
    margin-block-end: 4px;
  }

  .tvd-sub-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 6px 12px;
    margin-block-end: 10px;
  }

  .ma-warmup-pill {
    display: inline-flex;
    align-items: center;
    padding: 3px 10px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid #3a3a40;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 10.5px;
    color: #9a9aa0;
    white-space: nowrap;
  }

  .tvd-toolbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 8px 12px;
    margin-block-end: 10px;
  }

  .tvd-hud {
    display: inline-flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 5px 12px;
    padding: 6px 10px;
    border-radius: 10px;
    background: #232326;
    border: 1px solid #34343a;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 11px;
    font-variant-numeric: tabular-nums;
  }

  .hud-date {
    color: #a3a3ab;
    font-weight: 600;
  }

  .hud-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }

  .hud-dot {
    inline-size: 6px;
    block-size: 6px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .hud-lbl {
    color: #8a8a93;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 10.5px;
    font-weight: 500;
  }

  .hud-val {
    color: #e5e5e5;
    font-weight: 500;
  }

  .hud-val.is-amber {
    color: #f2b94b;
    font-weight: 600;
  }

  .tvd-controls {
    display: inline-flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
  }

  .tvd-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    height: 26px;
    padding: 0 10px;
    border-radius: 999px;
    border: 1px solid #3a3a40;
    background: #232326;
    color: #76767e;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 11px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 140ms ease, border-color 140ms ease, color 140ms ease;
  }

  .tvd-pill.is-on {
    background: #323238;
    border-color: #4f4f58;
    color: #f0f0f3;
  }

  .tvd-pill:hover {
    border-color: #62626c;
    color: #f8f8f8;
  }

  .dot {
    inline-size: 6px;
    block-size: 6px;
    border-radius: 50%;
    opacity: 0.45;
  }

  .tvd-pill.is-on .dot {
    opacity: 1;
  }

  .tvd-zoom-group {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    border: 1px solid #3a3a40;
    background: #232326;
    overflow: hidden;
  }

  .tvd-zoom-btn {
    height: 24px;
    min-inline-size: 26px;
    padding: 0 7px;
    border: 0;
    border-inline-end: 1px solid #34343a;
    background: transparent;
    color: #d4d4d8;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 140ms ease, color 140ms ease;
  }

  .tvd-zoom-btn:last-child {
    border-inline-end: 0;
  }

  .tvd-zoom-btn:hover {
    background: #323238;
    color: #f8f8f8;
  }

  .tvd-zoom-fit {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 10.5px;
    font-weight: 500;
    padding: 0 9px;
  }

  .tvd-canvas {
    inline-size: 100%;
    max-inline-size: 100%;
    border-radius: 14px;
    overflow: hidden;
  }

  @media (max-width: 640px) {
    .tvd-hud {
      font-size: 10px;
      gap: 4px 8px;
      padding: 5px 8px;
    }
  }
</style>
