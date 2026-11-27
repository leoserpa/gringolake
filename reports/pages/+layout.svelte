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

    const viewportWidth = document.documentElement?.clientWidth || window.innerWidth || 0;
    const currentWidth = viewportWidth > 0 ? Math.min(headerEl.clientWidth || viewportWidth, viewportWidth) : headerEl.clientWidth;
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

    const availableWidth = Math.min(headerInnerEl.clientWidth, viewportWidth || headerInnerEl.clientWidth);
    const fits = headerInnerEl.scrollWidth <= availableWidth + 1;

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
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('evidence-theme', 'dark');
    } catch {
      document.documentElement.setAttribute('data-theme', 'dark');
    }

    syncNavLayout(true);

    let resizeRaf = 0;
    const scheduleSync = (force = false) => {
      if (resizeRaf) cancelAnimationFrame(resizeRaf);
      resizeRaf = requestAnimationFrame(() => {
        resizeRaf = 0;
        syncNavLayout(force);
      });
    };

    const observer = new ResizeObserver(() => scheduleSync(false));
    if (headerEl) observer.observe(headerEl);
    if (menuEl) observer.observe(menuEl);
    observer.observe(document.documentElement);

    const onWindowResize = () => scheduleSync(true);
    window.addEventListener('resize', onWindowResize, { passive: true });

    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(() => syncNavLayout(true));
    }

    return () => {
      if (resizeRaf) cancelAnimationFrame(resizeRaf);
      window.removeEventListener('resize', onWindowResize);
      observer.disconnect();
    };
  });

  $: if ($page.url.pathname) {
    closeMobileMenu();
  }
</script>

