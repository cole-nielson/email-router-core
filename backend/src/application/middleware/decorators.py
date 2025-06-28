"""
Authorization Decorators for Route Protection
🛡️ Simplified decorators for protecting routes with permissions and roles.
"""

import logging
from functools import wraps
from typing import Callable, List, Optional

from fastapi import HTTPException, status

from ..core.auth_context import SecurityContext
from .rbac import get_rbac_manager

logger = logging.getLogger(__name__)


def require_permission(permission: str, client_id_param: Optional[str] = None):
    """
    Decorator to require specific permission for route access.

    This decorator integrates with the unified security system and can be
    used on route functions that have SecurityContext as a parameter.

    Args:
        permission: Required permission (e.g., "routing:write")
        client_id_param: Parameter name containing client_id for scoping

    Usage:
        @require_permission("routing:write", "client_id")
        async def update_routing_rule(
            client_id: str,
            security_context: SecurityContext = Depends(require_auth)
        ):
            # Route logic here
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find SecurityContext in function arguments
            security_context = None

            # Check positional arguments
            for arg in args:
                if isinstance(arg, SecurityContext):
                    security_context = arg
                    break

            # Check keyword arguments
            if not security_context:
                for key, value in kwargs.items():
                    if isinstance(value, SecurityContext):
                        security_context = value
                        break

            if not security_context:
                logger.error(f"SecurityContext not found in {func.__name__} arguments")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication system error",
                )

            # Extract client_id if specified
            client_id = None
            if client_id_param:
                client_id = kwargs.get(client_id_param)

            # Check permission using RBAC manager
            rbac_manager = get_rbac_manager()
            rbac_manager.check_permission(security_context, permission, client_id)

            # Execute the route function
            return await func(*args, **kwargs)

        # Add metadata for introspection
        wrapper._required_permission = permission
        wrapper._client_id_param = client_id_param

        return wrapper

    return decorator


def require_role(*roles: str):
    """
    Decorator to require specific role(s) for route access.

    Args:
        *roles: Required roles (e.g., "super_admin", "client_admin")

    Usage:
        @require_role("super_admin", "client_admin")
        async def admin_only_route(
            security_context: SecurityContext = Depends(require_auth)
        ):
            # Route logic here
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find SecurityContext in function arguments
            security_context = None

            for arg in args:
                if isinstance(arg, SecurityContext):
                    security_context = arg
                    break

            if not security_context:
                for key, value in kwargs.items():
                    if isinstance(value, SecurityContext):
                        security_context = value
                        break

            if not security_context:
                logger.error(f"SecurityContext not found in {func.__name__} arguments")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication system error",
                )

            # Check role requirement using RBAC manager
            rbac_manager = get_rbac_manager()
            rbac_manager.check_role(security_context, list(roles))

            # Execute the route function
            return await func(*args, **kwargs)

        # Add metadata for introspection
        wrapper._required_roles = roles

        return wrapper

    return decorator


