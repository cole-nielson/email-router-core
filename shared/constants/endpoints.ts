/**
 * Shared API endpoint constants
 */

export const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8080';

export const ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    ME: '/auth/me',
    REGISTER: '/auth/register',
    CHANGE_PASSWORD: '/auth/me/password',
  },

  // Client Management
  CLIENTS: {
    LIST: '/api/v1/clients',
    DETAIL: (id: string) => `/api/v1/clients/${id}`,
    VALIDATE: (id: string) => `/api/v1/clients/${id}/validate`,
  },

  // Configuration
  CONFIG: {
    CLIENT: (id: string) => `/api/v2/clients/${id}`,
    ROUTING: (id: string) => `/api/v2/clients/${id}/routing`,
    BRANDING: (id: string) => `/api/v2/clients/${id}/branding`,
  },

  // Webhooks
  WEBHOOKS: {
    MAILGUN: '/webhooks/mailgun/inbound',
    STATUS: '/webhooks/status',
  },

  // System
  SYSTEM: {
    HEALTH: '/health',
    HEALTH_DETAILED: '/health/detailed',
    METRICS: '/metrics',
    STATUS: '/api/v1/status',
  },

  // Dashboard
  DASHBOARD: {
    METRICS: '/api/v1/dashboard/metrics',
    ACTIVITY: '/api/v1/dashboard/activity',
  },
} as const;

export const HTTP_METHODS = {
  GET: 'GET',
  POST: 'POST',
  PUT: 'PUT',
  DELETE: 'DELETE',
  PATCH: 'PATCH',
} as const;