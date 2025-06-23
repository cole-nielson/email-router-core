"""
Security Headers Middleware
🛡️ Adds security headers to all responses for production hardening.
"""

import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import get_security_config

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.

    This middleware enhances security by adding standard security headers
    that protect against common web vulnerabilities.
    """

    def __init__(self, app):
        """Initialize security headers middleware."""
        super().__init__(app)
        self.security_config = get_security_config()

        logger.info("Security headers middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add security headers to response.

        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler

        Returns:
            Response with security headers added
        """
        # Process request
        response = await call_next(request)

        # Add security headers
        self._add_security_headers(response, request)

        return response

    def _add_security_headers(self, response: Response, request: Request) -> None:
        """
        Add security headers to response.

        Args:
            response: FastAPI response object
            request: FastAPI request object
        """
        try:
            # Get environment for header customization
            try:
                from core import get_app_config

                environment = get_app_config().environment.value
            except Exception:
                environment = "production"

            # Get security headers from config
            headers = self.security_config.get_security_headers(environment)

            # Add each header to response
            for header, value in headers.items():
                response.headers[header] = value

            # Add custom headers based on request
            self._add_custom_headers(response, request, environment)

        except Exception as e:
            logger.warning(f"Failed to add security headers: {e}")

    def _add_custom_headers(self, response: Response, request: Request, environment: str) -> None:
        """
        Add custom security headers based on request context.

        Args:
            response: FastAPI response object
            request: FastAPI request object
            environment: Application environment
        """
        # Add CORS headers if not already present
        if "Access-Control-Allow-Origin" not in response.headers:
            if environment == "development":
                response.headers["Access-Control-Allow-Origin"] = "*"
            else:
                # In production, CORS should be handled by CORSMiddleware
                pass

        # Add cache control for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # Add security headers for authentication endpoints
        if request.url.path.startswith("/auth/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Clear-Site-Data"] = '"cache", "cookies", "storage"'

        # Add content type options for JSON responses
        if response.headers.get("content-type", "").startswith("application/json"):
            response.headers["X-Content-Type-Options"] = "nosniff"
