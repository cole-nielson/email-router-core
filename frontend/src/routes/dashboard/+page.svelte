<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { currentUser, authService } from '$lib/stores/authStore';
  import AuthGuard from '$lib/components/auth/AuthGuard.svelte';
  import SystemMonitor from '$lib/components/monitoring/SystemMonitor.svelte';
  import RealtimeMetrics from '$lib/components/realtime/RealtimeMetrics.svelte';
  import RealtimeActivityFeed from '$lib/components/realtime/RealtimeActivityFeed.svelte';
  import ConnectionStatus from '$lib/components/realtime/ConnectionStatus.svelte';
  import RealtimeAlerts from '$lib/components/realtime/RealtimeAlerts.svelte';
  import { services } from '$lib/services';
  import { websocketStore, realtimeMetrics } from '$lib/stores/websocket';
  import type { DashboardMetrics, ActivityItem } from '$lib/types/dashboard';
  import {
    User,
    Shield,
    Clock,
    LogOut,
    Settings,
    Bell,
    Mail,
    BarChart3,
    ChevronDown,
    ChevronUp,
    Activity,
    Zap,
    CheckCircle,
    AlertTriangle,
    TrendingUp
  } from 'lucide-svelte';

  // State
  let showMonitoring = false;

  // Handle logout
  async function handleLogout() {
    await authService.logout();
  }

  // Initialize WebSocket connection on mount
  onMount(() => {
    if ($currentUser?.client_id) {
      // WebSocket will auto-connect via the websocket store
      websocketStore.connect($currentUser.client_id);
    }
  });

  // Toggle monitoring section
  function toggleMonitoring() {
    showMonitoring = !showMonitoring;
  }

  // Get role badge color
  function getRoleBadgeColor(role: string): string {
    switch (role) {
      case 'super_admin':
        return 'bg-purple-100 text-purple-800';
      case 'client_admin':
        return 'bg-blue-100 text-blue-800';
      case 'client_user':
        return 'bg-green-100 text-green-800';
      case 'api_user':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }

  // Format date
  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString();
  }
</script>

<svelte:head>
  <title>Dashboard - Email Router</title>
  <meta name="description" content="Email Router dashboard for managing AI-powered email automation." />
</svelte:head>

