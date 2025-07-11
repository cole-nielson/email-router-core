/**
 * Shared API Types
 * Common interfaces used across the application
 */

// Re-export auth types for shared access
export type {
  LoginRequest,
  TokenResponse,
  AuthenticatedUser,
  UserSession,
  RefreshTokenRequest,
  PasswordChangeRequest,
  UserRegistrationRequest,
  UserResponse,
  APIError,
} from '../../src/lib/types/auth';

// Re-export client types
export type {
  ClientSummary,
  ClientConfig,
  RoutingRule,
  RoutingConfig,
  BrandingConfig,
  AIPromptConfig,
  ClientValidationResult,
  DomainResolutionResult,
  CreateClientRequest,
  UpdateClientRequest,
  UpdateRoutingRequest,
  UpdateBrandingRequest,
  CreateAIPromptRequest,
} from '../../src/lib/types/client';

// Re-export dashboard types
export type {
  DashboardMetrics,
  ActivityItem,
  SystemHealth,
  ComponentStatus,
  TrendAnalysis,
  TimeSeriesData,
  SystemMetrics,
  ProcessingActivity,
} from '../../src/lib/types/dashboard';

/**
 * Generic API Response wrapper
 */
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  timestamp: string;
}

/**
 * Paginated response wrapper
 */
export interface PaginatedApiResponse<T> {
  success: boolean;
  data: {
    items: T[];
    pagination: {
      total: number;
      limit: number;
      offset: number;
      has_more: boolean;
    };
  };
  message?: string;
  timestamp: string;
}

/**
 * Error response structure
 */
export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
}
