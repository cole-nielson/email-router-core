# Frontend-Backend API Integration Guide

🔗 **Complete guide for integrating the SvelteKit frontend with the FastAPI backend**

## Overview

This guide provides specific instructions for connecting the existing frontend components to the comprehensive backend APIs. The backend provides 50+ endpoints covering authentication, client management, analytics, and real-time features.

## API Client Architecture

### **Complete Service Layer** ✅ **PRODUCTION-READY**

**New Service Architecture**: `frontend/src/lib/services/`

```typescript
// Complete service layer now available
import { services } from '$lib/services';

// All backend APIs accessible through standardized services:
✅ AuthService - User management, JWT, RBAC, sessions
✅ ClientService - Client config, routing, branding, domains
✅ DashboardService - Metrics, analytics, activity feeds
✅ SystemService - Health monitoring, diagnostics, logs
✅ BaseService - Standardized error handling & patterns
✅ TypeScript types for all API domains
✅ 50+ endpoint mappings with consistent patterns
```

### **APIClient Foundation** ✅ **PRODUCTION-READY**

Location: `frontend/src/lib/api/apiClient.ts`

```typescript
class APIClient {
  // Already implemented features:
  ✅ JWT token management with automatic refresh
  ✅ Request/response interceptors
  ✅ Error handling with custom APIError class
  ✅ Retry logic for failed requests
  ✅ Environment-aware base URL configuration
  ✅ Type-safe request/response handling
}
```

**Current Configuration:**
```typescript
// Development: http://localhost:8080
// Production: https://email-router-696958557925.us-central1.run.app
```

## Authentication Integration

### **Login Flow** ✅ **COMPLETE**

**Frontend Component**: `frontend/src/lib/components/auth/LoginForm.svelte`
**Backend Endpoint**: `POST /auth/login`

```typescript
// Already implemented in authStore.ts
interface LoginRequest {
  username: string;
  password: string;
  client_id?: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
  client_id?: string;
  role: "super_admin" | "client_admin" | "client_user";
  permissions: string[];
}
```

**Integration Status**: ✅ **Complete - Working authentication flow**

### **User Management** 🔄 **NEEDS COMPONENTS**

**Required Components**: User registration, user list, session management
**Backend Endpoints**:
```typescript
POST /auth/register          // Create new user (admin only)
GET  /auth/users            // List users with pagination
DELETE /auth/users/{id}     // Delete user (super admin only)
GET  /auth/sessions         // List active sessions
DELETE /auth/sessions/{id}  // Revoke specific session
```

**Implementation Plan**:
```svelte
<!-- src/lib/components/admin/UserManagement.svelte -->
<script lang="ts">
  import { apiClient } from '$lib/api/apiClient';
  import { authStore } from '$lib/stores/authStore';

  interface User {
    id: number;
    username: string;
    email: string;
    full_name: string;
    role: string;
    client_id?: string;
    status: string;
    created_at: string;
    last_login_at?: string;
  }

  let users: User[] = [];
  let loading = false;

  // Load users (admin only)
  const loadUsers = async () => {
    if (!$authStore.user?.permissions.includes('users:read')) return;

    loading = true;
    try {
      const response = await apiClient.get('/auth/users');
      users = response.users;
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      loading = false;
    }
  };

  // Create new user
  const createUser = async (userData: any) => {
    try {
      await apiClient.post('/auth/register', userData);
      await loadUsers(); // Refresh list
    } catch (error) {
      console.error('Failed to create user:', error);
    }
  };
</script>
```

## Client Management Integration

### **Client List Component** 🔄 **NEEDS BUILDING**

**Backend Endpoint**: `GET /api/v1/clients`
**Response Data**:
```typescript
interface ClientSummary {
  id: string;
  name: string;
  industry: string;
  status: "active" | "inactive";
  domain_count: number;
  last_activity: string;
  health_status: "healthy" | "warning" | "error";
  email_volume_24h: number;
}
```

**Implementation**:
```svelte
<!-- src/lib/components/clients/ClientList.svelte -->
<script lang="ts">
  import { apiClient } from '$lib/api/apiClient';
  import { MetricsCard } from '$lib/components/dashboard';

  let clients: ClientSummary[] = [];
  let loading = true;

  const loadClients = async () => {
    try {
      const response = await apiClient.get('/api/v1/clients');
      clients = response.clients;
    } catch (error) {
      console.error('Failed to load clients:', error);
    } finally {
      loading = false;
    }
  };

  onMount(loadClients);
</script>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {#each clients as client}
    <MetricsCard
      title={client.name}
      value={client.email_volume_24h}
      subtitle="emails/24h"
      status={client.health_status}
      trend="up"
      onClick={() => goto(`/dashboard/clients/${client.id}`)}
    />
  {/each}
</div>
```

