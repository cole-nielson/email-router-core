<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import DashboardLayout from '$lib/components/Layout/DashboardLayout.svelte';
  import MetricsCard from '$lib/components/Dashboard/MetricsCard.svelte';
  import LiveFeed from '$lib/components/Dashboard/LiveFeed.svelte';
  import { dashboardStore, metrics, activities, isLoading, error } from '$lib/stores/dashboard';
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
    Globe
  } from 'lucide-svelte';

  // Note: data prop removed as it's currently unused

  // Mock client ID for development - in production this would come from auth/routing
  const clientId = 'client-001-cole-nielson';
  let user = {
    name: 'Cole Nielson',
    email: 'cole@colesportfolio.com'
  };

  onMount(() => {
    // Initialize dashboard with mock authentication
    dashboardStore.initialize(clientId);
  });

  onDestroy(() => {
    dashboardStore.destroy();
  });

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
    dashboardStore.refresh(clientId);
  }

  function handleViewAllActivities() {
    goto('/activity');
  }
</script>

<DashboardLayout {clientId} {user}>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Page header -->
      <div class="mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-gray-900">Dashboard Overview</h1>
            <p class="text-gray-600 mt-2">Monitor your AI automation performance and activity</p>
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
              on:click={() => dashboardStore.refresh(clientId)}
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
                  <span class="text-sm font-semibold text-emerald-600">99.8%</span>
                </div>
                
                <div class="flex justify-between items-center">
                  <span class="text-sm font-medium text-gray-600">Success Rate</span>
                  <span class="text-sm font-semibold text-emerald-600">98.2%</span>
                </div>
                
                <div class="flex justify-between items-center">
                  <span class="text-sm font-medium text-gray-600">Avg Processing</span>
                  <span class="text-sm font-semibold text-blue-600">
                    {$metrics ? `${$metrics.average_response_time.toFixed(1)}s` : '0s'}
                  </span>
                </div>
                
                <div class="flex justify-between items-center">
                  <span class="text-sm font-medium text-gray-600">Peak Today</span>
                  <span class="text-sm font-semibold text-amber-600">156 emails/hr</span>
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
                    <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span class="text-xs font-medium text-green-700">Healthy</span>
                  </div>
                </div>
                
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium text-gray-600">AI Classifier</span>
                  <div class="flex items-center space-x-2">
                    <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span class="text-xs font-medium text-green-700">Online</span>
                  </div>
                </div>
                
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium text-gray-600">Email Delivery</span>
                  <div class="flex items-center space-x-2">
                    <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span class="text-xs font-medium text-green-700">Operational</span>
                  </div>
                </div>
                
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium text-gray-600">WebSocket</span>
                  <div class="flex items-center space-x-2">
                    <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span class="text-xs font-medium text-green-700">Connected</span>
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