<script>
  import { createEventDispatcher } from 'svelte';

  export let total = 0;
  export let startIdx = 0;
  export let endIdx = 0;
  export let startLabel = '';
  export let endLabel = '';

  const dispatch = createEventDispatcher();
  let trackEl;
  let dragMode = null; // 'left' | 'right' | 'window'
  let dragStartX = 0;
  let dragOrigStart = 0;
  let dragOrigEnd = 0;

  $: maxIdx = Math.max(1, total - 1);
  $: clampedStart = Math.max(0, Math.min(startIdx, maxIdx));
  $: clampedEnd = Math.max(clampedStart, Math.min(endIdx, maxIdx));
  $: leftPct = (clampedStart / maxIdx) * 100;
  $: rightPct = (clampedEnd / maxIdx) * 100;
  $: widthPct = Math.max(6, rightPct - leftPct);
  $: adjustedLeftPct = Math.min(leftPct, 100 - widthPct);

  function emitRange(from, to) {
    dispatch('change', { from, to });
  }

  function stepPan(direction) {
    if (total <= 1) return;
    const span = clampedEnd - clampedStart;
    if (span >= maxIdx - 0.5) {
      // If fully zoomed out, zoom into 70% window towards the clicked side
      const nextSpan = Math.max(Math.min(5, maxIdx), maxIdx * 0.7);
      if (direction < 0) {
        emitRange(0, nextSpan);
      } else {
        emitRange(maxIdx - nextSpan, maxIdx);
      }
      return;
    }
    const step = Math.max(1, span * 0.25) * direction;
    const nextStart = Math.max(0, Math.min(clampedStart + step, maxIdx - span));
    emitRange(nextStart, nextStart + span);
  }

  function startDrag(mode, e) {
    if (total <= 1 || !trackEl) return;
    e.preventDefault();
    e.stopPropagation();
    dragMode = mode;
    dragStartX = e.clientX;
    dragOrigStart = clampedStart;
    dragOrigEnd = clampedEnd;
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
  }

  function onMove(e) {
    if (!dragMode || !trackEl) return;
    const rect = trackEl.getBoundingClientRect();
    if (rect.width <= 0) return;
    const deltaIdx = ((e.clientX - dragStartX) / rect.width) * maxIdx;
    const minSpan = Math.min(5, maxIdx);

    let nextStart = dragOrigStart;
    let nextEnd = dragOrigEnd;

    if (dragMode === 'left') {
      nextStart = Math.max(0, Math.min(dragOrigStart + deltaIdx, dragOrigEnd - minSpan));
    } else if (dragMode === 'right') {
      nextEnd = Math.min(maxIdx, Math.max(dragOrigEnd + deltaIdx, dragOrigStart + minSpan));
    } else if (dragMode === 'window') {
      const span = dragOrigEnd - dragOrigStart;
      nextStart = Math.max(0, Math.min(dragOrigStart + deltaIdx, maxIdx - span));
      nextEnd = nextStart + span;
    }

    emitRange(nextStart, nextEnd);
  }

  function onUp() {
    dragMode = null;
    window.removeEventListener('pointermove', onMove);
    window.removeEventListener('pointerup', onUp);
  }
</script>

{#if total > 1}
  <div class="tv-scroll-wrap">
    <div class="tv-scroll-bar">
      <button
        type="button"
        class="tv-scroll-arrow"
        on:click={() => stepPan(-1)}
        aria-label="Rolar gráfico para esquerda"
        title="Mover para esquerda"
      >
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none" aria-hidden="true">
          <path d="M7.5 2.5L4 6l3.5 3.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>

      <div class="tv-scroll-track" bind:this={trackEl}>
        <div
          class="tv-scroll-thumb"
          style={`left: ${adjustedLeftPct}%; width: ${widthPct}%;`}
          on:pointerdown={(e) => startDrag('window', e)}
          role="slider"
          tabindex="0"
          aria-label="Barra de rolagem horizontal do gráfico"
          aria-valuemin={0}
          aria-valuemax={maxIdx}
          aria-valuenow={Math.round(clampedStart)}
        >
          <span
            class="tv-scroll-edge is-left"
            on:pointerdown={(e) => startDrag('left', e)}
            title={startLabel || 'Ajustar início'}
          ></span>
          <span class="tv-scroll-grip" aria-hidden="true"></span>
          <span
            class="tv-scroll-edge is-right"
            on:pointerdown={(e) => startDrag('right', e)}
            title={endLabel || 'Ajustar fim'}
          ></span>
        </div>
      </div>

      <button
        type="button"
        class="tv-scroll-arrow"
        on:click={() => stepPan(1)}
        aria-label="Rolar gráfico para direita"
        title="Mover para direita"
      >
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none" aria-hidden="true">
          <path d="M4.5 2.5L8 6l-3.5 3.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
    </div>

    {#if startLabel || endLabel}
      <div class="tv-scroll-dates">
        <span>{startLabel}</span>
        <span>{endLabel}</span>
      </div>
    {/if}
  </div>
{/if}

<style>
  .tv-scroll-wrap {
    margin-block-start: 8px;
    user-select: none;
    touch-action: none;
  }

  .tv-scroll-bar {
    display: flex;
    align-items: center;
    gap: 2px;
    block-size: 20px;
    padding: 2px;
    border-radius: 6px;
    background: #232326;
    border: 1px solid #36363c;
  }

  .tv-scroll-arrow {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    inline-size: 18px;
    block-size: 14px;
    padding: 0;
    border: 0;
    border-radius: 4px;
    background: transparent;
    color: #9a9aa4;
    cursor: pointer;
    flex-shrink: 0;
    transition: background-color 120ms ease, color 120ms ease;
  }

  .tv-scroll-arrow:hover {
    background: #34343a;
    color: #f5f5f5;
  }

  .tv-scroll-track {
    position: relative;
    flex: 1;
    block-size: 12px;
    border-radius: 4px;
    background: #1b1b1e;
    overflow: hidden;
  }

  .tv-scroll-thumb {
    position: absolute;
    inset-block: 1px;
    border-radius: 3px;
    background: #64646d;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: grab;
    transition: background-color 120ms ease;
  }

  .tv-scroll-thumb:hover {
    background: #7d7d88;
  }

  .tv-scroll-thumb:active {
    cursor: grabbing;
    background: #92929e;
  }

  .tv-scroll-grip {
    inline-size: 14px;
    block-size: 2px;
    border-radius: 2px;
    background: rgba(255, 255, 255, 0.35);
    pointer-events: none;
  }

  .tv-scroll-edge {
    position: absolute;
    inset-block: 0;
    inline-size: 8px;
    cursor: ew-resize;
  }

  .tv-scroll-edge.is-left {
    inset-inline-start: 0;
  }

  .tv-scroll-edge.is-right {
    inset-inline-end: 0;
  }

  .tv-scroll-dates {
    display: flex;
    justify-content: space-between;
    margin-block-start: 4px;
    padding-inline: 2px;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 9.5px;
    color: #76767e;
  }
</style>
