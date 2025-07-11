/**
 * Service Layer Index
 * Centralized exports for all API services
 */

// Base service exports
export { BaseService } from './base.service';
export type { ServiceResponse, PaginationParams, PaginationResponse } from './base.service';

// Authentication service
export { AuthService, authService } from './auth.service';
export type { UserFilters, SessionListResponse } from './auth.service';

// Client management service
export { ClientService, clientService } from './client.service';
export type { ClientFilters, ClientListResponse } from './client.service';

// Dashboard and analytics service
export { DashboardService, dashboardService } from './dashboard.service';
export type { ActivityFilters, MetricsFilters, AnalyticsRequest } from './dashboard.service';

// System monitoring service
export { SystemService, systemService } from './system.service';
export type { SystemStatus, SystemMetrics, DiagnosticInfo } from './system.service';

// Import service instances
import { authService } from './auth.service';
import { clientService } from './client.service';
import { dashboardService } from './dashboard.service';
import { systemService } from './system.service';

// Convenience object with all services
export const services = {
  auth: authService,
  client: clientService,
  dashboard: dashboardService,
  system: systemService,
} as const;

// Service type for dependency injection
export type Services = typeof services;
