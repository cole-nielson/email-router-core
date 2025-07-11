/**
 * Dashboard and Analytics Service
 * Handles metrics, activity feeds, analytics, and real-time data.
 */

import { BaseService, type ServiceResponse, type PaginationParams, type PaginationResponse } from './base.service';
import type {
  DashboardMetrics,
  ActivityItem,
  SystemHealth,
  TrendAnalysis,
  TimeSeriesData,
  SystemMetrics, // Legacy support
  ProcessingActivity, // Legacy support
} from '$lib/types/dashboard';

export interface ActivityFilters {
  type?: string;
  status?: 'success' | 'warning' | 'error' | 'info';
  client_id?: string;
  date_range?: {
    start: string;
    end: string;
  };
}

export interface MetricsFilters {
  period?: '1h' | '24h' | '7d' | '30d';
  client_id?: string;
}

export interface AnalyticsRequest {
  period: '24h' | '7d' | '30d' | '90d';
  client_id?: string;
  metrics?: string[];
}

/**
 * DashboardService handles all dashboard and analytics operations
 */
export class DashboardService extends BaseService {

  // =============================================================================
  // METRICS OPERATIONS
  // =============================================================================

  /**
   * Get dashboard metrics for a specific client or system-wide
   */
  async getMetrics(clientId?: string, filters: MetricsFilters = {}): Promise<ServiceResponse<DashboardMetrics>> {
    const queryParams = this.buildQueryParams({
      period: filters.period ?? '24h',
      ...filters,
    });

    const endpoint = clientId
      ? `/api/v1/dashboard/clients/${clientId}/metrics${queryParams}`
      : `/api/v1/dashboard/metrics${queryParams}`;

    return this.executeRequest(async () => {
      return await this.apiClient.request<DashboardMetrics>(endpoint);
    }, 'Get dashboard metrics');
  }

  /**
   * Get legacy system metrics (for backward compatibility)
   */
  async getSystemMetrics(): Promise<ServiceResponse<SystemMetrics>> {
    return this.executeRequest(async () => {
      const response = await this.apiClient.request<DashboardMetrics>('/api/v1/dashboard/metrics');

      // Convert new format to legacy format
      return {
        emails_processed: response.emails_processed_30d,
        emails_processed_24h: response.emails_processed_24h,
        classification_accuracy: response.classification_accuracy,
        average_response_time: response.avg_processing_time,
        system_uptime: response.system_uptime,
        active_automations: response.active_automations,
        error_count_24h: Math.round(response.emails_processed_24h * (response.error_rate / 100)),
        last_updated: response.last_updated,
      };
    }, 'Get system metrics (legacy)');
  }

  /**
   * Get real-time metrics updates
   */
  async getRealtimeMetrics(clientId?: string): Promise<ServiceResponse<DashboardMetrics>> {
    const endpoint = clientId
      ? `/api/v1/dashboard/clients/${clientId}/metrics/realtime`
      : `/api/v1/dashboard/metrics/realtime`;

    return this.executeRequest(async () => {
      return await this.apiClient.request<DashboardMetrics>(endpoint);
    }, 'Get realtime metrics');
  }

  // =============================================================================
  // ACTIVITY FEED OPERATIONS
  // =============================================================================

  /**
   * Get paginated activity feed
   */
  async getActivity(
    pagination: PaginationParams = {},
    filters: ActivityFilters = {}
  ): Promise<ServiceResponse<PaginationResponse<ActivityItem>>> {

    const queryParams = this.buildQueryParams({
      ...pagination,
      ...filters,
      limit: pagination.limit ?? 50,
      offset: pagination.offset ?? 0,
      start_date: filters.date_range?.start,
      end_date: filters.date_range?.end,
    });

    const endpoint = filters.client_id
      ? `/api/v1/dashboard/clients/${filters.client_id}/activity${queryParams}`
      : `/api/v1/dashboard/activity${queryParams}`;

    return this.executeRequest(async () => {
      const response = await this.apiClient.request<{
        activities: ActivityItem[];
        pagination: {
          total: number;
          limit: number;
          offset: number;
          has_more: boolean;
        };
      }>(endpoint);

      return {
        items: response.activities,
        total: response.pagination.total,
        limit: response.pagination.limit,
        offset: response.pagination.offset,
        has_more: response.pagination.has_more,
      };
    }, 'Get activity feed');
  }

