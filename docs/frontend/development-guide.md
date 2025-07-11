# Frontend Development Guide

🛠️ **Comprehensive guide for developing frontend features using established patterns and components**

## Development Philosophy

The frontend foundation is **70-80% complete** with professional patterns established. The goal is to **build upon existing infrastructure** rather than reinvent patterns. Follow the established component architecture, state management patterns, and design system.

## Quick Start

### **Development Setup**

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (already configured)
npm install

# Start development server with backend proxy
npm run dev

# Backend should be running on localhost:8080
# Frontend will be available on localhost:5173
```

### **Environment Configuration**
```bash
# .env.local (for development)
PUBLIC_API_BASE_URL=http://localhost:8080
PUBLIC_WS_BASE_URL=ws://localhost:8080
NODE_ENV=development
```

## Development Patterns

### **1. Component Development Pattern**

Follow the established component structure for consistency:

```svelte
<!-- src/lib/components/example/NewComponent.svelte -->
<script lang="ts">
  // 1. Type imports first
  import type { ComponentData } from '$lib/types';

  // 2. Component imports
  import { LoadingSkeleton, GlassCard } from '$lib/components/ui';

  // 3. Store imports
  import { authStore } from '$lib/stores/authStore';

  // 4. API imports
  import { apiClient } from '$lib/api/apiClient';

  // 5. Props with types
  export let data: ComponentData;
  export let variant: 'primary' | 'secondary' = 'primary';

  // 6. Local state
  let loading = false;
  let error: string | null = null;

  // 7. Reactive statements
  $: hasPermission = $authStore.user?.permissions.includes('resource:action');

  // 8. Functions
  const handleAction = async () => {
    loading = true;
    error = null;

    try {
      await apiClient.post('/some/endpoint', data);
      // Handle success
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  };

  // 9. Lifecycle (if needed)
  onMount(() => {
    // Initialization
  });
</script>

<!-- Template with proper structure -->
<GlassCard class="p-6">
  {#if loading}
    <LoadingSkeleton />
  {:else if error}
    <div class="alert alert-error">
      <span>{error}</span>
      <button on:click={handleAction} class="btn btn-sm">Retry</button>
    </div>
  {:else}
    <!-- Main content -->
    <div class="space-y-4">
      <h3 class="text-lg font-semibold">{data.title}</h3>

      {#if hasPermission}
        <button on:click={handleAction} class="btn btn-primary">
          Action
        </button>
      {/if}
    </div>
  {/if}
</GlassCard>

<style>
  /* Component-specific styles (minimal - use Tailwind) */
</style>
```

### **2. API Service Pattern**

Create service classes for domain-specific API operations:

```typescript
// src/lib/services/clientService.ts
import { apiClient } from '$lib/api/apiClient';
import type { ClientConfig, RoutingRules, BrandingConfig } from '$lib/types';

export class ClientService {
  // Get operations
  async getClient(clientId: string): Promise<ClientConfig> {
    return await apiClient.get(`/api/v2/config/clients/${clientId}`);
  }

  async getClients(): Promise<ClientConfig[]> {
    const response = await apiClient.get('/api/v1/clients');
    return response.clients;
  }

  async getRoutingRules(clientId: string): Promise<RoutingRules> {
    return await apiClient.get(`/api/v2/config/clients/${clientId}/routing`);
  }

  async getBranding(clientId: string): Promise<BrandingConfig> {
    return await apiClient.get(`/api/v2/config/clients/${clientId}/branding`);
  }

  // Update operations
  async updateClient(clientId: string, data: Partial<ClientConfig>): Promise<ClientConfig> {
    return await apiClient.put(`/api/v2/config/clients/${clientId}`, data);
  }

  async updateRoutingRule(clientId: string, category: string, email: string): Promise<void> {
    await apiClient.put(`/api/v2/config/clients/${clientId}/routing/${category}`, {
      email,
      priority: 1
    });
  }

  async updateBranding(clientId: string, branding: Partial<BrandingConfig>): Promise<BrandingConfig> {
    return await apiClient.put(`/api/v2/config/clients/${clientId}/branding`, branding);
  }

  // Validation operations
  async validateClient(clientId: string): Promise<any> {
    return await apiClient.post(`/api/v1/clients/${clientId}/validate`);
  }
}

// Export singleton instance
export const clientService = new ClientService();
```

### **3. Store Pattern**

Create stores for state management following the established pattern:

```typescript
// src/lib/stores/clientStore.ts
import { writable, derived } from 'svelte/store';
import { clientService } from '$lib/services/clientService';
import type { ClientConfig, RoutingRules, BrandingConfig } from '$lib/types';

interface ClientState {
  currentClient: ClientConfig | null;
  routingRules: RoutingRules | null;
  branding: BrandingConfig | null;
  clients: ClientConfig[];
  loading: boolean;
  error: string | null;
}

const initialState: ClientState = {
  currentClient: null,
  routingRules: null,
  branding: null,
  clients: [],
  loading: false,
  error: null
};

// Main store
export const clientStore = writable<ClientState>(initialState);

// Derived stores
export const currentClient = derived(clientStore, $store => $store.currentClient);
export const isLoading = derived(clientStore, $store => $store.loading);

// Actions
export const clientActions = {
  async loadClients() {
    clientStore.update(state => ({ ...state, loading: true, error: null }));

    try {
      const clients = await clientService.getClients();
      clientStore.update(state => ({ ...state, clients, loading: false }));
    } catch (error) {
      clientStore.update(state => ({
        ...state,
        loading: false,
        error: error.message
      }));
    }
  },

  async loadClient(clientId: string) {
    clientStore.update(state => ({ ...state, loading: true, error: null }));

    try {
      const [client, routingRules, branding] = await Promise.all([
        clientService.getClient(clientId),
        clientService.getRoutingRules(clientId),
        clientService.getBranding(clientId)
      ]);

      clientStore.update(state => ({
        ...state,
        currentClient: client,
        routingRules,
        branding,
        loading: false
      }));
    } catch (error) {
      clientStore.update(state => ({
        ...state,
        loading: false,
        error: error.message
      }));
    }
  },

  async updateRoutingRule(clientId: string, category: string, email: string) {
    try {
      await clientService.updateRoutingRule(clientId, category, email);

      // Update local state
      clientStore.update(state => ({
        ...state,
        routingRules: {
          ...state.routingRules,
          rules: {
            ...state.routingRules?.rules,
            [category]: email
          }
        }
      }));
    } catch (error) {
      clientStore.update(state => ({ ...state, error: error.message }));
    }
  }
};
```

### **4. Form Pattern**

Use established form patterns with validation:

```svelte
<!-- src/lib/components/forms/ClientForm.svelte -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { ClientConfig } from '$lib/types';

  // Props
  export let client: Partial<ClientConfig> = {};
  export let loading = false;

  // Form data
  let formData = {
    name: client.name || '',
    industry: client.industry || '',
    timezone: client.timezone || 'UTC',
    business_hours: client.business_hours || '9-17',
    ...client
  };

  // Validation
  let errors: Record<string, string> = {};

  const validate = () => {
    errors = {};

    if (!formData.name) errors.name = 'Name is required';
    if (!formData.industry) errors.industry = 'Industry is required';
    if (!formData.timezone) errors.timezone = 'Timezone is required';

    return Object.keys(errors).length === 0;
  };

  // Events
  const dispatch = createEventDispatcher<{
    save: ClientConfig;
    cancel: void;
  }>();

  const handleSubmit = () => {
    if (validate()) {
      dispatch('save', formData as ClientConfig);
    }
  };
</script>

<form on:submit|preventDefault={handleSubmit} class="space-y-6">
  <div class="glass-card p-6">
    <h3 class="text-lg font-semibold mb-4">Client Information</h3>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label class="label">
          <span class="label-text">Client Name</span>
        </label>
        <input
          bind:value={formData.name}
          class="input input-bordered w-full"
          class:input-error={errors.name}
          disabled={loading}
        />
        {#if errors.name}
          <label class="label">
            <span class="label-text-alt text-error">{errors.name}</span>
          </label>
        {/if}
      </div>

      <div>
        <label class="label">
          <span class="label-text">Industry</span>
        </label>
        <select
          bind:value={formData.industry}
          class="select select-bordered w-full"
          class:select-error={errors.industry}
          disabled={loading}
        >
          <option value="">Select Industry</option>
          <option value="technology">Technology</option>
          <option value="healthcare">Healthcare</option>
          <option value="finance">Finance</option>
          <option value="education">Education</option>
          <option value="other">Other</option>
        </select>
        {#if errors.industry}
          <label class="label">
            <span class="label-text-alt text-error">{errors.industry}</span>
          </label>
        {/if}
      </div>
    </div>

    <div class="flex justify-end space-x-4 mt-6">
      <button
        type="button"
        class="btn btn-outline"
        on:click={() => dispatch('cancel')}
        disabled={loading}
      >
        Cancel
      </button>
      <button
        type="submit"
        class="btn btn-primary"
        disabled={loading}
      >
        {#if loading}
          <span class="loading loading-spinner loading-sm"></span>
        {/if}
        Save Client
      </button>
    </div>
  </div>
</form>
```

## Using Existing Components

### **Layout Components** ✅ **USE AS-IS**

```svelte
<!-- Use existing layouts -->
<script>
  import { DashboardLayout, Header, Sidebar } from '$lib/components/layout';
</script>

<DashboardLayout>
  <svelte:fragment slot="header">
    <Header />
  </svelte:fragment>

  <svelte:fragment slot="sidebar">
    <Sidebar />
  </svelte:fragment>

  <!-- Your content here -->
  <div class="p-6">
    <!-- Page content -->
  </div>
</DashboardLayout>
```

### **UI Components** ✅ **USE EXISTING**

```svelte
<script>
  import {
    GlassCard,
    LoadingSkeleton,
    ThemeToggle,
    ToastContainer,
    FloatingActionButton
  } from '$lib/components/ui';
</script>

<!-- Glass morphism cards -->
<GlassCard class="p-6">
  <h3 class="text-lg font-semibold">Card Title</h3>
  <p>Card content with glass effect</p>
</GlassCard>

<!-- Loading states -->
{#if loading}
  <LoadingSkeleton />
{/if}

<!-- Floating action button -->
<FloatingActionButton
  icon="plus"
  on:click={handleAdd}
  tooltip="Add New Item"
/>
```

### **Dashboard Components** ✅ **ENHANCE WITH REAL DATA**

```svelte
<script>
  import { MetricsCard, LiveFeed, SystemMonitor } from '$lib/components/dashboard';
  import { AnimatedChart } from '$lib/components/Charts';

  // Load real data
  let metrics = {
    emails_processed: 156,
    classification_accuracy: 94.5,
    avg_processing_time: 3.2,
    system_uptime: 99.8
  };
</script>

<!-- Use existing components with real data -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
  <MetricsCard
    title="Emails Processed"
    value={metrics.emails_processed}
    subtitle="Last 24 hours"
    trend="up"
    status="success"
  />

  <MetricsCard
    title="Accuracy"
    value={metrics.classification_accuracy}
    subtitle="Classification"
    format="percentage"
    status="success"
  />
</div>

<!-- Real-time components -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
  <LiveFeed />
  <SystemMonitor />
</div>
```

## Design System Usage

### **Colors** ✅ **USE ESTABLISHED PALETTE**

```css
/* Use existing color system */
.custom-element {
  /* Primary colors */
  @apply bg-primary text-primary-content;

  /* Glass effect */
  @apply bg-glass-light dark:bg-glass-dark;

  /* Status colors */
  @apply text-success; /* or warning, error, info */

  /* Brand colors */
  @apply bg-gradient-to-br from-primary to-secondary;
}
```

### **Typography** ✅ **USE ESTABLISHED SCALE**

```svelte
<!-- Headings -->
<h1 class="text-3xl font-bold">Main Title</h1>
<h2 class="text-2xl font-semibold">Section Title</h2>
<h3 class="text-lg font-medium">Subsection</h3>

<!-- Body text -->
<p class="text-base text-base-content">Regular text</p>
<p class="text-sm text-base-content/70">Secondary text</p>

<!-- Special text -->
<span class="badge badge-primary">Status Badge</span>
<code class="code">Code text</code>
```

### **Spacing & Layout** ✅ **USE ESTABLISHED PATTERNS**

```svelte
<!-- Standard spacing -->
<div class="space-y-6">        <!-- Vertical spacing -->
  <div class="space-x-4">     <!-- Horizontal spacing -->

    <!-- Grid layouts -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <!-- Grid items -->
    </div>

    <!-- Flex layouts -->
    <div class="flex justify-between items-center">
      <!-- Flex items -->
    </div>

  </div>
</div>

<!-- Standard padding/margin -->
<div class="p-6">              <!-- Padding -->
  <div class="m-4">            <!-- Margin -->
    <div class="px-4 py-2">    <!-- Specific padding -->
      Content
    </div>
  </div>
</div>
```

## Testing Patterns

### **Component Testing**

```typescript
// src/lib/components/example/NewComponent.test.ts
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { vi } from 'vitest';
import NewComponent from './NewComponent.svelte';
import { apiClient } from '$lib/api/apiClient';

// Mock API client
vi.mock('$lib/api/apiClient', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}));

describe('NewComponent', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render with initial data', () => {
    const props = { data: { title: 'Test Title' } };
    render(NewComponent, { props });

    expect(screen.getByText('Test Title')).toBeInTheDocument();
  });

  it('should handle API call success', async () => {
    const mockResponse = { success: true };
    apiClient.post.mockResolvedValue(mockResponse);

    const props = { data: { title: 'Test' } };
    render(NewComponent, { props });

    const button = screen.getByRole('button', { name: /action/i });
    await fireEvent.click(button);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith('/some/endpoint', props.data);
    });
  });

  it('should handle API errors gracefully', async () => {
    const mockError = new Error('API Error');
    apiClient.post.mockRejectedValue(mockError);

    const props = { data: { title: 'Test' } };
    render(NewComponent, { props });

    const button = screen.getByRole('button', { name: /action/i });
    await fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });
});
```

### **Store Testing**

```typescript
// src/lib/stores/clientStore.test.ts
import { get } from 'svelte/store';
import { vi } from 'vitest';
import { clientStore, clientActions } from './clientStore';
import { clientService } from '$lib/services/clientService';

