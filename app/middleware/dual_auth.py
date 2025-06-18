"""
Dual Authentication Middleware for multi-tenant email router.
🔐 Supports both JWT tokens (humans) and API keys (bots/integrations).

⚠️ DEPRECATED: This middleware is deprecated and will be removed in the next version.
Please use app.security.authentication.middleware.UnifiedAuthMiddleware instead.
"""

import logging
import warnings
from typing import Annotated, Optional, Union

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

# Issue deprecation warning
warnings.warn(
    "DualAuthMiddleware is deprecated. Use app.security.authentication.middleware.UnifiedAuthMiddleware instead. "
    "This middleware will be removed in the next version.",
    DeprecationWarning,
    stacklevel=2
)

from ..database.connection import get_database_session
from ..middleware.jwt_auth import _get_user_from_token_logic
from ..services.auth_service import AuthenticatedUser
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Security scheme for both auth types
bearer_scheme = HTTPBearer(auto_error=False)


# =============================================================================
# DUAL AUTHENTICATION TYPES
# =============================================================================


class APIKeyUser:
    """Represents an API key authenticated user/bot."""

    def __init__(self, client_id: str, key_name: str = "api_key"):
        self.id = 0  # API keys don't have user IDs
        self.username = f"api_key_{key_name}"
        self.email = f"api_{key_name}@{client_id}.local"
        self.full_name = f"API Key ({key_name})"
        self.role = "api_user"  # Special role for API access
        self.client_id = client_id
        self.permissions = [
            "webhooks:write",  # For webhook endpoints
            "client:read",  # For reading client config
            "system:monitor",  # For health checks
        ]
        self.rate_limit_tier = "api_standard"
        self.auth_type = "api_key"


class DualAuthUser:
    """Wrapper for either JWT or API key authenticated user."""

    def __init__(self, user: Union[AuthenticatedUser, APIKeyUser], auth_type: str):
        # Copy all attributes from the underlying user
        self.id = user.id
        self.username = user.username
        self.email = user.email
        self.full_name = user.full_name
        self.role = user.role
        self.client_id = user.client_id
        self.permissions = user.permissions
        self.rate_limit_tier = user.rate_limit_tier
        self.auth_type = auth_type
        self.underlying_user = user


# =============================================================================
# DUAL AUTHENTICATION DEPENDENCIES
# =============================================================================


async def get_dual_auth_user(request: Request) -> Optional[DualAuthUser]:
    """
    Get authenticated user from request state set by DualAuthMiddleware.
    """
    return getattr(request.state, "current_user", None)


async def require_dual_auth(
    user: Annotated[Optional[DualAuthUser], Depends(get_dual_auth_user)],
) -> DualAuthUser:
    """Require either JWT or API key authentication."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide either a JWT Bearer token or API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"Dual auth successful: {user.username} via {user.auth_type}")
    return user


async def require_jwt_only(
    user: Annotated[Optional[DualAuthUser], Depends(get_dual_auth_user)],
) -> DualAuthUser:
    """Require JWT authentication only (no API keys)."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.auth_type != "jwt":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT authentication required for this endpoint",
        )

    return user


