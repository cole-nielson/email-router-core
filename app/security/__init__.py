"""
Unified Security Module for Email Router
🔐 Centralized authentication, authorization, and security management.

This module consolidates all security-related functionality including:
- JWT and API key authentication
- Role-based access control (RBAC)
- Security middleware and headers
- Permission management and validation
- Security configuration and monitoring

Phase 3: Security Architecture Refactor - Unified implementation
"""

from .authentication.dependencies import (
    get_current_user,
    get_security_context,
    require_api_key_only,
    require_auth,
    require_jwt_only,
)

# Authentication components
from .authentication.handlers import APIKeyHandler, AuthenticationHandler, JWTHandler
from .authentication.middleware import UnifiedAuthMiddleware
from .authorization.decorators import (
    require_client_access,
    require_permission,
    require_role,
)
from .authorization.permissions import Permissions, ResourceActions

# Authorization components
from .authorization.rbac import Permission, RBACManager, Role

# Core security components
from .core.auth_context import AuthenticationType, SecurityContext

# Configuration
from .core.config import SecurityConfig
from .core.security_manager import SecurityManager

# Security middleware
from .middleware.security_headers import SecurityHeadersMiddleware
from .middleware.threat_detection import ThreatDetectionMiddleware

__all__ = [
    # Core
    "SecurityContext",
    "AuthenticationType",
    "SecurityManager",
    "SecurityConfig",
    # Authentication
    "AuthenticationHandler",
    "JWTHandler",
    "APIKeyHandler",
    "UnifiedAuthMiddleware",
    "require_auth",
    "require_jwt_only",
    "require_api_key_only",
    "get_current_user",
    "get_security_context",
    # Authorization
    "RBACManager",
    "Permission",
    "Role",
    "Permissions",
    "ResourceActions",
    "require_permission",
    "require_role",
    "require_client_access",
    # Middleware
    "SecurityHeadersMiddleware",
    "ThreatDetectionMiddleware",
]

# Version info
__version__ = "3.0.0"
__security_version__ = "unified-architecture"