vi.mock('$lib/services/clientService');

describe('clientStore', () => {
  beforeEach(() => {
    clientStore.set({
      currentClient: null,
      routingRules: null,
      branding: null,
      clients: [],
      loading: false,
      error: null
    });
    vi.clearAllMocks();
  });

  it('should load clients successfully', async () => {
    const mockClients = [{ id: '1', name: 'Test Client' }];
    clientService.getClients.mockResolvedValue(mockClients);

    await clientActions.loadClients();

    const state = get(clientStore);
    expect(state.clients).toEqual(mockClients);
    expect(state.loading).toBe(false);
    expect(state.error).toBe(null);
  });

  it('should handle errors when loading clients', async () => {
    const mockError = new Error('Failed to load');
    clientService.getClients.mockRejectedValue(mockError);

    await clientActions.loadClients();

    const state = get(clientStore);
    expect(state.clients).toEqual([]);
    expect(state.loading).toBe(false);
    expect(state.error).toBe('Failed to load');
  });
});
```

## Performance Considerations

### **Code Splitting**

```typescript
// Use dynamic imports for large components
const LazyComponent = lazy(() => import('./HeavyComponent.svelte'));

// Or in routes
export const load = async () => {
  const { default: Component } = await import('$lib/components/HeavyComponent.svelte');
  return { Component };
};
```

### **Optimized Data Loading**

```typescript
// Use parallel loading when possible
const loadPageData = async (clientId: string) => {
  const [client, metrics, activities] = await Promise.all([
    clientService.getClient(clientId),
    dashboardService.getMetrics(clientId),
    dashboardService.getActivities(clientId)
  ]);

  return { client, metrics, activities };
};

