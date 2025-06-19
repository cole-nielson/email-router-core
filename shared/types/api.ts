/**
 * Shared API type definitions
 * Used by both frontend and backend for type safety
 */

// Authentication Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserInfo;
}

export interface UserInfo {
  id: string;
  username: string;
  email: string | null;
  role: string;
  client_id: string | null;
  permissions: string[];
}

export interface AuthenticatedUser {
  id: number;
  username: string;
  email: string | null;
  role: string;
  client_id: string | null;
  permissions: string[];
  created_at: string;
  last_login: string | null;
}

export interface UserSession {
  id: string;
  user_id: number;
  created_at: string;
  last_activity: string;
  ip_address: string;
  user_agent: string;
  is_active: boolean;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

export interface UserRegistrationRequest {
  username: string;
  password: string;
  email?: string;
  role: string;
  client_id?: string;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string | null;
  role: string;
  client_id: string | null;
  created_at: string;
  last_login: string | null;
  is_active: boolean;
}

// Client Management Types
export interface ClientConfig {
  id: string;
  name: string;
  domains: string[];
  routing_rules: RoutingRules;
  branding: BrandingConfig;
  enabled: boolean;
}

export interface RoutingRules {
  support: string;
  billing: string;
  sales: string;
  general: string;
  escalation?: {
    urgent?: string;
    emergency?: string;
  };
}

export interface BrandingConfig {
  primary_color: string;
  secondary_color: string;
  logo_url?: string;
  footer_text?: string;
}

// Email Processing Types
export interface EmailClassification {
  category: string;
  confidence: number;
  reasoning: string;
}

export interface EmailProcessingResult {
  client_id: string;
  classification: EmailClassification;
  routing_decision: string;
  processing_time_ms: number;
  success: boolean;
}

// Dashboard Types
export interface SystemMetrics {
  total_emails_processed: number;
  active_clients: number;
  average_processing_time: number;
  classification_accuracy: number;
  uptime_percentage: number;
}

export interface EmailMetrics {
  hourly_volume: number[];
  category_distribution: Record<string, number>;
  client_activity: Record<string, number>;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

// Error Types
export interface APIError {
  error: string;
  details?: Record<string, any>;
  timestamp: string;
}