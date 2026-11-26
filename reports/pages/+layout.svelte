<script>
  import '@evidence-dev/tailwind/fonts.css';
  import '../app.css';
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { base } from '$app/paths';
  import { EvidenceDefaultLayout } from '@evidence-dev/core-components';

  export let data;

  const navItems = [
    { label: 'Panorama', path: '/' },
    { label: 'Fluxo Diário', path: '/fluxo-diario' },
    { label: 'Curto Prazo', path: '/curto-prazo' },
    { label: 'Comparativo', path: '/comparativo' },
    { label: 'Ibovespa', path: '/ibovespa' },
    { label: 'Linhagem', path: '/linhagem' },
  ];

  let headerEl;
  let headerInnerEl;
  let menuEl;
  let isWide = false;
  let isMeasuring = false;
  let lastCollapsedWidth = 0;

  function normalizePath(pathname) {
    if (!pathname) return '/';
    let p = pathname;
    if (base && p.startsWith(base)) {
      p = p.slice(base.length) || '/';
    }
    if (p.length > 1 && p.endsWith('/')) {
      p = p.slice(0, -1);
    }
    return p || '/';
  }

  function isCurrent(itemPath, currentPathname) {
    return normalizePath(currentPathname) === itemPath;
  }

  function closeMobileMenu() {
    if (!menuEl || isWide) return;
    try {
      if (typeof menuEl.hidePopover === 'function' && menuEl.matches(':popover-open')) {
        menuEl.hidePopover();
      }
    } catch {
      menuEl.classList.remove(':popover-open');
    }
  }

  function syncNavLayout(force = false) {
    if (!headerEl || !headerInnerEl || !menuEl) return;

    const currentWidth = headerEl.clientWidth;
    if (!force && !isWide && currentWidth <= lastCollapsedWidth) {
      return;
    }

    let wasOpen = false;
    try {
      wasOpen = menuEl.matches(':popover-open');
    } catch {
      wasOpen = menuEl.classList.contains(':popover-open');
    }

    isMeasuring = true;
    headerEl.classList.add('is-measuring', 'is-wide');
    menuEl.removeAttribute('popover');

    const fits = headerInnerEl.scrollWidth <= headerInnerEl.clientWidth + 1;

    if (fits) {
      isWide = true;
      lastCollapsedWidth = 0;
    } else {
      isWide = false;
      lastCollapsedWidth = currentWidth;
      headerEl.classList.remove('is-wide');
      menuEl.setAttribute('popover', 'auto');
      if (wasOpen && typeof menuEl.showPopover === 'function') {
        try {
          menuEl.showPopover();
        } catch {
          // Ignore if browser rejects re-opening during resize
        }
      }
    }

    requestAnimationFrame(() => {
      isMeasuring = false;
      headerEl?.classList.remove('is-measuring');
    });
  }

  function handleFallbackToggle() {
    if (!menuEl || isWide) return;
    if (Object.hasOwn(HTMLElement.prototype, 'popover')) return;
    menuEl.classList.toggle(':popover-open');
  }

  onMount(() => {
    try {
      document.documentElement.setAttribute('data-theme', 'light');
      localStorage.setItem('evidence-theme', 'light');
    } catch {
      document.documentElement.setAttribute('data-theme', 'light');
    }

    syncNavLayout(true);

    const observer = new ResizeObserver(() => {
      syncNavLayout(false);
    });
    if (headerEl) observer.observe(headerEl);
    if (menuEl) observer.observe(menuEl);

    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(() => syncNavLayout(true));
    }

    return () => {
      observer.disconnect();
    };
  });

  $: if ($page.url.pathname) {
    closeMobileMenu();
  }
</script>

<svelte:head>
  <meta name="color-scheme" content="light" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <link rel="icon" type="image/svg+xml" href={`${base}/favicon.svg`} />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
  <link
    href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=Inter:wght@500;600;700&display=swap"
    rel="stylesheet"
  />
</svelte:head>

<EvidenceDefaultLayout
  {data}
  title="GringoLake"
  fullWidth={true}
  hideSidebar={true}
  hideHeader={true}
  hideBreadcrumbs={true}
  hideTOC={true}
  neverShowQueries={true}
  builtWithEvidence={false}