<svelte:head>
  <meta name="color-scheme" content="dark" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <link rel="icon" type="image/svg+xml" href={`${base}/favicon.svg`} />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
  <link
    href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap"
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
    <div class="gl-header-sticky-wrap">
      <header
        bind:this={headerEl}
        class="site-header"
        class:is-wide={isWide}
        class:is-measuring={isMeasuring}
      >
        <div bind:this={headerInnerEl} class="header-inner">
          <a class="site-brand" href={`${base}/`}>
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
              <path
                d="M6 18C6 9.5 12.5 5 21 7.5"
                stroke="#F5F5F5"
                stroke-width="2.6"
                stroke-linecap="round"
              />
              <path
                d="M26 14C26 22.5 19.5 27 11 24.5"
                stroke="#8A8A93"
                stroke-width="2.6"
                stroke-linecap="round"
              />
              <path
                d="M8 17L14 13L18 19L24 11"
                stroke="#F5F5F5"
                stroke-width="2.1"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <circle cx="24.25" cy="10.75" r="2.75" fill="#F2B94B" />
            </svg>
            <span class="brand-name">GringoLake</span>
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
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
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
            <a
              class="prov-chip"
              href={`${base}/linhagem`}
              title="Dados oficiais B3 (BDI e GetPortfolioDay) · Defasagem oficial D+2"
            >
              <span class="prov-exchange">B3</span>
              <span class="prov-official">Oficial</span>
              <span class="prov-sep" aria-hidden="true"></span>
              <span class="prov-lag">D+2</span>
            </a>
          </div>
        </div>
      </header>
    </div>

    <div class="gl-page-container">
      <slot />

      <footer class="gl-footer" aria-label="Rodapé institucional e metodologia">
        <div class="footer-brand-row">
          <a class="footer-brand" href={`${base}/`} aria-label="Voltar ao início do GringoLake">
            <svg width="24" height="24" viewBox="0 0 32 32" fill="none" aria-hidden="true">
              <path
                d="M6 18C6 9.5 12.5 5 21 7.5"
                stroke="#F5F5F5"
                stroke-width="2.6"
                stroke-linecap="round"
              />
              <path
                d="M26 14C26 22.5 19.5 27 11 24.5"
                stroke="#8A8A93"
                stroke-width="2.6"
                stroke-linecap="round"
              />
              <path
                d="M8 17L14 13L18 19L24 11"
                stroke="#F5F5F5"
                stroke-width="2.1"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <circle cx="24.25" cy="10.75" r="2.75" fill="#F2B94B" />
            </svg>
            <span class="footer-brand-name">GringoLake</span>
          </a>
        </div>

        <div class="footer-rule" aria-hidden="true"></div>

        <div class="footer-meta-row">
          <p class="footer-legal">
            GringoLake · 100% B3 Oficial (BDI SharesInvesVolum &amp; GetPortfolioDay) · Licença GPL v3
          </p>
          <span class="footer-sla">Atualização diária pós-SLA B3 (21h BRT) · Lag D+2</span>
        </div>

        <nav class="footer-nav" aria-label="Links do rodapé">
          {#each navItems as item}
            <a
              href={item.path === '/' ? `${base}/` : `${base}${item.path}`}
              aria-current={isCurrent(item.path, $page.url.pathname) ? 'page' : undefined}
            >
              {item.label}
            </a>
          {/each}
        </nav>

        <p class="footer-methodology">
          Desacumulação MTD ancorada no calendário oficial do Ibovespa (ADR-003). A soma das 5 categorias
          oficiais fecha em R$ 0 (tolerância ≤ R$ 20 mil). Conteúdo exclusivamente informativo e
          analítico, sem recomendação de investimento.
        </p>
      </footer>
    </div>
  </div>
</EvidenceDefaultLayout>

<style>
  :global(:root),
  :global(html),
  :global(html[data-theme='dark']) {
    color-scheme: dark;
    accent-color: #f2b94b;
    --ag-canvas: #222222;
    --ag-card: #2b2b2b;
    --ag-well: #262626;
    --ag-elevated: #343434;
    --ag-inverse: #f5f5f5;
    --ag-border: #363636;
    --ag-border-badge: #555555;
    --ag-hairline: #3a3a3f;
    --ag-text: #f8f8f8;
    --ag-text-secondary: #a3a3a3;
    --ag-text-muted: #767676;
    --ag-focal: #f2b94b;
    --ag-context: #9a9aa0;
    --ag-baseline: #5c5c62;
    --ag-scrollbar-thumb: #6e6e74;
    --ag-scrollbar-track: #222222;
    scrollbar-color: var(--ag-scrollbar-thumb) var(--ag-scrollbar-track);
    scroll-padding-top: calc(5.5rem + env(safe-area-inset-top, 0px));
    --target-size: 24px;
    --base-100: #2b2b2b;
    --base-200: #343434;
    --base-300: #3a3a3f;
    --base-content: #e5e5e5;
    --base-content-muted: #a3a3a3;
    --base-heading: #f8f8f8;
    --primary: #f2b94b;
    --twc-primary: 40 86% 62%;
    --twc-base-100: 0 0% 17%;
    --twc-base-200: 0 0% 20%;
    --twc-base-300: 0 0% 23%;
    --twc-base-content: 0 0% 90%;
    --twc-base-content-muted: 0 0% 64%;
  }

  @supports not (scrollbar-color: auto) {
    :global(html) {
      scrollbar-width: auto;
    }
    :global(html)::-webkit-scrollbar {
      width: 10px;
      height: 10px;
    }
    :global(html)::-webkit-scrollbar-thumb {
      background: var(--ag-scrollbar-thumb);
      border-radius: 999px;
    }
    :global(html)::-webkit-scrollbar-track {
      background: var(--ag-scrollbar-track);
    }
  }

  @media (pointer: coarse) {
    :global(:root) {
      --target-size: 44px;
    }
  }

  :global(html),
  :global(body) {
    margin: 0;
    background-color: #222222 !important;
    color: #f8f8f8 !important;
    font-family: 'Plus Jakarta Sans', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    overflow-wrap: break-word;
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
    background-color: transparent !important;
    overflow: visible !important;
  }

  :global(#evidence-main-article > header),
  :global(#evidence-main-article h1.title) {
    display: none !important;
  }

  :global(h1),
  :global(h2),
  :global(h3) {
    color: #f8f8f8;
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
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  :global(:where(a, code)) {
    overflow-wrap: anywhere;
  }

  /* ==================== ATELIER GRAPHITE SHELL (#222222) ==================== */
  .gl-app-shell {
    inline-size: 100%;
    min-block-size: 100dvh;
    background-color: #222222;
    color: #f8f8f8;
  }

  /* ==================== FULL-WIDTH STICKY TOPNAV ==================== */
  .gl-header-sticky-wrap {
    position: sticky;
    inset-block-start: 0;
    z-index: 40;
    inline-size: 100%;
    padding: 0;
  }

  .site-header {
    inline-size: 100%;
    max-inline-size: 100%;
    margin: 0;
    box-sizing: border-box;
    background: rgba(43, 43, 43, 0.94);
    backdrop-filter: blur(12px);
    border: 0;
    border-block-end: 1px solid #363636;
    border-radius: 0;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.22);
    padding-block-start: env(safe-area-inset-top, 0px);
  }

  .site-header.is-measuring {
    overflow: hidden;
  }

  .header-inner {
    inline-size: 100%;
    max-inline-size: min(1440px, 100%);
    min-inline-size: 0;
    margin-inline: auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    min-block-size: 62px;
    padding-block: 8px;
    padding-inline-start: max(clamp(16px, 2.5vw, 32px), env(safe-area-inset-left, 0px));
    padding-inline-end: max(clamp(16px, 2.5vw, 32px), env(safe-area-inset-right, 0px));
    box-sizing: border-box;
  }

  .site-header.is-measuring .header-inner {
    overflow: hidden;
  }

  .header-inner > * {
    flex-shrink: 0;
    white-space: nowrap;
  }

  .site-brand {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    min-block-size: max(40px, var(--target-size));
    padding-inline: 2px;
  }

  .brand-name {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 15.5px;
    font-weight: 700;
    color: #f8f8f8;
    letter-spacing: -0.025em;
  }

  .brand-dot {
    inline-size: 6px;
    block-size: 6px;
    border-radius: 50%;
    background: #f8f8f8;
    opacity: 0.9;
    flex-shrink: 0;
  }

  .site-brand:focus-visible,
  .menu-button:focus-visible,
  .site-menu a:focus-visible {
    outline: 2px solid #f2b94b;
    outline-offset: 2px;
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
    min-block-size: max(38px, var(--target-size));
    min-inline-size: max(38px, var(--target-size));
    padding: 0;
    border-radius: 999px;
    border: 1px solid #45454a;
    background: #343434;
    color: #f8f8f8;
    cursor: pointer;
    transition: background-color 0.16s ease, border-color 0.16s ease;
  }

  .menu-button:hover {
    background: #3e3e42;
    border-color: #55555b;
  }

  .site-menu {
    position: fixed;
    inset: auto;
    inset-block-start: calc(4.25rem + env(safe-area-inset-top, 0px));
    inset-block-start: anchor(--menu-button bottom);
    inset-inline-start: max(1rem, env(safe-area-inset-left, 0px));
    inline-size: min(84dvw, 19rem);
    max-inline-size: calc(100dvw - 2rem);
    block-size: fit-content;
    max-block-size: calc(100dvh - 5.5rem);
    margin: 0.6rem 0 0;
    padding: 8px;
    list-style: none;
    overflow: auto;
    border-radius: 22px;
    border: 1px solid #45454a;
    background: #2b2b2b;
    box-shadow: 0 20px 48px rgba(0, 0, 0, 0.56);
  }

  .site-menu::backdrop {
    background: rgba(18, 18, 18, 0.56);
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
    min-block-size: max(42px, var(--target-size));
    padding: 6px 14px;
    border-radius: 999px;
    color: #a3a3a3;
    text-decoration: none;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 13px;
    font-weight: 500;
    border: 1px solid transparent;
    transition: background-color 0.15s ease, color 0.15s ease;
  }

  .site-menu a:hover {
    background: #343434;
    color: #f8f8f8;
  }

  .site-menu a[aria-current='page'] {
    background: #f5f5f5;
    color: #222222;
    font-weight: 600;
    border-color: #f5f5f5;
  }

  .site-header.is-wide .menu-button {
    display: none;
  }

  .site-header.is-wide .site-menu {
    position: static;
    display: flex;
    align-items: center;
    gap: 2px;
    inline-size: auto;
    max-inline-size: none;
    block-size: auto;
    max-block-size: none;
    overflow: visible;
    margin: 0;
    padding: 4px;
    border-radius: 999px;
    border: 1px solid #363636;
    background: #262626;
    box-shadow: none;
  }

  .site-header.is-wide .site-menu::backdrop {
    display: none;
  }

  .site-header.is-wide .site-menu a {
    min-block-size: max(34px, var(--target-size));
    padding: 6px 15px;
    font-size: 12.5px;
    font-weight: 500;
    color: #a3a3a3;
    border-radius: 999px;
  }

  .site-header.is-wide .site-menu a:hover {
    background: rgba(255, 255, 255, 0.06);
    color: #f8f8f8;
  }

  .site-header.is-wide .site-menu a[aria-current='page'] {
    background: #f5f5f5;
    color: #222222;
    font-weight: 600;
    border-color: #f5f5f5;
  }

  .site-header.is-measuring * {
    transition: none !important;
  }

  .header-provenance {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-inline-start: auto;
  }

  .site-header.is-wide .header-provenance {
    margin-inline-start: 0;
  }

  .prov-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-block-size: 34px;
    padding: 0 12px;
    border-radius: 999px;
    background: #262626;
    border: 1px solid #363636;
    text-decoration: none;
    transition: background-color 0.16s ease, border-color 0.16s ease;
  }

  .prov-chip:hover {
    background: #2f2f33;
    border-color: #4a4a52;
  }

  .prov-chip:focus-visible {
    outline: 2px solid #f2b94b;
    outline-offset: 2px;
  }

  .prov-exchange {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.02em;
    color: #f5f5f5;
    line-height: 1;
  }

  .prov-official {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 11.5px;
    font-weight: 500;
    color: #9a9aa4;
    line-height: 1;
  }

  .prov-sep {
    inline-size: 1px;
    block-size: 12px;
    background: #3e3e44;
    margin-inline: 2px;
    flex-shrink: 0;
  }

  .prov-lag {
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 11px;
    font-weight: 600;
    color: #d4d4dc;
    line-height: 1;
    font-variant-numeric: tabular-nums;
  }

  @media (max-width: 720px) {
    .header-inner {
      gap: 10px;
      padding-block: 7px;
      padding-inline-start: max(14px, env(safe-area-inset-left, 0px));
      padding-inline-end: max(14px, env(safe-area-inset-right, 0px));
      min-block-size: 56px;
    }
    .brand-dot,
    .prov-official {
      display: none;
    }
    .prov-chip {
      min-block-size: 32px;
      padding: 0 10px;
      gap: 5px;
    }
  }

  @media (forced-colors: active) {
    .site-menu a[aria-current='page'] {
      border-color: Highlight;
      text-decoration: underline;
    }
  }

  /* ==================== CENTERED 1376px PAGE CONTAINER ==================== */
  .gl-page-container {
    inline-size: 100%;
    max-inline-size: 1440px;
    box-sizing: border-box;
    margin-inline: auto;
    padding-block-start: 18px;
    padding-block-end: max(44px, env(safe-area-inset-bottom, 0px));
    padding-inline-start: max(clamp(16px, 2.5vw, 32px), env(safe-area-inset-left, 0px));
    padding-inline-end: max(clamp(16px, 2.5vw, 32px), env(safe-area-inset-right, 0px));
  }

  /* ==================== ATELIER GRAPHITE PAGE HERO ==================== */
  :global(.page-hero) {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-block-end: 22px;
  }

  :global(.page-eyebrow) {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    color: #f2b94b;
    letter-spacing: 0.08em;
    margin: 0;
  }

  :global(.page-head-row) {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px 20px;
  }

  :global(.page-title-group) {
    display: flex;
    flex-direction: column;
    gap: 5px;
    min-inline-size: 0;
  }

  :global(.page-title) {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
    font-size: clamp(24px, 2.3vw, 31px);
    font-weight: 700;
    color: #f8f8f8;
    margin: 0;
    line-height: 1.18;
    letter-spacing: -0.028em;
  }

  :global(.page-subtitle) {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 13px;
    color: #8a8a91;
    margin: 0;
    line-height: 1.45;
  }

  :global(.controls-right) {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
  }

  /* ==================== ROUNDED PILL SEGMENTED CONTROLS ==================== */
  :global(.controls-right [role='group']),
  :global(.page-head-row [role='group']) {
    background: #2b2b2b !important;
    border: 1px solid #363636 !important;
    border-radius: 999px !important;
    padding: 4px !important;
    height: auto !important;
    min-block-size: max(40px, var(--target-size));
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.16) !important;
    margin-bottom: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 2px !important;
  }

  :global(.controls-right [role='group'] button),
  :global(.page-head-row [role='group'] button) {
    min-block-size: max(32px, var(--target-size));
    padding: 6px 14px !important;
    border-radius: 999px !important;
    border: 0 !important;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    background-color: transparent !important;
    color: #a3a3a3 !important;
    transition: background-color 0.15s ease, color 0.15s ease;
  }

  :global(.controls-right [role='group'] button:hover),
  :global(.page-head-row [role='group'] button:hover) {
    background-color: rgba(255, 255, 255, 0.06) !important;
    color: #f8f8f8 !important;
  }

  :global(.controls-right [role='group'] button.text-primary),
  :global(.controls-right [role='group'] button.bg-base-200),
  :global(.page-head-row [role='group'] button.text-primary),
  :global(.page-head-row [role='group'] button.bg-base-200) {
    background-color: #f5f5f5 !important;
    color: #222222 !important;
    font-weight: 600 !important;
  }

  :global(.controls-right .inline-block),
  :global(.page-head-row .inline-block) {
    margin: 0 !important;
  }

  /* ==================== AIRY ROUNDED KPI & LARGE 2x2 GRIDS ==================== */
  :global(.kpi-grid-4) {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
    margin-block-end: 22px;
  }

  :global(.terminal-grid-2) {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 20px;
    margin-block-end: 20px;
    align-items: stretch;
  }

  :global(.terminal-grid-1) {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 20px;
    margin-block-end: 20px;
  }

  /* ==================== ATELIER GRAPHITE ROUNDED CARDS ==================== */
  :global(.terminal-panel) {
    display: flex;
    flex-direction: column;
    inline-size: 100%;
    max-inline-size: 100%;
    box-sizing: border-box;
    background: #2b2b2b;
    border: 1px solid #363636;
    border-radius: 28px;
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.20);
    padding: 24px 26px;
    min-inline-size: 0;
    --base-100: #2b2b2b;
    --twc-base-100: 0 0% 17%;
  }

  :global(.terminal-panel .chart-container),
  :global(.terminal-panel .chart-container > div),
  :global(.terminal-panel .bg-base-100),
  :global(.terminal-panel canvas) {
    background-color: transparent !important;
  }

  :global(.terminal-panel .chart-container) {
    inline-size: 100% !important;
    max-inline-size: 100% !important;
    min-inline-size: 0 !important;
  }

  :global(.terminal-panel-title) {
    display: flex;
    align-items: baseline;
    gap: 8px;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
    font-size: 15.5px;
    font-weight: 600;
    letter-spacing: -0.015em;
    color: #f8f8f8;
    margin: 0 0 4px 0;
    line-height: 1.3;
  }

  :global(.terminal-panel-sub) {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 12.5px;
    color: #8a8a91;
    margin: 0 0 14px 0;
    line-height: 1.45;
  }

  /* ==================== STANDARD EVIDENCE TABLES (TUFTE GRAPHITE) ==================== */
  :global(.terminal-panel:not(.exec-explorer):not(.monthly-panel):not(.heatmap-panel):not(.daily-panel):not(.annual-ibov-panel) .table-container),
  :global(.terminal-panel:not(.exec-explorer):not(.monthly-panel):not(.heatmap-panel):not(.daily-panel):not(.annual-ibov-panel) .overflow-auto),
  :global(.terminal-panel:not(.exec-explorer):not(.monthly-panel):not(.heatmap-panel):not(.daily-panel):not(.annual-ibov-panel) .overflow-x-auto) {
    max-inline-size: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    background: transparent !important;
    border-color: #363636 !important;
  }

  :global(.terminal-panel:not(.exec-explorer):not(.monthly-panel):not(.heatmap-panel):not(.daily-panel):not(.annual-ibov-panel) table) {
    background: transparent !important;
    border-collapse: separate;
    border-spacing: 0;
    inline-size: 100%;
  }

  :global(.terminal-panel:not(.exec-explorer):not(.monthly-panel):not(.heatmap-panel):not(.daily-panel):not(.annual-ibov-panel) thead th) {
    position: sticky;
    inset-block-start: 0;
    z-index: 1;
    background: #2b2b2b !important;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
    font-size: 10.5px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #767676 !important;
    border-bottom: 1px solid #3a3a3f !important;
    padding-block: 10px !important;
    white-space: nowrap;
  }

  :global(.terminal-panel:not(.exec-explorer):not(.monthly-panel):not(.heatmap-panel):not(.daily-panel):not(.annual-ibov-panel) tbody td) {
    font-size: 12px !important;
    color: #e5e5e5 !important;
    border-bottom: 1px solid #343438 !important;
    padding-block: 10px !important;
    white-space: nowrap;
    background: transparent !important;
  }

  :global(.terminal-panel:not(.exec-explorer):not(.monthly-panel):not(.heatmap-panel):not(.daily-panel):not(.annual-ibov-panel) tbody tr:hover td) {
    background: #323236 !important;
  }

  :global(.terminal-panel:not(.exec-explorer):not(.monthly-panel):not(.heatmap-panel):not(.daily-panel):not(.annual-ibov-panel) tbody tr:last-child td) {
    border-bottom: 0 !important;
  }

  :global(.terminal-panel:not(.exec-explorer):not(.monthly-panel):not(.heatmap-panel):not(.daily-panel):not(.annual-ibov-panel) .pagination),
  :global(.terminal-panel:not(.exec-explorer):not(.monthly-panel):not(.heatmap-panel):not(.daily-panel):not(.annual-ibov-panel) button),
  :global(.terminal-panel:not(.exec-explorer):not(.monthly-panel):not(.heatmap-panel):not(.daily-panel):not(.annual-ibov-panel) input) {
    color: #a3a3a3;
    border-color: #3a3a3f;
  }

  /* ==================== EDITORIAL FOOTER (BLOOMBERG-INSPIRED) ==================== */
  .gl-footer {
    margin-block-start: 48px;
    padding: 8px 0 4px;
    background: transparent;
    border: 0;
    border-radius: 0;
    display: flex;
    flex-direction: column;
    gap: 16px;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  }

  .footer-brand-row {
    display: flex;
    justify-content: flex-end;
    align-items: center;
  }

  .footer-brand {
    display: inline-flex;
    align-items: center;
    gap: 9px;
    text-decoration: none;
    color: #f5f5f5;
    transition: opacity 0.16s ease;
  }

  .footer-brand:hover {
    opacity: 0.85;
  }

  .footer-brand:focus-visible {
    outline: 2px solid #f2b94b;
    outline-offset: 4px;
    border-radius: 6px;
  }

  .footer-brand-name {
    font-size: 17px;
    font-weight: 700;
    letter-spacing: -0.025em;
    color: #f5f5f5;
  }

  .footer-rule {
    inline-size: 100%;
    block-size: 1px;
    background: #35353a;
  }

  .footer-meta-row {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 6px 20px;
  }

  .footer-legal {
    margin: 0;
    font-size: 12px;
    color: #8a8a93;
    line-height: 1.5;
  }

  .footer-sla {
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 11px;
    color: #6e6e76;
    white-space: nowrap;
  }

  .footer-nav {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px 24px;
  }

  .footer-nav a {
    font-size: 12.5px;
    font-weight: 500;
    color: #c4c4cc;
    text-decoration: none;
    transition: color 0.15s ease;
  }

  .footer-nav a:hover,
  .footer-nav a[aria-current='page'] {
    color: #f8f8f8;
  }

  .footer-nav a:focus-visible {
    outline: 2px solid #f2b94b;
    outline-offset: 3px;
    border-radius: 4px;
  }

  .footer-methodology {
    margin: 0;
    max-inline-size: 92ch;
    font-size: 11.5px;
    color: #6f6f78;
    line-height: 1.55;
  }

  /* ==================== RESPONSIVENESS ==================== */
  @media (max-width: 960px) {
    :global(.terminal-grid-2) {
      grid-template-columns: minmax(0, 1fr);
    }
    :global(.kpi-grid-4) {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }

  @media (max-width: 640px) {
    .gl-page-container {
      padding-block-start: 14px;
      padding-inline-start: max(14px, env(safe-area-inset-left, 0px));
      padding-inline-end: max(14px, env(safe-area-inset-right, 0px));
    }

    :global(.kpi-grid-4) {
      gap: 12px;
      margin-block-end: 16px;
    }

    :global(.terminal-panel) {
      border-radius: 22px;
      padding: 18px 16px;
    }

    :global(.terminal-grid-2),
    :global(.terminal-grid-1) {
      gap: 16px;
      margin-block-end: 16px;
    }

    :global(.page-head-row) {
      flex-direction: column;
      align-items: stretch;
      gap: 12px;
    }

    :global(.controls-right) {
      inline-size: 100%;
      gap: 10px;
    }

    :global(.controls-right .inline-block),
    :global(.page-head-row .inline-block) {
      inline-size: 100%;
      display: block !important;
    }

    :global(.controls-right [role='group']),
    :global(.page-head-row [role='group']) {
      display: flex !important;
      flex-wrap: wrap !important;
      inline-size: 100% !important;
      box-sizing: border-box;
    }

    :global(.controls-right [role='group'] button),
    :global(.page-head-row [role='group'] button) {
      flex: 1 1 auto;
      min-block-size: max(38px, var(--target-size));
      padding: 6px 10px !important;
      font-size: 12px !important;
      text-align: center;
      justify-content: center;
    }

    .gl-footer {
      margin-block-start: 36px;
      gap: 14px;
    }

    .footer-brand-row {
      justify-content: flex-start;
    }

    .footer-sla {
      white-space: normal;
    }

    .footer-nav {
      gap: 10px 18px;
    }
  }

  @media (max-width: 350px) {
    :global(.kpi-grid-4) {
      grid-template-columns: minmax(0, 1fr);
    }
  }
</style>
