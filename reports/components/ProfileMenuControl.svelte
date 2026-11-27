<script>
  import { onMount, tick } from 'svelte';
  import { get } from 'svelte/store';
  import { getInputContext } from '@evidence-dev/sdk/utils/svelte';

  export let name = 'perfil_foco';
  export let label = 'Perfil';
  export let defaultValue = 'pessoa_fisica';
  export let options = [
    { value: 'pessoa_fisica', label: 'Pessoa Física' },
    { value: 'institucional', label: 'Institucional' },
    { value: 'estrangeiro', label: 'Estrangeiro' },
    { value: 'instituicoes_financeiras', label: 'Inst. Financeiras' },
    { value: 'outros', label: 'Outros' }
  ];

  const inputs = getInputContext();

  function isValidOption(val) {
    return typeof val === 'string' && options.some((opt) => opt.value === val);
  }

  function resolveFallbackValue() {
    return isValidOption(defaultValue) ? defaultValue : (options[0]?.value ?? '');
  }

  $: fallbackValue = isValidOption(defaultValue) ? defaultValue : (options[0]?.value ?? '');

  // Ensure SSR prerendering starts with a valid default option before reactive updates flush.
  if (inputs && !isValidOption(get(inputs)?.[name])) {
    const initialFallback = resolveFallbackValue();
    if (initialFallback) {
      $inputs[name] = initialFallback;
    }
  }

  $: if (inputs && fallbackValue && !isValidOption($inputs?.[name])) {
    $inputs[name] = fallbackValue;
  }

  let currentValue = resolveFallbackValue();
  $: currentValue = isValidOption($inputs?.[name]) ? $inputs[name] : fallbackValue;
  $: currentIndex = Math.max(
    0,
    options.findIndex((opt) => opt.value === currentValue)
  );
  $: currentOption = options[currentIndex] || options[0];

  let open = false;
  let rootEl;
  let triggerEl;
  let desktopTabEls = [];
  let mobileOptionEls = [];

  function closeMenu(restoreFocus = false) {
    if (!open) return;
    open = false;
    if (restoreFocus) {
      tick().then(() => triggerEl?.focus());
    }
  }

  function selectDesktopOption(val) {
    if (inputs) {
      $inputs[name] = val;
    }
  }

  function selectMobileOption(val, restoreFocus = true) {
    if (inputs) {
      $inputs[name] = val;
    }
    closeMenu(restoreFocus);
  }

  async function openMenuAndFocus(index) {
    open = true;
    await tick();
    const bounded = Math.max(0, Math.min(options.length - 1, index));
    mobileOptionEls[bounded]?.focus();
  }

  function toggleMenu() {
    if (open) {
      closeMenu(false);
    } else {
      openMenuAndFocus(currentIndex);
    }
  }

  function handleDesktopKeydown(event, idx) {
    let nextIdx = null;
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      nextIdx = (idx + 1) % options.length;
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      nextIdx = (idx - 1 + options.length) % options.length;
    } else if (event.key === 'Home') {
      nextIdx = 0;
    } else if (event.key === 'End') {
      nextIdx = options.length - 1;
    }

    if (nextIdx === null) return;
    event.preventDefault();
    const targetOpt = options[nextIdx];
    if (targetOpt) {
      selectDesktopOption(targetOpt.value);
      desktopTabEls[nextIdx]?.focus();
    }
  }

  function handleTriggerKeydown(event) {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      openMenuAndFocus(open ? (currentIndex + 1) % options.length : currentIndex);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      openMenuAndFocus(
        open ? (currentIndex - 1 + options.length) % options.length : options.length - 1
      );
    } else if (event.key === 'Escape' && open) {
      event.preventDefault();
      closeMenu(true);
    }
  }

  function handleOptionKeydown(event, idx) {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      mobileOptionEls[(idx + 1) % options.length]?.focus();
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      mobileOptionEls[(idx - 1 + options.length) % options.length]?.focus();
    } else if (event.key === 'Home') {
      event.preventDefault();
      mobileOptionEls[0]?.focus();
    } else if (event.key === 'End') {
      event.preventDefault();
      mobileOptionEls[options.length - 1]?.focus();
    } else if (event.key === 'Escape') {
      event.preventDefault();
      closeMenu(true);
    } else if (event.key === 'Tab') {
      closeMenu(false);
    }
  }

  function handleGlobalKeydown(event) {
    if (event.key === 'Escape' && open) {
      event.preventDefault();
      closeMenu(true);
    }
  }

  onMount(() => {
    const handlePointerDown = (event) => {
      if (open && rootEl && !rootEl.contains(event.target)) {
        closeMenu(false);
      }
    };

    document.addEventListener('pointerdown', handlePointerDown);
    document.addEventListener('keydown', handleGlobalKeydown);

    return () => {
      document.removeEventListener('pointerdown', handlePointerDown);
      document.removeEventListener('keydown', handleGlobalKeydown);
    };
  });
</script>

