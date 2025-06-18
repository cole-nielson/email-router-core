"""
Unified Authorization Module
🛡️ Consolidated RBAC, permissions, and authorization logic.
"""

from .decorators import require_client_access, require_permission, require_role
from .permissions import Permissions, ResourceActions
from .rbac import Permission, RBACManager, Role

__all__ = [
    "RBACManager",
    "Permission",
    "Role",
    "Permissions",
    "ResourceActions",
    "require_permission",
    "require_role",
    "require_client_access",
]