### **Client Detail Component** 🔄 **NEEDS BUILDING**

**Backend Endpoints**:
```typescript
GET /api/v2/config/clients/{id}              // Full client configuration
GET /api/v2/config/clients/{id}/routing      // Routing rules
GET /api/v2/config/clients/{id}/branding     // Branding configuration
```

**Implementation**:
```svelte
<!-- src/lib/components/clients/ClientDetail.svelte -->
<script lang="ts">
  import { page } from '$app/stores';

  interface ClientConfig {
    id: string;
    name: string;
    industry: string;
    status: "active" | "inactive";
    timezone: string;
    business_hours: string;
    domains: string[];
    created_at: string;
    updated_at: string;
  }

  const clientId = $page.params.clientId;
  let clientConfig: ClientConfig | null = null;
  let routingRules: Record<string, string> = {};
  let branding: any = null;

  const loadClientData = async () => {
    try {
      const [configRes, routingRes, brandingRes] = await Promise.all([
        apiClient.get(`/api/v2/config/clients/${clientId}`),
        apiClient.get(`/api/v2/config/clients/${clientId}/routing`),
        apiClient.get(`/api/v2/config/clients/${clientId}/branding`)
      ]);

      clientConfig = configRes;
      routingRules = routingRes.rules;
      branding = brandingRes;
    } catch (error) {
      console.error('Failed to load client data:', error);
    }
  };
</script>
```

## Dashboard Analytics Integration

### **Metrics Integration** 🔄 **REPLACE MOCK DATA**

**Existing Component**: `frontend/src/lib/components/dashboard/MetricsCard.svelte`
**Backend Endpoint**: `GET /api/v1/dashboard/clients/{id}/metrics`

**Current Mock Data → Real API Integration**:
```typescript
// Replace this mock data:
const mockMetrics = {
  emails_processed_24h: 156,
  classification_accuracy: 94.5,
  avg_processing_time: 3.2,
  system_uptime: 99.8
};

// With real API call:
interface DashboardMetrics {
  emails_processed_24h: number;
  emails_processed_7d: number;
  classification_accuracy: number;
  avg_processing_time: number;
  routing_success_rate: number;
  system_uptime: number;
  active_automations: number;
  last_updated: string;
}

const loadMetrics = async (clientId: string): Promise<DashboardMetrics> => {
  return await apiClient.get(`/api/v1/dashboard/clients/${clientId}/metrics`);
};
```

### **Live Feed Integration** 🔄 **CONNECT TO REAL DATA**

**Existing Component**: `frontend/src/lib/components/dashboard/LiveFeed.svelte`
**Backend Endpoint**: `GET /api/v1/dashboard/clients/{id}/activity`

```typescript
interface ActivityItem {
  id: string;
  timestamp: string;
  type: "email_received" | "classification_completed" | "routing_completed" | "email_sent";
  description: string;
  details: {
    sender?: string;
    recipient?: string;
    category?: string;
    confidence?: number;
    processing_time?: number;
  };
  status: "success" | "warning" | "error";
}

// Replace mock data with real API
const loadActivity = async (clientId: string): Promise<ActivityItem[]> => {
  const response = await apiClient.get(`/api/v1/dashboard/clients/${clientId}/activity`);
  return response.activities;
};
```

### **Charts Integration** 🔄 **CONNECT TO ANALYTICS**

**Existing Component**: `frontend/src/lib/components/Charts/AnimatedChart.svelte`
**Backend Endpoints**:
```typescript
GET /api/v1/dashboard/analytics/trends              // Trend analysis
GET /api/v1/dashboard/analytics/volume-patterns     // Email volume patterns
GET /api/v1/dashboard/analytics/performance-insights // Performance data
```

**Implementation**:
```typescript
// Volume patterns chart
const loadVolumeData = async (clientId: string) => {
  const response = await apiClient.get(`/api/v1/dashboard/analytics/volume-patterns?client_id=${clientId}`);

  return {
    labels: response.time_periods,
    datasets: [{
      label: 'Email Volume',
      data: response.volumes,
      borderColor: 'rgb(75, 192, 192)',
      tension: 0.1
    }]
  };
};

// Performance trends chart
const loadPerformanceData = async (clientId: string) => {
  const response = await apiClient.get(`/api/v1/dashboard/analytics/performance-insights?client_id=${clientId}`);

  return {
    labels: response.time_periods,
    datasets: [
      {
        label: 'Processing Time (s)',
        data: response.processing_times,
        borderColor: 'rgb(255, 99, 132)'
      },
      {
        label: 'Classification Accuracy (%)',
        data: response.accuracy_scores,
        borderColor: 'rgb(54, 162, 235)'
      }
    ]
  };
};
```

