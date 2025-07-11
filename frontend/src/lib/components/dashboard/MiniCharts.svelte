<script lang="ts">
  import { onMount } from 'svelte';
  import AnimatedChart from '$lib/components/Charts/AnimatedChart.svelte';
  import GlassCard from '$lib/components/UI/GlassCard.svelte';
  import { TrendingUp, BarChart3, PieChart, Activity } from 'lucide-svelte';
  import { theme } from '$lib/stores/theme';

  export let metrics: any = null; // Used for future real data integration
  export let loading = false;

  // Sample data for demonstration
  const emailVolumeData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [{
      label: 'Emails Processed',
      data: [45, 67, 89, 56, 78, 34, 23],
      borderColor: '#667eea',
      backgroundColor: 'rgba(102, 126, 234, 0.1)',
      fill: true,
      tension: 0.4
    }]
  };

  const accuracyData = {
    labels: ['Correct', 'Incorrect'],
    datasets: [{
      data: [95.8, 4.2],
      backgroundColor: [
        'rgba(16, 185, 129, 0.8)',
        'rgba(239, 68, 68, 0.8)'
      ],
      borderColor: [
        '#10b981',
        '#ef4444'
      ],
      borderWidth: 2
    }]
  };

  const responseTimeData = {
    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
    datasets: [{
      label: 'Response Time (s)',
      data: [2.1, 1.8, 2.4, 3.1, 2.7, 2.0],
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      fill: true
    }]
  };

  const categoryData = {
    labels: ['Support', 'Sales', 'Billing', 'General'],
    datasets: [{
      data: [42, 28, 18, 12],
      backgroundColor: [
        'rgba(102, 126, 234, 0.8)',
        'rgba(16, 185, 129, 0.8)',
        'rgba(245, 158, 11, 0.8)',
        'rgba(139, 69, 19, 0.8)'
      ],
      borderColor: [
        '#667eea',
        '#10b981',
        '#f59e0b',
        '#8b4513'
      ],
      borderWidth: 2
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        enabled: true
      }
    },
    scales: {
      x: {
        display: false
      },
      y: {
        display: false
      }
    },
    elements: {
      point: {
        radius: 2,
        hoverRadius: 4
      }
    }
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      }
    },
    cutout: '70%'
  };
</script>

<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
  <!-- Email Volume Trend -->
  <GlassCard variant="minimal" padding="md" animate={true} delay={100}>
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center space-x-2">
        <TrendingUp class="w-4 h-4 text-primary" />
        <h4 class="text-sm font-medium text-base-content/80">Volume Trend</h4>
      </div>
      <span class="text-xs text-success font-medium">+12%</span>
    </div>

    <div class="h-20 mb-2">
      {#if !loading}
        <AnimatedChart
          type="area"
          data={emailVolumeData}
          options={chartOptions}
          height={80}
          gradient={true}
          theme={$theme}
        />
      {:else}
        <div class="w-full h-full bg-base-300 animate-pulse rounded"></div>
      {/if}
    </div>

    <div class="text-xs text-base-content/60">Last 7 days</div>
  </GlassCard>

  <!-- Classification Accuracy -->
  <GlassCard variant="minimal" padding="md" animate={true} delay={200}>
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center space-x-2">
        <PieChart class="w-4 h-4 text-success" />
        <h4 class="text-sm font-medium text-base-content/80">Accuracy</h4>
      </div>
      <span class="text-xs text-success font-medium">95.8%</span>
    </div>

    <div class="h-20 mb-2">
      {#if !loading}
        <AnimatedChart
          type="doughnut"
          data={accuracyData}
          options={doughnutOptions}
          height={80}
          theme={$theme}
        />
      {:else}
        <div class="w-full h-full bg-base-300 animate-pulse rounded-full"></div>
      {/if}
    </div>

    <div class="text-xs text-base-content/60">AI Classification</div>
  </GlassCard>

  <!-- Response Time -->
  <GlassCard variant="minimal" padding="md" animate={true} delay={300}>
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center space-x-2">
        <Activity class="w-4 h-4 text-info" />
        <h4 class="text-sm font-medium text-base-content/80">Response Time</h4>
      </div>
      <span class="text-xs text-info font-medium">2.3s avg</span>
    </div>

    <div class="h-20 mb-2">
      {#if !loading}
        <AnimatedChart
          type="line"
          data={responseTimeData}
          options={chartOptions}
          height={80}
          gradient={true}
          theme={$theme}
        />
      {:else}
        <div class="w-full h-full bg-base-300 animate-pulse rounded"></div>
      {/if}
    </div>

    <div class="text-xs text-base-content/60">24h average</div>
  </GlassCard>

  <!-- Category Distribution -->
  <GlassCard variant="minimal" padding="md" animate={true} delay={400}>
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center space-x-2">
        <BarChart3 class="w-4 h-4 text-secondary" />
        <h4 class="text-sm font-medium text-base-content/80">Categories</h4>
      </div>
      <span class="text-xs text-secondary font-medium">4 types</span>
    </div>

    <div class="h-20 mb-2">
      {#if !loading}
        <AnimatedChart
          type="doughnut"
          data={categoryData}
          options={doughnutOptions}
          height={80}
          theme={$theme}
        />
      {:else}
        <div class="w-full h-full bg-base-300 animate-pulse rounded-full"></div>
      {/if}
    </div>

    <div class="text-xs text-base-content/60">Distribution</div>
  </GlassCard>
</div>
