"""
Unified Authentication Middleware
🔐 Single middleware that replaces all existing authentication middleware.
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.auth_context import SecurityContext
from ..core.config import get_security_config
from ..core.security_manager import SecurityManager
from .handlers import AuthenticationManager

logger = logging.getLogger(__name__)


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
