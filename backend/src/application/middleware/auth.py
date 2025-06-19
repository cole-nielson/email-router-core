"""
Unified Authentication Middleware
🔐 Single middleware that replaces all existing authentication middleware.
"""

import logging
import time
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.auth_context import SecurityContext
from ..core.config import get_security_config
from ..core.security_manager import SecurityManager
from .handlers import AuthenticationManager

logger = logging.getLogger(__name__)


# =============================================================================
# BACKWARD COMPATIBILITY CLASSES
# =============================================================================


class APIKeyUser:
    """
    Backward compatibility wrapper for API key authentication.

    This class provides compatibility with legacy code that expects APIKeyUser objects.
    """

    def __init__(self, client_id: str, scope: str = "general"):
        """Initialize API key user."""
        self.client_id = client_id
        self.scope = scope
        self.auth_type = "api_key"

    def __str__(self):
        return f"APIKeyUser(client_id={self.client_id}, scope={self.scope})"


class DualAuthUser:
    """
    Backward compatibility wrapper for dual authentication.

    This class provides compatibility with legacy code that expects DualAuthUser objects.
    """

    def __init__(self, user, auth_type: str):
        """Initialize dual auth user."""
        self.user = user
        self.underlying_user = user  # Alias for backward compatibility
        self.auth_type = auth_type
        self.client_id = getattr(user, "client_id", None)

        # Copy common attributes from the underlying user
        for attr in ["id", "username", "email", "role", "permissions"]:
            if hasattr(user, attr):
                setattr(self, attr, getattr(user, attr))

    def __str__(self):
        return f"DualAuthUser(user={self.user}, auth_type={self.auth_type})"


# =============================================================================
# BACKWARD COMPATIBILITY FUNCTIONS
# =============================================================================


async def get_dual_auth_user(request: Request) -> Optional["DualAuthUser"]:
    """
    Backward compatibility function for getting dual auth user.

    Returns None if not authenticated (for optional authentication).
    """
    try:
        from .dependencies import get_current_user_optional

        security_context = await get_current_user_optional(request)

        if security_context and security_context.is_authenticated:
            # Create a compatibility user object
            if security_context.auth_type.value == "api_key":
                api_user = APIKeyUser(security_context.client_id or "unknown")
                return DualAuthUser(api_user, "api_key")
            else:
                # For JWT, create a simple user object
                class JWTUser:
                    def __init__(self, context):
                        self.username = context.username
                        self.email = getattr(context, "email", None)
                        self.role = context.role
                        self.client_id = context.client_id

                jwt_user = JWTUser(security_context)
                return DualAuthUser(jwt_user, "jwt")

        return None
    except Exception as e:
        logger.warning(f"Error in get_dual_auth_user compatibility function: {e}")
        return None


async def require_dual_auth(request: Request) -> "DualAuthUser":
    """
    Backward compatibility function for requiring dual auth.

    Raises HTTPException if not authenticated.
    """
    from fastapi import HTTPException, status

    dual_user = await get_dual_auth_user(request)
    if dual_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return dual_user


async def require_api_key_only(request: Request) -> "APIKeyUser":
    """Backward compatibility function for API key only authentication."""
    from fastapi import HTTPException, status

    from .dependencies import get_security_context

    security_context = await get_security_context(request)

    if not security_context.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key authentication required",
        )

    if security_context.auth_type.value != "api_key":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key authentication required for this endpoint",
        )

    return APIKeyUser(security_context.client_id or "unknown")


async def require_jwt_only(request: Request) -> "DualAuthUser":
    """Backward compatibility function for JWT only authentication."""
    from fastapi import HTTPException, status

    from .dependencies import get_security_context

    security_context = await get_security_context(request)

    if not security_context.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if security_context.auth_type.value != "jwt":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT authentication required for this endpoint",
        )

    # Create JWT user wrapper
    class JWTUser:
        def __init__(self, context):
            self.username = context.username
            self.email = getattr(context, "email", None)
            self.role = context.role
            self.client_id = context.client_id

    jwt_user = JWTUser(security_context)
    return DualAuthUser(jwt_user, "jwt")


def extract_api_key_from_request(request: Request) -> Optional[str]:
    """Extract API key from request headers."""
    # Check X-API-Key header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key

    # Check Authorization header with "Bearer" scheme
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        # Simple check if it looks like an API key (not JWT)
        if not token.count(".") == 2:  # JWTs have 2 dots
            return token

    return None


def extract_client_from_api_key(api_key: str) -> Optional[str]:
    """Extract client ID from API key."""
    # This is a simple implementation for backward compatibility
    # In practice, you'd validate against your API key database
    if api_key.startswith("sk-"):
        parts = api_key.split("-")
        if len(parts) >= 3:
            return f"client-{parts[1]}"

    return "unknown-client"


def get_auth_type_for_endpoint(request: Request) -> str:
    """Determine required auth type for endpoint."""
    # Simple implementation - could be enhanced with route analysis
    if request.url.path.startswith("/webhooks/"):
        return "api_key"
    elif request.url.path.startswith("/auth/"):
        return "optional"
    else:
        return "dual"


