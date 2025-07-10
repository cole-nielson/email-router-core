<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import { Mail, CheckCircle, XCircle, Clock, AlertTriangle, RefreshCw, Send } from 'lucide-svelte';
  import { formatDistanceToNow } from 'date-fns';
  import type { ActivityItem } from '$lib/types/dashboard';

  export let activities: ActivityItem[] = [];
  export let loading = false;
  export let maxItems = 10;
  export let autoRefresh = false;
  export let refreshInterval = 30000; // 30 seconds

  const dispatch = createEventDispatcher();

  let refreshTimer: any = null;

  onMount(() => {
    if (autoRefresh) {
      refreshTimer = setInterval(() => {
        dispatch('refresh');
      }, refreshInterval);
    }
  });

  onDestroy(() => {
    if (refreshTimer) {
      clearInterval(refreshTimer);
    }
  });

  function getActivityIcon(type: string, status?: string) {
    switch (type) {
      case 'email_received':
        return Mail;
      case 'classification_completed':
        return status === 'success' ? CheckCircle : XCircle;
      case 'routing_completed':
        return CheckCircle;
      case 'email_sent':
        return Send;
      case 'error':
      case 'alert':
        return AlertTriangle;
      default:
        return Clock;
    }
  }

  function getActivityColor(type: string, status?: string) {
    if (status === 'success') return 'text-green-600 bg-green-50';
    if (status === 'error') return 'text-red-600 bg-red-50';
    if (status === 'processing') return 'text-blue-600 bg-blue-50';

    switch (type) {
      case 'email_received':
        return 'text-blue-600 bg-blue-50';
      case 'classification_complete':
        return 'text-green-600 bg-green-50';
      case 'routing_complete':
        return 'text-purple-600 bg-purple-50';
      case 'delivery_complete':
        return 'text-green-600 bg-green-50';
      case 'error':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  }

  function getStatusBadge(status?: string) {
    const badges: Record<string, string> = {
      'success': 'bg-green-100 text-green-800',
      'error': 'bg-red-100 text-red-800',
      'processing': 'bg-blue-100 text-blue-800',
      'pending': 'bg-yellow-100 text-yellow-800',
      'completed': 'bg-green-100 text-green-800',
      'failed': 'bg-red-100 text-red-800'
    };
    return badges[status || 'pending'] || badges.pending;
  }

  function handleActivityClick(activity: ActivityItem) {
    dispatch('activity-click', activity);
  }

  function formatTime(timestamp: string) {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    } catch {
      return 'Unknown time';
    }
  }

  function getActivityTitle(activity: ActivityItem): string {
    switch (activity.type) {
      case 'email_received':
        return `Email received from ${activity.details.sender || 'unknown sender'}`;
      case 'classification_completed':
        return `Email classified as ${activity.details.category || 'unknown category'}`;
      case 'routing_completed':
        return `Email routed to ${activity.details.recipient || 'unknown recipient'}`;
      case 'email_sent':
        return 'Response sent successfully';
      case 'error':
        return `Error: ${activity.details.error_message || 'Unknown error'}`;
      case 'alert':
        return 'System alert triggered';
      default:
        return activity.description || 'Activity occurred';
    }
  }

  function getActivitySubtitle(activity: ActivityItem): string {
    const details: string[] = [];

    if (activity.details.processing_time) {
      details.push(`${activity.details.processing_time}s`);
    }
    if (activity.details.confidence) {
      details.push(`${Math.round(activity.details.confidence * 100)}% confidence`);
    }
    if (activity.details.subject) {
      details.push(`"${activity.details.subject.substring(0, 30)}${activity.details.subject.length > 30 ? '...' : ''}"`);
    }

    return details.join(' • ') || activity.description || '';
  }

  // Display activities, slice to maxItems
  $: displayActivities = activities.slice(0, maxItems);
</script>

<div class="h-full">
  {#if loading}
    <!-- Loading state -->
    <div class="space-y-4">
      {#each Array(5) as _}
        <div class="animate-pulse flex items-start space-x-3">
          <div class="w-10 h-10 bg-gray-200 rounded-full"></div>
          <div class="flex-1 space-y-2">
            <div class="h-4 bg-gray-200 rounded w-3/4"></div>
            <div class="h-3 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      {/each}
    </div>
  {:else if displayActivities.length === 0}
    <!-- Empty state -->
    <div class="text-center py-8">
      <div class="w-12 h-12 mx-auto mb-4 text-gray-400">
        <Clock class="w-full h-full" />
      </div>
      <p class="text-gray-500 text-sm">No recent activity</p>
      <button
        class="mt-2 text-blue-600 hover:text-blue-700 text-sm font-medium"
        on:click={() => dispatch('refresh')}
      >
        Refresh to check for updates
      </button>
    </div>
  {:else}
    <!-- Activity list -->
    <div class="space-y-4">
      {#each displayActivities as activity (activity.id)}
        <div
          class="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer border border-transparent hover:border-gray-200"
          on:click={() => handleActivityClick(activity)}
          role="button"
          tabindex="0"
          on:keydown={(e) => e.key === 'Enter' && handleActivityClick(activity)}
        >
          <!-- Icon -->
          <div class="flex-shrink-0">
            <div class="w-10 h-10 rounded-full flex items-center justify-center {getActivityColor(activity.type, activity.status)}">
              <svelte:component this={getActivityIcon(activity.type, activity.status)} class="w-5 h-5" />
            </div>
          </div>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between">
              <p class="text-sm font-medium text-gray-900 truncate">
                {getActivityTitle(activity)}
              </p>
              <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium {getStatusBadge(activity.status)}">
                {activity.status || 'pending'}
              </span>
            </div>

            <div class="mt-1 text-xs text-gray-500">
              <div class="flex items-center space-x-2">
                <span>{formatTime(activity.timestamp)}</span>
                {#if getActivitySubtitle(activity)}
                  <span>•</span>
                  <span class="truncate">{getActivitySubtitle(activity)}</span>
                {/if}
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>

    <!-- Footer actions -->
    <div class="mt-6 pt-4 border-t border-gray-200 flex items-center justify-between">
      <button
        class="flex items-center text-sm text-gray-600 hover:text-gray-900 transition-colors"
        on:click={() => dispatch('refresh')}
      >
        <RefreshCw class="w-4 h-4 mr-1" />
        Refresh
      </button>

      <button
        class="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
        on:click={() => dispatch('view-all')}
      >
        View all activity →
      </button>
    </div>
  {/if}
</div>