<div class="pmc-root" bind:this={rootEl}>
  <div class="pmc-desktop-bar" role="radiogroup" aria-label={label}>
    {#each options as opt, idx (opt.value)}
      <button
        type="button"
        role="radio"
        aria-checked={currentValue === opt.value}
        tabindex={currentValue === opt.value ? 0 : -1}
        class="pmc-tab"
        class:is-active={currentValue === opt.value}
        bind:this={desktopTabEls[idx]}
        on:click={() => selectDesktopOption(opt.value)}
        on:keydown={(e) => handleDesktopKeydown(e, idx)}
      >
        {opt.label}
      </button>
    {/each}
  </div>

  <div class="pmc-mobile-wrap">
    <button
      type="button"
      class="pmc-trigger"
      class:is-open={open}
      aria-haspopup="listbox"
      aria-expanded={open}
      aria-label={`${label}: ${currentOption?.label ?? ''}`}
      bind:this={triggerEl}
      on:click={toggleMenu}
      on:keydown={handleTriggerKeydown}
    >
      <span class="pmc-trigger-left">
        <span class="pmc-label">{label}</span>
        <span class="pmc-sep" aria-hidden="true"></span>
        <span class="pmc-current">{currentOption?.label ?? ''}</span>
      </span>
      <svg
        class="pmc-chevron"
        class:is-open={open}
        width="15"
        height="15"
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M6 9l6 6 6-6"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </button>

    {#if open}
      <div class="pmc-dropdown" role="listbox" aria-label={label}>
        {#each options as opt, idx (opt.value)}
          <button
            type="button"
            role="option"
            aria-selected={currentValue === opt.value}
            class="pmc-option"
            class:is-active={currentValue === opt.value}
            bind:this={mobileOptionEls[idx]}
            on:click={() => selectMobileOption(opt.value, true)}
            on:keydown={(e) => handleOptionKeydown(e, idx)}
          >
            <span>{opt.label}</span>
            {#if currentValue === opt.value}
              <span class="pmc-dot" aria-hidden="true"></span>
            {/if}
          </button>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  .pmc-root {
    display: inline-flex;
    align-items: center;
    max-inline-size: 100%;
    position: relative;
  }

  .pmc-desktop-bar {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    padding: 4px;
    min-block-size: max(40px, var(--target-size, 40px));
    background: #2b2b2b;
    border: 1px solid #363636;
    border-radius: 999px;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.16);
    box-sizing: border-box;
  }

  .pmc-tab {
    appearance: none;
    min-block-size: max(32px, var(--target-size, 32px));
    padding: 6px 14px;
    border: 0;
    border-radius: 999px;
    background: transparent;
    color: #a3a3a3;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 12px;
    font-weight: 500;
    white-space: nowrap;
    cursor: pointer;
    transition: background-color 0.15s ease, color 0.15s ease;
  }

  .pmc-tab:hover {
    background: rgba(255, 255, 255, 0.06);
    color: #f8f8f8;
  }

  .pmc-tab.is-active {
    background: #f5f5f5;
    color: #222222;
    font-weight: 600;
  }

  .pmc-tab:focus-visible,
  .pmc-trigger:focus-visible,
  .pmc-option:focus-visible {
    outline: 2px solid #f2b94b;
    outline-offset: 2px;
  }

  .pmc-mobile-wrap {
    display: none;
    position: relative;
    inline-size: 100%;
  }

  .pmc-trigger {
    appearance: none;
    inline-size: 100%;
    min-block-size: max(42px, var(--target-size, 42px));
    padding: 0 16px;
    border-radius: 999px;
    border: 1px solid #363636;
    background: #2b2b2b;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.16);
    color: #f8f8f8;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    cursor: pointer;
    box-sizing: border-box;
    transition: border-color 0.15s ease, background-color 0.15s ease;
  }

  .pmc-trigger:hover,
  .pmc-trigger.is-open {
    border-color: #4c4c54;
    background: #303034;
  }

  .pmc-trigger-left {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    min-inline-size: 0;
  }

  .pmc-label {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #8a8a91;
    white-space: nowrap;
  }

  .pmc-sep {
    inline-size: 1px;
    block-size: 14px;
    background: #44444a;
    flex-shrink: 0;
  }

  .pmc-current {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: #f8f8f8;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .pmc-chevron {
    color: #a3a3a3;
    flex-shrink: 0;
    transition: transform 0.18s ease, color 0.15s ease;
  }

  .pmc-chevron.is-open {
    transform: rotate(180deg);
    color: #f2b94b;
  }

  .pmc-dropdown {
    position: absolute;
    inset-block-start: calc(100% + 8px);
    inset-inline: 0;
    z-index: 60;
    padding: 6px;
    border-radius: 18px;
    border: 1px solid #3a3a40;
    background: #262629;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.48);
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .pmc-option {
    appearance: none;
    inline-size: 100%;
    min-block-size: 40px;
    padding: 8px 14px;
    border: 0;
    border-radius: 12px;
    background: transparent;
    color: #c7c7cc;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 13px;
    font-weight: 500;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    text-align: left;
    cursor: pointer;
    transition: background-color 0.14s ease, color 0.14s ease;
  }

  .pmc-option:hover {
    background: rgba(255, 255, 255, 0.06);
    color: #f8f8f8;
  }

  .pmc-option.is-active {
    background: #34343a;
    color: #f8f8f8;
    font-weight: 600;
  }

  .pmc-dot {
    inline-size: 7px;
    block-size: 7px;
    border-radius: 50%;
    background: #f2b94b;
    flex-shrink: 0;
  }

  @media (max-width: 900px) {
    .pmc-root {
      min-inline-size: 240px;
    }

    .pmc-desktop-bar {
      display: none;
    }

    .pmc-mobile-wrap {
      display: block;
    }
  }

  @media (max-width: 640px) {
    .pmc-root {
      display: block;
      inline-size: 100%;
      min-inline-size: 0;
    }
  }
</style>
