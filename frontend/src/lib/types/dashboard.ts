// Dashboard and analytics types for the Email Router application

export interface ClientInfo {
  id: string;
  name: string;
  industry: string;
  status: 'active' | 'inactive' | 'setup';
  avatar?: string;
  timezone: string;
  business_hours: string;
}

export interface DashboardMetrics {
  // Core metrics
  emails_processed_24h: number;
  emails_processed_7d: number;
  emails_processed_30d: number;

  // Performance metrics
  classification_accuracy: number;
  avg_processing_time: number;
  routing_success_rate: number;

  // System metrics
  system_uptime: number;
  active_automations: number;
  error_rate: number;

  // Trends
  volume_trend: 'up' | 'down' | 'stable';
  performance_trend: 'up' | 'down' | 'stable';

  // Metadata
  last_updated: string;
  client_id?: string;
}

// Legacy interface for backward compatibility
export interface SystemMetrics {
  emails_processed: number;
  emails_processed_24h: number;
  classification_accuracy: number;
  average_response_time: number;
  system_uptime: number;
  active_automations: number;
  error_count_24h: number;
  last_updated: string;
}

export interface AutomationStatus {
  id: string;
  name: string;
  type: 'email_processing' | 'lead_qualification' | 'support_escalation' | 'custom';
  status: 'active' | 'paused' | 'error' | 'maintenance';
  last_run: string;
  success_rate: number;
  total_executions: number;
  executions_24h: number;
}

export interface ActivityItem {
  id: string;
  timestamp: string;
  type: 'email_received' | 'classification_completed' | 'routing_completed' | 'email_sent' | 'error' | 'alert';
  description: string;
  details: {
    sender?: string;
    recipient?: string;
    subject?: string;
    category?: string;
    confidence?: number;
    processing_time?: number;
    error_code?: string;
    error_message?: string;
  };
  status: 'success' | 'warning' | 'error' | 'info';
  client_id?: string;
}

// Legacy interface for backward compatibility
export interface ProcessingActivity {
  id: string;
  timestamp: string;
  type: 'email_received' | 'classification_complete' | 'routing_success' | 'integration_sync' | 'error';
  title: string;
  description: string;
  status?: 'pending' | 'success' | 'error' | 'warning';
  metadata: {
    email_from?: string;
    email_subject?: string;
    classification?: string;
    confidence?: number;
    routing_destination?: string;
    integration?: string;
    error_code?: string;
    from?: string; // Add this for backward compatibility
    category?: string;
    processing_time?: number;
  };
  severity: 'info' | 'success' | 'warning' | 'error';
}

export interface IntegrationHealth {
  id: string;
  name: string;
  type: 'email' | 'crm' | 'communication' | 'analytics' | 'custom';
  status: 'healthy' | 'warning' | 'error' | 'maintenance';
  last_check: string;
  response_time: number;
  error_count_24h: number;
  uptime_percentage: number;
  endpoint_url?: string;
}

export interface AnalyticsData {
  timeframe: '1h' | '24h' | '7d' | '30d';
  metrics: {
    timestamp: string;
    emails_volume: number;
    classification_accuracy: number;
    response_time: number;
    error_rate: number;
  }[];
  category_breakdown: {
    category: string;
    count: number;
    percentage: number;
    color: string;
  }[];
  performance_trends: {
    metric: string;
    current_value: number;
    previous_value: number;
    change_percentage: number;
    trend: 'up' | 'down' | 'stable';
  }[];
}

export interface AlertRule {
  id: string;
  name: string;
  condition: string;
  threshold: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  enabled: boolean;
  notifications: {
    email: boolean;
    slack: boolean;
    webhook?: string;
  };
}

export interface Alert {
  id: string;
  rule_id: string;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  resolved: boolean;
  resolved_at?: string;
  metadata: Record<string, any>;
}

export interface SystemAlert {
  id: string;
  rule_id: string;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  resolved: boolean;
  resolved_at?: string;
  metadata: Record<string, any>;
}

export interface WebSocketMessage {
  type: 'metric_update' | 'activity_feed' | 'system_alert' | 'integration_status' | 'heartbeat';
  timestamp: string;
  data: SystemMetrics | ProcessingActivity | SystemAlert | IntegrationHealth | null;
  client_id: string;
}

export interface ChartDataPoint {
  x: string | number;
  y: number;
  label?: string;
  color?: string;
}

export interface ChartConfig {
  type: 'line' | 'bar' | 'doughnut' | 'pie' | 'area';
  title: string;
  data: ChartDataPoint[];
  options?: {
    responsive: boolean;
    maintainAspectRatio: boolean;
    plugins?: Record<string, any>;
    scales?: Record<string, any>;
  };
}

// API Response types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_previous: boolean;
}

// Authentication types
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'client' | 'viewer';
  client_id?: string;
  permissions: string[];
  last_login?: string;
}

export interface AuthSession {
  user: User;
  token: string;
  expires_at: string;
  refresh_token: string;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'down';
  components: {
    api_server: ComponentStatus;
    ai_classifier: ComponentStatus;
    email_service: ComponentStatus;
    database: ComponentStatus;
    webhooks: ComponentStatus;
    cache: ComponentStatus;
  };
  performance: {
    avg_response_time: number;
    requests_per_minute: number;
    error_rate: number;
    cpu_usage?: number;
    memory_usage?: number;
  };
  last_check: string;
  uptime_percentage: number;
}

export interface ComponentStatus {
  status: 'healthy' | 'warning' | 'error' | 'unknown';
  response_time?: number;
  last_check: string;
  error_message?: string;
  details?: Record<string, any>;
}

// Analytics types
export interface TrendAnalysis {
  period: '24h' | '7d' | '30d' | '90d';
  metrics: {
    email_volume: TimeSeriesData;
    processing_time: TimeSeriesData;
    classification_accuracy: TimeSeriesData;
    error_rate: TimeSeriesData;
  };
  insights: Array<{
    type: 'trend' | 'anomaly' | 'threshold';
    metric: string;
    description: string;
    severity: 'low' | 'medium' | 'high';
    timestamp: string;
  }>;
}

export interface TimeSeriesData {
  timestamps: string[];
  values: number[];
  trend: 'increasing' | 'decreasing' | 'stable';
  change_percentage: number;
}

// Dashboard state management
export interface DashboardState {
  client: ClientInfo | null;
  metrics: SystemMetrics | null;
  automations: AutomationStatus[];
  activities: ProcessingActivity[];
  integrations: IntegrationHealth[];
  alerts: SystemAlert[];
  analytics: AnalyticsData | null;
  websocket_connected: boolean;
  last_updated: string;
  loading: boolean;
  error: string | null;
}

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: string;
  client_id?: string;
}
