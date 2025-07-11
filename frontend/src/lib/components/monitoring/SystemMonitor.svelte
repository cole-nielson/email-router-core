<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import {
    Activity,
    CheckCircle,
    AlertCircle,
    Clock,
    Mail,
    Users,
    Server,
    Database,
    Zap,
    AlertTriangle,
    Wifi
  } from 'lucide-svelte';
  import { services } from '$lib/services';
  import type { SystemHealth, ComponentStatus } from '$lib/types/dashboard';

  // State
  let systemHealth: SystemHealth | null = null;
  let isLoading = true;
  let error = '';
  let refreshInterval: any;

  // Health data
  let components: Record<string, ComponentStatus> = {};
  let overallStatus: 'healthy' | 'degraded' | 'down' = 'healthy';
  let lastUpdated = '';

  async function fetchHealthData() {
    try {
      error = '';
      const healthResponse = await services.system.getDetailedHealth();

      if (healthResponse.success && healthResponse.data) {
        systemHealth = healthResponse.data;
        components = healthResponse.data.components;
        overallStatus = healthResponse.data.status;
        lastUpdated = new Date().toLocaleTimeString();
      } else {
        error = healthResponse.error || 'Failed to fetch health data';
      }
    } catch (err) {
      console.error('Error fetching health data:', err);
      error = 'Network error occurred';
    } finally {
      isLoading = false;
    }
  }
  function getComponentStatusIcon(status: string) {
    switch (status) {
      case 'healthy':
        return CheckCircle;
      case 'warning':
        return AlertTriangle;
      case 'error':
        return AlertCircle;
      default:
        return Clock;
    }
  }

  function getComponentStatusColor(status: string) {
    switch (status) {
      case 'healthy':
        return 'text-green-500';
      case 'warning':
        return 'text-yellow-500';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  }

  function getComponentIcon(componentName: string) {
    switch (componentName) {
      case 'api_server':
        return Server;
      case 'database':
        return Database;
      case 'ai_classifier':
        return Zap;
      case 'email_service':
        return Mail;
      case 'webhooks':
        return Wifi;
      case 'cache':
        return Activity;
      default:
        return Server;
    }
  }

  function getOverallStatusColor(status: string) {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'down':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  }

  function formatUptime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  }

  function formatNumber(num: number): string {
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'k';
    }
    return num.toString();
  }

  onMount(() => {
    // Initial fetch
    fetchHealthData();

    // Set up auto-refresh every 30 seconds
    refreshInterval = setInterval(fetchHealthData, 30000);
  });

  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });
</script>

<div class="space-y-6">
  <!-- System Status Header -->
  <div class="bg-white rounded-lg shadow p-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="flex-shrink-0">
          {#if isLoading}
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          {:else if error}
            <AlertCircle class="h-8 w-8 text-red-500" />
          {:else}
            <svelte:component this={getComponentStatusIcon(overallStatus)} class="h-8 w-8 {getComponentStatusColor(overallStatus)}" />
          {/if}
        </div>
        <div>
          <h2 class="text-lg font-semibold text-gray-900">System Health</h2>
          <p class="text-sm text-gray-500">
            {#if isLoading}
              Checking system status...
            {:else if error}
              {error}
            {:else}
              Last updated: {lastUpdated}
            {/if}
          </p>
        </div>
      </div>

      {#if !isLoading && !error}
        <div class="flex items-center space-x-2">
          <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border {getOverallStatusColor(overallStatus)}">
            {overallStatus.charAt(0).toUpperCase() + overallStatus.slice(1)}
          </span>
          <button
            on:click={fetchHealthData}
            class="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            title="Refresh"
          >
            <Activity class="h-4 w-4" />
          </button>
        </div>
      {/if}
    </div>
  </div>

  <!-- Performance Metrics -->
  {#if systemHealth && !isLoading}
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- Uptime -->
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <Clock class="h-8 w-8 text-blue-500" />
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">
                  System Uptime
                </dt>
                <dd class="text-lg font-medium text-gray-900">
                  {systemHealth.uptime_percentage.toFixed(1)}%
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <!-- Response Time -->
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <Zap class="h-8 w-8 text-yellow-500" />
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">
                  Avg Response Time
                </dt>
                <dd class="text-lg font-medium text-gray-900">
                  {systemHealth.performance.avg_response_time}ms
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <!-- Requests Per Minute -->
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <Activity class="h-8 w-8 text-green-500" />
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">
                  Requests/Min
                </dt>
                <dd class="text-lg font-medium text-gray-900">
                  {systemHealth.performance.requests_per_minute}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}


  <!-- Component Status -->
  <div class="bg-white shadow rounded-lg">
    <div class="px-4 py-5 sm:p-6">
      <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
        System Components
      </h3>

      {#if isLoading}
        <div class="animate-pulse">
          <div class="space-y-3">
            {#each Array(5) as _}
              <div class="h-4 bg-gray-200 rounded w-3/4"></div>
            {/each}
          </div>
        </div>
      {:else if error}
        <div class="text-center py-8">
          <AlertCircle class="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p class="text-gray-600">{error}</p>
          <button
            on:click={fetchHealthData}
            class="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {#each Object.entries(components) as [name, component]}
            {@const StatusIcon = getComponentStatusIcon(component.status)}
            {@const ComponentIcon = getComponentIcon(name)}

            <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <div class="flex items-center">
                <div class="flex items-center justify-center w-10 h-10 rounded-lg bg-gray-100 mr-3">
                  <ComponentIcon class="h-5 w-5 text-gray-600" />
                </div>
                <div>
                  <p class="text-sm font-medium text-gray-900">
                    {name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </p>
                  <p class="text-xs text-gray-500">
                    Last check: {component.last_check ? new Date(component.last_check).toLocaleTimeString() : 'Unknown'}
                  </p>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                {#if component.response_time}
                  <span class="text-xs text-gray-500">{component.response_time}ms</span>
                {/if}
                <div class="flex items-center">
                  <StatusIcon class="h-4 w-4 {getComponentStatusColor(component.status)} mr-1" />
                  <span class="text-sm font-medium capitalize {getComponentStatusColor(component.status)}">
                    {component.status}
                  </span>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>

  <!-- Auto-refresh indicator -->
  {#if !isLoading && !error}
    <div class="text-center text-sm text-gray-500">
      <div class="flex items-center justify-center space-x-2">
        <div class="animate-pulse h-2 w-2 bg-green-500 rounded-full"></div>
        <span>Auto-refreshing every 30 seconds</span>
      </div>
    </div>
  {/if}
</div>

<style>
  .animate-spin {
    animation: spin 1s linear infinite;
  }

  .animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: .5;
    }
  }
</style>