class UnifiedAuthMiddleware(BaseHTTPMiddleware):
    """
    Unified authentication middleware that replaces:
    - DualAuthMiddleware
    - JWTAuthMiddleware
    - APIKeyMiddleware

    This middleware provides a single, consistent authentication layer
    that handles all authentication methods and integrates with the
    unified security architecture.
    """

    def __init__(self, app):
        """Initialize unified authentication middleware."""
        super().__init__(app)

        # Initialize security components
        self.security_config = get_security_config()
        self.security_manager = SecurityManager(self.security_config)
        self.auth_manager = AuthenticationManager(self.security_config)

        # Public endpoints that skip authentication
        self.public_endpoints = {
            "/",
            "/health",
            "/health/detailed",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/refresh",
        }

        logger.info("Unified authentication middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through unified authentication pipeline.

        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler

        Returns:
            Response from downstream handler
        """
        start_time = time.time()

        try:
            # Create initial security context
            security_context = self.security_manager.create_security_context(request)

            # Add security manager to request state for handlers to use
            request.state.security_manager = self.security_manager
            request.state.security_context = security_context

            # Validate request security policies
            self.security_manager.validate_request_security(request)

            # Skip authentication for public endpoints
            if self._is_public_endpoint(str(request.url.path)):
                logger.debug(f"Skipping authentication for public endpoint: {request.url.path}")
                response = await call_next(request)
                self._add_security_headers(response)
                return response

            # Authenticate the request
            authenticated_context = self.security_manager.authenticate_request(
                request, security_context
            )

            # Update request state with authenticated context
            request.state.security_context = authenticated_context

            # Log authentication result
            if authenticated_context.is_authenticated:
                logger.debug(
                    f"Authentication successful: {authenticated_context.username} "
                    f"via {authenticated_context.auth_type} for {request.url.path}"
                )
            else:
                logger.debug(f"No authentication for {request.url.path}")

            # Process request with authenticated context
            response = await call_next(request)

            # Add security headers and metadata
            self._add_security_headers(response)
            self._add_auth_metadata(response, authenticated_context, start_time)

            return response

        except Exception as e:
            # Log security event for unexpected errors
            self.security_manager.log_security_event(
                "middleware_error",
                {"error": str(e), "path": str(request.url.path)},
                getattr(request.state, "security_context", SecurityContext()).ip_address,
            )
            logger.error(f"Unified auth middleware error: {e}")
            raise

    def _is_public_endpoint(self, path: str) -> bool:
        """
        Check if endpoint is public (no authentication required).

        Args:
            path: Request path

        Returns:
            True if endpoint is public
        """
        # Check exact matches
        if path in self.public_endpoints:
            return True

        # Check prefix matches for static assets
        public_prefixes = ["/static/", "/favicon.ico"]
        if any(path.startswith(prefix) for prefix in public_prefixes):
            return True

        return False

    def _add_security_headers(self, response: Response) -> None:
        """
        Add security headers to response.

        Args:
            response: FastAPI response object
        """
        try:
            # Get environment from unified config for header customization
            try:
                from ...core import get_app_config

                environment = get_app_config().environment.value
            except Exception:
                environment = "production"

            headers = self.security_config.get_security_headers(environment)

            for header, value in headers.items():
                response.headers[header] = value

        except Exception as e:
            logger.warning(f"Failed to add security headers: {e}")

    def _add_auth_metadata(
        self, response: Response, security_context: SecurityContext, start_time: float
    ) -> None:
        """
        Add authentication metadata to response headers.

        Args:
            response: FastAPI response object
            security_context: Current security context
            start_time: Request start time
        """
        try:
            # Add timing and request metadata
            response.headers["X-Response-Time"] = f"{(time.time() - start_time):.3f}s"

            if security_context.request_id:
                response.headers["X-Request-ID"] = security_context.request_id

            # Add authentication metadata (without sensitive info)
            if security_context.is_authenticated:
                response.headers["X-Auth-Type"] = security_context.auth_type

                if security_context.client_id:
                    response.headers["X-Client-ID"] = security_context.client_id

                if security_context.role:
                    response.headers["X-User-Role"] = security_context.role

                # Add rate limit tier for client understanding
                response.headers["X-Rate-Limit-Tier"] = security_context.rate_limit_tier

        except Exception as e:
            logger.warning(f"Failed to add auth metadata: {e}")


# Backward compatibility aliases for gradual migration
class DualAuthMiddleware(UnifiedAuthMiddleware):
    """
    Backward compatibility alias for DualAuthMiddleware.

    This allows existing code to continue working while migrating
    to the new unified authentication system.
    """

    def __init__(self, app):
        logger.warning(
            "DualAuthMiddleware is deprecated. Use UnifiedAuthMiddleware instead. "
            "This compatibility wrapper will be removed in the next version."
        )
        super().__init__(app)


class JWTAuthMiddleware(UnifiedAuthMiddleware):
    """
    Backward compatibility alias for JWTAuthMiddleware.

    This allows existing code to continue working while migrating
    to the new unified authentication system.
    """

    def __init__(self, app):
        logger.warning(
            "JWTAuthMiddleware is deprecated. Use UnifiedAuthMiddleware instead. "
            "This compatibility wrapper will be removed in the next version."
        )
        super().__init__(app)
