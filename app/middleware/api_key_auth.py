"""
API key authentication middleware.
🔐 Validates API keys and manages authentication for protected endpoints.

⚠️ DEPRECATED: This middleware is deprecated and will be removed in the next version.
Please use app.security.authentication.middleware.UnifiedAuthMiddleware instead.
"""

import logging
import secrets
import warnings
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Issue deprecation warning
warnings.warn(
    "APIKeyAuthMiddleware is deprecated. Use app.security.authentication.middleware.UnifiedAuthMiddleware instead. "
    "This middleware will be removed in the next version.",
    DeprecationWarning,
    stacklevel=2
)

logger = logging.getLogger(__name__)


class APIKeyStore:
    """In-memory API key storage and validation."""

    def __init__(self):
        """Initialize API key store."""
        self.api_keys: Dict[str, Dict] = {}
        self.client_keys: Dict[str, List[str]] = {}  # client_id -> [api_keys]

        # Create a default development API key
        self._create_default_keys()

    def _create_default_keys(self):
        """Create default API keys for development."""
        # Master admin key
        admin_key = "sk-dev-admin-12345678901234567890"
        self.api_keys[admin_key] = {
            "key_id": "admin_001",
            "name": "Development Admin Key",
            "client_id": "*",  # Global access
            "permissions": ["read", "write", "admin"],
            "rate_limit": 1000,  # Higher limit for admin
            "created_at": datetime.utcnow(),
            "last_used": None,
            "is_active": True,
            "usage_count": 0,
        }

        # Client-specific key for existing client
        client_key = "sk-dev-client-001-abcdef1234567890"
        self.api_keys[client_key] = {
            "key_id": "client_001_key_001",
            "name": "Development Client Key",
            "client_id": "client-001-cole-nielson",
            "permissions": ["read", "write"],
            "rate_limit": 100,
            "created_at": datetime.utcnow(),
            "last_used": None,
            "is_active": True,
            "usage_count": 0,
        }

        # Update client keys mapping
        self.client_keys["*"] = [admin_key]
        self.client_keys["client-001-cole-nielson"] = [client_key]

        logger.info("Created default development API keys")

    def validate_key(self, api_key: str) -> Optional[Dict]:
        """
        Validate API key and return key information.

        Args:
            api_key: API key to validate

        Returns:
            Key information if valid, None if invalid
        """
        if not api_key or api_key not in self.api_keys:
            return None

        key_info = self.api_keys[api_key]

        # Check if key is active
        if not key_info["is_active"]:
            return None

        # Update usage statistics
        key_info["last_used"] = datetime.utcnow()
        key_info["usage_count"] += 1

        return key_info.copy()

    def get_client_keys(self, client_id: str) -> List[Dict]:
        """Get all API keys for a client."""
        keys = self.client_keys.get(client_id, [])
        return [self.api_keys[key] for key in keys if key in self.api_keys]

    def create_key(
        self, client_id: str, name: str, permissions: List[str], rate_limit: int = 60
    ) -> str:
        """
        Create a new API key.

        Args:
            client_id: Client identifier
            name: Human-readable key name
            permissions: List of permissions
            rate_limit: Rate limit for this key

        Returns:
            Generated API key
        """
        # Generate secure API key
        prefix = "sk-prod" if client_id != "*" else "sk-admin"
        random_part = secrets.token_urlsafe(24)
        api_key = f"{prefix}-{random_part}"

        # Generate key ID
        key_id = f"{client_id}_key_{len(self.client_keys.get(client_id, [])) + 1:03d}"

        # Store key information
        self.api_keys[api_key] = {
            "key_id": key_id,
            "name": name,
            "client_id": client_id,
            "permissions": permissions,
            "rate_limit": rate_limit,
            "created_at": datetime.utcnow(),
            "last_used": None,
            "is_active": True,
            "usage_count": 0,
        }

        # Update client keys mapping
        if client_id not in self.client_keys:
            self.client_keys[client_id] = []
        self.client_keys[client_id].append(api_key)

        logger.info(f"Created API key {key_id} for client {client_id}")
        return api_key

    def revoke_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key in self.api_keys:
            self.api_keys[api_key]["is_active"] = False
            logger.info(f"Revoked API key {self.api_keys[api_key]['key_id']}")
            return True
        return False

    def get_key_stats(self) -> Dict:
        """Get API key usage statistics."""
        total_keys = len(self.api_keys)
        active_keys = sum(1 for key in self.api_keys.values() if key["is_active"])
        total_usage = sum(key["usage_count"] for key in self.api_keys.values())

        return {
            "total_keys": total_keys,
            "active_keys": active_keys,
            "revoked_keys": total_keys - active_keys,
            "total_usage": total_usage,
        }


