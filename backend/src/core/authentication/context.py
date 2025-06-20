"""
Security Context for Request-Scoped Authentication
🔐 Centralized authentication state management for each request.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AuthenticationType(str, Enum):
    """Authentication method types."""

    JWT = "jwt"
    API_KEY = "api_key"
    NONE = "none"


class SecurityContext(BaseModel):
    """
    Request-scoped security context containing authentication and authorization state.

    This class centralizes all security-related information for a request,
    providing a single source of truth for authentication and authorization decisions.
    """

    # Authentication state
    is_authenticated: bool = False
    auth_type: AuthenticationType = AuthenticationType.NONE
    auth_token: Optional[str] = None

    # User information
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None

    # Authorization data
    role: Optional[str] = None
    client_id: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)

    # Security metadata
    rate_limit_tier: str = "standard"
    session_id: Optional[str] = None
    api_key_id: Optional[str] = None
    last_activity: Optional[datetime] = None

    # Request context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None

    # Security flags
    requires_mfa: bool = False
    is_super_admin: bool = False
    has_api_access: bool = True

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True

    @classmethod
    def create_unauthenticated(
        cls,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> "SecurityContext":
        """
        Create an unauthenticated security context.

        Args:
            request_id: Unique request identifier
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            SecurityContext instance for unauthenticated request
        """
        return cls(
            is_authenticated=False,
            auth_type=AuthenticationType.NONE,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @classmethod
    def create_from_jwt_user(
        cls,
        user: Any,  # AuthenticatedUser from auth service
        token: str,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> "SecurityContext":
        """
        Create security context from JWT authenticated user.

        Args:
            user: Authenticated user object
            token: JWT token
            request_id: Unique request identifier
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            SecurityContext instance for JWT authenticated user
        """
        return cls(
            is_authenticated=True,
            auth_type=AuthenticationType.JWT,
            auth_token=token,
            user_id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            client_id=user.client_id,
            permissions=user.permissions,
            rate_limit_tier=user.rate_limit_tier,
            is_super_admin=(user.role == "super_admin"),
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            last_activity=datetime.utcnow(),
        )

    @classmethod
    def create_from_api_key(
        cls,
        client_id: str,
        api_key_id: str,
        permissions: List[str],
        token: str,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> "SecurityContext":
        """
        Create security context from API key authentication.

        Args:
            client_id: Client identifier
            api_key_id: API key identifier
            permissions: List of granted permissions
            token: API key token
            request_id: Unique request identifier
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            SecurityContext instance for API key authenticated request
        """
        return cls(
            is_authenticated=True,
            auth_type=AuthenticationType.API_KEY,
            auth_token=token,
            user_id=0,  # API keys don't have user IDs
            username=f"api_key_{api_key_id}",
            email=f"api_{api_key_id}@{client_id}.local",
            full_name=f"API Key ({api_key_id})",
            role="api_user",
            client_id=client_id,
            permissions=permissions,
            rate_limit_tier="api_standard",
            api_key_id=api_key_id,
            is_super_admin=False,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            last_activity=datetime.utcnow(),
        )

    def has_permission(self, permission: str, target_client_id: Optional[str] = None) -> bool:
        """
        Check if the security context has a specific permission.

        Args:
            permission: Permission string (e.g., "routing:write")
            target_client_id: Target client ID for scoped permissions

        Returns:
            True if permission is granted
        """
        if not self.is_authenticated:
            return False

        # Super admin has all permissions
        if self.is_super_admin:
            return True

        # Check explicit permissions
        if permission not in self.permissions:
            return False

        # Check client scoping for non-super-admin users
        if target_client_id and self.client_id and self.client_id != target_client_id:
            return False

        return True

    def has_role(self, required_role: Union[str, List[str]]) -> bool:
        """
        Check if the security context has a required role.

        Args:
            required_role: Single role or list of acceptable roles

        Returns:
            True if role requirement is met
        """
        if not self.is_authenticated or not self.role:
            return False

        if isinstance(required_role, str):
            return self.role == required_role

        return self.role in required_role

    def has_client_access(self, target_client_id: str) -> bool:
        """
        Check if the security context has access to a specific client.

        Args:
            target_client_id: Client ID to check access for

        Returns:
            True if access is granted
        """
        if not self.is_authenticated:
            return False

        # Super admin has access to all clients
        if self.is_super_admin:
            return True

        # Check client scoping
        return self.client_id == target_client_id

    def can_access_endpoint(self, endpoint_path: str, method: str) -> bool:
        """
        Check if the security context can access a specific endpoint.

        Args:
            endpoint_path: API endpoint path
            method: HTTP method

        Returns:
            True if access is granted
        """
        # Public endpoints
        public_endpoints = [
            "/",
            "/health",
            "/health/detailed",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/refresh",
        ]

        if any(endpoint_path.startswith(public) for public in public_endpoints):
            return True

        # Webhook endpoints (API key preferred)
        if endpoint_path.startswith("/webhooks/"):
            return self.is_authenticated

        # Configuration endpoints (JWT required)
        if endpoint_path.startswith("/api/v2/"):
            return self.auth_type == AuthenticationType.JWT

        # Default: require authentication
        return self.is_authenticated

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert security context to dictionary for logging/debugging.

        Returns:
            Dictionary representation of security context
        """
        return {
            "is_authenticated": self.is_authenticated,
            "auth_type": self.auth_type,
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "client_id": self.client_id,
            "permissions_count": len(self.permissions),
            "rate_limit_tier": self.rate_limit_tier,
            "is_super_admin": self.is_super_admin,
            "request_id": self.request_id,
            "ip_address": self.ip_address,
        }

    def __str__(self) -> str:
        """String representation for logging."""
        if not self.is_authenticated:
            return f"SecurityContext(unauthenticated, req_id={self.request_id})"

        return (
            f"SecurityContext("
            f"user={self.username}, "
            f"auth_type={self.auth_type}, "
            f"role={self.role}, "
            f"client={self.client_id}, "
            f"req_id={self.request_id})"
        )
