/**
 * Shared API Type Definitions
 * 🌐 TypeScript types that correspond to Python Pydantic models.
 * These types are automatically synchronized with backend schemas.
 */

// =============================================================================
// API VERSIONING AND METADATA
// =============================================================================

export type APIVersion = 'v1' | 'v2';

export type HTTPMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'OPTIONS' | 'HEAD';

export interface APIEndpoint {
  path: string;
  method: HTTPMethod;
  version: APIVersion;
  description: string;
  requires_auth: boolean;
  permissions: string[];
}

// =============================================================================
// AUTHENTICATION TYPES
// =============================================================================

export type AuthenticationType = 'jwt' | 'api_key' | 'none';

export type UserRole = 'super_admin' | 'client_admin' | 'client_user' | 'api_user';

export type RateLimitTier = 'standard' | 'premium' | 'api_standard' | 'api_premium';

export interface LoginRequest {
  username: string;
  password: string;
  remember_me?: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserInfo;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface PasswordChangeResponse {
  success: boolean;
  message: string;
  tokens_revoked: number;
}

export interface UserInfo {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  client_id: string | null;
  permissions: string[];
  rate_limit_tier: RateLimitTier;
  is_active: boolean;
  last_login: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserCreateRequest {
  username: string;
  email: string;
  full_name: string;
  password: string;
  role?: UserRole;
  client_id?: string | null;
  permissions?: string[];
}

export interface SessionInfo {
  session_id: string;
  user_id: number;
  ip_address: string;
  user_agent: string;
  created_at: string;
  last_activity: string;
  expires_at: string;
  is_current: boolean;
}

export interface SecurityContextInfo {
  is_authenticated: boolean;
  auth_type: AuthenticationType;
  user: UserInfo | null;
  permissions: string[];
  rate_limit_tier: RateLimitTier;
  is_super_admin: boolean;
  client_id: string | null;
  session_expires_at: string | null;
}

// =============================================================================
// API RESPONSE PATTERNS
// =============================================================================

export interface APIResponse {
  success: boolean;
  message: string;
  timestamp: string;
  request_id?: string | null;
}

export interface DataResponse<T = any> extends APIResponse {
  data: T;
  metadata?: Record<string, any> | null;
}

export interface PaginatedResponse {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ListResponse<T = any> extends APIResponse {
  data: T[];
  pagination?: PaginatedResponse | null;
  filters?: Record<string, any> | null;
  sort?: Record<string, any> | null;
}

// =============================================================================
// HEALTH AND STATUS TYPES
// =============================================================================

export type ComponentStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';

export type ServiceStatus = 'operational' | 'degraded_performance' | 'partial_outage' | 'major_outage' | 'maintenance';

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  uptime_seconds?: number | null;
  response_time_ms?: number | null;
  components: Record<string, string>;
}

export interface SystemMetrics {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  avg_response_time_ms: number;
  requests_per_minute: number;
  error_rate: number;
  uptime_seconds: number;
}

export interface APIStatusResponse {
  api_version: string;
  status: string;
  timestamp: string;
  uptime_seconds: number;
  total_clients: number;
  total_domains: number;
  health_score: number;
  features_enabled: string[];
  metrics: SystemMetrics;
  component_status: Record<string, string>;
}

// =============================================================================
// ERROR TYPES
// =============================================================================

export interface ValidationError {
  field: string;
  message: string;
  code: string;
  value?: any;
}

export interface ErrorResponse {
  error: boolean;
  status_code: number;
  message: string;
  timestamp: string;
  path: string;
  method: string;
  request_id?: string | null;
  details?: Record<string, any> | null;
}

export interface APIError {
  error_type: string;
  error_code: string;
  message: string;
  details?: Record<string, any> | null;
  validation_errors?: ValidationError[] | null;
  help_url?: string | null;
}

// =============================================================================
// CLIENT MANAGEMENT TYPES
// =============================================================================

export interface ClientSummary {
  client_id: string;
  name: string;
  industry: string;
  status: string;
  domains: string[];
  primary_domain: string;
  routing_categories: string[];
  total_domains: number;
  settings: Record<string, boolean>;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ClientListResponse {
  total: number;
  clients: ClientSummary[];
  pagination?: Record<string, any> | null;
}

export interface DomainResolutionResult {
  domain: string;
  client_id?: string | null;
  confidence: number;
  method: string;
  domain_used: string;
  is_successful: boolean;
  similar_clients?: Array<Record<string, any>> | null;
}

// =============================================================================
// EMAIL PROCESSING TYPES
// =============================================================================

export interface EmailClassificationRequest {
  subject: string;
  body: string;
  sender?: string | null;
  recipient?: string | null;
  client_id?: string | null;
}

export interface EmailClassificationResponse {
  category: string;
  confidence: number;
  reasoning: string;
  suggested_actions: string[];
  processing_time_ms: number;
  client_id?: string | null;
  method: string;
  timestamp: string;
}

export interface RoutingResult {
  category: string;
  destination: string;
  confidence: number;
  method: string;
  special_handling: string[];
  escalated: boolean;
  business_hours: boolean;
}

export interface WebhookResponse {
  status: string;
  message: string;
  client_id?: string | null;
  processing_id?: string | null;
  timestamp: string;
}

// =============================================================================
// FILTERING AND SORTING TYPES
// =============================================================================

export type SortOrder = 'asc' | 'desc';

export interface SortCriteria {
  field: string;
  order: SortOrder;
}

export type FilterOperator = 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'contains' | 'starts_with' | 'ends_with' | 'in' | 'not_in';

export interface FilterCriteria {
  field: string;
  operator: FilterOperator;
  value: any;
}

export interface QueryParams {
  page?: number;
  per_page?: number;
  sort?: SortCriteria[];
  filters?: FilterCriteria[];
  search?: string;
}

// =============================================================================
// WEBHOOK AND EVENT TYPES
// =============================================================================

export type WebhookEventType =
  | 'email.received'
  | 'email.classified'
  | 'email.routed'
  | 'email.delivered'
  | 'email.failed'
  | 'client.created'
  | 'client.updated'
  | 'client.deleted'
  | 'user.login'
  | 'user.logout'
  | 'api_key.created'
  | 'api_key.revoked';

export interface WebhookEvent {
  id: string;
  type: WebhookEventType;
  timestamp: string;
  source: string;
  data: Record<string, any>;
  client_id?: string | null;
  user_id?: number | null;
}

// =============================================================================
// MONITORING AND METRICS TYPES
// =============================================================================

export type MetricType = 'counter' | 'gauge' | 'histogram' | 'timer';

export interface MetricValue {
  name: string;
  type: MetricType;
  value: number;
  timestamp: string;
  labels?: Record<string, string> | null;
  unit?: string | null;
}

export interface TimeSeriesPoint {
  timestamp: string;
  value: number;
}

export interface TimeSeries {
  name: string;
  points: TimeSeriesPoint[];
  metadata?: Record<string, any> | null;
}

// =============================================================================
// LEGACY COMPATIBILITY (DEPRECATED)
// =============================================================================

/** @deprecated Use LoginResponse instead */
export interface TokenResponse extends LoginResponse {}

/** @deprecated Use UserInfo instead */
export interface AuthenticatedUser extends UserInfo {}

/** @deprecated Use SessionInfo instead */
export interface UserSession extends SessionInfo {}

/** @deprecated Use UserCreateRequest instead */
export interface UserRegistrationRequest extends UserCreateRequest {}

/** @deprecated Use APIResponse instead */
export interface ApiResponse<T = any> extends DataResponse<T> {}
