"""
Unified Authentication Module
🔐 Consolidated JWT and API key authentication with middleware integration.
"""

from .dependencies import (
    get_current_user,
    get_security_context,
    require_api_key_only,
    require_auth,
    require_jwt_only,
)
from .handlers import APIKeyHandler, AuthenticationHandler, JWTHandler
from .middleware import UnifiedAuthMiddleware

__all__ = [
    "AuthenticationHandler",
    "JWTHandler",
    "APIKeyHandler",
    "UnifiedAuthMiddleware",
    "require_auth",
    "require_jwt_only",
    "require_api_key_only",
    "get_current_user",
    "get_security_context",
]
