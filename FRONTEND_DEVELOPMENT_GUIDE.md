# Frontend Development Guide for Email Router

🎨 **Comprehensive guide for building the Email Router frontend with complete backend integration**

## Project Overview

The Email Router is a **production-ready enterprise multi-tenant AI email router** with sophisticated authentication, client management, and email processing capabilities. This guide provides everything needed to build a modern frontend that integrates with our completed backend system.

### **Current Backend Status (COMPLETED)**
- ✅ **Multi-tenant Architecture** - Complete client isolation and domain matching
- ✅ **AI Email Classification** - Claude 3.5 Sonnet integration with 95%+ accuracy
- ✅ **Email Processing Pipeline** - Mailgun integration with 5-7 second processing
- ✅ **Authentication System** - Enterprise-grade JWT + API key dual authentication
- ✅ **Role-Based Access Control** - 3-tier permission system with client scoping
- ✅ **Configuration APIs** - Complete CRUD operations for client management
- ✅ **Real-time Processing** - Live email routing with comprehensive logging

### **Authentication Architecture**
```
┌─────────────────┐    JWT Tokens     ┌──────────────────┐
│   Web Frontend  │ ◄──────────────► │  FastAPI Backend │
│   (SvelteKit)   │                  │                  │
└─────────────────┘                  └──────────────────┘
        │                                      │
        │ Login/Register                       │ Validate/Authorize
        │ Client Management                    │ RBAC Permissions
        │ Real-time Updates                    │ Multi-tenant Data
        └──────────────────────────────────────┘
```

### **User Roles & Permissions**
- **`super_admin`** - Global system access, all clients, user management
- **`client_admin`** - Full access to assigned client, user management for client
- **`client_user`** - Read-only access to assigned client
- **`api_user`** - Automated system access via API keys

## Existing Frontend Codebase Analysis

### **Current UI Directory Structure**
```
ui/
├── .svelte-kit/           # SvelteKit build artifacts (IGNORE - auto-generated)
│   ├── ambient.d.ts       # Modified but auto-generated
│   └── generated/         # All auto-generated
├── src/                   # Main source directory (LIKELY OUTDATED)
├── static/                # Static assets
├── package.json           # Dependencies (REVIEW & UPDATE)
├── svelte.config.js       # SvelteKit configuration
├── vite.config.js         # Vite build configuration
└── tsconfig.json          # TypeScript configuration
```

### **⚠️ IMPORTANT: Existing Frontend Status**
The existing `ui/` directory contains:
- **SvelteKit setup** - Good foundation but likely outdated
- **Generated files** - Should be ignored (`.svelte-kit/`)
- **Legacy components** - May not match current backend API
- **No authentication integration** - Missing JWT auth flows
- **No real data integration** - Likely contains placeholder/demo data