## Configuration Management Integration

### **Routing Rules Editor** 🔄 **NEEDS BUILDING**

**Backend Endpoints**:
```typescript
GET /api/v2/config/clients/{id}/routing           // Get routing rules
PUT /api/v2/config/clients/{id}/routing/{category} // Update specific rule
```

**Implementation**:
```svelte
<!-- src/lib/components/config/RoutingEditor.svelte -->
<script lang="ts">
  interface RoutingRule {
    category: string;
    email: string;
    fallback_email?: string;
    priority: number;
  }

  let routingRules: RoutingRule[] = [];
  let editingRule: RoutingRule | null = null;

  const loadRoutingRules = async () => {
    const response = await apiClient.get(`/api/v2/config/clients/${clientId}/routing`);
    routingRules = Object.entries(response.rules).map(([category, email]) => ({
      category,
      email: email as string,
      priority: 1
    }));
  };

  const updateRoutingRule = async (category: string, email: string) => {
    try {
      await apiClient.put(`/api/v2/config/clients/${clientId}/routing/${category}`, {
        email,
        fallback_email: null,
        priority: 1
      });
      await loadRoutingRules(); // Refresh
    } catch (error) {
      console.error('Failed to update routing rule:', error);
    }
  };
</script>

<div class="space-y-4">
  {#each routingRules as rule}
    <div class="glass-card p-4">
      <div class="flex justify-between items-center">
        <span class="font-medium">{rule.category}</span>
        <input
          type="email"
          value={rule.email}
          on:blur={(e) => updateRoutingRule(rule.category, e.target.value)}
          class="input input-bordered"
        />
      </div>
    </div>
  {/each}
</div>
```

### **Branding Editor** 🔄 **NEEDS BUILDING**

**Backend Endpoints**:
```typescript
GET /api/v2/config/clients/{id}/branding    // Get branding config
PUT /api/v2/config/clients/{id}/branding    // Update branding
```

**Implementation**:
```svelte
<!-- src/lib/components/config/BrandingEditor.svelte -->
<script lang="ts">
  interface BrandingConfig {
    company_name: string;
    primary_color: string;
    secondary_color: string;
    logo_url?: string;
    email_signature: string;
    footer_text?: string;
  }

  let branding: BrandingConfig = {
    company_name: '',
    primary_color: '#667eea',
    secondary_color: '#764ba2',
    email_signature: '',
    footer_text: ''
  };

  const loadBranding = async () => {
    const response = await apiClient.get(`/api/v2/config/clients/${clientId}/branding`);
    branding = response;
  };

  const saveBranding = async () => {
    try {
      await apiClient.put(`/api/v2/config/clients/${clientId}/branding`, branding);
      // Show success message
    } catch (error) {
      console.error('Failed to save branding:', error);
    }
  };
</script>

<form on:submit|preventDefault={saveBranding} class="space-y-6">
  <div class="glass-card p-6">
    <h3 class="text-lg font-semibold mb-4">Company Branding</h3>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label class="label">Company Name</label>
        <input bind:value={branding.company_name} class="input input-bordered w-full" />
      </div>

      <div>
        <label class="label">Logo URL</label>
        <input bind:value={branding.logo_url} class="input input-bordered w-full" />
      </div>

      <div>
        <label class="label">Primary Color</label>
        <input type="color" bind:value={branding.primary_color} class="input input-bordered w-full" />
      </div>

      <div>
        <label class="label">Secondary Color</label>
        <input type="color" bind:value={branding.secondary_color} class="input input-bordered w-full" />
      </div>
    </div>

    <div class="mt-4">
      <label class="label">Email Signature</label>
      <textarea bind:value={branding.email_signature} class="textarea textarea-bordered w-full h-32"></textarea>
    </div>

    <button type="submit" class="btn btn-primary mt-4">Save Branding</button>
  </div>
</form>

<!-- Live Preview -->
<div class="glass-card p-6 mt-6">
  <h3 class="text-lg font-semibold mb-4">Preview</h3>
  <div class="border rounded-lg p-4" style="background: linear-gradient(135deg, {branding.primary_color}22, {branding.secondary_color}22)">
    <div class="flex items-center mb-4">
      {#if branding.logo_url}
        <img src={branding.logo_url} alt="Logo" class="h-12 mr-4" />
      {/if}
      <h4 class="text-xl font-bold" style="color: {branding.primary_color}">{branding.company_name}</h4>
    </div>
    <div class="whitespace-pre-line text-sm">{branding.email_signature}</div>
  </div>
</div>
```

