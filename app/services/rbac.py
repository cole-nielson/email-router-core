"""
Role-Based Access Control (RBAC) system for multi-tenant email router.
🛡️ Fine-grained permission management optimized for agentic workflows.
"""

import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from fastapi import HTTPException, status

from .auth_service import AuthenticatedUser, UserTokenClaims

logger = logging.getLogger(__name__)

# =============================================================================
# PERMISSION DEFINITIONS
# =============================================================================


class Permissions:
    """Centralized permission definitions for consistency."""

    # Client management
    CLIENT_READ = "client:read"
    CLIENT_WRITE = "client:write"
    CLIENT_DELETE = "client:delete"
    CLIENT_ADMIN = "client:admin"

    # Multi-client access (super admin)
    CLIENTS_READ = "clients:read"
    CLIENTS_WRITE = "clients:write"
    CLIENTS_DELETE = "clients:delete"
    CLIENTS_ADMIN = "clients:admin"

    # Routing rules
    ROUTING_READ = "routing:read"
    ROUTING_WRITE = "routing:write"
    ROUTING_DELETE = "routing:delete"
    ROUTING_ADMIN = "routing:admin"

    # Branding configuration
    BRANDING_READ = "branding:read"
    BRANDING_WRITE = "branding:write"
    BRANDING_DELETE = "branding:delete"
    BRANDING_ADMIN = "branding:admin"

    # AI prompts
    AI_PROMPTS_READ = "ai_prompts:read"
    AI_PROMPTS_WRITE = "ai_prompts:write"
    AI_PROMPTS_DELETE = "ai_prompts:delete"
    AI_PROMPTS_ADMIN = "ai_prompts:admin"

    # Response times
    RESPONSE_TIMES_READ = "response_times:read"
    RESPONSE_TIMES_WRITE = "response_times:write"
    RESPONSE_TIMES_DELETE = "response_times:delete"
    RESPONSE_TIMES_ADMIN = "response_times:admin"

    # User management
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"
    USERS_ADMIN = "users:admin"

    # System administration
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"


