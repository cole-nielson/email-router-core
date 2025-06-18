"""
Backward Compatibility for RBAC Migration
🔄 This module provides backward compatibility for the migrated RBAC system.

⚠️ DEPRECATED: This module has been moved to app.security.authorization.rbac
Please update your imports. This compatibility layer will be removed in the next version.
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "app.services.rbac is deprecated. Import from app.security.authorization.rbac instead. "
    "This compatibility import will be removed in the next version.",
    DeprecationWarning,
    stacklevel=2
)

# Import and re-export everything from the new location
from ..security.authorization.rbac import (
    RBACService,
    AgenticPermissions,
    Permissions,
    convert_legacy_user_to_security_context,
    get_rbac_manager,
)

# Legacy decorator imports
from ..security.authorization.decorators import (
    require_permission,
    require_role,
    require_client_access,
)

__all__ = [
    "RBACService",
    "AgenticPermissions", 
    "Permissions",
    "require_permission",
    "require_role", 
    "require_client_access",
]