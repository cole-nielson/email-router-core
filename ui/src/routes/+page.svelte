<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import LoginForm from '$lib/components/Auth/LoginForm.svelte';
  import DashboardLayout from '$lib/components/Layout/DashboardLayout.svelte';
  import MetricsCard from '$lib/components/Dashboard/MetricsCard.svelte';
  import LiveFeed from '$lib/components/Dashboard/LiveFeed.svelte';
  import { dashboardStore, metrics, activities, isLoading, error, isConnected } from '$lib/stores/dashboard';
  import { authStore, isAuthenticated, currentClient, clientId } from '$lib/stores/auth';
  import { 
    Mail, 
    CheckCircle, 
    Clock, 
    Zap, 
    TrendingUp,
    Activity,
    AlertTriangle,
    Settings,
    Plus,
    BarChart3,
    Users,
    Globe,
    LogOut
  } from 'lucide-svelte';

  // Reactive user object derived from auth store
  $: user = $currentClient ? {
    name: $currentClient.name || 'Client',
    email: `client@${$currentClient.primary_domain || 'example.com'}`
  } : null;

  // Calculate system status from metrics and connection state
  $: systemHealth = {
    emailRouter: {
      status: $metrics && $metrics.emails_processed_24h >= 0 ? 'healthy' : 'warning',
      text: $metrics && $metrics.emails_processed_24h >= 0 ? 'Healthy' : 'Warning',
      color: $metrics && $metrics.emails_processed_24h >= 0 ? 'green' : 'yellow'
    },
    aiClassifier: {
      status: $metrics && $metrics.classification_accuracy > 0.7 ? 'healthy' : 'warning',
      text: $metrics && $metrics.classification_accuracy > 0.7 ? 'Online' : 'Degraded',
      color: $metrics && $metrics.classification_accuracy > 0.7 ? 'green' : 'yellow'
    },
    emailDelivery: {
      status: $metrics && $metrics.successful_routes >= 0 ? 'healthy' : 'error',
      text: $metrics && $metrics.successful_routes >= 0 ? 'Operational' : 'Error',
      color: $metrics && $metrics.successful_routes >= 0 ? 'green' : 'red'
    },
    websocket: {
      status: $isConnected ? 'healthy' : 'warning',
      text: $isConnected ? 'Connected' : 'Disconnected',
      color: $isConnected ? 'green' : 'yellow'
    }
  };

  onMount(() => {
    // Auth store will auto-initialize from localStorage
    // Dashboard will be initialized after successful login
  });

  onDestroy(() => {
    dashboardStore.destroy();
  });

  // Handle successful login
  async function handleLoginSuccess(event: CustomEvent<{ clientId: string; apiKey: string }>) {
    const { clientId } = event.detail;
    // Initialize dashboard with the authenticated client
    await dashboardStore.initialize(clientId);
  }

  // Handle logout
  function handleLogout() {
    authStore.logout();
    dashboardStore.destroy();
  }

  // Handle metric card clicks
  function handleMetricClick(metric: string) {
    switch (metric) {
      case 'emails':
        goto('/activity');
        break;
      case 'accuracy':
        goto('/analytics');
        break;
      case 'response_time':
        goto('/analytics');
        break;
      case 'automations':
        goto('/automations');
        break;
    }
  }

  // Handle live feed events
  function handleActivityClick(event: CustomEvent) {
    const activity = event.detail;
    goto(`/activity/${activity.id}`);
  }

  function handleRefreshFeed() {
    if ($clientId) {
      dashboardStore.refresh($clientId);
    }
  }

  function handleViewAllActivities() {
    goto('/activity');
  }
</script>