def require_client_access(client_id_param: str):
    """
    Decorator to require access to specific client.

    Args:
        client_id_param: Parameter name containing client_id

    Usage:
        @require_client_access("client_id")
        async def client_route(
            client_id: str,
            security_context: SecurityContext = Depends(require_auth)
        ):
            # Route logic here
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find SecurityContext in function arguments
            security_context = None

            for arg in args:
                if isinstance(arg, SecurityContext):
                    security_context = arg
                    break

            if not security_context:
                for key, value in kwargs.items():
                    if isinstance(value, SecurityContext):
                        security_context = value
                        break

            if not security_context:
                logger.error(f"SecurityContext not found in {func.__name__} arguments")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication system error",
                )

            # Extract client_id
            client_id = kwargs.get(client_id_param)
            if not client_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required parameter: {client_id_param}",
                )

            # Check client access using RBAC manager
            rbac_manager = get_rbac_manager()
            rbac_manager.check_client_access(security_context, client_id)

            # Execute the route function
            return await func(*args, **kwargs)

        # Add metadata for introspection
        wrapper._client_id_param = client_id_param

        return wrapper

    return decorator


def require_any_permission(*permissions: str, client_id_param: Optional[str] = None):
    """
    Decorator to require any one of multiple permissions.

    Args:
        *permissions: Required permissions (user needs at least one)
        client_id_param: Parameter name containing client_id for scoping

    Usage:
        @require_any_permission("routing:read", "routing:write", client_id_param="client_id")
        async def view_routing(
            client_id: str,
            security_context: SecurityContext = Depends(require_auth)
        ):
            # Route logic here
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find SecurityContext in function arguments
            security_context = None

            for arg in args:
                if isinstance(arg, SecurityContext):
                    security_context = arg
                    break

            if not security_context:
                for key, value in kwargs.items():
                    if isinstance(value, SecurityContext):
                        security_context = value
                        break

            if not security_context:
                logger.error(f"SecurityContext not found in {func.__name__} arguments")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication system error",
                )

            # Extract client_id if specified
            client_id = None
            if client_id_param:
                client_id = kwargs.get(client_id_param)

            # Check if user has any of the required permissions
            rbac_manager = get_rbac_manager()
            has_permission = False

            for permission in permissions:
                if rbac_manager.check_permission(
                    security_context, permission, client_id, raise_on_deny=False
                ):
                    has_permission = True
                    break

            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these permissions required: {', '.join(permissions)}",
                )

            # Execute the route function
            return await func(*args, **kwargs)

        # Add metadata for introspection
        wrapper._required_permissions = permissions
        wrapper._client_id_param = client_id_param

        return wrapper

    return decorator


def require_all_permissions(*permissions: str, client_id_param: Optional[str] = None):
    """
    Decorator to require all of multiple permissions.

    Args:
        *permissions: Required permissions (user needs all of them)
        client_id_param: Parameter name containing client_id for scoping

    Usage:
        @require_all_permissions("routing:read", "routing:write", client_id_param="client_id")
        async def manage_routing(
            client_id: str,
            security_context: SecurityContext = Depends(require_auth)
        ):
            # Route logic here
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find SecurityContext in function arguments
            security_context = None

            for arg in args:
                if isinstance(arg, SecurityContext):
                    security_context = arg
                    break

            if not security_context:
                for key, value in kwargs.items():
                    if isinstance(value, SecurityContext):
                        security_context = value
                        break

            if not security_context:
                logger.error(f"SecurityContext not found in {func.__name__} arguments")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication system error",
                )

            # Extract client_id if specified
            client_id = None
            if client_id_param:
                client_id = kwargs.get(client_id_param)

            # Check that user has all required permissions
            rbac_manager = get_rbac_manager()

            for permission in permissions:
                rbac_manager.check_permission(security_context, permission, client_id)

            # Execute the route function
            return await func(*args, **kwargs)

        # Add metadata for introspection
        wrapper._required_permissions = permissions
        wrapper._client_id_param = client_id_param

        return wrapper

    return decorator


# Utility functions for introspection
def get_route_permissions(route_func: Callable) -> List[str]:
    """
    Get permissions required by a route function.

    Args:
        route_func: Route function to inspect

    Returns:
        List of required permissions
    """
    permissions = []

    if hasattr(route_func, "_required_permission"):
        permissions.append(route_func._required_permission)

    if hasattr(route_func, "_required_permissions"):
        permissions.extend(route_func._required_permissions)

    return permissions


def get_route_roles(route_func: Callable) -> List[str]:
    """
    Get roles required by a route function.

    Args:
        route_func: Route function to inspect

    Returns:
        List of required roles
    """
    if hasattr(route_func, "_required_roles"):
        return list(route_func._required_roles)

    return []


def get_route_security_info(route_func: Callable) -> dict:
    """
    Get comprehensive security information for a route.

    Args:
        route_func: Route function to inspect

    Returns:
        Dictionary with security requirements
    """
    return {
        "permissions": get_route_permissions(route_func),
        "roles": get_route_roles(route_func),
        "client_id_param": getattr(route_func, "_client_id_param", None),
        "requires_auth": bool(
            get_route_permissions(route_func)
            or get_route_roles(route_func)
            or hasattr(route_func, "_client_id_param")
        ),
    }