async def require_api_key_only(
    user: Annotated[Optional[DualAuthUser], Depends(get_dual_auth_user)],
) -> DualAuthUser:
    """Require API key authentication only (no JWTs)."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key authentication required"
        )

    if user.auth_type != "api_key":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key authentication required for this endpoint",
        )

    return user


# =============================================================================
# ROLE-BASED DUAL AUTH DEPENDENCIES
# =============================================================================


async def require_human_user(
    user: Annotated[DualAuthUser, Depends(require_jwt_only)],
) -> DualAuthUser:
    """Require human user (JWT only) with client admin or super admin role."""
    if user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


async def require_super_admin_dual(
    user: Annotated[DualAuthUser, Depends(require_dual_auth)],
) -> DualAuthUser:
    """Require super admin role via either auth type."""
    if user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required"
        )
    return user


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def extract_api_key_from_request(request: Request) -> Optional[str]:
    """Extract API key from request headers."""
    # Try X-API-Key header (preferred)
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key

    # Try Authorization header with Bearer scheme for API keys
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer sk-"):
        return auth_header[7:]  # Remove "Bearer " prefix

    return None


def extract_client_from_api_key(api_key: str) -> Optional[str]:
    """
    Extract client ID from API key.
    This is a simplified implementation - in production you'd have a proper lookup.
    """
    # Example API key format: sk-client001-abc123def456
    if api_key.startswith("sk-") and len(api_key) > 10:
        parts = api_key.split("-")
        if len(parts) >= 3:
            client_part = parts[1]
            # Map known client prefixes to client IDs
            client_mapping = {
                "client001": "client-001-cole-nielson",
                "test": "test-client",
                "demo": "demo-client",
            }
            return client_mapping.get(client_part)

    return None


def is_webhook_endpoint(path: str) -> bool:
    """Check if the path is a webhook endpoint that should allow API key auth."""
    webhook_paths = ["/webhooks/mailgun/inbound", "/webhooks/test", "/health", "/metrics"]
    return any(path.startswith(webhook_path) for webhook_path in webhook_paths)


def get_auth_type_for_endpoint(path: str) -> str:
    """Determine preferred auth type for endpoint."""
    if is_webhook_endpoint(path):
        return "api_key_preferred"
    elif path.startswith("/auth/"):
        return "public"  # Auth endpoints are public or handle their own auth
    elif path.startswith("/api/v2/"):
        return "jwt_required"  # Configuration endpoints need human users
    else:
        return "dual_auth"  # Most endpoints accept either


# =============================================================================
# MIDDLEWARE CLASS
# =============================================================================


class DualAuthMiddleware(BaseHTTPMiddleware):
    """Middleware that automatically applies the right auth strategy per endpoint."""

    def __init__(self, app):
        super().__init__(app)
        self.auth_cache = {}

    async def dispatch(self, request: Request, call_next):
        """Apply appropriate authentication strategy based on endpoint."""
        path = request.url.path
        auth_strategy = get_auth_type_for_endpoint(path)

        # Skip auth for public endpoints
        if auth_strategy == "public" or self._is_public_endpoint(path):
            response = await call_next(request)
            return response

        # Try to authenticate and add to request state
        db = None
        try:
            db = get_database_session()
            user = None
            if auth_strategy == "api_key_preferred":
                # For webhooks, try API key first
                user = await self._try_api_key_auth(request, db)
                if not user:
                    user = await self._try_jwt_auth(request, db)
            elif auth_strategy == "jwt_required":
                # For config endpoints, require JWT
                user = await self._try_jwt_auth(request, db)
            else:
                # For other endpoints, try both
                user = await self._try_jwt_auth(request, db)
                if not user:
                    user = await self._try_api_key_auth(request, db)

            if user:
                request.state.current_user = user
                request.state.auth_type = user.auth_type
                logger.debug(f"Auth success: {user.username} via {user.auth_type}")

        except Exception as e:
            logger.warning(f"Auth middleware error: {e}")
        finally:
            if db:
                db.close()

        response = await call_next(request)
        return response

    async def _try_jwt_auth(self, request: Request, db: Session) -> Optional[DualAuthUser]:
        """Try JWT authentication."""
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1]
                jwt_user = await _get_user_from_token_logic(token, db)
                if jwt_user:
                    return DualAuthUser(jwt_user, "jwt")
        except Exception:
            pass
        return None

    async def _try_api_key_auth(self, request: Request, db: Session) -> Optional[DualAuthUser]:
        """Try API key authentication."""
        try:
            api_key = extract_api_key_from_request(request)
            if api_key and api_key.startswith("sk-"):
                client_id = extract_client_from_api_key(api_key)
                if client_id:
                    api_user = APIKeyUser(client_id, "webhook_key")
                    return DualAuthUser(api_user, "api_key")
        except Exception:
            pass
        return None

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (no authentication required)."""
        public_paths = [
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

        return any(path.startswith(public_path) for public_path in public_paths)
