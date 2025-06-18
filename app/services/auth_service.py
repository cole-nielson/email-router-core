"""
Backward Compatibility for AuthService Migration
🔄 This module provides backward compatibility for the migrated auth service.

⚠️ DEPRECATED: This module has been moved to app.security.authentication.jwt_service
Please update your imports. This compatibility layer will be removed in the next version.
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