class ResourceActions:
    """Standard actions for any resource."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


# =============================================================================
# RBAC PERMISSION CHECKER
# =============================================================================


class RBACService:
    """Role-based access control service for permission management."""

    @staticmethod
    def check_permission(
        user: Union[AuthenticatedUser, UserTokenClaims],
        permission: str,
        client_id: Optional[str] = None,
        raise_on_deny: bool = True,
    ) -> bool:
        """
        Check if user has specified permission.

        Args:
            user: Authenticated user or token claims
            permission: Permission string (e.g., "routing:write")
            client_id: Required client ID for scoped resources
            raise_on_deny: Whether to raise HTTPException on permission denial

        Returns:
            bool: True if permission granted

        Raises:
            HTTPException: If permission denied and raise_on_deny=True
        """
        # Extract user data
        if isinstance(user, AuthenticatedUser):
            role = user.role  # Already a string from auth_service
            user_client_id = user.client_id
            permissions = user.permissions
        else:  # UserTokenClaims
            role = user.role
            user_client_id = user.client_id
            permissions = user.permissions

        # Super admin has all permissions
        if role == "super_admin":
            logger.debug(f"Super admin access granted for permission: {permission}")
            return True

        # Check explicit permissions
        if permission in permissions:
            # For scoped resources, check client context
            if client_id and user_client_id and user_client_id != client_id:
                if raise_on_deny:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied to client {client_id}",
                    )
                return False

            logger.debug(f"Permission granted: {permission}")
            return True

        # Permission denied
        if raise_on_deny:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission denied: {permission}"
            )

        logger.warning(f"Permission denied: {permission} for user with role {role}")
        return False

    @staticmethod
    def check_client_access(
        user: Union[AuthenticatedUser, UserTokenClaims], client_id: str, raise_on_deny: bool = True
    ) -> bool:
        """
        Check if user has access to specific client.

        Args:
            user: Authenticated user or token claims
            client_id: Client ID to check access for
            raise_on_deny: Whether to raise HTTPException on access denial

        Returns:
            bool: True if access granted
        """
        # Extract user data
        if isinstance(user, AuthenticatedUser):
            role = user.role  # Already a string from auth_service
            user_client_id = user.client_id
        else:  # UserTokenClaims
            role = user.role
            user_client_id = user.client_id

        # Super admin has access to all clients
        if role == "super_admin":
            return True

        # Check client scoping
        if user_client_id == client_id:
            return True

        # Access denied
        if raise_on_deny:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Access denied to client {client_id}"
            )

        return False

    @staticmethod
    def require_role(
        user: Union[AuthenticatedUser, UserTokenClaims],
        required_roles: Union[str, List[str]],
        raise_on_deny: bool = True,
    ) -> bool:
        """
        Check if user has one of the required roles.

        Args:
            user: Authenticated user or token claims
            required_roles: Single role string or list of acceptable roles
            raise_on_deny: Whether to raise HTTPException on role mismatch

        Returns:
            bool: True if role requirement met
        """
        # Extract role
        if isinstance(user, AuthenticatedUser):
            user_role = user.role  # Already a string from auth_service
        else:  # UserTokenClaims
            user_role = user.role

        # Normalize to list
        if isinstance(required_roles, str):
            required_roles = [required_roles]

        # Check role
        if user_role in required_roles:
            return True

        # Role requirement not met
        if raise_on_deny:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role requirement not met. Required: {required_roles}, Current: {user_role}",
            )

        return False


# =============================================================================
# DECORATORS FOR ROUTE PROTECTION
# =============================================================================


def require_permission(permission: str, client_id_param: Optional[str] = None):
    """
    Decorator to require specific permission for route access.

    Args:
        permission: Required permission (e.g., "routing:write")
        client_id_param: Parameter name containing client_id for scoping

    Usage:
        @require_permission("routing:write", "client_id")
        async def update_routing_rule(client_id: str, current_user: AuthenticatedUser):
            # Route logic
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find current_user in function signature
            current_user = None
            for arg in args:
                if isinstance(arg, (AuthenticatedUser, UserTokenClaims)):
                    current_user = arg
                    break

            # Check kwargs for current_user
            if not current_user:
                current_user = kwargs.get("current_user")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
                )

            # Extract client_id if specified
            client_id = None
            if client_id_param:
                client_id = kwargs.get(client_id_param)

            # Check permission
            RBACService.check_permission(current_user, permission, client_id)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(*roles: str):
    """
    Decorator to require specific role(s) for route access.

    Args:
        *roles: Required roles (e.g., "super_admin", "client_admin")

    Usage:
        @require_role("super_admin", "client_admin")
        async def admin_only_route(current_user: AuthenticatedUser):
            # Route logic
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find current_user in function signature
            current_user = None
            for arg in args:
                if isinstance(arg, (AuthenticatedUser, UserTokenClaims)):
                    current_user = arg
                    break

            # Check kwargs for current_user
            if not current_user:
                current_user = kwargs.get("current_user")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
                )

            # Check role requirement
            RBACService.require_role(current_user, list(roles))

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_client_access(client_id_param: str):
    """
    Decorator to require access to specific client.

    Args:
        client_id_param: Parameter name containing client_id

    Usage:
        @require_client_access("client_id")
        async def client_route(client_id: str, current_user: AuthenticatedUser):
            # Route logic
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find current_user in function signature
            current_user = None
            for arg in args:
                if isinstance(arg, (AuthenticatedUser, UserTokenClaims)):
                    current_user = arg
                    break

            # Check kwargs for current_user
            if not current_user:
                current_user = kwargs.get("current_user")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
                )

            # Extract client_id
            client_id = kwargs.get(client_id_param)
            if not client_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required parameter: {client_id_param}",
                )

            # Check client access
            RBACService.check_client_access(current_user, client_id)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# PERMISSION HELPERS FOR AGENTIC WORKFLOWS
# =============================================================================


class AgenticPermissions:
    """Permission helpers optimized for AI agent workflows."""

    @staticmethod
    def can_read_client_config(
        user: Union[AuthenticatedUser, UserTokenClaims], client_id: str
    ) -> bool:
        """Check if user can read client configuration."""
        return RBACService.check_permission(
            user, Permissions.CLIENT_READ, client_id, raise_on_deny=False
        )

    @staticmethod
    def can_modify_routing(user: Union[AuthenticatedUser, UserTokenClaims], client_id: str) -> bool:
        """Check if user can modify routing rules."""
        return RBACService.check_permission(
            user, Permissions.ROUTING_WRITE, client_id, raise_on_deny=False
        )

    @staticmethod
    def can_manage_ai_prompts(
        user: Union[AuthenticatedUser, UserTokenClaims], client_id: str
    ) -> bool:
        """Check if user can manage AI prompts."""
        return RBACService.check_permission(
            user, Permissions.AI_PROMPTS_WRITE, client_id, raise_on_deny=False
        )

    @staticmethod
    def is_super_admin(user: Union[AuthenticatedUser, UserTokenClaims]) -> bool:
        """Check if user is super admin."""
        role = user.role  # Already a string from auth_service for both types
        return role == "super_admin"

    @staticmethod
    def get_accessible_resources(
        user: Union[AuthenticatedUser, UserTokenClaims],
    ) -> Dict[str, List[str]]:
        """Get list of resources user can access (for agent planning)."""
        permissions = user.permissions
        resources = {}

        for permission in permissions:
            if ":" in permission:
                resource, action = permission.split(":", 1)
                if resource not in resources:
                    resources[resource] = []
                resources[resource].append(action)

        return resources
