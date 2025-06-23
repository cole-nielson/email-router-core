"""
Shared Authentication Types
🔐 Common authentication and authorization types for frontend and backend.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

# =============================================================================
# AUTHENTICATION ENUMS
# =============================================================================


class AuthenticationType(str, Enum):
    """Authentication method types."""

    JWT = "jwt"
    API_KEY = "api_key"
    NONE = "none"


class UserRole(str, Enum):
    """User role types."""

    SUPER_ADMIN = "super_admin"
    CLIENT_ADMIN = "client_admin"
    CLIENT_USER = "client_user"
    API_USER = "api_user"


class RateLimitTier(str, Enum):
    """Rate limiting tiers."""

    STANDARD = "standard"
    PREMIUM = "premium"
    API_STANDARD = "api_standard"
    API_PREMIUM = "api_premium"


# =============================================================================
# AUTHENTICATION REQUEST/RESPONSE SCHEMAS
# =============================================================================


class LoginRequest(BaseModel):
    """User login request."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")
    remember_me: bool = Field(default=False, description="Remember login session")


class LoginResponse(BaseModel):
    """User login response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: "UserInfo" = Field(..., description="User information")


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str = Field(..., description="Refresh token")


class RefreshTokenResponse(BaseModel):
    """Token refresh response."""

    access_token: str = Field(..., description="New access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class ChangePasswordRequest(BaseModel):
    """Password change request."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., description="New password")


class PasswordChangeResponse(BaseModel):
    """Password change response."""

    success: bool = Field(..., description="Whether password was changed")
    message: str = Field(..., description="Response message")
    tokens_revoked: int = Field(..., description="Number of tokens revoked")


# =============================================================================
# USER INFORMATION SCHEMAS
# =============================================================================


class UserInfo(BaseModel):
    """User information for API responses."""

    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: str = Field(..., description="Full name")
    role: UserRole = Field(..., description="User role")
    client_id: Optional[str] = Field(None, description="Associated client ID")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    rate_limit_tier: RateLimitTier = Field(
        default=RateLimitTier.STANDARD, description="Rate limit tier"
    )
    is_active: bool = Field(..., description="Whether user is active")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class UserCreateRequest(BaseModel):
    """User creation request."""

    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: str = Field(..., description="Full name")
    password: str = Field(..., description="Password")
    role: UserRole = Field(default=UserRole.CLIENT_USER, description="User role")
    client_id: Optional[str] = Field(None, description="Associated client ID")
    permissions: List[str] = Field(default_factory=list, description="Additional permissions")


class UserUpdateRequest(BaseModel):
    """User update request."""

    email: Optional[str] = Field(None, description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    role: Optional[UserRole] = Field(None, description="User role")
    client_id: Optional[str] = Field(None, description="Associated client ID")
    permissions: Optional[List[str]] = Field(None, description="User permissions")
    is_active: Optional[bool] = Field(None, description="Whether user is active")


class UserListResponse(BaseModel):
    """User list response."""

    total: int = Field(..., description="Total number of users")
    users: List[UserInfo] = Field(..., description="User information list")
    pagination: Optional[Dict[str, Any]] = Field(None, description="Pagination information")


# =============================================================================
# SESSION MANAGEMENT SCHEMAS
# =============================================================================


class SessionInfo(BaseModel):
    """Session information."""

    session_id: str = Field(..., description="Session identifier")
    user_id: int = Field(..., description="User ID")
    ip_address: str = Field(..., description="IP address")
    user_agent: str = Field(..., description="User agent string")
    created_at: datetime = Field(..., description="Session creation timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    is_current: bool = Field(..., description="Whether this is the current session")


class SessionListResponse(BaseModel):
    """Session list response."""

    sessions: List[SessionInfo] = Field(..., description="Active sessions")
    total: int = Field(..., description="Total number of sessions")


# =============================================================================
# PERMISSION MANAGEMENT SCHEMAS
# =============================================================================


class Permission(BaseModel):
    """Permission definition."""

    name: str = Field(..., description="Permission name")
    resource: str = Field(..., description="Resource type")
    action: str = Field(..., description="Action type")
    description: str = Field(..., description="Permission description")
    requires_client_scope: bool = Field(
        default=False, description="Whether permission is client-scoped"
    )


class PermissionCheck(BaseModel):
    """Permission check request."""

    permission: str = Field(..., description="Permission to check")
    client_id: Optional[str] = Field(None, description="Target client ID")


class PermissionCheckResponse(BaseModel):
    """Permission check response."""

    has_permission: bool = Field(..., description="Whether permission is granted")
    reason: str = Field(..., description="Reason for permission result")


# =============================================================================
# SECURITY CONTEXT (SIMPLIFIED FOR FRONTEND)
# =============================================================================


class SecurityContextInfo(BaseModel):
    """
    Simplified security context for frontend use.

    Contains only non-sensitive information that can be safely
    exposed to client applications.
    """

    is_authenticated: bool = Field(..., description="Whether user is authenticated")
    auth_type: AuthenticationType = Field(..., description="Authentication method")
    user: Optional[UserInfo] = Field(None, description="User information")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    rate_limit_tier: RateLimitTier = Field(
        default=RateLimitTier.STANDARD, description="Rate limit tier"
    )
    is_super_admin: bool = Field(default=False, description="Whether user is super admin")
    client_id: Optional[str] = Field(None, description="Associated client ID")
    session_expires_at: Optional[datetime] = Field(None, description="Session expiration")


# =============================================================================
# API KEY MANAGEMENT SCHEMAS (AUTH-RELATED)
# =============================================================================


class APIKeyCreateRequest(BaseModel):
    """API key creation request."""

    name: str = Field(..., description="API key name")
    client_id: str = Field(..., description="Associated client ID")
    permissions: List[str] = Field(..., description="API key permissions")
    rate_limit: int = Field(default=1000, description="Requests per minute limit")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")


class APIKeyCreateResponse(BaseModel):
    """API key creation response."""

    key_id: str = Field(..., description="API key identifier")
    name: str = Field(..., description="API key name")
    api_key: str = Field(..., description="The actual API key (only shown once)")
    client_id: str = Field(..., description="Associated client ID")
    permissions: List[str] = Field(..., description="API key permissions")
    rate_limit: int = Field(..., description="Requests per minute limit")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")


class APIKeyUpdateRequest(BaseModel):
    """API key update request."""

    name: Optional[str] = Field(None, description="API key name")
    permissions: Optional[List[str]] = Field(None, description="API key permissions")
    rate_limit: Optional[int] = Field(None, description="Requests per minute limit")
    is_active: Optional[bool] = Field(None, description="Whether key is active")


# =============================================================================
# BACKWARD COMPATIBILITY ALIASES
# =============================================================================

# For backward compatibility with existing backend code
AuthType = AuthenticationType
