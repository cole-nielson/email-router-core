"""
Backward Compatibility Module for AuthService Migration
🔄 This module provides backward compatibility for the migrated auth service.

⚠️ DEPRECATED: Import from app.security.authentication.jwt_service instead.
This compatibility module will be removed in the next version.
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "app.services.auth_service is deprecated. Import from app.security.authentication.jwt_service instead. "
    "This compatibility import will be removed in the next version.",
    DeprecationWarning,
    stacklevel=2
)

# Import and re-export everything from the new location
from ..security.authentication.jwt_service import *

# Ensure get_auth_service is available for backward compatibility
from ..security.authentication.jwt_service import get_auth_service

__all__ = [
    "AuthService",
    "TokenResponse", 
    "UserTokenClaims",
    "LoginRequest",
    "AuthenticatedUser",
    "get_auth_service",
]