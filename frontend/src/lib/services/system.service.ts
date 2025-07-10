/**
 * System Monitoring and Health Service
 * Handles system status, health checks, monitoring, and diagnostics.
 */

import { BaseService, type ServiceResponse } from './base.service';
import type { SystemHealth, ComponentStatus } from '$lib/types/dashboard';

export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'down';
  timestamp: string;
  version: string;
  uptime_seconds: number;
  components: Record<string, ComponentStatus>;
}

export interface SystemMetrics {
  requests_total: number;
  requests_per_minute: number;
  error_rate: number;
  avg_response_time: number;
  active_connections: number;
  memory_usage: number;
  cpu_usage: number;
  disk_usage: number;
}

export interface DiagnosticInfo {
  environment: string;
  version: string;
  build_time: string;
  commit_hash?: string;
  python_version: string;
  dependencies: Record<string, string>;
  configuration: {
    api_keys_configured: string[];
    database_connected: boolean;
    cache_connected: boolean;
    email_service_configured: boolean;
  };
}

/**
 * SystemService handles all system monitoring and health operations
 */
export class SystemService extends BaseService {

  // =============================================================================
  // HEALTH CHECK OPERATIONS
  // =============================================================================

  /**
   * Get basic system health status
   */
  async getBasicHealth(): Promise<ServiceResponse<{ status: string; timestamp: string }>> {
    return this.executeRequest(async () => {
      return await this.apiClient.request('/health');
    }, 'Basic health check');
  }

  /**
   * Get detailed system health with component status
   */
  async getDetailedHealth(): Promise<ServiceResponse<SystemHealth>> {
    return this.executeRequest(async () => {
      return await this.apiClient.request<SystemHealth>('/health/detailed');
    }, 'Detailed health check');
  }

  /**
   * Get comprehensive system status
   */
  async getSystemStatus(): Promise<ServiceResponse<SystemStatus>> {
    return this.executeRequest(async () => {
      return await this.apiClient.request<SystemStatus>('/api/v1/status');
    }, 'Get system status');
  }

  /**
   * Perform health check for specific component
   */
  async checkComponent(componentName: string): Promise<ServiceResponse<ComponentStatus>> {
    this.validateRequired({ componentName }, ['componentName']);

    return this.executeRequest(async () => {
      return await this.apiClient.request<ComponentStatus>(`/health/components/${componentName}`);
    }, `Check ${componentName} component`);
  }

  // =============================================================================
  // METRICS AND MONITORING
  // =============================================================================

  /**
   * Get system performance metrics
   */
  async getSystemMetrics(): Promise<ServiceResponse<SystemMetrics>> {
    return this.executeRequest(async () => {
      return await this.apiClient.request<SystemMetrics>('/api/v1/system/metrics');
    }, 'Get system metrics');
  }