{#if !$isAuthenticated}
  <!-- Show login form when not authenticated -->
  <LoginForm on:success={handleLoginSuccess} />
{:else}
  <!-- Show dashboard when authenticated -->
  <DashboardLayout clientId={$clientId} {user}>
    <div class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <!-- Page header -->
        <div class="mb-8">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-3xl font-bold text-gray-900">Dashboard Overview</h1>
              <p class="text-gray-600 mt-2">Monitor your AI automation performance and activity</p>
              {#if $currentClient}
                <p class="text-sm text-gray-500 mt-1">Client: {$currentClient.name}</p>
              {/if}
            </div>
            
            <div class="flex items-center space-x-3">
              <button 
                class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                on:click={() => goto('/settings')}
              >
                <Settings class="w-4 h-4 mr-2" />
                Settings
              </button>
              <button 
                class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors shadow-sm"
                on:click={() => goto('/automations/new')}
              >
                <Plus class="w-4 h-4 mr-2" />
                New Automation
              </button>
              <button 
                class="inline-flex items-center px-4 py-2 border border-red-300 rounded-lg text-sm font-medium text-red-700 bg-white hover:bg-red-50 transition-colors"
                on:click={handleLogout}
              >
                <LogOut class="w-4 h-4 mr-2" />
                Logout
              </button>
            </div>
          </div>
        </div>

        <!-- Error state -->
        {#if $error}
          <div class="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div class="flex items-center">
              <AlertTriangle class="w-5 h-5 text-red-600 mr-3" />
              <div>
                <h3 class="text-sm font-medium text-red-800">Failed to load dashboard</h3>
                <p class="text-sm text-red-700 mt-1">{$error}</p>
              </div>
              <button 
                class="ml-auto bg-red-100 text-red-600 px-3 py-1 rounded-md text-sm hover:bg-red-200 transition-colors"
                on:click={() => $clientId && dashboardStore.refresh($clientId)}
              >
                Retry
              </button>
            </div>
          </div>
        {/if}

        <!-- Metrics grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricsCard
            title="Emails Processed"
            value={$metrics?.emails_processed_24h ?? 0}
            subtitle="Last 24 hours"
            trend="up"
            trendValue="+12%"
            icon={Mail}
            color="primary"
            loading={$isLoading}
            clickable={true}
            on:click={() => handleMetricClick('emails')}
          />

          <MetricsCard
            title="Classification Accuracy"
            value={$metrics ? `${($metrics.classification_accuracy * 100).toFixed(1)}%` : '0%'}
            subtitle="AI confidence score"
            trend="up"
            trendValue="+2.3%"
            icon={CheckCircle}
            color="success"
            loading={$isLoading}
            clickable={true}
            on:click={() => handleMetricClick('accuracy')}
          />

          <MetricsCard
            title="Avg Response Time"
            value={$metrics ? `${$metrics.average_response_time.toFixed(1)}s` : '0s'}
            subtitle="End-to-end processing"
            trend="down"
            trendValue="-0.3s"
            icon={Clock}
            color="info"
            loading={$isLoading}
            clickable={true}
            on:click={() => handleMetricClick('response_time')}
          />

          <MetricsCard
            title="Active Automations"
            value={$metrics?.active_automations ?? 0}
            subtitle="Running workflows"
            trend="neutral"
            icon={Zap}
            color="secondary"
            loading={$isLoading}
            clickable={true}
            on:click={() => handleMetricClick('automations')}
          />
        </div>

        <!-- Main content grid -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <!-- Live activity feed -->
          <div class="lg:col-span-2">
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
              <div class="px-6 py-4 border-b border-gray-200">
                <div class="flex items-center justify-between">
                  <h2 class="text-lg font-semibold text-gray-900">Recent Activity</h2>
                  <button 
                    class="text-sm text-blue-600 hover:text-blue-700 font-medium"
                    on:click={handleViewAllActivities}
                  >
                    View all →
                  </button>
                </div>
              </div>
              <div class="p-6">
                <LiveFeed
                  activities={$activities}
                  loading={$isLoading}
                  maxItems={15}
                  autoRefresh={true}
                  on:activity-click={handleActivityClick}
                  on:refresh={handleRefreshFeed}
                  on:view-all={handleViewAllActivities}
                />
              </div>
            </div>
          </div>

          <!-- Sidebar with quick stats and system status -->
          <div class="space-y-6">
            <!-- Quick performance stats -->
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
              <div class="px-6 py-4 border-b border-gray-200">
                <h3 class="text-lg font-semibold text-gray-900 flex items-center">
                  <BarChart3 class="w-5 h-5 mr-2 text-blue-600" />
                  Performance
                </h3>
              </div>
              <div class="p-6">
                <div class="space-y-4">
                  <div class="flex justify-between items-center">
                    <span class="text-sm font-medium text-gray-600">Uptime</span>
                    <span class="text-sm font-semibold text-emerald-600">
                      {$metrics ? `${($metrics.uptime_hours / 24 * 100).toFixed(1)}%` : '0%'}
                    </span>
                  </div>
                  
                  <div class="flex justify-between items-center">
                    <span class="text-sm font-medium text-gray-600">Success Rate</span>
                    <span class="text-sm font-semibold text-emerald-600">
                      {$metrics && ($metrics.successful_routes + $metrics.failed_routes) > 0 
                        ? `${($metrics.successful_routes / ($metrics.successful_routes + $metrics.failed_routes) * 100).toFixed(1)}%`
                        : '100%'}
                    </span>
                  </div>
                  
                  <div class="flex justify-between items-center">
                    <span class="text-sm font-medium text-gray-600">Avg Processing</span>
                    <span class="text-sm font-semibold text-blue-600">
                      {$metrics ? `${$metrics.average_response_time.toFixed(1)}s` : '0s'}
                    </span>
                  </div>
                  
                  <div class="flex justify-between items-center">
                    <span class="text-sm font-medium text-gray-600">Peak Today</span>
                    <span class="text-sm font-semibold text-amber-600">
                      {$metrics ? `${Math.max(Math.round($metrics.emails_processed_24h / 24 * 1.5), $metrics.emails_processed_24h)} emails/hr` : '0 emails/hr'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- System status -->
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
              <div class="px-6 py-4 border-b border-gray-200">
                <h3 class="text-lg font-semibold text-gray-900 flex items-center">
                  <Activity class="w-5 h-5 mr-2 text-green-600" />
                  System Status
                </h3>
              </div>
              <div class="p-6">
                <div class="space-y-3">
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium text-gray-600">Email Router</span>
                    <div class="flex items-center space-x-2">
                      <div class="w-2 h-2 rounded-full {systemHealth.emailRouter.color === 'green' ? 'bg-green-500' : systemHealth.emailRouter.color === 'yellow' ? 'bg-yellow-500' : 'bg-red-500'}"></div>
                      <span class="text-xs font-medium {systemHealth.emailRouter.color === 'green' ? 'text-green-700' : systemHealth.emailRouter.color === 'yellow' ? 'text-yellow-700' : 'text-red-700'}">{systemHealth.emailRouter.text}</span>
                    </div>
                  </div>
                  
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium text-gray-600">AI Classifier</span>
                    <div class="flex items-center space-x-2">
                      <div class="w-2 h-2 rounded-full {systemHealth.aiClassifier.color === 'green' ? 'bg-green-500' : systemHealth.aiClassifier.color === 'yellow' ? 'bg-yellow-500' : 'bg-red-500'}"></div>
                      <span class="text-xs font-medium {systemHealth.aiClassifier.color === 'green' ? 'text-green-700' : systemHealth.aiClassifier.color === 'yellow' ? 'text-yellow-700' : 'text-red-700'}">{systemHealth.aiClassifier.text}</span>
                    </div>
                  </div>
                  
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium text-gray-600">Email Delivery</span>
                    <div class="flex items-center space-x-2">
                      <div class="w-2 h-2 rounded-full {systemHealth.emailDelivery.color === 'green' ? 'bg-green-500' : systemHealth.emailDelivery.color === 'yellow' ? 'bg-yellow-500' : 'bg-red-500'}"></div>
                      <span class="text-xs font-medium {systemHealth.emailDelivery.color === 'green' ? 'text-green-700' : systemHealth.emailDelivery.color === 'yellow' ? 'text-yellow-700' : 'text-red-700'}">{systemHealth.emailDelivery.text}</span>
                    </div>
                  </div>
                  
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium text-gray-600">WebSocket</span>
                    <div class="flex items-center space-x-2">
                      <div class="w-2 h-2 rounded-full {systemHealth.websocket.color === 'green' ? 'bg-green-500' : systemHealth.websocket.color === 'yellow' ? 'bg-yellow-500' : 'bg-red-500'}"></div>
                      <span class="text-xs font-medium {systemHealth.websocket.color === 'green' ? 'text-green-700' : systemHealth.websocket.color === 'yellow' ? 'text-yellow-700' : 'text-red-700'}">{systemHealth.websocket.text}</span>
                    </div>
                  </div>
                </div>
                
                <button 
                  class="w-full mt-4 bg-gray-50 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-100 transition-colors border border-gray-200"
                  on:click={() => goto('/status')}
                >
                  View Detailed Status
                </button>
              </div>
            </div>

            <!-- Quick Actions -->
            <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
              <div class="px-6 py-4 border-b border-gray-200">
                <h3 class="text-lg font-semibold text-gray-900">Quick Actions</h3>
              </div>
              <div class="p-6">
                <div class="space-y-3">
                  <button 
                    class="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                    on:click={() => goto('/automations/new')}
                  >
                    <Plus class="w-4 h-4 mr-2" />
                    Create Automation
                  </button>
                  
                  <button 
                    class="w-full flex items-center justify-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
                    on:click={() => goto('/analytics')}
                  >
                    <BarChart3 class="w-4 h-4 mr-2" />
                    View Analytics
                  </button>
                  
                  <button 
                    class="w-full flex items-center justify-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
                    on:click={() => goto('/integrations')}
                  >
                    <Globe class="w-4 h-4 mr-2" />
                    Manage Integrations
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </DashboardLayout>
{/if}