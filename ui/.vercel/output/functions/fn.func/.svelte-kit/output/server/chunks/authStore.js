import { d as derived, w as writable } from "./index.js";
import { g as goto } from "./client.js";
class APIError extends Error {
  constructor(status, message, details) {
    super(message);
    this.status = status;
    this.message = message;
    this.details = details;
    this.name = "APIError";
  }
}
class APIClient {
  baseURL;
  accessToken = null;
  refreshToken = null;
  isRefreshing = false;
  refreshPromise = null;
  constructor() {
    this.baseURL = this.getBaseURL();
  }
  getBaseURL() {
    if (typeof window !== "undefined") {
      if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
        return "http://localhost:8080";
      }
      return `${window.location.protocol}//api.${window.location.hostname}`;
    }
    return "http://localhost:8080";
  }
  // Set tokens
  setTokens(accessToken, refreshToken) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
  }
  // Clear tokens
  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    this.isRefreshing = false;
    this.refreshPromise = null;
  }
  // Get current access token
  getAccessToken() {
    return this.accessToken;
  }
  // Generic request method with automatic token refresh
  async request(endpoint, options = {}) {
    if (this.accessToken && this.isTokenExpiringSoon()) {
      await this.refreshAccessToken();
    }
    let response = await this.makeRequest(endpoint, options);
    if (response.status === 401 && this.refreshToken && !this.isRefreshing) {
      try {
        await this.refreshAccessToken();
        response = await this.makeRequest(endpoint, options);
      } catch (refreshError) {
        this.handleAuthenticationFailure();
        throw new APIError(401, "Session expired. Please log in again.");
      }
    }
    return this.handleResponse(response);
  }
  // Make HTTP request with proper headers
  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      ...options.headers
    };
    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }
    return fetch(url, {
      ...options,
      headers
    });
  }
  // Handle response and errors
  async handleResponse(response) {
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      let errorDetails = {};
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
        errorDetails = errorData;
      } catch {
      }
      throw new APIError(response.status, errorMessage, errorDetails);
    }
    if (response.status === 204 || response.headers.get("content-length") === "0") {
      return {};
    }
    try {
      return await response.json();
    } catch {
      throw new APIError(500, "Invalid JSON response from server");
    }
  }
  // Check if token is expiring soon (within 5 minutes)
  isTokenExpiringSoon() {
    if (!this.accessToken) return false;
    try {
      const payload = JSON.parse(atob(this.accessToken.split(".")[1]));
      const exp = payload.exp * 1e3;
      const now = Date.now();
      const fiveMinutes = 5 * 60 * 1e3;
      return exp - now < fiveMinutes;
    } catch {
      return true;
    }
  }
  // Refresh access token
  async refreshAccessToken() {
    if (this.isRefreshing && this.refreshPromise) {
      await this.refreshPromise;
      return;
    }
    if (!this.refreshToken) {
      throw new APIError(401, "No refresh token available");
    }
    this.isRefreshing = true;
    this.refreshPromise = this.performTokenRefresh();
    try {
      await this.refreshPromise;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }
  // Perform the actual token refresh
  async performTokenRefresh() {
    try {
      const response = await fetch(`${this.baseURL}/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          refresh_token: this.refreshToken
        })
      });
      if (!response.ok) {
        throw new APIError(response.status, "Failed to refresh token");
      }
      const tokenData = await response.json();
      this.setTokens(tokenData.access_token, tokenData.refresh_token);
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("token-refreshed", {
          detail: tokenData
        }));
      }
    } catch (error) {
      this.clearTokens();
      throw error;
    }
  }
  // Handle authentication failure
  handleAuthenticationFailure() {
    this.clearTokens();
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("auth-failed"));
      if (!window.location.pathname.includes("/login")) {
        goto();
      }
    }
  }
  // =============================================================================
  // AUTHENTICATION ENDPOINTS
  // =============================================================================
  async login(credentials) {
    try {
      const response = await fetch(`${this.baseURL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(credentials)
      });
      if (!response.ok) {
        let errorMessage = "Login failed";
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
        }
        throw new APIError(response.status, errorMessage);
      }
      const tokenData = await response.json();
      this.setTokens(tokenData.access_token, tokenData.refresh_token);
      return tokenData;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError(0, "Network error during login");
    }
  }
  async logout() {
    try {
      if (this.accessToken) {
        await this.request("/auth/logout", {
          method: "POST"
        });
      }
    } catch (error) {
      console.warn("Logout request failed:", error);
    } finally {
      this.clearTokens();
    }
  }
  async getCurrentUser() {
    return this.request("/auth/me");
  }
  async changePassword(request) {
    await this.request("/auth/me/password", {
      method: "PUT",
      body: JSON.stringify(request)
    });
  }
  async getUserSessions() {
    return this.request("/auth/sessions");
  }
  async revokeSession(sessionId) {
    await this.request(`/auth/sessions/${sessionId}`, {
      method: "DELETE"
    });
  }
  // Admin endpoints
  async registerUser(request) {
    return this.request("/auth/register", {
      method: "POST",
      body: JSON.stringify(request)
    });
  }
  async getUsers(clientId, limit = 50, offset = 0) {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString()
    });
    if (clientId) {
      params.append("client_id", clientId);
    }
    return this.request(`/auth/users?${params}`);
  }
  async deleteUser(userId) {
    await this.request(`/auth/users/${userId}`, {
      method: "DELETE"
    });
  }
  // =============================================================================
  // HEALTH AND STATUS ENDPOINTS
  // =============================================================================
  async getHealth() {
    return this.request("/health");
  }
  async getDetailedHealth() {
    return this.request("/health/detailed");
  }
}
new APIClient();
const initialState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  accessToken: null,
  refreshToken: null
};
const authState = writable(initialState);
const isAuthenticated = derived(authState, ($state) => $state.isAuthenticated);
const currentUser = derived(authState, ($state) => $state.user);
const isLoading = derived(authState, ($state) => $state.isLoading);
const authError = derived(authState, ($state) => $state.error);
export {
  isLoading as a,
  authError as b,
  currentUser as c,
  isAuthenticated as i
};
//# sourceMappingURL=authStore.js.map
