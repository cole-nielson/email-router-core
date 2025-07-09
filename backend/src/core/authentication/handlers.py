"""
Authentication Handlers for Unified Security Architecture
🔐 Consolidated JWT and API key authentication logic.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from fastapi import Request

from infrastructure.config.security import SecurityConfig

from .context import SecurityContext

logger = logging.getLogger(__name__)


class AuthenticationHandler(ABC):
    """
    Abstract base class for authentication handlers.

    This provides the interface that all authentication methods must implement,
    allowing for consistent authentication handling across different methods.
    """

    def __init__(self, config: SecurityConfig):
        """
        Initialize authentication handler.

        Args:
            config: Security configuration
        """
        self.config = config

    @abstractmethod
    async def authenticate(
        self, request: Request, security_context: SecurityContext
    ) -> SecurityContext:
        """
        Attempt to authenticate the request.

        Args:
            request: FastAPI request object
            security_context: Current security context

        Returns:
            Updated security context (authenticated or unchanged)
        """
        pass

    @abstractmethod
    def can_handle_request(self, request: Request) -> bool:
        """
        Check if this handler can process the request.

        Args:
            request: FastAPI request object

        Returns:
            True if this handler can process the request
        """
        pass


class JWTHandler(AuthenticationHandler):
    """
    JWT authentication handler.

    Handles Bearer token authentication using the existing auth service,
    but integrated into the unified security architecture.
    """

    def can_handle_request(self, request: Request) -> bool:
        """Check if request contains JWT Bearer token."""
        auth_header = request.headers.get("Authorization", "")
        return auth_header.startswith("Bearer ") and not auth_header.startswith("Bearer sk-")

    async def authenticate(
        self, request: Request, security_context: SecurityContext
    ) -> SecurityContext:
        """
        Authenticate request using JWT Bearer token.

        Args:
            request: FastAPI request object
            security_context: Current security context

        Returns:
            Updated security context with JWT authentication
        """
        if not self.can_handle_request(request):
            return security_context

        try:
            # Extract token from Authorization header
            auth_header = request.headers.get("Authorization", "")
            token = auth_header[7:]  # Remove "Bearer " prefix

            # Use existing auth service for validation
            user = await self._validate_jwt_token(token, request)

            if user:
                return SecurityContext.create_from_jwt_user(
                    user=user,
                    token=token,
                    request_id=security_context.request_id,
                    ip_address=security_context.ip_address,
                    user_agent=security_context.user_agent,
                )

        except Exception as e:
            logger.debug(f"JWT authentication failed: {e}")
            # Log security event for monitoring

            if hasattr(request.state, "security_manager"):
                request.state.security_manager.log_security_event(
                    "invalid_jwt_token", {"error": str(e)}, security_context.ip_address
                )

        return security_context

    async def _validate_jwt_token(self, token: str, request: Request = None):
        """
        Validate JWT token using auth service from request state if available.

        Args:
            token: JWT token string
            request: FastAPI request object (optional)

        Returns:
            User-like object with JWT claims or None
        """
        try:
            logger.debug(f"Attempting to validate JWT token: {token[:20]}...")

            # Try to use auth service from request state for database validation
            if request and hasattr(request.state, "auth_service") and request.state.auth_service:
                logger.debug("Using auth service from request state for full validation")
                auth_service = request.state.auth_service

                # Check if this is the new auth service (has async validate_token)
                if hasattr(auth_service, "validate_token") and hasattr(
                    auth_service.__class__.validate_token, "__code__"
                ):
                    # New auth service - use async validate_token
                    claims = await auth_service.validate_token(token)
                else:
                    # Legacy auth service - use sync validate_token
                    claims = auth_service.validate_token(token)
            else:
                # Fallback to stateless validation if no auth service available
                logger.debug("Using stateless validation (no auth service available)")
                from .jwt import AuthService as LegacyAuthService

                claims = LegacyAuthService.validate_token_stateless(token)
                logger.debug(f"JWT stateless validation result: {claims}")

            if claims:
                # Handle different claim structures between new and legacy services
                if hasattr(claims, "user_id"):
                    # New auth service structure
                    user_id = claims.user_id
                    username = claims.username
                    email = claims.email
                    role = claims.role
                    client_id = claims.client_id
                    permissions = getattr(claims, "permissions", [])
                else:
                    # Legacy auth service structure
                    user_id = int(claims.sub)
                    username = claims.username
                    email = claims.email
                    role = claims.role
                    client_id = claims.client_id
                    permissions = getattr(claims, "permissions", [])

                # Return a user-like object with basic info from JWT claims
                user_obj = type(
                    "JWTUser",
                    (),
                    {
                        "id": user_id,
                        "username": username,
                        "email": email,
                        "role": role,
                        "client_id": client_id,
                        "permissions": permissions or [],
                        "auth_type": "jwt",
                    },
                )()
                logger.debug(f"Created JWT user object: {user_obj.username}")
                return user_obj

        except Exception as e:
            logger.error(f"JWT validation error in handler: {e}")

        return None


class APIKeyHandler(AuthenticationHandler):
    """
    API key authentication handler.

    Handles API key authentication for webhooks and automated systems,
    integrated into the unified security architecture.
    """

    def can_handle_request(self, request: Request) -> bool:
        """Check if request contains API key."""
        # Check X-API-Key header
        if request.headers.get("X-API-Key"):
            return True

        # Check Authorization header with API key format
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer sk-"):
            return True

        return False

    async def authenticate(
        self, request: Request, security_context: SecurityContext
    ) -> SecurityContext:
        """
        Authenticate request using API key.

        Args:
            request: FastAPI request object
            security_context: Current security context

        Returns:
            Updated security context with API key authentication
        """
        if not self.can_handle_request(request):
            return security_context

        try:
            api_key = self._extract_api_key(request)
            if not api_key:
                return security_context

            # Validate API key and extract client info
            client_id, permissions, key_id = await self._validate_api_key(api_key)

            if client_id:
                return SecurityContext.create_from_api_key(
                    client_id=client_id,
                    api_key_id=key_id,
                    permissions=permissions,
                    token=api_key,
                    request_id=security_context.request_id,
                    ip_address=security_context.ip_address,
                    user_agent=security_context.user_agent,
                )

        except Exception as e:
            logger.debug(f"API key authentication failed: {e}")
            # Log security event for monitoring

            if hasattr(request.state, "security_manager"):
                request.state.security_manager.log_security_event(
                    "invalid_api_key", {"error": str(e)}, security_context.ip_address
                )

        return security_context

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """
        Extract API key from request headers.

        Args:
            request: FastAPI request object

        Returns:
            API key string or None
        """
        # Try X-API-Key header (preferred)
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key

        # Try Authorization header with Bearer scheme for API keys
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer sk-"):
            return auth_header[7:]  # Remove "Bearer " prefix

        return None

    async def _validate_api_key(self, api_key: str) -> tuple[Optional[str], list[str], str]:
        """
        Validate API key and return client info.

        Args:
            api_key: API key to validate

        Returns:
            Tuple of (client_id, permissions, key_id)
        """
        # This is a simplified implementation
        # In production, this would query a proper API key management system

        if not api_key.startswith("sk-"):
            return None, [], ""

        # Extract client from API key format: sk-{client}-{random}
        parts = api_key.split("-")
        if len(parts) < 3:
            return None, [], ""

        client_part = parts[1]

        # Map client prefixes to full client IDs
        client_mapping = {
            "dev": "client-001-cole-nielson",
            "client001": "client-001-cole-nielson",
            "admin": "*",  # Global admin key
            "test": "test-client",
            "demo": "demo-client",
        }

        client_id = client_mapping.get(client_part)
        if not client_id:
            return None, [], ""

        # Define permissions based on client type
        if client_id == "*":
            # Admin API key - full permissions
            permissions = [
                "clients:read",
                "clients:write",
                "clients:admin",
                "system:admin",
                "system:monitor",
                "webhooks:write",
                "webhooks:read",
            ]
        else:
            # Client-specific API key - limited permissions
            permissions = [
                "client:read",
                "webhooks:write",
                "system:monitor",
                "routing:read",
            ]

        key_id = f"{client_part}_api_key"

        return client_id, permissions, key_id


class AuthenticationManager:
    """
    Manager that coordinates multiple authentication handlers.

    This class orchestrates the authentication process by trying
    different authentication methods in the appropriate order.
    """

    def __init__(self, config: SecurityConfig):
        """
        Initialize authentication manager.

        Args:
            config: Security configuration
        """
        self.config = config
        self.handlers = [
            JWTHandler(config),
            APIKeyHandler(config),
        ]

    async def authenticate_request(
        self,
        request: Request,
        security_context: SecurityContext,
        preferred_method: Optional[str] = None,
    ) -> SecurityContext:
        """
        Authenticate request using available handlers.

        Args:
            request: FastAPI request object
            security_context: Current security context
            preferred_method: Preferred authentication method ("jwt" or "api_key")

        Returns:
            Updated security context with authentication state
        """
        # Determine handler order based on preference
        handlers = self._get_ordered_handlers(request, preferred_method)

        # Try each handler until one succeeds
        for handler in handlers:
            if handler.can_handle_request(request):
                authenticated_context = await handler.authenticate(request, security_context)
                if authenticated_context.is_authenticated:
                    logger.debug(
                        f"Authentication successful: {handler.__class__.__name__} "
                        f"for user {authenticated_context.username}"
                    )
                    return authenticated_context

        # No authentication succeeded
        return security_context

    def _get_ordered_handlers(
        self, request: Request, preferred_method: Optional[str] = None
    ) -> list[AuthenticationHandler]:
        """
        Get handlers in order of preference.

        Args:
            request: FastAPI request object
            preferred_method: Preferred authentication method

        Returns:
            List of handlers in order of preference
        """
        # Get endpoint-based preference if not specified
        if not preferred_method:
            path = str(request.url.path)
            if path.startswith("/webhooks/"):
                preferred_method = "api_key"
            elif path.startswith("/api/v2/"):
                preferred_method = "jwt"
            else:
                preferred_method = "jwt"  # Default preference

        # Order handlers based on preference
        jwt_handler = next(h for h in self.handlers if isinstance(h, JWTHandler))
        api_key_handler = next(h for h in self.handlers if isinstance(h, APIKeyHandler))

        if preferred_method == "api_key":
            return [api_key_handler, jwt_handler]
        else:
            return [jwt_handler, api_key_handler]