  /**
   * Get recent activity (for live feed components)
   */
  async getRecentActivity(clientId?: string, limit = 20): Promise<ServiceResponse<ActivityItem[]>> {
    const queryParams = this.buildQueryParams({ limit });

    const endpoint = clientId
      ? `/api/v1/dashboard/clients/${clientId}/activity/recent${queryParams}`
      : `/api/v1/dashboard/activity/recent${queryParams}`;

    return this.executeRequest(async () => {
      const response = await this.apiClient.request<{ activities: ActivityItem[] }>(endpoint);
      return response.activities;
    }, 'Get recent activity');
  }

  /**
   * Get legacy processing activity (for backward compatibility)
   */
  async getProcessingActivity(limit = 50): Promise<ServiceResponse<ProcessingActivity[]>> {
    return this.executeRequest(async () => {
      const response = await this.getRecentActivity(undefined, limit);

      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to get activity');
      }

      // Convert new format to legacy format
      const legacyActivities: ProcessingActivity[] = response.data.map(activity => ({
        id: activity.id,
        timestamp: activity.timestamp,
        type: this.mapActivityType(activity.type),
        title: this.generateActivityTitle(activity),
        description: activity.description,
        status: this.mapActivityStatus(activity.status),
        metadata: {
          email_from: activity.details.sender,
          email_subject: activity.details.subject,
          classification: activity.details.category,
          confidence: activity.details.confidence,
          routing_destination: activity.details.recipient,
          error_code: activity.details.error_code,
          from: activity.details.sender, // Backward compatibility
          category: activity.details.category,
          processing_time: activity.details.processing_time,
        },
        severity: this.mapActivitySeverity(activity.status),
      }));

      return legacyActivities;
    }, 'Get processing activity (legacy)');
  }

  // =============================================================================
  // ANALYTICS OPERATIONS
  // =============================================================================

  /**
   * Get trend analysis data
   */
  async getTrendAnalysis(request: AnalyticsRequest): Promise<ServiceResponse<TrendAnalysis>> {
    const queryParams = this.buildQueryParams(request);

    return this.executeRequest(async () => {
      return await this.apiClient.request<TrendAnalysis>(`/api/v1/dashboard/analytics/trends${queryParams}`);
    }, 'Get trend analysis');
  }

  /**
   * Get volume patterns
   */
  async getVolumePatterns(clientId?: string, period = '30d'): Promise<ServiceResponse<{
    hourly: TimeSeriesData;
    daily: TimeSeriesData;
    weekly: TimeSeriesData;
  }>> {
    const queryParams = this.buildQueryParams({ client_id: clientId, period });

    return this.executeRequest(async () => {
      return await this.apiClient.request(`/api/v1/dashboard/analytics/volume-patterns${queryParams}`);
    }, 'Get volume patterns');
  }

  /**
   * Get performance insights
   */
  async getPerformanceInsights(clientId?: string, period = '7d'): Promise<ServiceResponse<{
    processing_time: {
      average: number;
      p50: number;
      p95: number;
      p99: number;
      trend: TimeSeriesData;
    };
    classification: {
      accuracy: number;
      confidence_distribution: Record<string, number>;
      category_performance: Record<string, {
        accuracy: number;
        volume: number;
        avg_confidence: number;
      }>;
    };
    routing: {
      success_rate: number;
      failure_reasons: Record<string, number>;
    };
  }>> {
    const queryParams = this.buildQueryParams({ client_id: clientId, period });

    return this.executeRequest(async () => {
      return await this.apiClient.request(`/api/v1/dashboard/analytics/performance-insights${queryParams}`);
    }, 'Get performance insights');
  }

  // =============================================================================
  // SYSTEM HEALTH OPERATIONS
  // =============================================================================

  /**
   * Get basic system health
   */
  async getBasicHealth(): Promise<ServiceResponse<{ status: string; timestamp: string }>> {
    return this.executeRequest(async () => {
      return await this.apiClient.request('/health');
    }, 'Get basic health');
  }

  /**
   * Get detailed system health
   */
  async getDetailedHealth(): Promise<ServiceResponse<SystemHealth>> {
    return this.executeRequest(async () => {
      return await this.apiClient.request<SystemHealth>('/health/detailed');
    }, 'Get detailed health');
  }

  /**
   * Get Prometheus metrics
   */
  async getPrometheusMetrics(): Promise<ServiceResponse<string>> {
    return this.executeRequest(async () => {
      const response = await fetch(`${this.apiClient.getAccessToken()}/metrics`);
      return await response.text();
    }, 'Get Prometheus metrics');
  }

  // =============================================================================
  // ALERT OPERATIONS
  // =============================================================================

  /**
   * Get active alerts
   */
  async getActiveAlerts(clientId?: string): Promise<ServiceResponse<Array<{
    id: string;
    type: 'error' | 'warning' | 'info';
    title: string;
    message: string;
    timestamp: string;
    client_id?: string;
    acknowledged: boolean;
  }>>> {
    const queryParams = clientId ? this.buildQueryParams({ client_id: clientId }) : '';

    return this.executeRequest(async () => {
      const response = await this.apiClient.request<{ alerts: any[] }>(`/api/v1/dashboard/alerts${queryParams}`);
      return response.alerts;
    }, 'Get active alerts');
  }

  /**
   * Acknowledge alert
   */
  async acknowledgeAlert(alertId: string): Promise<ServiceResponse<void>> {
    this.validateRequired({ alertId }, ['alertId']);

    return this.executeRequest(async () => {
      await this.apiClient.request(`/api/v1/dashboard/alerts/${alertId}/acknowledge`, {
        method: 'POST',
      });
      this.log('Alert acknowledged', { alertId });
    }, 'Acknowledge alert');
  }

  // =============================================================================
  // UTILITY METHODS
  // =============================================================================

  /**
   * Map new activity type to legacy format
   */
  private mapActivityType(type: string): 'email_received' | 'classification_complete' | 'routing_success' | 'integration_sync' | 'error' {
    const typeMap: Record<string, 'email_received' | 'classification_complete' | 'routing_success' | 'integration_sync' | 'error'> = {
      'email_received': 'email_received',
      'classification_completed': 'classification_complete',
      'routing_completed': 'routing_success',
      'email_sent': 'integration_sync',
      'error': 'error',
      'alert': 'error',
    };
    return typeMap[type] || 'error';
  }

  /**
   * Map activity status to legacy format
   */
  private mapActivityStatus(status: string): 'pending' | 'success' | 'error' | 'warning' {
    const statusMap: Record<string, 'pending' | 'success' | 'error' | 'warning'> = {
      'success': 'success',
      'warning': 'warning',
      'error': 'error',
      'info': 'pending',
    };
    return statusMap[status] || 'pending';
  }

  /**
   * Map activity status to severity
   */
  private mapActivitySeverity(status: string): 'info' | 'success' | 'warning' | 'error' {
    const severityMap: Record<string, 'info' | 'success' | 'warning' | 'error'> = {
      'success': 'success',
      'warning': 'warning',
      'error': 'error',
      'info': 'info',
    };
    return severityMap[status] || 'info';
  }

  /**
   * Generate activity title from activity data
   */
  private generateActivityTitle(activity: ActivityItem): string {
    switch (activity.type) {
      case 'email_received':
        return `Email received from ${activity.details.sender || 'unknown'}`;
      case 'classification_completed':
        return `Email classified as ${activity.details.category || 'unknown'}`;
      case 'routing_completed':
        return `Email routed to ${activity.details.recipient || 'unknown'}`;
      case 'email_sent':
        return 'Email sent successfully';
      case 'error':
        return `Error: ${activity.details.error_message || 'Unknown error'}`;
      default:
        return activity.description || 'Activity occurred';
    }
  }
}

// Export singleton instance
export const dashboardService = new DashboardService();
