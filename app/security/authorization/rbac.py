"""
Unified Role-Based Access Control (RBAC) Manager
🛡️ Consolidated authorization logic replacing scattered RBAC implementations.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Union

from fastapi import HTTPException, status
from pydantic import BaseModel

from ..core.auth_context import SecurityContext
from .permissions import Permissions, PermissionSets, PermissionUtils

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """Standard roles in the system."""

    SUPER_ADMIN = "super_admin"
    CLIENT_ADMIN = "client_admin"
    CLIENT_USER = "client_user"
    API_USER = "api_user"


class Permission(BaseModel):
    """Individual permission model."""

    resource: str
    action: str
    client_id: Optional[str] = None  # For client-scoped permissions

    @property
    def permission_string(self) -> str:
        """Get permission as string format."""
        return f"{self.resource}:{self.action}"

    def matches(self, permission_string: str, target_client_id: Optional[str] = None) -> bool:
        """
        Check if this permission matches a permission string.

        Args:
            permission_string: Permission to check (e.g., "routing:write")
            target_client_id: Target client for scoped permissions

        Returns:
            True if permission matches
        """
        if self.permission_string != permission_string:
            return False

        # Check client scoping
        if self.client_id and target_client_id:
            return self.client_id == target_client_id

        return True


class RBACManager:
    """
    Unified Role-Based Access Control manager.

    This class consolidates all authorization logic from the old scattered
    RBAC implementations into a single, consistent system.
    """

    def __init__(self):
        """Initialize RBAC manager with role definitions."""
        self._role_permissions = self._initialize_role_permissions()

    def _initialize_role_permissions(self) -> Dict[str, List[str]]:
        """Initialize role-to-permissions mapping."""
        return {
            Role.SUPER_ADMIN.value: PermissionSets.SUPER_ADMIN,
            Role.CLIENT_ADMIN.value: PermissionSets.CLIENT_ADMIN,
            Role.CLIENT_USER.value: PermissionSets.BASIC_USER,
            Role.API_USER.value: PermissionSets.API_KEY_STANDARD,
        }

    # =========================================================================
    # PERMISSION CHECKING
    # =========================================================================

    def check_permission(
        self,
        security_context: SecurityContext,
        permission: str,
        target_client_id: Optional[str] = None,
        raise_on_deny: bool = True,
    ) -> bool:
        """
        Check if security context has specific permission.

        Args:
            security_context: Current security context
            permission: Permission to check (e.g., "routing:write")
            target_client_id: Target client for scoped permissions
            raise_on_deny: Whether to raise HTTPException on denial

        Returns:
            True if permission is granted

        Raises:
            HTTPException: If permission denied and raise_on_deny=True
        """
        if not security_context.is_authenticated:
            if raise_on_deny:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
                )
            return False

        # Super admin has all permissions
        if security_context.is_super_admin:
            logger.debug(f"Super admin access granted for permission: {permission}")
            return True

        # Check explicit permissions from security context
        if permission in security_context.permissions:
            # For scoped resources, check client context
            if target_client_id and security_context.client_id:
                if security_context.client_id != target_client_id:
                    if raise_on_deny:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Access denied to client {target_client_id}",
                        )
                    return False

            logger.debug(f"Permission granted: {permission}")
            return True

        # Check role-based permissions
        role_permissions = self._role_permissions.get(security_context.role, [])
        if permission in role_permissions:
            # Apply client scoping for non-super-admin roles
            if (
                target_client_id
                and security_context.role != Role.SUPER_ADMIN.value
                and security_context.client_id
                and security_context.client_id != target_client_id
            ):

                if raise_on_deny:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied to client {target_client_id}",
                    )
                return False

            logger.debug(f"Role-based permission granted: {permission}")
            return True

        # Permission denied
        if raise_on_deny:
            logger.warning(
                f"Permission denied: {permission} for user {security_context.username} "
                f"(role: {security_context.role})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission denied: {permission}"
            )

        return False

    def check_role(
        self,
        security_context: SecurityContext,
        required_roles: Union[str, List[str]],
        raise_on_deny: bool = True,
    ) -> bool:
        """
        Check if security context has required role.

        Args:
            security_context: Current security context
            required_roles: Single role or list of acceptable roles
            raise_on_deny: Whether to raise HTTPException on denial

        Returns:
            True if role requirement is met

        Raises:
            HTTPException: If role requirement not met and raise_on_deny=True
        """
        if not security_context.is_authenticated:
            if raise_on_deny:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
                )
            return False

        # Normalize to list
        if isinstance(required_roles, str):
            required_roles = [required_roles]

        # Check role
        if security_context.role in required_roles:
            return True

        # Role requirement not met
        if raise_on_deny:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role requirement not met. Required: {required_roles}, Current: {security_context.role}",
            )

        return False

    def check_client_access(
        self, security_context: SecurityContext, client_id: str, raise_on_deny: bool = True
    ) -> bool:
        """
        Check if security context has access to specific client.

        Args:
            security_context: Current security context
            client_id: Client ID to check access for
            raise_on_deny: Whether to raise HTTPException on denial

        Returns:
            True if access granted

        Raises:
            HTTPException: If access denied and raise_on_deny=True
        """
        if not security_context.is_authenticated:
            if raise_on_deny:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
                )
            return False

        # Super admin has access to all clients
        if security_context.is_super_admin:
            return True

        # Check client scoping
        if security_context.client_id == client_id:
            return True

        # Access denied
        if raise_on_deny:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Access denied to client {client_id}"
            )

        return False

    # =========================================================================
    # ROLE MANAGEMENT
    # =========================================================================

    def get_role_permissions(self, role: str) -> List[str]:
        """
        Get permissions for a specific role.

        Args:
            role: Role name

        Returns:
            List of permissions for the role
        """
        return self._role_permissions.get(role, [])

    def add_role_permission(self, role: str, permission: str) -> None:
        """
        Add permission to a role.

        Args:
            role: Role name
            permission: Permission to add
        """
        if role not in self._role_permissions:
            self._role_permissions[role] = []

        if permission not in self._role_permissions[role]:
            self._role_permissions[role].append(permission)
            logger.info(f"Added permission {permission} to role {role}")

    def remove_role_permission(self, role: str, permission: str) -> None:
        """
        Remove permission from a role.

        Args:
            role: Role name
            permission: Permission to remove
        """
        if role in self._role_permissions and permission in self._role_permissions[role]:
            self._role_permissions[role].remove(permission)
            logger.info(f"Removed permission {permission} from role {role}")

    def create_custom_role(self, role_name: str, permissions: List[str]) -> None:
        """
        Create a custom role with specific permissions.

        Args:
            role_name: Name of the new role
            permissions: List of permissions for the role
        """
        # Validate permissions
        is_valid, errors = PermissionUtils.validate_permissions(permissions)
        if not is_valid:
            raise ValueError(f"Invalid permissions: {errors}")

        self._role_permissions[role_name] = permissions.copy()
        logger.info(f"Created custom role {role_name} with {len(permissions)} permissions")

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_user_effective_permissions(self, security_context: SecurityContext) -> List[str]:
        """
        Get all effective permissions for a user.

        Args:
            security_context: Current security context

        Returns:
            List of all effective permissions
        """
        permissions = set()

        # Add explicit permissions
        permissions.update(security_context.permissions)

        # Add role-based permissions
        role_permissions = self.get_role_permissions(security_context.role or "")
        permissions.update(role_permissions)

        # Super admin gets all permissions
        if security_context.is_super_admin:
            permissions.update(PermissionUtils.get_all_permissions())

        return sorted(list(permissions))

    def get_accessible_resources(self, security_context: SecurityContext) -> Dict[str, List[str]]:
        """
        Get resources accessible to the user.

        Args:
            security_context: Current security context

        Returns:
            Dictionary of resource -> [actions]
        """
        resources = {}
        permissions = self.get_user_effective_permissions(security_context)

        for permission in permissions:
            try:
                resource, action = PermissionUtils.parse_permission(permission)
                if resource not in resources:
                    resources[resource] = []
                if action not in resources[resource]:
                    resources[resource].append(action)
            except ValueError:
                continue  # Skip invalid permission format

        return resources

    def can_perform_action(
        self,
        security_context: SecurityContext,
        resource: str,
        action: str,
        target_client_id: Optional[str] = None,
    ) -> bool:
        """
        Check if user can perform specific action on resource.

        Args:
            security_context: Current security context
            resource: Resource name
            action: Action name
            target_client_id: Target client for scoped resources

        Returns:
            True if action is allowed
        """
        permission = PermissionUtils.build_permission(resource, action)
        return self.check_permission(
            security_context, permission, target_client_id, raise_on_deny=False
        )


# Global RBAC manager instance
_rbac_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """
    Get the global RBAC manager instance.

    Returns:
        RBACManager instance
    """
    global _rbac_manager

    if _rbac_manager is None:
        _rbac_manager = RBACManager()
        logger.info("RBAC manager initialized")

    return _rbac_manager


# Convenience functions for backward compatibility
def check_permission(
    security_context: SecurityContext, permission: str, client_id: Optional[str] = None
) -> bool:
    """Check permission using global RBAC manager."""
    return get_rbac_manager().check_permission(
        security_context, permission, client_id, raise_on_deny=False
    )


def require_permission(
    security_context: SecurityContext, permission: str, client_id: Optional[str] = None
) -> None:
    """Require permission using global RBAC manager."""
    get_rbac_manager().check_permission(security_context, permission, client_id, raise_on_deny=True)


# =============================================================================
# LEGACY COMPATIBILITY LAYER
# =============================================================================

def convert_legacy_user_to_security_context(user) -> SecurityContext:
    """
    Convert legacy user objects to SecurityContext for unified RBAC.
    
    Args:
        user: AuthenticatedUser or UserTokenClaims from legacy system
        
    Returns:
        SecurityContext compatible with unified system
    """
    from ...authentication.jwt_service import AuthenticatedUser, UserTokenClaims
    
    if hasattr(user, 'id') and hasattr(user, 'username'):
        # AuthenticatedUser
        return SecurityContext(
            is_authenticated=True,
            auth_type="jwt",
            user_id=user.id,
            username=user.username,
            role=user.role,
            client_id=user.client_id,
            permissions=getattr(user, 'permissions', []),
            is_super_admin=user.role == "super_admin",
            rate_limit_tier=getattr(user, 'rate_limit_tier', 'standard')
        )
    elif hasattr(user, 'sub') and hasattr(user, 'username'):
        # UserTokenClaims
        return SecurityContext(
            is_authenticated=True,
            auth_type="jwt",
            user_id=int(user.sub),
            username=user.username,
            role=user.role,
            client_id=user.client_id,
            permissions=user.permissions,
            is_super_admin=user.role == "super_admin"
        )
    else:
        raise ValueError(f"Unknown user type: {type(user)}")


class AgenticPermissions:
    """
    Helper class for AI agent permission checking (migrated from legacy RBAC).
    Provides convenient methods for agentic workflows.
    """
    
    def __init__(self, security_context: SecurityContext):
        self.security_context = security_context
        self.rbac_manager = get_rbac_manager()
    
    @classmethod
    def from_legacy_user(cls, user):
        """Create from legacy user object."""
        security_context = convert_legacy_user_to_security_context(user)
        return cls(security_context)
    
    def can_read_client_config(self, client_id: str) -> bool:
        """Check if agent can read client configuration."""
        return self.rbac_manager.check_permission(
            self.security_context, Permissions.CLIENT_READ, client_id, raise_on_deny=False
        )
    
    def can_write_client_config(self, client_id: str) -> bool:
        """Check if agent can write client configuration."""
        return self.rbac_manager.check_permission(
            self.security_context, Permissions.CLIENT_WRITE, client_id, raise_on_deny=False
        )
    
    def can_manage_routing(self, client_id: str) -> bool:
        """Check if agent can manage routing rules."""
        return self.rbac_manager.check_permission(
            self.security_context, Permissions.ROUTING_WRITE, client_id, raise_on_deny=False
        )
    
    def can_access_webhooks(self) -> bool:
        """Check if agent can access webhook endpoints."""
        return self.rbac_manager.check_permission(
            self.security_context, Permissions.WEBHOOKS_WRITE, raise_on_deny=False
        )
    
    def can_monitor_system(self) -> bool:
        """Check if agent can monitor system status."""
        return self.rbac_manager.check_permission(
            self.security_context, Permissions.SYSTEM_MONITOR, raise_on_deny=False
        )
    
    def require_client_access(self, client_id: str) -> None:
        """Require access to specific client or raise exception."""
        self.rbac_manager.check_client_access(self.security_context, client_id)
    
    def require_admin_access(self) -> None:
        """Require admin access or raise exception."""
        if not self.security_context.is_super_admin:
            self.rbac_manager.check_role(self.security_context, [Role.SUPER_ADMIN.value])


# =============================================================================
# LEGACY RBAC SERVICE COMPATIBILITY CLASS
# =============================================================================

class RBACService:
    """
    Legacy RBAC service compatibility layer.
    
    ⚠️ DEPRECATED: This class provides backward compatibility for the migrated RBAC system.
    New code should use the unified RBACManager directly or SecurityContext-based functions.
    """
    
    @staticmethod
    def check_permission(
        user, 
        permission: str, 
        client_id: Optional[str] = None, 
        raise_on_deny: bool = True
    ) -> bool:
        """
        Check user permission (legacy compatibility method).
        
        Args:
            user: AuthenticatedUser or UserTokenClaims
            permission: Permission string (e.g., "routing:write")
            client_id: Optional client ID for scoped permissions
            raise_on_deny: Whether to raise exception on denial
            
        Returns:
            True if permission is granted
        """
        security_context = convert_legacy_user_to_security_context(user)
        return get_rbac_manager().check_permission(
            security_context, permission, client_id, raise_on_deny
        )
    
    @staticmethod
    def check_client_access(
        user, 
        client_id: str, 
        raise_on_deny: bool = True
    ) -> bool:
        """
        Check user access to specific client (legacy compatibility method).
        
        Args:
            user: AuthenticatedUser or UserTokenClaims
            client_id: Client ID to check access for
            raise_on_deny: Whether to raise exception on denial
            
        Returns:
            True if access is granted
        """
        security_context = convert_legacy_user_to_security_context(user)
        return get_rbac_manager().check_client_access(
            security_context, client_id, raise_on_deny
        )
    
    @staticmethod
    def require_role(user, required_roles: Union[str, List[str]]) -> None:
        """
        Require specific role (legacy compatibility method).
        
        Args:
            user: AuthenticatedUser or UserTokenClaims  
            required_roles: Required role(s)
        """
        security_context = convert_legacy_user_to_security_context(user)
        if isinstance(required_roles, str):
            required_roles = [required_roles]
        get_rbac_manager().check_role(security_context, required_roles)
    
    @staticmethod
    def get_agentic_permissions(user):
        """Get AgenticPermissions helper for user (legacy compatibility method)."""
        return AgenticPermissions.from_legacy_user(user)
