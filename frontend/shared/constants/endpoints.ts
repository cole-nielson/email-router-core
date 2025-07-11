/**
 * API Endpoint Constants
 * Centralized endpoint definitions for consistent API calls
 */

// Base URL configuration
export const API_BASE_URL = 'http://localhost:8080';
export const WS_BASE_URL = 'ws://localhost:8080';

/**
 * API Endpoints organized by domain
 */
export const ENDPOINTS = {
  // Authentication endpoints
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    ME: '/auth/me',
    CHANGE_PASSWORD: '/auth/me/password',
    REGISTER: '/auth/register',
    USERS: '/auth/users',
    SESSIONS: '/auth/sessions',
    DELETE_USER: (userId: string) => `/auth/users/${userId}`,
    DELETE_SESSION: (sessionId: string) => `/auth/sessions/${sessionId}`,
  },

  // Client management endpoints
  CLIENTS: {
    LIST: '/api/v1/clients',
    STATUS: '/api/v1/status',
    DETAIL: (clientId: string) => `/api/v2/config/clients/${clientId}`,
    VALIDATE: (clientId: string) => `/api/v1/clients/${clientId}/validate`,

    // Configuration endpoints
    CONFIG: (clientId: string) => `/api/v2/config/clients/${clientId}`,
    ROUTING: (clientId: string) => `/api/v2/config/clients/${clientId}/routing`,
    ROUTING_RULE: (clientId: string, category: string) =>
      `/api/v2/config/clients/${clientId}/routing/${category}`,
    BRANDING: (clientId: string) => `/api/v2/config/clients/${clientId}/branding`,
    AI_PROMPTS: (clientId: string) => `/api/v2/config/clients/${clientId}/ai-prompts`,
    AI_PROMPT: (clientId: string, type: string) =>
      `/api/v2/config/clients/${clientId}/ai-prompts/${type}`,

    // Domain management
    DOMAINS: (clientId: string) => `/api/v2/config/clients/${clientId}/domains`,
    DOMAIN: (clientId: string, domain: string) =>
      `/api/v2/config/clients/${clientId}/domains/${encodeURIComponent(domain)}`,
  },

  // Dashboard and analytics endpoints
  DASHBOARD: {
    METRICS: '/api/v1/dashboard/metrics',
    CLIENT_METRICS: (clientId: string) => `/api/v1/dashboard/clients/${clientId}/metrics`,
    ACTIVITY: '/api/v1/dashboard/activity',
    CLIENT_ACTIVITY: (clientId: string) => `/api/v1/dashboard/clients/${clientId}/activity`,
    ALERTS: '/api/v1/dashboard/alerts',
    CLIENT_ALERTS: (clientId: string) => `/api/v1/dashboard/clients/${clientId}/alerts`,

    // Analytics endpoints
    TRENDS: '/api/v1/dashboard/analytics/trends',
    VOLUME_PATTERNS: '/api/v1/dashboard/analytics/volume-patterns',
    PERFORMANCE_INSIGHTS: '/api/v1/dashboard/analytics/performance-insights',
  },

  // System monitoring endpoints
  SYSTEM: {
    HEALTH: '/health',
    HEALTH_DETAILED: '/health/detailed',
    STATUS: '/api/v1/status',
    METRICS: '/metrics',
    DIAGNOSTICS: '/api/v1/system/diagnostics',
    LOGS: '/api/v1/system/logs',
    ERRORS: '/api/v1/system/errors',
    MAINTENANCE: '/api/v1/system/maintenance',
    CACHE: '/api/v1/system/cache',
    RESOURCES: '/api/v1/system/resources',
  },

  // Domain resolution endpoint
  DOMAIN: {
    RESOLVE: '/api/v1/domain/resolve',
  },

  // WebSocket endpoints
  WEBSOCKET: {
    CLIENT: (clientId: string) => `/ws/client/${clientId}`,
    SYSTEM: '/ws/system',
  },

  // Webhook endpoints (for reference)
  WEBHOOKS: {
    MAILGUN: '/webhooks/mailgun/inbound',
    TEST: '/webhooks/test',
    STATUS: '/webhooks/status',
  },
} as const;

/**
 * HTTP Methods
 */
export const HTTP_METHODS = {
  GET: 'GET',
  POST: 'POST',
  PUT: 'PUT',
  DELETE: 'DELETE',
  PATCH: 'PATCH',
} as const;

/**
 * Common HTTP Status Codes
 */
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
  GATEWAY_TIMEOUT: 504,
} as const;

/**
 * API Configuration
 */
export const API_CONFIG = {
  DEFAULT_TIMEOUT: 30000, // 30 seconds
  DEFAULT_RETRY_ATTEMPTS: 3,
  DEFAULT_RETRY_DELAY: 1000, // 1 second
  MAX_REQUEST_SIZE: 10 * 1024 * 1024, // 10MB

  // Pagination defaults
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,

  // Cache configuration
  DEFAULT_CACHE_TTL: 300, // 5 minutes

  // WebSocket configuration
  WS_RECONNECT_INTERVAL: 5000, // 5 seconds
  WS_MAX_RECONNECT_ATTEMPTS: 10,
} as const;