<AuthGuard requireAuth={true}>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <!-- Logo and title -->
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <Mail class="h-4 w-4 text-white" />
              </div>
            </div>
            <div class="ml-4">
              <h1 class="text-xl font-semibold text-gray-900">Email Router</h1>
            </div>
          </div>

          <!-- User menu -->
          <div class="flex items-center space-x-4">
            {#if $currentUser}
              <div class="flex items-center space-x-3">
                <!-- Real-time connection status -->
                <ConnectionStatus variant="badge" />
                <span class="text-sm text-gray-700">
                  Welcome, {$currentUser.full_name}
                </span>
                <button
                  on:click={handleLogout}
                  class="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <LogOut class="h-4 w-4 mr-2" />
                  Logout
                </button>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </header>

    <!-- Main content -->
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div class="px-4 py-6 sm:px-0">
        <!-- Welcome section -->
        <div class="bg-white overflow-hidden shadow rounded-lg mb-6">
          <div class="px-4 py-5 sm:p-6">
            <h2 class="text-lg leading-6 font-medium text-gray-900 mb-4">
              {#if $currentUser?.client_id}
                Email Router Dashboard - {$currentUser.client_id}
              {:else}
                Email Router System Dashboard
              {/if}
            </h2>
            <p class="text-sm text-gray-600">
              Real-time monitoring and analytics for your AI-powered email automation platform.
            </p>
          </div>
        </div>

        <!-- Real-time Metrics -->
        <RealtimeMetrics
          clientId={$currentUser?.client_id}
          showConnectionStatus={false}
        />

        <!-- Dashboard Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <!-- Real-time Activity Feed -->
          <div class="lg:col-span-2">
            <RealtimeActivityFeed
              clientId={$currentUser?.client_id}
              maxItems={15}
              showConnectionStatus={false}
            />
          </div>

          <!-- Side Panel -->
          <div class="space-y-6">
            <!-- Quick Stats -->
            {#if $realtimeMetrics}
              <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="px-4 py-5 sm:p-6">
                  <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
                    Quick Stats
                  </h3>
                  <dl class="space-y-4">
                    <div>
                      <dt class="text-sm font-medium text-gray-500">7-Day Volume</dt>
                      <dd class="text-2xl font-bold text-gray-900">{$realtimeMetrics.emails_processed_7d?.toLocaleString() || '0'}</dd>
                    </div>
                    <div>
                      <dt class="text-sm font-medium text-gray-500">30-Day Volume</dt>
                      <dd class="text-2xl font-bold text-gray-900">{$realtimeMetrics.emails_processed_30d?.toLocaleString() || '0'}</dd>
                    </div>
                    <div>
                      <dt class="text-sm font-medium text-gray-500">Routing Success</dt>
                      <dd class="text-2xl font-bold text-gray-900">{$realtimeMetrics.routing_success_rate?.toFixed(1) || '0'}%</dd>
                    </div>
                    <div>
                      <dt class="text-sm font-medium text-gray-500">Active Automations</dt>
                      <dd class="text-2xl font-bold text-gray-900">{$realtimeMetrics.active_automations || '0'}</dd>
                    </div>
                  </dl>
                </div>
              </div>
            {/if}

            <!-- System Monitoring Toggle -->
            <div class="bg-white overflow-hidden shadow rounded-lg">
              <div class="px-4 py-5 sm:p-6">
                <button
                  on:click={toggleMonitoring}
                  class="w-full flex items-center justify-between p-4 border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                >
                  <div class="flex items-center">
                    <BarChart3 class="h-6 w-6 {showMonitoring ? 'text-blue-600' : 'text-gray-400'}" />
                    <div class="ml-3 text-left">
                      <p class="text-sm font-medium text-gray-900">System Health</p>
                      <p class="text-sm text-gray-500">{showMonitoring ? 'Hide details' : 'Show health details'}</p>
                    </div>
                  </div>
                  <div class="ml-4">
                    {#if showMonitoring}
                      <ChevronUp class="h-4 w-4 text-gray-400" />
                    {:else}
                      <ChevronDown class="h-4 w-4 text-gray-400" />
                    {/if}
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- User information card -->
        {#if $currentUser}
          <div class="bg-white overflow-hidden shadow rounded-lg mb-6">
            <div class="px-4 py-5 sm:p-6">
              <div class="flex items-center mb-4">
                <User class="h-5 w-5 text-gray-400 mr-2" />
                <h3 class="text-lg leading-6 font-medium text-gray-900">
                  User Information
                </h3>
              </div>

              <dl class="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                <div>
                  <dt class="text-sm font-medium text-gray-500">Full Name</dt>
                  <dd class="mt-1 text-sm text-gray-900">{$currentUser.full_name}</dd>
                </div>

                <div>
                  <dt class="text-sm font-medium text-gray-500">Username</dt>
                  <dd class="mt-1 text-sm text-gray-900">{$currentUser.username}</dd>
                </div>

                <div>
                  <dt class="text-sm font-medium text-gray-500">Email</dt>
                  <dd class="mt-1 text-sm text-gray-900">{$currentUser.email}</dd>
                </div>

                <div>
                  <dt class="text-sm font-medium text-gray-500">Role</dt>
                  <dd class="mt-1">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getRoleBadgeColor($currentUser.role)}">
                      <Shield class="h-3 w-3 mr-1" />
                      {$currentUser.role.replace('_', ' ').toUpperCase()}
                    </span>
                  </dd>
                </div>

                <div>
                  <dt class="text-sm font-medium text-gray-500">Status</dt>
                  <dd class="mt-1">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {$currentUser.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                      {$currentUser.status.toUpperCase()}
                    </span>
                  </dd>
                </div>

                {#if $currentUser.client_id}
                  <div>
                    <dt class="text-sm font-medium text-gray-500">Client ID</dt>
                    <dd class="mt-1 text-sm text-gray-900">{$currentUser.client_id}</dd>
                  </div>
                {/if}

                <div>
                  <dt class="text-sm font-medium text-gray-500">Account Created</dt>
                  <dd class="mt-1 text-sm text-gray-900">
                    <div class="flex items-center">
                      <Clock class="h-4 w-4 text-gray-400 mr-1" />
                      {formatDate($currentUser.created_at)}
                    </div>
                  </dd>
                </div>

                {#if $currentUser.last_login_at}
                  <div>
                    <dt class="text-sm font-medium text-gray-500">Last Login</dt>
                    <dd class="mt-1 text-sm text-gray-900">
                      <div class="flex items-center">
                        <Clock class="h-4 w-4 text-gray-400 mr-1" />
                        {formatDate($currentUser.last_login_at)}
                      </div>
                    </dd>
                  </div>
                {/if}
              </dl>
            </div>
          </div>
        {/if}

        <!-- Quick actions -->
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
              Quick Actions
            </h3>

            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <!-- Coming soon placeholders -->
              <button
                disabled
                class="relative group p-4 border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div class="flex items-center">
                  <Settings class="h-6 w-6 text-gray-400" />
                  <div class="ml-3">
                    <p class="text-sm font-medium text-gray-900">Client Management</p>
                    <p class="text-sm text-gray-500">Coming in Week 2</p>
                  </div>
                </div>
              </button>

              <button
                on:click={toggleMonitoring}
                class="relative group p-4 border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                <div class="flex items-center justify-between w-full">
                  <div class="flex items-center">
                    <BarChart3 class="h-6 w-6 {showMonitoring ? 'text-blue-600' : 'text-gray-400'}" />
                    <div class="ml-3">
                      <p class="text-sm font-medium text-gray-900">System Monitoring</p>
                      <p class="text-sm text-gray-500">{showMonitoring ? 'Hide monitoring' : 'Show real-time monitoring'}</p>
                    </div>
                  </div>
                  <div class="ml-4">
                    {#if showMonitoring}
                      <ChevronUp class="h-4 w-4 text-gray-400" />
                    {:else}
                      <ChevronDown class="h-4 w-4 text-gray-400" />
                    {/if}
                  </div>
                </div>
              </button>

              <button
                disabled
                class="relative group p-4 border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div class="flex items-center">
                  <Bell class="h-6 w-6 text-gray-400" />
                  <div class="ml-3">
                    <p class="text-sm font-medium text-gray-900">Advanced Features</p>
                    <p class="text-sm text-gray-500">Coming in Week 4</p>
                  </div>
                </div>
              </button>
            </div>
          </div>
        </div>

        <!-- Real-time System Monitoring -->
        {#if showMonitoring}
          <div class="mt-6 transition-all duration-300 ease-in-out">
            <div class="bg-white overflow-hidden shadow rounded-lg">
              <div class="px-4 py-5 sm:p-6">
                <div class="flex items-center justify-between mb-6">
                  <h3 class="text-lg leading-6 font-medium text-gray-900">
                    Real-time System Monitoring
                  </h3>
                  <div class="flex items-center space-x-2">
                    <div class="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span class="text-sm text-gray-500">Live</span>
                  </div>
                </div>

                <SystemMonitor />
              </div>
            </div>
          </div>
        {/if}

        <!-- Implementation status -->
        <div class="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div class="flex">
            <Shield class="h-5 w-5 text-blue-600 mt-0.5" />
            <div class="ml-3">
              <h3 class="text-sm font-medium text-blue-800">
                ✅ Phase 2.2: Monitoring Dashboard Complete!
              </h3>
              <div class="mt-2 text-sm text-blue-700">
                <ul class="list-disc list-inside space-y-1">
                  <li>JWT authentication system ✅</li>
                  <li>Frontend-backend API connection ✅</li>
                  <li>Real-time system monitoring ✅</li>
                  <li>Health check dashboards ✅</li>
                  <li>Component status tracking ✅</li>
                  <li>Performance metrics display ✅</li>
                </ul>
              </div>
              <div class="mt-3">
                <p class="text-sm text-blue-700">
                  <strong>Next:</strong> Customer Onboarding Workflow
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Real-time Alerts -->
    <RealtimeAlerts position="top-right" />
  </div>
</AuthGuard>