# Global API key store
key_store = APIKeyStore()


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    API key authentication middleware.

    Features:
    - API key validation for protected endpoints
    - Permission checking based on endpoint requirements
    - Usage tracking and statistics
    - Automatic rate limit integration
    """

    def __init__(self, app):
        """Initialize API key middleware."""
        super().__init__(app)

        # Define public endpoints that don't require authentication
        self.public_endpoints = {
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/health/detailed",
            "/metrics",
            "/auth/login",
            "/auth/refresh",
        }

        # Define webhook endpoints (use different auth)
        self.webhook_endpoints = {"/webhooks/mailgun/inbound", "/webhooks/status", "/webhooks/test"}

        # Define admin-only endpoints
        self.admin_endpoints = {"/api/v1/admin", "/api/v1/keys", "/api/v1/system"}

        logger.info("API key authentication middleware initialized")

    async def dispatch(self, request: Request, call_next):
        """Process request with API key authentication."""
        try:
            path = request.url.path

            # Skip authentication for public endpoints
            if self._is_public_endpoint(path):
                return await call_next(request)

            # Skip authentication for webhook endpoints (they use signature auth)
            if self._is_webhook_endpoint(path):
                return await call_next(request)

            # Extract and validate API key
            api_key = self._extract_api_key(request)
            if not api_key:
                return self._auth_error_response("Missing API key. Include X-API-Key header.")

            # Validate API key
            key_info = key_store.validate_key(api_key)
            if not key_info:
                return self._auth_error_response("Invalid API key.")

            # Check permissions
            if not self._check_permissions(path, key_info, request):
                return self._auth_error_response("Insufficient permissions for this endpoint.")

            # Add authentication info to request state
            request.state.auth = {
                "api_key": api_key,
                "key_info": key_info,
                "client_id": key_info["client_id"],
                "permissions": key_info["permissions"],
            }

            # Process request
            response = await call_next(request)

            # Add authentication headers
            response.headers["X-Client-ID"] = key_info["client_id"]
            response.headers["X-Key-ID"] = key_info["key_id"]

            return response

        except Exception as e:
            logger.error(f"API key middleware error: {e}")
            return self._auth_error_response("Authentication error.")

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public."""
        # Exact match
        if path in self.public_endpoints:
            return True

        # Prefix match for static assets
        public_prefixes = ["/static/", "/favicon.ico"]
        return any(path.startswith(prefix) for prefix in public_prefixes)

    def _is_webhook_endpoint(self, path: str) -> bool:
        """Check if endpoint is a webhook."""
        # Check if path starts with /webhooks/ - all webhook endpoints should be public
        return path.startswith("/webhooks/")

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request headers."""
        # Try X-API-Key header (preferred)
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key

        # Try Authorization header with Bearer scheme
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer ") and auth_header.startswith("Bearer sk-"):
            return auth_header[7:]  # Remove "Bearer " prefix

        # Try query parameter (less secure, for development only)
        return request.query_params.get("api_key")

    def _check_permissions(self, path: str, key_info: Dict, request: Request) -> bool:
        """Check if API key has required permissions for endpoint."""
        permissions = key_info["permissions"]
        client_id = key_info["client_id"]

        # Admin keys have global access
        if "admin" in permissions:
            return True

        # Check admin-only endpoints
        if any(path.startswith(endpoint) for endpoint in self.admin_endpoints):
            return "admin" in permissions

        # Check write operations
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            if "write" not in permissions:
                return False

        # Check read operations
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            if "read" not in permissions:
                return False

        # Check client-specific access
        if client_id != "*":  # Not a global key
            # Extract client ID from path if present
            path_parts = path.split("/")
            if "clients" in path_parts:
                try:
                    path_client_id = path_parts[path_parts.index("clients") + 1]
                    if path_client_id != client_id:
                        return False
                except (IndexError, ValueError):
                    pass

        return True

    def _auth_error_response(self, message: str) -> JSONResponse:
        """Create authentication error response."""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": True,
                "status_code": 401,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "hint": "Include a valid X-API-Key header with your request.",
            },
            headers={"WWW-Authenticate": 'ApiKey realm="API"'},
        )


def get_current_user(request: Request) -> Optional[Dict]:
    """Get current authenticated user from request."""
    return getattr(request.state, "auth", None)


def require_permissions(required_permissions: List[str]):
    """Decorator to require specific permissions for an endpoint."""

    def decorator(func):
        func.required_permissions = required_permissions
        return func

    return decorator


def get_api_key_info(api_key: str) -> Optional[Dict]:
    """Get API key information."""
    return key_store.validate_key(api_key)


def create_api_key(client_id: str, name: str, permissions: List[str], rate_limit: int = 60) -> str:
    """Create a new API key."""
    return key_store.create_key(client_id, name, permissions, rate_limit)


def revoke_api_key(api_key: str) -> bool:
    """Revoke an API key."""
    return key_store.revoke_key(api_key)


def list_api_keys(client_id: Optional[str] = None) -> List[Dict]:
    """List API keys for a client or all keys."""
    if client_id:
        return key_store.get_client_keys(client_id)
    else:
        return list(key_store.api_keys.values())


def get_api_key_stats() -> Dict:
    """Get API key usage statistics."""
    return key_store.get_key_stats()
