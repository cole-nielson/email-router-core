/**
 * Base service class providing standardized API interaction patterns
 * for the Email Router frontend application.
 */

import { apiClient, handleAPIError, APIError } from '$lib/api/apiClient';
import type { APIError as APIErrorType } from '$lib/types/auth';

export interface ServiceResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  status?: number;
}

export interface PaginationParams {
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginationResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

/**
 * Base service class with common API interaction patterns
 */
export abstract class BaseService {
  protected readonly apiClient = apiClient;

  /**
   * Execute an API request with standardized error handling
   */
  protected async executeRequest<T>(
    requestFn: () => Promise<T>,
    context = 'API request'
  ): Promise<ServiceResponse<T>> {
    try {
      const data = await requestFn();
      return {
        success: true,
        data,
      };
    } catch (error) {
      const errorMessage = this.handleError(error, context);
      return {
        success: false,
        error: errorMessage,
        status: error instanceof APIError ? error.status : 500,
      };
    }
  }

  /**
   * Handle API errors with context-aware messaging
   */
  protected handleError(error: unknown, context: string): string {
    if (error instanceof APIError) {
      // Map common HTTP status codes to user-friendly messages
      switch (error.status) {
        case 400:
          return `Invalid request: ${error.message}`;
        case 401:
          return 'Authentication required. Please log in again.';
        case 403:
          return 'Access denied. You do not have permission for this action.';
        case 404:
          return `${context} not found.`;
        case 409:
          return `Conflict: ${error.message}`;
        case 422:
          return `Validation error: ${error.message}`;
        case 429:
          return 'Too many requests. Please wait and try again.';
        case 500:
          return 'Internal server error. Please try again later.';
        case 502:
        case 503:
        case 504:
          return 'Service temporarily unavailable. Please try again later.';
        default:
          return error.message || `${context} failed`;
      }
    }

    if (error instanceof Error) {
      return error.message;
    }

    return `An unexpected error occurred during ${context}`;
  }

  /**
   * Build query parameters for API requests
   */
  protected buildQueryParams(params: Record<string, any>): string {
    const urlParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        urlParams.append(key, String(value));
      }
    });

    const queryString = urlParams.toString();
    return queryString ? `?${queryString}` : '';
  }

  /**
   * Handle paginated API responses
   */
  protected async executePaginatedRequest<T>(
    endpoint: string,
    params: PaginationParams = {},
    context = 'Paginated request'
  ): Promise<ServiceResponse<PaginationResponse<T>>> {
    const queryParams = this.buildQueryParams({
      limit: params.limit ?? 50,
      offset: params.offset ?? 0,
      sort_by: params.sort_by,
      sort_order: params.sort_order ?? 'asc',
    });

    return this.executeRequest(async () => {
      const response = await this.apiClient.request<{
        items?: T[];
        users?: T[];
        clients?: T[];
        activities?: T[];
        total: number;
        limit: number;
        offset: number;
        has_more: boolean;
      }>(`${endpoint}${queryParams}`);

      // Handle different response formats from backend
      const items = response.items ?? response.users ?? response.clients ?? response.activities ?? [];

      return {
        items,
        total: response.total,
        limit: response.limit,
        offset: response.offset,
        has_more: response.has_more,
      };
    }, context);
  }

  /**
   * Validate required parameters
   */
  protected validateRequired(params: Record<string, any>, requiredFields: string[]): void {
    const missing = requiredFields.filter(field =>
      params[field] === undefined || params[field] === null || params[field] === ''
    );

    if (missing.length > 0) {
      throw new Error(`Missing required fields: ${missing.join(', ')}`);
    }
  }

  /**
   * Log service actions for debugging
   */
  protected log(action: string, details?: any): void {
    if (import.meta.env.DEV) {
      console.log(`[${this.constructor.name}] ${action}`, details);
    }
  }
}
