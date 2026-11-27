<script>
  import { onMount, onDestroy } from 'svelte';
  import TradingViewRangeSlider from './TradingViewRangeSlider.svelte';

  export let data = [];
  export let panelTitle = 'Qual a trajetória do Ibovespa no horizonte selecionado?';
  export let panelSubtitle = 'Velas (Candlestick) oficiais da B3 · Alternância 1S (Semanal), 1M (Mensal) e 1D + MM21/MM50/MM200';
  export let height = 340;

  let containerEl;
  let chart = null;
  let candleSeries = null;
  let ma21Series = null;
  let ma50Series = null;
  let ma200Series = null;
  let retSeries = null;
  let resizeObserver = null;
  let mounted = false;

  let timeframe = '1S'; // '1D' | '1S' | '1M'
  let showMa21 = true;
  let showMa50 = true;
  let showMa200 = true;
  let showRet = true;

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

  function formatPts(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '—';
    return Math.round(Number(v)).toLocaleString('pt-BR');
  }

  function formatPct(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '—';
    const num = Number(v);
    const sign = num > 0 ? '+' : num < 0 ? '-' : '';
    return `${sign}${Math.abs(num).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}%`;
  }

  function getWeekKey(iso) {
    const [y, m, d] = iso.split('-').map(Number);
    const dt = new Date(Date.UTC(y, m - 1, d));
    const day = dt.getUTCDay() || 7; // Mon=1 .. Sun=7
    dt.setUTCDate(dt.getUTCDate() - (day - 1)); // Monday of that week
    return dt.toISOString().slice(0, 10);
  }

  $: rawRows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  $: dailyParsed = (() => {
    const seen = new Set();
    const out = [];
    for (const r of rawRows) {
      const time = toIsoDate(r.trading_date);
      if (!time || seen.has(time)) continue;
      const close = r.ibov_close === null || r.ibov_close === undefined ? null : Number(r.ibov_close);
      if (close === null || Number.isNaN(close)) continue;
      seen.add(time);
      out.push({
        time,
        close,
        ret: r.ibov_return_1d_pct === null || r.ibov_return_1d_pct === undefined ? null : Number(r.ibov_return_1d_pct),
        ma21: r.ibov_ma21 === null || r.ibov_ma21 === undefined ? null : Number(r.ibov_ma21),
        ma50: r.ibov_ma50 === null || r.ibov_ma50 === undefined ? null : Number(r.ibov_ma50),
        ma200: r.ibov_ma200 === null || r.ibov_ma200 === undefined ? null : Number(r.ibov_ma200),
      });
    }
    out.sort((a, b) => (a.time < b.time ? -1 : a.time > b.time ? 1 : 0));
    return out;
  })();

  $: candles = (() => {
    if (!dailyParsed.length) return [];

    if (timeframe === '1D') {
      return dailyParsed.map((p, idx) => {
        const open = idx > 0 ? dailyParsed[idx - 1].close : p.close;
        const close = p.close;
        return {
          time: p.time,
          open,
          high: Math.max(open, close),
          low: Math.min(open, close),
          close,
          ret: p.ret,
          ma21: p.ma21,
          ma50: p.ma50,
          ma200: p.ma200,
        };
      });
    }

    const buckets = new Map();
    for (let i = 0; i < dailyParsed.length; i++) {
      const p = dailyParsed[i];
      const key = timeframe === '1M' ? p.time.slice(0, 7) : getWeekKey(p.time);
      let b = buckets.get(key);
      if (!b) {
        const prevClose = i > 0 ? dailyParsed[i - 1].close : p.close;
        b = {
          time: p.time,
          open: prevClose,
          high: Math.max(prevClose, p.close),
          low: Math.min(prevClose, p.close),
          close: p.close,
          ma21: p.ma21,
          ma50: p.ma50,
          ma200: p.ma200,
        };
        buckets.set(key, b);
      } else {
        b.time = p.time;
        b.high = Math.max(b.high, p.close);
        b.low = Math.min(b.low, p.close);
        b.close = p.close;
        b.ma21 = p.ma21;
        b.ma50 = p.ma50;
        b.ma200 = p.ma200;
      }
    }

    return Array.from(buckets.values()).map((b) => ({
      ...b,
      ret: b.open > 0 ? ((b.close / b.open) - 1) * 100 : 0,
    }));
  })();

  $: byDate = new Map(candles.map((c) => [c.time, c]));
  $: latest = candles.length ? candles[candles.length - 1] : null;
  $: activePoint = hovered || latest;
  $: sliderStartLabel = candles.length ? formatBrDate(candles[Math.max(0, Math.min(Math.round(visibleFrom), candles.length - 1))]?.time) : '';
  $: sliderEndLabel = candles.length ? formatBrDate(candles[Math.max(0, Math.min(Math.round(visibleTo), candles.length - 1))]?.time) : '';

  function syncSeriesData() {
    if (!chart || !candleSeries) return;
    candleSeries.setData(
      candles.map((c) => ({
        time: c.time,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }))
    );
    ma21Series.setData(candles.filter((c) => c.ma21 !== null).map((c) => ({ time: c.time, value: c.ma21 })));
    ma50Series.setData(candles.filter((c) => c.ma50 !== null).map((c) => ({ time: c.time, value: c.ma50 })));
    ma200Series.setData(candles.filter((c) => c.ma200 !== null).map((c) => ({ time: c.time, value: c.ma200 })));
    retSeries.setData(
      candles
        .filter((c) => c.ret !== null)
        .map((c) => ({
          time: c.time,
          value: c.ret,
          color: c.ret >= 0 ? 'rgba(242, 185, 75, 0.72)' : 'rgba(124, 124, 134, 0.58)',
        }))
    );

    const ts = chart.timeScale();
    if (timeframe === '1D' && candles.length > 140) {
      const from = candles.length - 140;
      const to = candles.length - 1;
      ts.setVisibleLogicalRange({ from, to: to + 3 });
      visibleFrom = from;
      visibleTo = to;
    } else {
      ts.fitContent();
      visibleFrom = 0;
      visibleTo = Math.max(0, candles.length - 1);
    }
  }

  function syncVisibility() {
    if (!chart) return;
    ma21Series?.applyOptions({ visible: showMa21 });
    ma50Series?.applyOptions({ visible: showMa50 });
    ma200Series?.applyOptions({ visible: showMa200 });
    retSeries?.applyOptions({ visible: showRet });
    chart.priceScale('right').applyOptions({
      scaleMargins: {
        top: 0.12,
        bottom: showRet ? 0.25 : 0.08,
      },
    });
  }

  function zoomBy(factor) {
    if (!chart) return;
    const ts = chart.timeScale();
    const range = ts.getVisibleLogicalRange();
    if (!range) return;
    const span = range.to - range.from;
    const newSpan = Math.max(8, span * factor);
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
    visibleTo = Math.max(0, candles.length - 1);
  }

  $: if (mounted && chart && candles) {
    hovered = null;
    syncSeriesData();
  }

  $: if (mounted && chart) {
    showMa21;
    showMa50;
    showMa200;
    showRet;
    syncVisibility();
  }

  onMount(async () => {
    mounted = true;
    const {
      createChart,
      CandlestickSeries,
      LineSeries,
      HistogramSeries,
      ColorType,
      CrosshairMode,
      LineStyle,
    } = await import('lightweight-charts');

    if (!containerEl || !mounted) return;

    const initialWidth = Math.max(280, containerEl.clientWidth || 640);
    chart = createChart(containerEl, {
      width: initialWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: '#2b2b2b' },
        textColor: '#8a8a93',
        fontFamily: "'JetBrains Mono', ui-monospace, monospace",
        fontSize: 11,
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
      rightPriceScale: {
        borderColor: '#3a3a3f',
        scaleMargins: { top: 0.12, bottom: 0.25 },
      },
      timeScale: {
        borderColor: '#3a3a3f',
        timeVisible: false,
        rightOffset: 4,
        minBarSpacing: 2,
      },
      localization: {
        locale: 'pt-BR',
        priceFormatter: (p) => Math.round(p).toLocaleString('pt-BR'),
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

    candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#f2b94b',
      downColor: '#7c7c86',
      borderVisible: false,
      wickUpColor: '#f2b94b',
      wickDownColor: '#8f8f99',
      priceLineVisible: true,
      priceLineColor: 'rgba(242, 185, 75, 0.5)',
      priceLineStyle: LineStyle.Dashed,
      lastValueVisible: true,
    });

    ma21Series = chart.addSeries(LineSeries, {
      color: '#f5f5f5',
      lineWidth: 1.35,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });

    ma50Series = chart.addSeries(LineSeries, {
      color: '#60a5fa',
      lineWidth: 1.3,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });

    ma200Series = chart.addSeries(LineSeries, {
      color: '#c084fc',
      lineWidth: 1.4,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });

    retSeries = chart.addSeries(HistogramSeries, {
      priceScaleId: 'ret',
      priceFormat: { type: 'percent' },
      priceLineVisible: false,
      lastValueVisible: false,
    });

    chart.priceScale('ret').applyOptions({
      scaleMargins: { top: 0.79, bottom: 0.0 },
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
      if (syncingFromSlider || !range || !candles.length) return;
      visibleFrom = Math.max(0, Math.min(range.from, candles.length - 1));
      visibleTo = Math.max(visibleFrom, Math.min(range.to, candles.length - 1));
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

<div class="tv-wrap">
  <div class="tv-head">
    <div class="tv-title-block">
      <h2 class="terminal-panel-title" style="margin: 0 0 4px 0;">
        <span>{panelTitle}</span>
      </h2>
      {#if panelSubtitle}
        <p class="terminal-panel-sub" style="margin: 0;">{panelSubtitle}</p>
      {/if}
    </div>

    <div class="tv-controls" role="group" aria-label="Período, indicadores e zoom do gráfico">
      <div class="tv-tf-group" role="group" aria-label="Tempo gráfico das velas">
        <button type="button" class="tv-tf-btn" class:is-active={timeframe === '1D'} on:click={() => (timeframe = '1D')}>1D</button>
        <button type="button" class="tv-tf-btn" class:is-active={timeframe === '1S'} on:click={() => (timeframe = '1S')}>1S</button>
        <button type="button" class="tv-tf-btn" class:is-active={timeframe === '1M'} on:click={() => (timeframe = '1M')}>1M</button>
      </div>
      <button type="button" class="tv-pill" class:is-on={showMa21} on:click={() => (showMa21 = !showMa21)}>
        <span class="dot" style="background: #f5f5f5;"></span>
        <span>MM21</span>
      </button>
      <button type="button" class="tv-pill" class:is-on={showMa50} on:click={() => (showMa50 = !showMa50)}>
        <span class="dot" style="background: #60a5fa;"></span>
        <span>MM50</span>
      </button>
      <button type="button" class="tv-pill" class:is-on={showMa200} on:click={() => (showMa200 = !showMa200)}>
        <span class="dot" style="background: #c084fc;"></span>
        <span>MM200</span>
      </button>
      <button type="button" class="tv-pill" class:is-on={showRet} on:click={() => (showRet = !showRet)}>
        <span class="dot" style="background: #f2b94b;"></span>
        <span>Var. %</span>
      </button>
      <div class="tv-zoom-group" role="group" aria-label="Controles de zoom">
        <button type="button" class="tv-zoom-btn" on:click={() => zoomBy(0.72)} title="Aproximar zoom" aria-label="Aproximar zoom">+</button>
        <button type="button" class="tv-zoom-btn" on:click={() => zoomBy(1.38)} title="Afastar zoom" aria-label="Afastar zoom">−</button>
        <button type="button" class="tv-zoom-btn tv-zoom-fit" on:click={resetFit} title="Resetar zoom e enquadramento">Ajustar</button>
      </div>
    </div>
  </div>

  {#if activePoint}
    <div class="tv-hud" aria-live="polite">
      <span class="hud-item hud-date">{formatBrDate(activePoint.time)}</span>
      <span class="hud-item">
        <span class="hud-lbl">A</span>
        <span class="hud-val">{formatPts(activePoint.open)}</span>
      </span>
      <span class="hud-item">
        <span class="hud-lbl">Máx</span>
        <span class="hud-val">{formatPts(activePoint.high)}</span>
      </span>
      <span class="hud-item">
        <span class="hud-lbl">Mín</span>
        <span class="hud-val">{formatPts(activePoint.low)}</span>
      </span>
      <span class="hud-item">
        <span class="hud-lbl">F</span>
        <strong class="hud-val" class:is-pos={activePoint.close >= activePoint.open} class:is-neg={activePoint.close < activePoint.open}>
          {formatPts(activePoint.close)}
        </strong>
      </span>
      {#if activePoint.ret !== null}
        <span class="hud-item">
          <strong class="hud-val" class:is-pos={activePoint.ret >= 0} class:is-neg={activePoint.ret < 0}>
            ({formatPct(activePoint.ret)})
          </strong>
        </span>
      {/if}
      {#if showMa21 && activePoint.ma21 !== null}
        <span class="hud-item">
          <span class="hud-lbl" style="color: #f5f5f5;">MM21</span>
          <span class="hud-val">{formatPts(activePoint.ma21)}</span>
        </span>
      {/if}
      {#if showMa50 && activePoint.ma50 !== null}
        <span class="hud-item">
          <span class="hud-lbl" style="color: #60a5fa;">MM50</span>
          <span class="hud-val">{formatPts(activePoint.ma50)}</span>
        </span>
      {/if}
      {#if showMa200 && activePoint.ma200 !== null}
        <span class="hud-item">
          <span class="hud-lbl" style="color: #c084fc;">MM200</span>
          <span class="hud-val">{formatPts(activePoint.ma200)}</span>
        </span>
      {/if}
    </div>
  {/if}

  <div class="tv-canvas" bind:this={containerEl} style={`height: ${height}px;`}></div>

  <TradingViewRangeSlider
    total={candles.length}
    startIdx={visibleFrom}
    endIdx={visibleTo}
    startLabel={sliderStartLabel}
    endLabel={sliderEndLabel}
    on:change={handleSliderChange}
  />
</div>

<style>
  .tv-wrap {
    inline-size: 100%;
    max-inline-size: 100%;
    min-inline-size: 0;
  }

  .tv-head {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px 16px;
    margin-block-end: 10px;
  }

  .tv-controls {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
  }

  .tv-tf-group {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    border: 1px solid #3a3a40;
    background: #232326;
    padding: 2px;
    gap: 2px;
  }

  .tv-tf-btn {
    height: 22px;
    padding: 0 9px;
    border: 0;
    border-radius: 999px;
    background: transparent;
    color: #8a8a93;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 10.5px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 140ms ease, color 140ms ease;
  }

  .tv-tf-btn:hover {
    color: #f5f5f5;
  }

  .tv-tf-btn.is-active {
    background: #f5f5f5;
    color: #222222;
  }

  .tv-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 28px;
    padding: 0 11px;
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

  .tv-pill.is-on {
    background: #323238;
    border-color: #4f4f58;
    color: #f0f0f3;
  }

  .tv-pill:hover {
    border-color: #62626c;
    color: #f8f8f8;
  }

  .tv-zoom-group {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    border: 1px solid #3a3a40;
    background: #232326;
    overflow: hidden;
  }

  .tv-zoom-btn {
    height: 26px;
    min-inline-size: 28px;
    padding: 0 8px;
    border: 0;
    border-inline-end: 1px solid #34343a;
    background: transparent;
    color: #d4d4d8;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 140ms ease, color 140ms ease;
  }

  .tv-zoom-btn:last-child {
    border-inline-end: 0;
  }

  .tv-zoom-btn:hover {
    background: #323238;
    color: #f8f8f8;
  }

  .tv-zoom-fit {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 11px;
    font-weight: 500;
    padding: 0 10px;
  }

  .dot {
    inline-size: 6px;
    block-size: 6px;
    border-radius: 50%;
    opacity: 0.45;
  }

  .tv-pill.is-on .dot {
    opacity: 1;
  }

  .tv-hud {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 5px 12px;
    padding: 7px 12px;
    margin-block-end: 8px;
    border-radius: 12px;
    background: #232326;
    border: 1px solid #34343a;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 11px;
    font-variant-numeric: tabular-nums;
  }

  .hud-item {
    display: inline-flex;
    align-items: baseline;
    gap: 4px;
  }

  .hud-date {
    color: #a3a3ab;
    font-weight: 600;
  }

  .hud-lbl {
    color: #76767e;
    font-size: 10px;
    font-weight: 600;
  }

  .hud-val {
    color: #e5e5e5;
    font-weight: 500;
  }

  .hud-val.is-pos {
    color: #f2b94b;
    font-weight: 600;
  }

  .hud-val.is-neg {
    color: #a3a3ab;
    font-weight: 600;
  }

  .tv-canvas {
    inline-size: 100%;
    max-inline-size: 100%;
    border-radius: 14px;
    overflow: hidden;
  }

  @media (max-width: 640px) {
    .tv-hud {
      font-size: 10px;
      gap: 4px 8px;
      padding: 6px 9px;
    }
  }
</style>
