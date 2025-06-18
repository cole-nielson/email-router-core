"""
JWT Authentication Middleware for multi-tenant email router.
🔐 Bearer token validation with client scoping and RBAC integration.
"""

import logging
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..services.auth_service import AuthenticatedUser

logger = logging.getLogger(__name__)

# =============================================================================
# JWT AUTHENTICATION DEPENDENCIES
# =============================================================================

# Security scheme for Swagger documentation
jwt_bearer = HTTPBearer(scheme_name="JWT Bearer", description="JWT token for authentication")


class JWTAuthMiddleware:
    """JWT Authentication middleware with request context."""

    def __init__(self):
        self.auth_service = None

    async def __call__(self, request: Request, call_next):
        """Process request with JWT authentication context."""
        # Skip authentication for public endpoints
        if self._is_public_endpoint(request.url.path):
            response = await call_next(request)
            return response

        # Extract and validate JWT token
        db = None
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1]

                # Initialize auth service if needed
                if not self.auth_service:
                    from ..database.connection import get_database_session
                    from ..services.auth_service import get_auth_service

                    db = get_database_session()
                    self.auth_service = get_auth_service(db)

                # Validate token and get user
                user = self.auth_service.get_current_user(token)
                if user:
                    # Add user to request state for route access
                    request.state.current_user = user
                    request.state.auth_token = token

                    # Log authentication success
                    logger.debug(f"Authenticated user: {user.username} (role: {user.role})")

        except Exception as e:
            logger.warning(f"JWT authentication error: {e}")
        finally:
            if db:
                db.close()

        response = await call_next(request)
        return response

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (no authentication required)."""
        public_paths = [
            "/",
            "/health",
            "/health/detailed",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/refresh",
            "/webhooks/mailgun/inbound",  # Mailgun webhooks use signature auth
            "/webhooks/test",
        ]

        return any(path.startswith(public_path) for public_path in public_paths)


# =============================================================================
# DEPENDENCY INJECTION FUNCTIONS
# =============================================================================


async def get_jwt_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_bearer)],
) -> str:
    """Extract JWT token from Authorization header."""
    return credentials.credentials


async def _get_user_from_token_logic(token: str, db: Session) -> Optional[AuthenticatedUser]:
    """Logic to get user from token, callable from other modules."""
    # Import auth service here to avoid circular imports
    from ..services.auth_service import get_auth_service

    auth_service = get_auth_service(db)
    return auth_service.get_current_user(token)


async def get_current_user_from_token(
    token: Annotated[str, Depends(get_jwt_token)],
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    """Get current authenticated user from JWT token."""
    user = await _get_user_from_token_logic(token, db)

    if not user:
        logger.warning("Invalid or expired JWT token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_optional(
    request: Request, db: Session = Depends(get_db)
) -> Optional[AuthenticatedUser]:
    """Get current user if authenticated, None otherwise."""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1]
        user = await _get_user_from_token_logic(token, db)
        return user

    except Exception as e:
        logger.debug(f"Optional authentication failed: {e}")
        return None


async def get_current_user_from_request(request: Request) -> Optional[AuthenticatedUser]:
    """Get current user from request state (set by middleware)."""
    return getattr(request.state, "current_user", None)


# =============================================================================
# ROLE-BASED DEPENDENCIES
# =============================================================================


async def require_super_admin(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user_from_token)],
) -> AuthenticatedUser:
    """Dependency that requires super admin role."""
    if current_user.role.value != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required"
        )
    return current_user


async def require_client_admin_or_super(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user_from_token)],
) -> AuthenticatedUser:
    """Dependency that requires client admin or super admin role."""
    if current_user.role.value not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


async def require_authenticated_user(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user_from_token)],
) -> AuthenticatedUser:
    """Dependency that requires any authenticated user."""
    return current_user


# =============================================================================
# CLIENT SCOPING DEPENDENCIES
# =============================================================================


def require_client_access(client_id_param: str = "client_id"):
    """
    Factory function for client-scoped access dependency.

    Args:
        client_id_param: Name of the path parameter containing client_id

    Returns:
        Dependency function that validates client access
    """

    async def validate_client_access(
        current_user: Annotated[AuthenticatedUser, Depends(get_current_user_from_token)],
        request: Request,
    ) -> AuthenticatedUser:
        """Validate user has access to requested client."""
        # Extract client_id from path parameters
        client_id = request.path_params.get(client_id_param)

        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Missing client ID in path"
            )

        # Super admin has access to all clients
        if current_user.role.value == "super_admin":
            return current_user

        # Check client scoping for other roles
        if current_user.client_id != client_id:
            logger.warning(
                f"User {current_user.username} denied access to client {client_id} "
                f"(user client: {current_user.client_id})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Access denied to client {client_id}"
            )

        return current_user

    return validate_client_access


# =============================================================================
# PERMISSION-BASED DEPENDENCIES
# =============================================================================


def require_permission(permission: str, client_id_param: str = "client_id"):
    """
    Factory function for permission-based access dependency.

    Args:
        permission: Required permission (e.g., "routing:write")
        client_id_param: Name of path parameter containing client_id

    Returns:
        Dependency function that validates permission
    """

    async def validate_permission(
        current_user: Annotated[AuthenticatedUser, Depends(get_current_user_from_token)],
        request: Request,
    ) -> AuthenticatedUser:
        """Validate user has required permission."""
        from ..services.rbac import RBACService

        # Extract client_id from path parameters if needed
        client_id = request.path_params.get(client_id_param) if client_id_param else None

        # Check permission
        RBACService.check_permission(current_user, permission, client_id)

        return current_user

    return validate_permission


# =============================================================================
# RATE LIMITING DEPENDENCIES
# =============================================================================


async def get_rate_limit_tier(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user_from_token)],
) -> str:
    """Get user's rate limit tier for agentic workflow management."""
    return current_user.rate_limit_tier


async def check_api_access_enabled(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user_from_token)],
) -> AuthenticatedUser:
    """Check if user has API access enabled (for agent workflows)."""
    # This would be expanded to check user.api_access_enabled from database
    # For now, all authenticated users have API access
    return current_user


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def extract_client_id_from_request(
    request: Request, param_name: str = "client_id"
) -> Optional[str]:
    """Extract client ID from request path parameters."""
    return request.path_params.get(param_name)


def get_request_metadata(request: Request) -> dict:
    """Extract request metadata for audit logging."""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("User-Agent"),
        "method": request.method,
        "path": str(request.url.path),
        "query_params": dict(request.query_params),
    }