// Use reactive statements for derived data
$: filteredData = data.filter(item =>
  item.category === selectedCategory
);
```

### **Memory Management**

```svelte
<script>
  import { onDestroy } from 'svelte';

  let websocketConnection;
  let intervalId;

  onMount(() => {
    // Setup connections
    websocketConnection = connectWebSocket();
    intervalId = setInterval(refreshData, 30000);
  });

  onDestroy(() => {
    // Cleanup
    websocketConnection?.close();
    clearInterval(intervalId);
  });
</script>
```

## Common Development Tasks

### **Adding a New Dashboard Widget**

1. **Create the component**:
```svelte
<!-- src/lib/components/dashboard/NewWidget.svelte -->
<script lang="ts">
  import { MetricsCard } from '$lib/components/dashboard';
  import { apiClient } from '$lib/api/apiClient';

  export let clientId: string;

  let data = null;
  let loading = true;

  const loadData = async () => {
    try {
      data = await apiClient.get(`/api/v1/dashboard/clients/${clientId}/new-metric`);
    } catch (error) {
      console.error('Failed to load widget data:', error);
    } finally {
      loading = false;
    }
  };

  onMount(loadData);
</script>

{#if loading}
  <div class="skeleton h-32 w-full"></div>
{:else if data}
  <MetricsCard
    title="New Metric"
    value={data.value}
    subtitle={data.subtitle}
    trend={data.trend}
    status={data.status}
  />
{/if}
```

2. **Add to dashboard page**:
```svelte
<!-- src/routes/dashboard/+page.svelte -->
<script>
  import { NewWidget } from '$lib/components/dashboard';

  // Add to existing widgets
</script>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
  <!-- Existing widgets -->
  <NewWidget {clientId} />
</div>
```

### **Adding a New Configuration Form**

1. **Create the form component** following the form pattern above
2. **Add service methods** for the new endpoints
3. **Update the store** if needed for state management
4. **Add to navigation** and routing

### **Adding Real-time Features**

1. **Extend WebSocket handler**:
```typescript
// Add new message type handling
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'new_metric_update':
      newMetricStore.update(data.value);
      break;
    // Existing cases...
  }
};
```

2. **Update components** to use real-time data

## Summary

The frontend development process is **streamlined and efficient** due to the excellent foundation already in place. Follow these patterns:

1. **Use existing components** rather than building new ones
2. **Follow established patterns** for consistency
3. **Build services** for API integration
4. **Create stores** for state management
5. **Write tests** for new functionality
6. **Enhance existing** rather than replace

With this approach, new features can be developed **rapidly** while maintaining **professional quality** and **consistency** throughout the application.