  /**
   * Get Prometheus-formatted metrics
   */
  async getPrometheusMetrics(): Promise<ServiceResponse<string>> {
    return this.executeRequest(async () => {
      // Note: Prometheus metrics endpoint typically returns plain text
      const response = await fetch(`${this.apiClient['baseURL']}/metrics`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.text();
    }, 'Get Prometheus metrics');
  }

  /**
   * Get resource usage statistics
   */
  async getResourceUsage(): Promise<ServiceResponse<{
    cpu: {
      usage_percent: number;
      cores: number;
      load_average: number[];
    };
    memory: {
      usage_percent: number;
      used_bytes: number;
      total_bytes: number;
      available_bytes: number;
    };
    disk: {
      usage_percent: number;
      used_bytes: number;
      total_bytes: number;
      free_bytes: number;
    };
    network: {
      bytes_sent: number;
      bytes_received: number;
      packets_sent: number;
      packets_received: number;
    };
  }>> {
    return this.executeRequest(async () => {
      return await this.apiClient.request('/api/v1/system/resources');
    }, 'Get resource usage');
  }

  // =============================================================================
  // DIAGNOSTIC OPERATIONS
  // =============================================================================

  /**
   * Get diagnostic information
   */
  async getDiagnosticInfo(): Promise<ServiceResponse<DiagnosticInfo>> {
    return this.executeRequest(async () => {
      return await this.apiClient.request<DiagnosticInfo>('/api/v1/system/diagnostics');
    }, 'Get diagnostic info');
  }

  /**
   * Test external service connections
   */
  async testExternalServices(): Promise<ServiceResponse<{
    anthropic_api: {
      status: 'connected' | 'error';
      response_time?: number;
      error?: string;
    };
    mailgun_api: {
      status: 'connected' | 'error';
      response_time?: number;
      error?: string;
    };
    database: {
      status: 'connected' | 'error';
      response_time?: number;
      error?: string;
    };
  }>> {
    return this.executeRequest(async () => {
      return await this.apiClient.request('/api/v1/system/test-connections');
    }, 'Test external services');
  }

  /**
   * Run system diagnostics
   */
  async runDiagnostics(): Promise<ServiceResponse<{
    timestamp: string;
    overall_status: 'healthy' | 'warning' | 'error';
    checks: Array<{
      name: string;
      status: 'pass' | 'warning' | 'fail';
      message: string;
      details?: any;
      duration_ms: number;
    }>;
    recommendations: string[];
  }>> {
    return this.executeRequest(async () => {
      return await this.apiClient.request('/api/v1/system/diagnostics/run', {
        method: 'POST',
      });
    }, 'Run system diagnostics');
  }

  // =============================================================================
  // LOG OPERATIONS
  // =============================================================================

  /**
   * Get recent system logs
   */
  async getSystemLogs(
    level?: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL',
    limit = 100,
    since?: string
  ): Promise<ServiceResponse<Array<{
    timestamp: string;
    level: string;
    logger: string;
    message: string;
    extra?: Record<string, any>;
  }>>> {
    const queryParams = this.buildQueryParams({
      level,
      limit,
      since,
    });

    return this.executeRequest(async () => {
      const response = await this.apiClient.request<{ logs: any[] }>(`/api/v1/system/logs${queryParams}`);
      return response.logs;
    }, 'Get system logs');
  }

  /**
   * Get error logs with stack traces
   */
  async getErrorLogs(limit = 50): Promise<ServiceResponse<Array<{
    timestamp: string;
    error_type: string;
    message: string;
    stack_trace?: string;
    request_id?: string;
    user_id?: string;
    client_id?: string;
  }>>> {
    const queryParams = this.buildQueryParams({ limit });

    return this.executeRequest(async () => {
      const response = await this.apiClient.request<{ errors: any[] }>(`/api/v1/system/errors${queryParams}`);
      return response.errors;
    }, 'Get error logs');
  }

  // =============================================================================
  // MAINTENANCE OPERATIONS
  // =============================================================================

  /**
   * Enable maintenance mode
   */
  async enableMaintenanceMode(reason?: string): Promise<ServiceResponse<void>> {
    return this.executeRequest(async () => {
      await this.apiClient.request('/api/v1/system/maintenance', {
        method: 'POST',
        body: JSON.stringify({ reason: reason || 'Scheduled maintenance' }),
      });
      this.log('Maintenance mode enabled', { reason });
    }, 'Enable maintenance mode');
  }

  /**
   * Disable maintenance mode
   */
  async disableMaintenanceMode(): Promise<ServiceResponse<void>> {
    return this.executeRequest(async () => {
      await this.apiClient.request('/api/v1/system/maintenance', {
        method: 'DELETE',
      });
      this.log('Maintenance mode disabled');
    }, 'Disable maintenance mode');
  }

  /**
   * Get maintenance status
   */
  async getMaintenanceStatus(): Promise<ServiceResponse<{
    enabled: boolean;
    reason?: string;
    started_at?: string;
    estimated_duration?: string;
  }>> {
    return this.executeRequest(async () => {
      return await this.apiClient.request('/api/v1/system/maintenance');
    }, 'Get maintenance status');
  }

  // =============================================================================
  // CACHE OPERATIONS
  // =============================================================================

  /**
   * Clear system cache
   */
  async clearCache(cacheType?: 'all' | 'api' | 'templates' | 'client_configs'): Promise<ServiceResponse<{
    cleared: string[];
    cache_size_before: number;
    cache_size_after: number;
  }>> {
    const body = cacheType ? JSON.stringify({ cache_type: cacheType }) : undefined;

    return this.executeRequest(async () => {
      const result = await this.apiClient.request<{
        cleared: string[];
        cache_size_before: number;
        cache_size_after: number;
      }>('/api/v1/system/cache/clear', {
        method: 'POST',
        body,
      });
      this.log('Cache cleared', { cacheType, result });
      return result;
    }, 'Clear cache');
  }

  /**
   * Get cache statistics
   */
  async getCacheStats(): Promise<ServiceResponse<{
    total_size: number;
    total_keys: number;
    hit_rate: number;
    miss_rate: number;
    caches: Record<string, {
      size: number;
      keys: number;
      hit_rate: number;
    }>;
  }>> {
    return this.executeRequest(async () => {
      return await this.apiClient.request('/api/v1/system/cache/stats');
    }, 'Get cache statistics');
  }

  // =============================================================================
  // UTILITY METHODS
  // =============================================================================

  /**
   * Get system uptime in human-readable format
   */
  formatUptime(uptimeSeconds: number): string {
    const days = Math.floor(uptimeSeconds / 86400);
    const hours = Math.floor((uptimeSeconds % 86400) / 3600);
    const minutes = Math.floor((uptimeSeconds % 3600) / 60);

    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  }

  /**
   * Format bytes to human-readable format
   */
  formatBytes(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`;
  }

  /**
   * Get overall system health status from components
   */
  getOverallHealthStatus(components: Record<string, ComponentStatus>): 'healthy' | 'degraded' | 'down' {
    const statuses = Object.values(components).map(c => c.status);

    if (statuses.some(s => s === 'error')) {
      return 'down';
    } else if (statuses.some(s => s === 'warning')) {
      return 'degraded';
    } else {
      return 'healthy';
    }
  }
}

// Export singleton instance
export const systemService = new SystemService();