## Real-time Integration

### **WebSocket Connection** ✅ **ARCHITECTURE READY**

**Existing Infrastructure**: `frontend/src/lib/utils/websocket.ts`
**Backend Endpoint**: `WS /ws/client/{client_id}`

**Implementation**:
```typescript
// Connect to real-time updates
const connectToWebSocket = (clientId: string) => {
  const wsUrl = `${WS_BASE_URL}/ws/client/${clientId}`;
  const socket = new WebSocket(wsUrl);

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.type) {
      case 'metric_update':
        dashboardStore.update(state => ({
          ...state,
          metrics: { ...state.metrics, ...data.metrics }
        }));
        break;

      case 'activity_update':
        dashboardStore.update(state => ({
          ...state,
          activities: [data.activity, ...state.activities.slice(0, 49)]
        }));
        break;

      case 'alert':
        toast.show(data.message, data.severity);
        break;
    }
  };

  return socket;
};
```

## System Monitoring Integration

### **Health Dashboard** 🔄 **ENHANCE EXISTING**

**Existing Component**: `frontend/src/lib/components/dashboard/SystemMonitor.svelte`
**Backend Endpoints**:
```typescript
GET /health              // Basic health check
GET /health/detailed     // Comprehensive diagnostics
GET /metrics            // Prometheus metrics
```

**Enhancement**:
```typescript
interface DetailedHealth {
  status: "healthy" | "degraded" | "down";
  components: {
    api_server: ComponentStatus;
    ai_classifier: ComponentStatus;
    email_service: ComponentStatus;
    database: ComponentStatus;
    webhooks: ComponentStatus;
  };
  performance: {
    avg_response_time: number;
    requests_per_minute: number;
    error_rate: number;
  };
  timestamp: string;
}

const loadSystemHealth = async (): Promise<DetailedHealth> => {
  return await apiClient.get('/health/detailed');
};
```

## Error Handling & Loading States

### **Standardized Error Handling**

```typescript
// Global error handler for API calls
const handleAPIError = (error: APIError, context: string) => {
  switch (error.status) {
    case 401:
      authStore.logout();
      goto('/login');
      break;
    case 403:
      toast.error('Permission denied');
      break;
    case 404:
      toast.error(`${context} not found`);
      break;
    case 500:
      toast.error('System error occurred');
      break;
    default:
      toast.error(error.message || 'An error occurred');
  }
};
```

### **Loading State Pattern**

```svelte
<script lang="ts">
  let loading = false;
  let error: string | null = null;
  let data: any = null;

  const loadData = async () => {
    loading = true;
    error = null;

    try {
      data = await apiClient.get('/some/endpoint');
    } catch (err) {
      error = err.message;
      handleAPIError(err, 'Data');
    } finally {
      loading = false;
    }
  };
</script>

{#if loading}
  <LoadingSkeleton />
{:else if error}
  <div class="alert alert-error">
    <span>{error}</span>
    <button on:click={loadData} class="btn btn-sm">Retry</button>
  </div>
{:else if data}
  <!-- Content -->
{/if}
```

## Development Workflow

### **API Development Pattern**

1. **Define Types**: Create TypeScript interfaces matching backend models
2. **Create Service**: Build service class for specific domain (clients, users, etc.)
3. **Build Component**: Create Svelte component using existing patterns
4. **Add to Store**: Integrate with appropriate Svelte store
5. **Handle Errors**: Implement proper error handling and loading states
6. **Add Tests**: Write unit tests for components and services

### **Testing API Integration**

```typescript
// Mock API client for testing
export const mockAPIClient = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn()
};

// Test component with real API integration
describe('ClientList', () => {
  it('should load clients from API', async () => {
    mockAPIClient.get.mockResolvedValue({
      clients: [{ id: '1', name: 'Test Client' }]
    });

    render(ClientList);

    await waitFor(() => {
      expect(screen.getByText('Test Client')).toBeInTheDocument();
    });
  });
});
```

## Summary

The frontend is **extremely well-positioned** for rapid API integration. The existing infrastructure handles authentication, error handling, loading states, and real-time updates.

**Immediate Tasks:**
1. Replace mock data in existing dashboard components
2. Build client management interfaces using established patterns
3. Create configuration management forms
4. Implement WebSocket integration for real-time updates

**Timeline**: With the excellent foundation in place, full API integration can be completed in **2-3 weeks** following the established patterns and component architecture.
