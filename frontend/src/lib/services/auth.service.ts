/**
 * Authentication and User Management Service
 * Handles user CRUD operations, session management, and RBAC permissions.
 */

import { BaseService, type ServiceResponse, type PaginationParams, type PaginationResponse } from './base.service';
import type {
  LoginRequest,
  TokenResponse,
  AuthenticatedUser,
  UserSession,
  PasswordChangeRequest,
  UserRegistrationRequest,
  UserResponse,
  RefreshTokenRequest,
} from '$lib/types/auth';

export interface UserFilters {
  search?: string;
  role?: string;
  status?: 'active' | 'inactive' | 'pending';
  client_id?: string;
}

export interface SessionListResponse {
  sessions: UserSession[];
}

/**
 * AuthService handles all authentication and user management operations
 */
export class AuthService extends BaseService {

  // =============================================================================
  // AUTHENTICATION OPERATIONS
  // =============================================================================

  /**
   * Authenticate user with username and password
   */
  async login(credentials: LoginRequest): Promise<ServiceResponse<TokenResponse>> {
    this.validateRequired(credentials, ['username', 'password']);
    this.log('Attempting login', { username: credentials.username });

    return this.executeRequest(async () => {
      const response = await this.apiClient.request<TokenResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      });

      this.log('Login successful', { role: response.role, client_id: response.client_id });
      return response;
    }, 'User login');
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshToken(refreshToken: string): Promise<ServiceResponse<TokenResponse>> {
    this.validateRequired({ refreshToken }, ['refreshToken']);

    return this.executeRequest(async () => {
      const request: RefreshTokenRequest = { refresh_token: refreshToken };
      return await this.apiClient.request<TokenResponse>('/auth/refresh', {
        method: 'POST',
        body: JSON.stringify(request),
      });
    }, 'Token refresh');
  }

  /**
   * Logout current user and revoke tokens
   */
  async logout(): Promise<ServiceResponse<void>> {
    return this.executeRequest(async () => {
      await this.apiClient.request<void>('/auth/logout', {
        method: 'POST',
      });
      this.log('User logged out');
    }, 'User logout');
  }

  /**
   * Get current authenticated user information
   */
  async getCurrentUser(): Promise<ServiceResponse<AuthenticatedUser>> {
    return this.executeRequest(async () => {
      return await this.apiClient.request<AuthenticatedUser>('/auth/me');
    }, 'Get current user');
  }

  /**
   * Change current user's password
   */
  async changePassword(request: PasswordChangeRequest): Promise<ServiceResponse<void>> {
    this.validateRequired(request, ['current_password', 'new_password']);

    return this.executeRequest(async () => {
      await this.apiClient.request<void>('/auth/me/password', {
        method: 'PUT',
        body: JSON.stringify(request),
      });
      this.log('Password changed');
    }, 'Password change');
  }

  // =============================================================================
  // USER MANAGEMENT OPERATIONS (Admin)
  // =============================================================================

  /**
   * Register a new user (admin only)
   */
  async registerUser(request: UserRegistrationRequest): Promise<ServiceResponse<UserResponse>> {
    this.validateRequired(request, ['username', 'email', 'password', 'full_name']);

    return this.executeRequest(async () => {
      const user = await this.apiClient.request<UserResponse>('/auth/register', {
        method: 'POST',
        body: JSON.stringify(request),
      });

      this.log('User registered', { username: request.username, role: request.role });
      return user;
    }, 'User registration');
  }

  /**
   * Get paginated list of users with filtering
   */
  async getUsers(
    pagination: PaginationParams = {},
    filters: UserFilters = {}
  ): Promise<ServiceResponse<PaginationResponse<UserResponse>>> {

    const queryParams = this.buildQueryParams({
      ...pagination,
      ...filters,
      limit: pagination.limit ?? 50,
      offset: pagination.offset ?? 0,
    });

    return this.executeRequest(async () => {
      const response = await this.apiClient.request<{
        users: UserResponse[];
        pagination: {
          total: number;
          limit: number;
          offset: number;
          has_more: boolean;
        };
      }>(`/auth/users${queryParams}`);

      return {
        items: response.users,
        total: response.pagination.total,
        limit: response.pagination.limit,
        offset: response.pagination.offset,
        has_more: response.pagination.has_more,
      };
    }, 'Get users list');
  }

  /**
   * Delete a user (super admin only)
   */
  async deleteUser(userId: number): Promise<ServiceResponse<void>> {
    this.validateRequired({ userId }, ['userId']);

    return this.executeRequest(async () => {
      await this.apiClient.request<void>(`/auth/users/${userId}`, {
        method: 'DELETE',
      });
      this.log('User deleted', { userId });
    }, 'User deletion');
  }

  // =============================================================================
  // SESSION MANAGEMENT
  // =============================================================================

  /**
   * Get active sessions for current user
   */
  async getUserSessions(): Promise<ServiceResponse<UserSession[]>> {
    return this.executeRequest(async () => {
      const response = await this.apiClient.request<SessionListResponse>('/auth/sessions');
      return response.sessions;
    }, 'Get user sessions');
  }

  /**
   * Revoke a specific session
   */
  async revokeSession(sessionId: string): Promise<ServiceResponse<void>> {
    this.validateRequired({ sessionId }, ['sessionId']);

    return this.executeRequest(async () => {
      await this.apiClient.request<void>(`/auth/sessions/${sessionId}`, {
        method: 'DELETE',
      });
      this.log('Session revoked', { sessionId });
    }, 'Session revocation');
  }

  // =============================================================================
  // PERMISSION UTILITIES
  // =============================================================================

  /**
   * Check if current user has specific permission
   */
  hasPermission(user: AuthenticatedUser | null, permission: string): boolean {
    if (!user) return false;

    // Super admin has all permissions
    if (user.role === 'super_admin') return true;

    // Role-based permissions
    switch (user.role) {
      case 'client_admin':
        return [
          'client:read', 'client:write',
          'routing:read', 'routing:write',
          'branding:read', 'branding:write',
          'users:read', 'users:write'
        ].includes(permission);

      case 'client_user':
        return [
          'client:read',
          'routing:read',
          'branding:read'
        ].includes(permission);

      case 'api_user':
        return ['client:read'].includes(permission);

      default:
        return false;
    }
  }

  /**
   * Check if user can access specific client
   */
  canAccessClient(user: AuthenticatedUser | null, clientId: string): boolean {
    if (!user) return false;

    // Super admin can access all clients
    if (user.role === 'super_admin') return true;

    // Other roles can only access their assigned client
    return user.client_id === clientId;
  }

  /**
   * Get user role hierarchy level (higher number = more permissions)
   */
  getRoleLevel(role: string): number {
    switch (role) {
      case 'super_admin': return 4;
      case 'client_admin': return 3;
      case 'client_user': return 2;
      case 'api_user': return 1;
      default: return 0;
    }
  }

  /**
   * Check if user can manage another user (based on role hierarchy)
   */
  canManageUser(currentUser: AuthenticatedUser | null, targetUser: UserResponse): boolean {
    if (!currentUser) return false;

    // Super admin can manage all users
    if (currentUser.role === 'super_admin') return true;

    // Users can only manage users with lower role levels
    const currentLevel = this.getRoleLevel(currentUser.role);
    const targetLevel = this.getRoleLevel(targetUser.role);

    // Must be higher level and same client (unless super admin)
    return currentLevel > targetLevel &&
           (currentLevel === 4 || currentUser.client_id === targetUser.client_id);
  }
}

// Export singleton instance
export const authService = new AuthService();