### **🚫 DO NOT USE:**
- Any existing demo/template data
- Hardcoded mock responses
- Fake user data or client configurations
- Legacy API endpoints that don't exist
- Generated SvelteKit files (they'll be regenerated)

### **✅ DO USE:**
- SvelteKit framework setup
- TypeScript configuration
- Vite build configuration
- Basic project structure concept

## Backend API Integration Points

### **Authentication Endpoints**
```typescript
// Base URL: http://localhost:8080 (development)
const API_BASE = process.env.PUBLIC_API_BASE_URL || 'http://localhost:8080';

// Authentication flows
POST /auth/login              // Login with username/password
POST /auth/refresh            // Refresh access token
POST /auth/logout             // Logout and revoke tokens
GET  /auth/me                 // Get current user info
PUT  /auth/me/password        // Change password
GET  /auth/sessions          // List active sessions
DELETE /auth/sessions/{id}    // Revoke specific session

// User management (admin only)
POST /auth/register          // Create new user
GET  /auth/users             // List users
DELETE /auth/users/{id}      // Delete user
```

### **Client Management Endpoints**
```typescript
// Client operations (requires JWT authentication)
GET  /api/v2/clients/{client_id}                    // Get client config
PUT  /api/v2/clients/{client_id}                    // Update client
GET  /api/v2/clients/{client_id}/routing            // Get routing rules
PUT  /api/v2/clients/{client_id}/routing/{category} // Update routing
GET  /api/v2/clients/{client_id}/branding           // Get branding
PUT  /api/v2/clients/{client_id}/branding           // Update branding
GET  /api/v2/clients/{client_id}/response-times     // Get response times
PUT  /api/v2/clients/{client_id}/ai-prompts/{type}  // Update AI prompts

// Legacy endpoints (API key auth - for reference)
GET  /api/v1/status                                 // System status
GET  /api/v1/clients                                // List clients
```

### **Real-time & Monitoring**
```typescript
// WebSocket for real-time updates
WS   /ws/client/{client_id}     // Real-time client data

// Health and monitoring
GET  /health                    // Basic health check
GET  /health/detailed          // Detailed system health
GET  /metrics                  // Prometheus metrics
GET  /webhooks/status          // Webhook processing status
```

## Data Models & Types

### **Authentication Types**
```typescript
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

interface AuthenticatedUser {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: "super_admin" | "client_admin" | "client_user";
  client_id?: string;
  status: "active" | "inactive" | "pending";
  created_at: string;
  last_login_at?: string;
}

interface UserSession {
  session_id: string;
  token_type: "access" | "refresh";
  created_at: string;
  last_used_at?: string;
  expires_at: string;
  ip_address?: string;
  user_agent?: string;
}
```

### **Client Configuration Types**
```typescript
interface ClientConfig {
  id: string;
  name: string;
  industry: string;
  status: "active" | "inactive";
  timezone: string;
  business_hours: string;
  created_at: string;
  updated_at: string;
}

interface RoutingRules {
  rules: Record<string, string>; // category -> email_address
}

interface BrandingConfig {
  company_name: string;
  primary_color: string;
  secondary_color: string;
  logo_url?: string;
  email_signature: string;
  footer_text?: string;
  colors?: Record<string, any>;
}

interface ResponseTimes {
  times: Record<string, {
    target_response: string;
    business_hours_only: boolean;
  }>;
}
```

### **System Status Types**
```typescript
interface SystemStatus {
  status: "healthy" | "degraded" | "down";
  components: {
    api_server: ComponentStatus;
    ai_classifier: ComponentStatus;
    email_service: ComponentStatus;
    database: ComponentStatus;
  };
  timestamp: string;
}

interface ComponentStatus {
  status: "healthy" | "degraded" | "down";
  response_time_ms: number;
  details: string;
}
```

## Development Milestones

### **🎯 Milestone 1: Authentication Foundation (Week 1)**

**Objective:** Build complete authentication system with JWT integration

**Tasks:**
1. **Setup & Dependencies**
   - Clean existing `ui/src/` directory
   - Install/update dependencies: SvelteKit, TypeScript, Tailwind CSS
   - Configure environment variables for API base URL
   - Setup development server with proxy to backend

2. **Authentication Service**
   ```typescript
   // src/lib/auth/authService.ts
   class AuthService {
     private accessToken: string | null = null;
     private refreshToken: string | null = null;

     async login(credentials: LoginRequest): Promise<TokenResponse>
     async refresh(): Promise<void>
     async logout(): Promise<void>
     getCurrentUser(): Promise<AuthenticatedUser>
     isAuthenticated(): boolean
     getToken(): string | null
   }
   ```

3. **Auth Store & Context**
   ```typescript
   // src/lib/stores/auth.ts
   export const authStore = writable<{
     user: AuthenticatedUser | null;
     isAuthenticated: boolean;
     isLoading: boolean;
   }>({
     user: null,
     isAuthenticated: false,
     isLoading: true
   });
   ```

4. **Login/Register Components**
   - Login form with validation
   - Password change form
   - Session management UI
   - Error handling and loading states

5. **Route Protection**
   ```typescript
   // src/lib/auth/authGuard.ts
   export function requireAuth(role?: string) {
     // Protect routes based on authentication and role
   }
   ```

**Deliverables:**
- Working login/logout flow
- Protected routes with role checking
- JWT token management with automatic refresh
- User profile and session management

---

### **🎯 Milestone 2: Client Management Dashboard (Week 2)**

**Objective:** Build client configuration and management interface

**Tasks:**
1. **Client Data Service**
   ```typescript
   // src/lib/services/clientService.ts
   class ClientService {
     async getClient(clientId: string): Promise<ClientConfig>
     async updateClient(clientId: string, data: Partial<ClientConfig>): Promise<ClientConfig>
     async getRoutingRules(clientId: string): Promise<RoutingRules>
     async updateRoutingRule(clientId: string, category: string, email: string): Promise<void>
     async getBranding(clientId: string): Promise<BrandingConfig>
     async updateBranding(clientId: string, branding: Partial<BrandingConfig>): Promise<BrandingConfig>
   }
   ```

2. **Client Dashboard Layout**
   - Sidebar navigation with sections:
     - Overview
     - Routing Rules
     - Branding
     - AI Prompts
     - Response Times
     - Users (admin only)
   - Header with user info and logout

3. **Configuration Forms**
   - Routing rules management (category → email mapping)
   - Branding configuration with live preview
   - Response time settings
   - Client details editing

4. **Permission-based UI**
   ```typescript
   // Show/hide features based on user role
   {#if $authStore.user?.role === 'super_admin'}
     <AdminOnlyFeature />
   {/if}

   {#if hasPermission('routing:write')}
     <EditRoutingButton />
   {/if}
   ```

**Deliverables:**
- Complete client management interface
- Role-based feature visibility
- Real-time configuration updates
- Form validation and error handling

---

### **🎯 Milestone 3: System Monitoring & Analytics (Week 3)**

**Objective:** Build system health monitoring and email processing analytics

**Tasks:**
1. **System Health Dashboard**
   ```typescript
   // src/lib/services/monitoringService.ts
   class MonitoringService {
     async getSystemStatus(): Promise<SystemStatus>
     async getDetailedHealth(): Promise<DetailedHealth>
     async getMetrics(): Promise<Metrics>
     async getWebhookStatus(): Promise<WebhookStatus>
   }
   ```

2. **Real-time Updates**
   ```typescript
   // src/lib/websocket/websocketService.ts
   class WebSocketService {
     connect(clientId: string): void
     onMessage(callback: (data: any) => void): void
     disconnect(): void
   }
   ```

3. **Analytics Components**
   - System health indicators
   - Email processing statistics
   - Response time charts
   - Error rate monitoring
   - Client usage analytics

4. **Real-time Email Flow**
   - Live email processing feed
   - Classification results display
   - Routing decisions visualization
   - Processing time metrics

**Deliverables:**
- System health monitoring dashboard
- Real-time email processing feed
- Performance analytics and charts
- Alert system for issues

---

### **🎯 Milestone 4: Advanced Features & Polish (Week 4)**

**Objective:** Complete the application with advanced features and production polish

**Tasks:**
1. **User Management (Super Admin)**
   ```typescript
   // src/lib/services/userService.ts
   class UserService {
     async getUsers(clientId?: string): Promise<AuthenticatedUser[]>
     async createUser(userData: UserCreateRequest): Promise<AuthenticatedUser>
     async deleteUser(userId: number): Promise<void>
     async getUserSessions(): Promise<UserSession[]>
     async revokeSession(sessionId: string): Promise<void>
   }
   ```

2. **Advanced Configuration**
   - AI prompt editing with syntax highlighting
   - Email template customization
   - Domain configuration management
   - Bulk operations interface

3. **Data Export & Import**
   - Configuration export/import
   - Email processing logs export
   - System configuration backup

4. **Production Features**
   - Dark/light theme toggle
   - Responsive mobile design
   - Accessibility improvements
   - Performance optimization
   - Error boundary components

**Deliverables:**
- Complete user management system
- Advanced configuration tools
- Production-ready UI/UX
- Mobile responsive design

## Technical Implementation Guidelines

### **API Integration Pattern**
```typescript
// src/lib/api/apiClient.ts
class APIClient {
  private baseURL: string;
  private authService: AuthService;

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.authService.getToken();

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
    });

    if (response.status === 401) {
      // Token expired, try refresh
      await this.authService.refresh();
      return this.request(endpoint, options); // Retry
    }

    if (!response.ok) {
      throw new APIError(response.status, await response.text());
    }

    return response.json();
  }
}
```

### **Error Handling Strategy**
```typescript
// src/lib/errors/errorHandling.ts
export class APIError extends Error {
  constructor(
    public status: number,
    public message: string,
    public details?: any
  ) {
    super(message);
  }
}

export function handleAPIError(error: APIError) {
  switch (error.status) {
    case 401:
      // Redirect to login
      goto('/login');
      break;
    case 403:
      // Show permission denied
      notifications.error('Permission denied');
      break;
    case 500:
      // Show system error
      notifications.error('System error occurred');
      break;
    default:
      notifications.error(error.message);
  }
}
```

### **State Management Pattern**
```typescript
// src/lib/stores/clientStore.ts
interface ClientState {
  currentClient: ClientConfig | null;
  routingRules: RoutingRules | null;
  branding: BrandingConfig | null;
  isLoading: boolean;
  error: string | null;
}

export const clientStore = writable<ClientState>({
  currentClient: null,
  routingRules: null,
  branding: null,
  isLoading: false,
  error: null,
});

// Actions
export const clientActions = {
  async loadClient(clientId: string) {
    clientStore.update(state => ({ ...state, isLoading: true }));

    try {
      const client = await clientService.getClient(clientId);
      const routingRules = await clientService.getRoutingRules(clientId);
      const branding = await clientService.getBranding(clientId);

      clientStore.set({
        currentClient: client,
        routingRules,
        branding,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      clientStore.update(state => ({
        ...state,
        isLoading: false,
        error: error.message,
      }));
    }
  },
};
```

### **Component Structure**
```
src/
├── lib/
│   ├── api/              # API client and services
│   ├── auth/             # Authentication logic
│   ├── components/       # Reusable UI components
│   │   ├── forms/        # Form components
│   │   ├── layouts/      # Layout components
│   │   └── ui/           # Basic UI elements
│   ├── stores/           # Svelte stores for state
│   ├── types/            # TypeScript type definitions
│   └── utils/            # Utility functions
├── routes/               # SvelteKit routes
│   ├── login/            # Login page
│   ├── dashboard/        # Main dashboard
│   │   ├── clients/      # Client management
│   │   ├── monitoring/   # System monitoring
│   │   └── users/        # User management
│   └── +layout.svelte    # Root layout
└── app.html              # HTML template
```

## Environment Configuration

### **Development Setup**
```bash
# .env.local
PUBLIC_API_BASE_URL=http://localhost:8080
PUBLIC_WS_BASE_URL=ws://localhost:8080
NODE_ENV=development
```

### **Production Configuration**
```bash
# .env.production
PUBLIC_API_BASE_URL=https://api.emailrouter.com
PUBLIC_WS_BASE_URL=wss://api.emailrouter.com
NODE_ENV=production
```

## Testing Strategy

### **Unit Testing**
```typescript
// src/lib/auth/authService.test.ts
import { describe, it, expect, vi } from 'vitest';
import { AuthService } from './authService';

describe('AuthService', () => {
  it('should login successfully with valid credentials', async () => {
    // Test authentication flows
  });

  it('should handle token refresh automatically', async () => {
    // Test token refresh logic
  });
});
```

### **Integration Testing**
- Test complete user flows
- API integration tests
- Authentication flow testing
- Permission-based access testing

### **E2E Testing**
- Login to dashboard flow
- Client configuration workflow
- System monitoring functionality
- User management operations

## Deployment Considerations

### **Build Configuration**
```typescript
// vite.config.js
export default {
  build: {
    target: 'es2020',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['svelte', '@sveltejs/kit'],
          auth: ['./src/lib/auth'],
          api: ['./src/lib/api'],
        },
      },
    },
  },
  define: {
    __API_BASE_URL__: JSON.stringify(process.env.PUBLIC_API_BASE_URL),
  },
};
```

### **Production Optimizations**
- Code splitting by feature
- Lazy loading for non-critical components
- Service worker for offline capability
- CDN integration for static assets

## Security Considerations

### **Frontend Security**
- XSS prevention with proper sanitization
- CSRF protection via SameSite cookies
- Secure token storage (memory only, no localStorage)
- Content Security Policy headers
- HTTPS enforcement

### **Data Validation**
```typescript
// src/lib/validation/schemas.ts
import { z } from 'zod';

export const loginSchema = z.object({
  username: z.string().min(3).max(50),
  password: z.string().min(8),
  client_id: z.string().optional(),
});

export const clientConfigSchema = z.object({
  name: z.string().min(1).max(100),
  industry: z.string().min(1),
  timezone: z.string(),
  business_hours: z.string().regex(/^\d{1,2}-\d{1,2}$/),
});
```

## Success Metrics

### **Functional Requirements**
- ✅ Complete authentication flow with JWT
- ✅ Role-based access control implementation
- ✅ Real-time data from backend APIs
- ✅ Client configuration management
- ✅ System monitoring dashboard
- ✅ Responsive design for all devices

### **Performance Requirements**
- Initial page load < 2 seconds
- Route transitions < 500ms
- Real-time updates < 1 second latency
- Bundle size < 500KB (gzipped)

### **User Experience**
- Intuitive navigation and workflows
- Clear error messages and validation
- Consistent design system
- Accessibility compliance (WCAG 2.1)

---

## **🚨 CRITICAL REMINDERS**

1. **NO FAKE DATA** - All data must come from real backend APIs
2. **AUTHENTICATION FIRST** - Every API call must use JWT tokens
3. **PERMISSION CHECKS** - UI must respect user roles and permissions
4. **ERROR HANDLING** - Comprehensive error states and user feedback
5. **REAL-TIME UPDATES** - Use WebSocket for live data where possible
6. **MOBILE RESPONSIVE** - Design for mobile-first approach
7. **PRODUCTION READY** - Code quality suitable for enterprise deployment

This frontend will complete the Email Router as a fully-featured, production-ready enterprise application with sophisticated authentication, real-time monitoring, and comprehensive client management capabilities.
