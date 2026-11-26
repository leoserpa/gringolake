<script>
  export let data = [];
  export let panelIndex = '';
  export let panelTitle = 'Participação no Volume da B3 (%)';
  export let panelSubtitle = 'Fatia de cada perfil no giro total negociado no mês (BDI) e no último pregão';

  $: rows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  $: sortedRows = [...rows].sort((a, b) => Number(b.mtd_share_pct ?? 0) - Number(a.mtd_share_pct ?? 0));
  $: maxShare = sortedRows.reduce((m, r) => Math.max(m, Number(r.mtd_share_pct ?? 0)), 1);

  function formatPct(v) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '—';
    return `${Number(v).toLocaleString('pt-BR', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    })}%`;
  }
</script>

<div class="share-wrap">
  <div class="share-head">
    <h2 class="terminal-panel-title" style="margin: 0 0 4px 0;">
      {#if panelIndex}
        <span class="panel-index">{panelIndex}</span>
      {/if}
      <span>{panelTitle}</span>
    </h2>
    {#if panelSubtitle}
      <p class="terminal-panel-sub" style="margin: 0;">{panelSubtitle}</p>
    {/if}
  </div>

  <div class="share-list">
    {#each sortedRows as row, idx}
      {@const mtdPct = Number(row.mtd_share_pct ?? 0)}
      {@const dayPct = Number(row.daily_share_pct ?? 0)}
      {@const barWidth = Math.max(2, (mtdPct / maxShare) * 100)}
      <div class="share-item">
        <div class="share-row-top">
          <span class="share-name" class:is-leader={idx === 0}>{row.investor_type_name_pt}</span>
          <span class="share-metrics">
            <span class="share-day">Dia {formatPct(dayPct)}</span>
            <strong class="share-mtd" class:is-leader={idx === 0}>{formatPct(mtdPct)}</strong>
          </span>
        </div>
        <div class="share-track" aria-hidden="true">
          <div
            class="share-fill"
            class:is-leader={idx === 0}
            style={`width: ${barWidth.toFixed(1)}%;`}
          ></div>
        </div>
      </div>
    {/each}
  </div>

  <div class="share-foot">
    <span>Soma das 5 categorias = 100% do volume financeiro da B3 (compras + vendas no BDI)</span>
  </div>
</div>

<style>
  .share-wrap {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    block-size: 100%;
    gap: 18px;
  }

  .share-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .share-item {
    display: flex;
    flex-direction: column;
    gap: 7px;
  }

  .share-row-top {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
  }

  .share-name {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 13px;
    font-weight: 500;
    color: #d4d4d8;
  }

  .share-name.is-leader {
    color: #f8f8f8;
    font-weight: 600;
  }

  .share-metrics {
    display: inline-flex;
    align-items: baseline;
    gap: 10px;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  .share-day {
    font-size: 11px;
    color: #767676;
  }

  .share-mtd {
    font-size: 13px;
    font-weight: 600;
    color: #e5e5e5;
    min-inline-size: 46px;
    text-align: right;
  }

  .share-mtd.is-leader {
    color: #f2b94b;
  }

  .share-track {
    inline-size: 100%;
    block-size: 8px;
    border-radius: 999px;
    background: #242426;
    overflow: hidden;
  }

  .share-fill {
    block-size: 100%;
    border-radius: 999px;
    background: #5c5c62;
    transition: width 0.25s ease;
  }

  .share-fill.is-leader {
    background: #f2b94b;
  }

  .share-foot {
    padding-block-start: 12px;
    border-block-start: 1px solid #343438;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 11.5px;
    color: #767676;
  }
</style>
