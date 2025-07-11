<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { TrendingUp, TrendingDown, Minus, MoreHorizontal } from 'lucide-svelte';
  import { tweened } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';
  import { onMount } from 'svelte';

  export let title: string;
  export let value: string | number;
  export let subtitle: string = '';
  export let trend: 'up' | 'down' | 'neutral' | null = null;
  export let trendValue: string = '';
  export let icon: any = null;
  export let color: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' = 'primary';
  export let loading: boolean = false;
  export let clickable: boolean = false;

  const dispatch = createEventDispatcher();

  // Animated counter for numeric values
  const animatedValue = tweened(0, {
    duration: 1200,
    easing: cubicOut
  });

  let mounted = false;

  onMount(() => {
    mounted = true;
    if (typeof value === 'number') {
      animatedValue.set(value);
    }
  });

  $: if (mounted && typeof value === 'number') {
    animatedValue.set(value);
  }

  $: displayValue = typeof value === 'number' && mounted
    ? Math.round($animatedValue).toLocaleString()
    : typeof value === 'number'
      ? value.toLocaleString()
      : value;

  function handleClick() {
    if (clickable) {
      dispatch('click');
    }
  }

  function getTrendIcon() {
    switch (trend) {
      case 'up': return TrendingUp;
      case 'down': return TrendingDown;
      default: return Minus;
    }
  }

  function getTrendColor() {
    switch (trend) {
      case 'up': return 'text-emerald-600';
      case 'down': return 'text-red-600';
      default: return 'text-gray-500';
    }
  }

  function getColorClasses() {
    const colors = {
      primary: 'border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100',
      secondary: 'border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50 hover:from-purple-100 hover:to-pink-100',
      success: 'border-emerald-200 bg-gradient-to-br from-emerald-50 to-green-50 hover:from-emerald-100 hover:to-green-100',
      warning: 'border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50 hover:from-amber-100 hover:to-orange-100',
      error: 'border-red-200 bg-gradient-to-br from-red-50 to-rose-50 hover:from-red-100 hover:to-rose-100',
      info: 'border-cyan-200 bg-gradient-to-br from-cyan-50 to-sky-50 hover:from-cyan-100 hover:to-sky-100'
    };
    return colors[color];
  }

  function getIconColor() {
    const colors = {
      primary: 'text-blue-600',
      secondary: 'text-purple-600',
      success: 'text-emerald-600',
      warning: 'text-amber-600',
      error: 'text-red-600',
      info: 'text-cyan-600'
    };
    return colors[color];
  }

  function getValueColor() {
    const colors = {
      primary: 'text-blue-900',
      secondary: 'text-purple-900',
      success: 'text-emerald-900',
      warning: 'text-amber-900',
      error: 'text-red-900',
      info: 'text-cyan-900'
    };
    return colors[color];
  }
</script>

{#if clickable}
  <div
    class="relative overflow-hidden rounded-xl border {getColorClasses()} p-6 transition-all duration-300 hover:shadow-lg hover:shadow-{color}-100/50 cursor-pointer hover:scale-[1.02]"
    on:click={handleClick}
    on:keydown={(e) => e.key === 'Enter' && handleClick()}
    role="button"
    tabindex="0"
  >
    <!-- Background pattern -->
    <div class="absolute top-0 right-0 w-20 h-20 opacity-5">
      <svg viewBox="0 0 24 24" fill="currentColor" class="w-full h-full {getIconColor()}">
        <path d="M12 2L2 7v10c0 5.55 3.84 9.739 9 9.739s9-4.189 9-9.739V7l-10-5z"/>
      </svg>
    </div>

    {#if loading}
      <!-- Loading state -->
      <div class="animate-pulse">
        <div class="flex items-center justify-between mb-4">
          <div class="h-4 bg-gray-300 rounded w-1/3"></div>
          <div class="h-4 bg-gray-300 rounded w-4"></div>
        </div>
        <div class="h-8 bg-gray-300 rounded w-1/2 mb-2"></div>
        <div class="h-3 bg-gray-300 rounded w-1/4"></div>
      </div>
    {:else}
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center space-x-2">
          {#if icon}
            <div class="p-2 rounded-lg bg-white/80 shadow-sm">
              <svelte:component this={icon} class="w-4 h-4 {getIconColor()}" />
            </div>
          {/if}
          <h3 class="text-sm font-semibold text-gray-700 uppercase tracking-wide">{title}</h3>
        </div>

        <button
          class="p-1 rounded-md hover:bg-white/60 transition-colors opacity-0 group-hover:opacity-100"
          on:click|stopPropagation={() => dispatch('menu')}
          aria-label="More options"
        >
          <MoreHorizontal class="w-4 h-4 text-gray-500" />
        </button>
      </div>

      <!-- Main value -->
      <div class="mb-3">
        <div class="text-3xl font-bold {getValueColor()} tracking-tight">
          {displayValue}
        </div>
      </div>

      <!-- Subtitle and trend -->
      <div class="flex items-center justify-between">
        <div class="text-sm text-gray-600">
          {subtitle}
        </div>

        {#if trend && trendValue}
          <div class="flex items-center space-x-1 {getTrendColor()}">
            <svelte:component this={getTrendIcon()} class="w-3 h-3" />
            <span class="text-xs font-medium">{trendValue}</span>
          </div>
        {/if}
      </div>
    {/if}
  </div>
{:else}
  <div
    class="relative overflow-hidden rounded-xl border {getColorClasses()} p-6 transition-all duration-300 hover:shadow-lg hover:shadow-{color}-100/50"
  >
    <!-- Background pattern -->
    <div class="absolute top-0 right-0 w-20 h-20 opacity-5">
      <svg viewBox="0 0 24 24" fill="currentColor" class="w-full h-full {getIconColor()}">
        <path d="M12 2L2 7v10c0 5.55 3.84 9.739 9 9.739s9-4.189 9-9.739V7l-10-5z"/>
      </svg>
    </div>

    {#if loading}
      <!-- Loading state -->
      <div class="animate-pulse">
        <div class="flex items-center justify-between mb-4">
          <div class="h-4 bg-gray-300 rounded w-1/3"></div>
          <div class="h-4 bg-gray-300 rounded w-4"></div>
        </div>
        <div class="h-8 bg-gray-300 rounded w-1/2 mb-2"></div>
        <div class="h-3 bg-gray-300 rounded w-1/4"></div>
      </div>
    {:else}
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center space-x-2">
          {#if icon}
            <div class="p-2 rounded-lg bg-white/80 shadow-sm">
              <svelte:component this={icon} class="w-4 h-4 {getIconColor()}" />
            </div>
          {/if}
          <h3 class="text-sm font-semibold text-gray-700 uppercase tracking-wide">{title}</h3>
        </div>
      </div>

      <!-- Main value -->
      <div class="mb-3">
        <div class="text-3xl font-bold {getValueColor()} tracking-tight">
          {displayValue}
        </div>
      </div>

      <!-- Subtitle and trend -->
      <div class="flex items-center justify-between">
        <div class="text-sm text-gray-600">
          {subtitle}
        </div>

        {#if trend && trendValue}
          <div class="flex items-center space-x-1 {getTrendColor()}">
            <svelte:component this={getTrendIcon()} class="w-3 h-3" />
            <span class="text-xs font-medium">{trendValue}</span>
          </div>
        {/if}
      </div>
    {/if}
  </div>
{/if}
