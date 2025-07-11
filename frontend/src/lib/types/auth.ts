// Authentication types for JWT-based authentication system

export interface LoginRequest {
  username: string;
  password: string;
  client_id?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
  client_id?: string;
  role: "super_admin" | "client_admin" | "client_user" | "api_user";
  permissions: string[];
}

export interface AuthenticatedUser {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: "super_admin" | "client_admin" | "client_user" | "api_user";
  client_id?: string;
  status: "active" | "inactive" | "pending";
  created_at: string;
  last_login_at?: string;
}

export interface UserSession {
  session_id: string;
  token_type: "access" | "refresh";
  created_at: string;
  last_used_at?: string;
  expires_at: string;
  ip_address?: string;
  user_agent?: string;
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
  email: string;
  password: string;
  full_name: string;
  client_id?: string;
  role: string;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
  client_id?: string;
  status: string;
  created_at: string;
  last_login_at?: string;
}

// Auth state interfaces
export interface AuthState {
  user: AuthenticatedUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  accessToken: string | null;
  refreshToken: string | null;
}

// API Error types
export interface APIError {
  message: string;
  status: number;
  details?: any;
}