>
  <div slot="content" class="gl-app-shell">
    <header
      bind:this={headerEl}
      class="site-header"
      class:is-wide={isWide}
      class:is-measuring={isMeasuring}
    >
      <div bind:this={headerInnerEl} class="header-inner">
        <a class="site-brand" href={`${base}/`}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <rect x="1" y="1" width="22" height="22" rx="6" fill="#FFFFFF" stroke="#E4E4E7" stroke-width="1.2" />
            <path d="M4.5 17.5C7 16 9.5 19 12 17.5C14.5 16 17 19 19.5 17.5" stroke="#CBD5E1" stroke-width="1.5" stroke-linecap="round" />
            <path d="M4.5 14C7 12.6 9.5 15.2 12 13.8C14.5 12.4 17 14.8 19.5 13.4" stroke="#94A3B8" stroke-width="1.5" stroke-linecap="round" />
            <path d="M5 10.8L9.2 8.2L12.6 10L18.2 6.4" stroke="#D97706" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" />
            <circle cx="18.4" cy="6.3" r="2" fill="#D97706" />
          </svg>
          <span class="brand-name">Gringo<span class="brand-accent">Lake</span></span>
        </a>

        <nav class="site-nav" aria-label="Navegação principal">
          <button
            class="menu-button"
            type="button"
            popovertarget="gl-site-menu"
            popovertargetaction="toggle"
            aria-controls="gl-site-menu"
            aria-label="Abrir menu de navegação"
            on:click={handleFallbackToggle}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path
                d="M4 7h16M4 12h16M4 17h16"
                stroke="currentColor"
                stroke-width="1.9"
                stroke-linecap="round"
              />
            </svg>
          </button>

          <ul bind:this={menuEl} id="gl-site-menu" class="site-menu" popover="auto">
            {#each navItems as item}
              <li>
                <a
                  href={item.path === '/' ? `${base}/` : `${base}${item.path}`}
                  aria-current={isCurrent(item.path, $page.url.pathname) ? 'page' : undefined}
                  on:click={closeMobileMenu}
                >
                  {item.label}
                </a>
              </li>
            {/each}
          </ul>
        </nav>

        <div class="header-provenance">
          <span class="prov-source">B3 Oficial</span>
          <span class="prov-sep" aria-hidden="true">|</span>
          <span class="prov-engine">DuckDB-WASM</span>
          <a
            class="repo-link"
            href="https://github.com/leoserpa/gringolake"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Abrir repositório no GitHub"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844a9.59 9.59 0 0 1 2.504.337c1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.02 10.02 0 0 0 22 12.017C22 6.484 17.522 2 12 2Z" />
            </svg>
          </a>
        </div>
      </div>
    </header>

    <div class="gl-page-container">
      <slot />

      <footer class="gl-footer">
        <span>Fonte: B3 S.A. (GetPortfolioDay IBOV · BDI SharesInvesVolum D+2) · Atualização útil pós-SLA 21:00 BRT</span>
        <span>GringoLake · GNU GPL v3.0</span>
      </footer>
    </div>
  </div>
</EvidenceDefaultLayout>

<style>
  :global(:root),
  :global(html[data-theme='light']) {
    color-scheme: light;
    accent-color: #d97706;
    --gl-canvas: #f5f5f4;
    --gl-surface: #ffffff;
    --gl-elevated: #fafaf9;
    --gl-border: #e4e4e7;
    --gl-divider: #f4f4f5;
    --gl-text: #18181b;
    --gl-text-secondary: #52525b;
    --gl-text-muted: #71717a;
    --gl-text-dim: #a1a1aa;
    --gl-accent: #d97706;
    --target-size: 24px;
    --base-100: #ffffff;
    --base-200: #f5f5f4;
    --base-300: #e4e4e7;
    --base-content: #27272a;
    --base-content-muted: #71717a;
    --base-heading: #18181b;
    --primary: #d97706;
    --twc-primary: 32.1 94.6% 43.7%;
  }

  @media (pointer: coarse) {
    :global(:root) {
      --target-size: 44px;
    }
  }

  :global(html),
  :global(body) {
    margin: 0;
    background-color: #f5f5f4 !important;
    color: #18181b !important;
    font-family: 'IBM Plex Sans', system-ui, -apple-system, sans-serif;
    -webkit-font-smoothing: antialiased;
  }

  :global([data-sveltekit-preload-data] > div:has(> main)),
  :global(main),
  :global(#evidence-main-article),
  :global(#evidence-main-article > div) {
    width: 100% !important;
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    background-color: #f5f5f4 !important;
    overflow: visible !important;
  }

  :global(#evidence-main-article > header),
  :global(#evidence-main-article h1.title) {
    display: none !important;
  }

  :global(h1),
  :global(h2),
  :global(h3) {
    font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
    letter-spacing: -0.018em;
    color: #18181b;
    text-wrap: balance;
  }

  :global(p),
  :global(li) {
    text-wrap: pretty;
  }

  :global(code),
  :global(pre),
  :global(table td),
  :global(table th),
  :global(.tabular-nums) {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  :global(a),
  :global(code) {
    overflow-wrap: anywhere;
  }

  /* ==================== FULL-WIDTH SHELL & STICKY 58px HEADER ==================== */
  .gl-app-shell {
    inline-size: 100%;
    min-block-size: 100dvh;
    background: #f5f5f4;
    color: #18181b;
  }

  .site-header {
    inline-size: 100%;
    box-sizing: border-box;
    position: sticky;
    inset-block-start: 0;
    z-index: 40;
    background: rgba(255, 255, 255, 0.96);
    backdrop-filter: blur(8px);
    border-block-end: 1px solid #e4e4e7;
    padding-block-start: env(safe-area-inset-top, 0px);
    padding-inline-start: max(clamp(16px, 2.5vw, 32px), env(safe-area-inset-left, 0px));
    padding-inline-end: max(clamp(16px, 2.5vw, 32px), env(safe-area-inset-right, 0px));
  }

  .header-inner {
    inline-size: 100%;
    max-inline-size: 1440px;
    margin-inline: auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    min-block-size: 58px;
  }

  .header-inner > * {
    flex-shrink: 0;
    white-space: nowrap;
  }

  .site-brand {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    text-decoration: none;
    min-block-size: var(--target-size);
  }

  .brand-name {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 15.5px;
    font-weight: 700;
    color: #18181b;
    letter-spacing: -0.02em;
  }

  .brand-accent {
    color: #d97706;
  }

  .site-brand:focus-visible,
  .menu-button:focus-visible,
  .repo-link:focus-visible,
  .site-menu a:focus-visible {
    outline: 2px solid #d97706;
    outline-offset: 2px;
    border-radius: 6px;
  }

  .site-nav {
    display: flex;
    align-items: center;
    order: -1;
    margin-inline-start: 0;
  }

  .site-header.is-wide .site-nav {
    order: 0;
    margin-inline: auto;
  }

  .menu-button {
    anchor-name: --menu-button;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-block-size: max(36px, var(--target-size));
    min-inline-size: max(36px, var(--target-size));
    padding: 0;
    border-radius: 6px;
    border: 1px solid #e4e4e7;
    background: #ffffff;
    color: #18181b;
    cursor: pointer;
  }

  .menu-button:hover {
    background: #f4f4f5;
  }

  .site-menu {
    position: fixed;
    inset: auto;
    inset-block-start: calc(3.85rem + env(safe-area-inset-top, 0px));
    inset-block-start: anchor(--menu-button bottom);
    inset-inline-start: max(1rem, env(safe-area-inset-left, 0px));
    inline-size: min(84dvw, 19rem);
    max-inline-size: calc(100dvw - 2rem);
    block-size: fit-content;
    max-block-size: calc(100dvh - 5.5rem);
    margin: 0.5rem 0 0;
    padding: 8px;
    list-style: none;
    overflow: auto;
    border-radius: 8px;
    border: 1px solid #e4e4e7;
    background: #ffffff;
    box-shadow: 0 18px 42px rgba(15, 23, 42, 0.12);
  }

  .site-menu::backdrop {
    background: rgba(15, 23, 42, 0.25);
  }

  @supports not selector(:popover-open) {
    .site-menu[popover]:not(.\:popover-open) {
      display: none;
    }
    .site-menu[popover].\:popover-open {
      display: block;
    }
  }

  .site-menu a {
    display: flex;
    align-items: center;
    min-block-size: max(40px, var(--target-size));
    padding: 6px 12px;
    border-radius: 6px;
    color: #52525b;
    text-decoration: none;
    font-size: 13px;
    font-weight: 400;
    border-inline-start: 2px solid transparent;
  }

  .site-menu a:hover {
    background: #f4f4f5;
    color: #18181b;
  }

  .site-menu a[aria-current='page'] {
    background: #fffbeb;
    color: #18181b;
    font-weight: 600;
    border-inline-start-color: #d97706;
  }

  .site-header.is-wide .menu-button {
    display: none;
  }

  .site-header.is-wide .site-menu {
    position: static;
    display: flex;
    align-items: stretch;
    gap: 8px;
    inline-size: auto;
    max-inline-size: none;
    block-size: auto;
    max-block-size: none;
    overflow: visible;
    margin: 0;
    padding: 0;
    border: 0;
    background: transparent;
    box-shadow: none;
  }

  .site-header.is-wide .site-menu::backdrop {
    display: none;
  }

  .site-header.is-wide .site-menu a {
    min-block-size: 58px;
    padding: 0 10px;
    font-size: 12.5px;
    color: #52525b;
    border-inline-start: 0;
    border-block-end: 2px solid transparent;
    border-radius: 0;
  }

  .site-header.is-wide .site-menu a:hover {
    background: transparent;
    color: #18181b;
  }

  .site-header.is-wide .site-menu a[aria-current='page'] {
    background: transparent;
    color: #18181b;
    font-weight: 600;
    border-block-end-color: #d97706;
  }

  .site-header.is-measuring * {
    transition: none !important;
  }

  .header-provenance {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 11.5px;
    margin-inline-start: auto;
  }

  .site-header.is-wide .header-provenance {
    margin-inline-start: 0;
  }

  .prov-source {
    color: #18181b;
    font-weight: 500;
  }

  .prov-sep {
    color: #d4d4d8;
  }

  .prov-engine {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 11px;
    color: #71717a;
  }

  .repo-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-block-size: var(--target-size);
    min-inline-size: var(--target-size);
    color: #71717a;
    text-decoration: none;
    margin-inline-start: 4px;
  }

  .repo-link:hover {
    color: #18181b;
  }

  @media (max-width: 720px) {
    .header-inner {
      gap: 12px;
    }
    .prov-source,
    .prov-sep,
    .prov-engine {
      display: none;
    }
  }

  @media (forced-colors: active) {
    .site-menu a[aria-current='page'] {
      border-color: Highlight;
      text-decoration: underline;
    }
  }

  /* ==================== CENTERED 1440px PAGE CONTAINER ==================== */
  .gl-page-container {
    inline-size: 100%;
    max-inline-size: 1440px;
    margin-inline: auto;
    padding-block-start: 24px;
    padding-block-end: max(36px, env(safe-area-inset-bottom, 0px));
    padding-inline-start: max(clamp(16px, 2.5vw, 32px), env(safe-area-inset-left, 0px));
    padding-inline-end: max(clamp(16px, 2.5vw, 32px), env(safe-area-inset-right, 0px));
  }

  /* ==================== PAGE HEADER & INLINE FILTER BAR ==================== */
  :global(.page-hero) {
    display: flex;
    flex-direction: column;
    gap: 14px;
    margin-block-end: 18px;
  }

  :global(.page-title-group) {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  :global(.page-title) {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: clamp(20px, 2vw, 24px);
    font-weight: 700;
    color: #18181b;
    margin: 0;
    line-height: 1.2;
    letter-spacing: -0.02em;
  }

  :global(.page-subtitle) {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 12.5px;
    color: #71717a;
    margin: 0;
    line-height: 1.4;
  }

  :global(.controls-bar) {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
    gap: 10px 12px;
  }

  :global(.controls-left),
  :global(.controls-right) {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    gap: 10px;
  }

  :global(.status-chip) {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-block-size: 32px;
    padding: 5px 12px;
    border-radius: 6px;
    background: #ffffff;
    border: 1px solid #e4e4e7;
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 11px;
    font-weight: 500;
    color: #52525b;
    white-space: nowrap;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
  }

  :global(.status-chip-accent) {
    color: #b45309;
    font-weight: 600;
  }

  /* ==================== BUTTON GROUPS & DROPDOWNS (AMBER ACCENT) ==================== */
  :global(.controls-bar [role='group']) {
    background: #ffffff !important;
    border: 1px solid #e4e4e7 !important;
    border-radius: 6px !important;
    height: auto !important;
    min-block-size: max(34px, var(--target-size));
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03) !important;
    margin-bottom: 0 !important;
  }

  :global(.controls-bar [role='group'] button) {
    min-block-size: max(34px, var(--target-size));
    padding: 6px 14px !important;
    font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    border-color: #e4e4e7 !important;
    background-color: #ffffff !important;
    color: #52525b !important;
    transition: background-color 0.15s ease, color 0.15s ease;
  }

  :global(.controls-bar [role='group'] button:hover) {
    background-color: #fafaf9 !important;
    color: #18181b !important;
  }

  :global(.controls-bar [role='group'] button.text-primary),
  :global(.controls-bar [role='group'] button.bg-base-200) {
    background-color: #fffbeb !important;
    color: #b45309 !important;
    font-weight: 600 !important;
  }

  :global(.controls-bar button[role='combobox']) {
    min-block-size: max(34px, var(--target-size));
    background-color: #ffffff !important;
    border-color: #e4e4e7 !important;
    color: #18181b !important;
    font-size: 12px !important;
  }

  :global(.controls-bar .inline-block) {
    margin: 0 !important;
  }

  /* ==================== FULL-WIDTH RESPONSIVE GRIDS ==================== */
  :global(.kpi-grid-5) {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 14px;
    margin-block-end: 18px;
  }

  :global(.kpi-grid-4) {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
    margin-block-end: 18px;
  }

  :global(.terminal-grid-2) {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 18px;
    margin-block-end: 18px;
    align-items: stretch;
  }

  :global(.terminal-grid-1) {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 18px;
    margin-block-end: 18px;
  }

  /* ==================== PANELS & DATA-INK CHARTS ==================== */
  :global(.terminal-panel) {
    display: flex;
    flex-direction: column;
    background: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 10px;
    padding: 20px 22px;
    min-inline-size: 0;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
    --base-100: #ffffff;
    --twc-base-100: 0 0% 100%;
  }

  :global(.terminal-panel .chart-container),
  :global(.terminal-panel .chart-container > div),
  :global(.terminal-panel .bg-base-100),
  :global(.terminal-panel canvas) {
    background-color: transparent !important;
  }

  :global(.terminal-panel-title) {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 14.5px;
    font-weight: 600;
    color: #18181b;
    margin: 0 0 3px 0;
    line-height: 1.3;
  }

  :global(.terminal-panel-sub) {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 11.5px;
    color: #71717a;
    margin: 0 0 12px 0;
    line-height: 1.35;
  }

  /* ==================== STANDARD EVIDENCE TABLES ==================== */
  :global(.terminal-panel:not(.exec-explorer) .table-container),
  :global(.terminal-panel:not(.exec-explorer) .overflow-auto),
  :global(.terminal-panel:not(.exec-explorer) .overflow-x-auto) {
    max-inline-size: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  :global(.terminal-panel:not(.exec-explorer) table) {
    background: transparent !important;
    border-collapse: collapse;
    inline-size: 100%;
  }

  :global(.terminal-panel:not(.exec-explorer) thead th) {
    position: sticky;
    inset-block-start: 0;
    background: #ffffff !important;
    font-family: 'IBM Plex Mono', ui-monospace, monospace !important;
    font-size: 10.5px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #71717a !important;
    border-bottom: 1px solid #e4e4e7 !important;
    padding-block: 9px !important;
    white-space: nowrap;
  }

  :global(.terminal-panel:not(.exec-explorer) tbody td) {
    font-size: 12px !important;
    color: #27272a !important;
    border-bottom: 1px solid #f4f4f5 !important;
    padding-block: 8px !important;
    white-space: nowrap;
  }

  :global(.terminal-panel:not(.exec-explorer) tbody tr:last-child td) {
    border-bottom: 0 !important;
  }

  /* ==================== FOOTER ==================== */
  .gl-footer {
    margin-block-start: 28px;
    padding-block-start: 16px;
    border-block-start: 1px solid #e4e4e7;
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 8px 16px;
    font-size: 11px;
    color: #71717a;
  }

  /* ==================== RESPONSIVENESS ==================== */
  @media (max-width: 1200px) {
    :global(.kpi-grid-5) {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }

  @media (max-width: 900px) {
    :global(.terminal-grid-2) {
      grid-template-columns: 1fr;
    }
    :global(.kpi-grid-4) {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }

  @media (max-width: 640px) {
    :global(.kpi-grid-5) {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    :global(.terminal-panel) {
      padding: 15px 14px;
    }

    :global(.controls-bar) {
      flex-direction: column;
      align-items: stretch;
    }

    :global(.controls-left),
    :global(.controls-right) {
      inline-size: 100%;
    }
  }

  @media (max-width: 380px) {
    :global(.kpi-grid-4),
    :global(.kpi-grid-5) {
      grid-template-columns: 1fr;
    }
  }
</style>
