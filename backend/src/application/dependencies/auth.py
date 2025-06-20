"""
FastAPI Authentication Dependencies for Unified Security
🔐 Simplified dependency injection for routes using unified security context.
"""

import logging
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status

from ...core.authentication.context import AuthenticationType, SecurityContext

logger = logging.getLogger(__name__)


# =============================================================================
# CORE DEPENDENCIES
# =============================================================================


async def get_security_context(request: Request) -> SecurityContext:
    """
    Get security context from request state.

    This is the primary dependency for accessing authentication state
    in route handlers. It provides access to the unified security context
    created by the UnifiedAuthMiddleware.

    Args:
        request: FastAPI request object

    Returns:
        SecurityContext from request state
    """
    security_context = getattr(request.state, "security_context", None)

    if security_context is None:
        # This should not happen if middleware is properly configured
        logger.error("Security context not found in request state")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication system error"
        )

    return security_context


async def get_current_user(
    security_context: Annotated[SecurityContext, Depends(get_security_context)],
) -> SecurityContext:
    """
    Get current authenticated user from security context.

    This dependency provides backward compatibility with existing code
    that expects user information from dependencies.

    Args:
        security_context: Security context from middleware

    Returns:
        SecurityContext (authenticated or raises exception)

    Raises:
        HTTPException: If user is not authenticated
    """
    if not security_context.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return security_context


# =============================================================================
# AUTHENTICATION METHOD DEPENDENCIES
# =============================================================================


async def require_auth(
    security_context: Annotated[SecurityContext, Depends(get_security_context)],
) -> SecurityContext:
    """
    Require any form of authentication (JWT or API key).

    This is the primary authentication dependency that accepts both
    JWT and API key authentication methods.

    Args:
        security_context: Security context from middleware

    Returns:
        Authenticated SecurityContext

    Raises:
        HTTPException: If not authenticated
    """
    if not security_context.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide either JWT Bearer token or API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return security_context


async def require_jwt_only(
    security_context: Annotated[SecurityContext, Depends(get_security_context)],
) -> SecurityContext:
    """
    Require JWT authentication only (no API keys).

    Use this dependency for endpoints that need human user authentication,
    such as configuration management and administrative functions.

    Args:
        security_context: Security context from middleware

    Returns:
        JWT-authenticated SecurityContext

    Raises:
        HTTPException: If not authenticated with JWT
    """
    if not security_context.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if security_context.auth_type != AuthenticationType.JWT:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT authentication required for this endpoint",
        )

    return security_context


async def require_api_key_only(
    security_context: Annotated[SecurityContext, Depends(get_security_context)],
) -> SecurityContext:
    """
    Require API key authentication only (no JWTs).

    Use this dependency for endpoints that are designed for automated
    systems and don't need human user authentication.

    Args:
        security_context: Security context from middleware

    Returns:
        API key authenticated SecurityContext

    Raises:
        HTTPException: If not authenticated with API key
    """
    if not security_context.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key authentication required",
        )

    if security_context.auth_type != AuthenticationType.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key authentication required for this endpoint",
        )

    return security_context


# =============================================================================
# ROLE-BASED DEPENDENCIES
# =============================================================================


async def require_super_admin(
    security_context: Annotated[SecurityContext, Depends(require_auth)],
) -> SecurityContext:
    """
    Require super admin role.

    Args:
        security_context: Authenticated security context

    Returns:
        Super admin SecurityContext

    Raises:
        HTTPException: If not super admin
    """
    if not security_context.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required"
        )

    return security_context


async def require_admin(
    security_context: Annotated[SecurityContext, Depends(require_auth)],
) -> SecurityContext:
    """
    Require admin role (client admin or super admin).

    Args:
        security_context: Authenticated security context

    Returns:
        Admin SecurityContext

    Raises:
        HTTPException: If not admin
    """
    admin_roles = ["super_admin", "client_admin"]

    if not security_context.has_role(admin_roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    return security_context


async def require_human_user(
    security_context: Annotated[SecurityContext, Depends(require_jwt_only)],
) -> SecurityContext:
    """
    Require human user with admin privileges (JWT only).

    This combines JWT-only authentication with admin role requirement,
    ensuring only human administrators can access sensitive endpoints.

    Args:
        security_context: JWT-authenticated security context

    Returns:
        Human admin SecurityContext

    Raises:
        HTTPException: If not human admin
    """
    admin_roles = ["super_admin", "client_admin"]

    if not security_context.has_role(admin_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Human admin access required"
        )

    return security_context


# =============================================================================
# CLIENT ACCESS DEPENDENCIES
# =============================================================================


def require_client_access(client_id_param: str = "client_id"):
    """
    Factory function for client-scoped access dependency.

    This creates a dependency that validates the user has access
    to a specific client based on a path parameter.

    Args:
        client_id_param: Name of the path parameter containing client_id

    Returns:
        Dependency function that validates client access
    """

    async def validate_client_access(
        security_context: Annotated[SecurityContext, Depends(require_auth)],
        request: Request,
    ) -> SecurityContext:
        """
        Validate user has access to requested client.

        Args:
            security_context: Authenticated security context
            request: FastAPI request object

        Returns:
            SecurityContext with validated client access

        Raises:
            HTTPException: If client access is denied
        """
        # Extract client_id from path parameters
        client_id = request.path_params.get(client_id_param)

        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing {client_id_param} in path"
            )

        # Check client access
        if not security_context.has_client_access(client_id):
            logger.warning(
                f"User {security_context.username} denied access to client {client_id} "
                f"(user client: {security_context.client_id})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Access denied to client {client_id}"
            )

        return security_context

    return validate_client_access


# =============================================================================
# PERMISSION-BASED DEPENDENCIES
# =============================================================================


def require_permission(permission: str, client_id_param: str = "client_id"):
    """
    Factory function for permission-based access dependency.

    This creates a dependency that validates the user has a specific
    permission, optionally scoped to a client.

    Args:
        permission: Required permission (e.g., "routing:write")
        client_id_param: Name of path parameter containing client_id (optional)

    Returns:
        Dependency function that validates permission
    """

    async def validate_permission(
        security_context: Annotated[SecurityContext, Depends(require_auth)],
        request: Request,
    ) -> SecurityContext:
        """
        Validate user has required permission.

        Args:
            security_context: Authenticated security context
            request: FastAPI request object

        Returns:
            SecurityContext with validated permission

        Raises:
            HTTPException: If permission is denied
        """
        # Extract client_id from path parameters if specified
        client_id = None
        if client_id_param:
            client_id = request.path_params.get(client_id_param)

        # Check permission
        if not security_context.has_permission(permission, client_id):
            logger.warning(
                f"Permission denied: {permission} for user {security_context.username} "
                f"(role: {security_context.role}, client: {security_context.client_id})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission denied: {permission}"
            )

        return security_context

    return validate_permission


# =============================================================================
# OPTIONAL DEPENDENCIES
# =============================================================================


async def get_current_user_optional(
    security_context: Annotated[SecurityContext, Depends(get_security_context)],
) -> Optional[SecurityContext]:
    """
    Get current user if authenticated, None if not.

    This dependency allows endpoints to optionally check for authentication
    without requiring it.

    Args:
        security_context: Security context from middleware

    Returns:
        SecurityContext if authenticated, None otherwise
    """
    return security_context if security_context.is_authenticated else None
