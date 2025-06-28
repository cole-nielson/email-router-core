"""
Authentication API Router for multi-tenant email router.
🔐 User login, logout, registration, and token management endpoints.
"""

import logging
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from api.v1.dependencies import (
    PaginationParams,
    UserFilterParams,
    user_filter_parameters,
    user_pagination_parameters,
)
from application.dependencies.auth import require_auth
from application.dependencies.repositories import get_auth_service, get_user_repository
from core.authentication.auth_service import AuthService
from core.authentication.context import SecurityContext
from core.models.schemas import (
    CreateUserRequest,
    LoginRequest,
    TokenResponse,
)
from core.ports.user_repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security scheme for Swagger docs
bearer_scheme = HTTPBearer()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class UserRegistrationRequest(BaseModel):
    """Request model for user registration."""

    username: str
    email: EmailStr
    password: str
    full_name: str
    client_id: Optional[str] = None
    role: str = "client_user"


class UserResponse(BaseModel):
    """Response model for user information."""

    id: int
    username: str
    email: str
    full_name: str
    role: str
    client_id: Optional[str]
    status: str
    created_at: str
    last_login_at: Optional[str]


class PasswordChangeRequest(BaseModel):
    """Request model for password change."""

    current_password: str
    new_password: str


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Request model for logout."""

    token: str


class PaginationMetadata(BaseModel):
    """Metadata for paginated responses."""

    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Maximum items per page")
    offset: int = Field(..., description="Number of items skipped")
    has_more: bool = Field(..., description="Whether there are more items")


class UserListResponse(BaseModel):
    """Response model for paginated user list."""

    users: List[UserResponse] = Field(..., description="List of users")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    req: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """User login with JWT token generation."""
    try:
        # Get client metadata
        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get("User-Agent")

        # Perform login
        token_response = await auth_service.login(request, ip_address, user_agent)

        logger.info(f"User '{request.username}' logged in successfully")
        return token_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Refresh access token using refresh token."""
    try:
        token_response = await auth_service.refresh_access_token(request.refresh_token)
        if not token_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        return token_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh",
        )


@router.post("/logout")
async def logout(
    security_context: Annotated[SecurityContext, Depends(require_auth)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Logout user by revoking current token."""
    try:
        # Extract token from request (this would need to be improved)
        # For now, we'll revoke all user tokens as a secure logout
        revoked_count = await auth_service.revoke_all_user_tokens(
            int(security_context.user_id), "user_logout"
        )

        logger.info(
            f"User '{security_context.username}' logged out, {revoked_count} tokens revoked"
        )

        return {"message": "Logged out successfully", "tokens_revoked": revoked_count}

    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout",
        )


# =============================================================================
# USER MANAGEMENT ENDPOINTS
# =============================================================================


@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(
    request: UserRegistrationRequest,
    security_context: Annotated[SecurityContext, Depends(require_auth)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Register a new user (admin only)."""
    try:
        # Check permissions - only super admin can create users
        if not security_context.has_permission("users:write"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: users:write",
            )

        # Create user data with hashed password
        hashed_password = auth_service.hash_password(request.password)

        user_data = CreateUserRequest(
            username=request.username,
            email=request.email,
            password=hashed_password,  # Already hashed
            full_name=request.full_name,
            role=request.role,
            client_id=request.client_id,
            status="active",  # Set to active for admin-created users
            api_access_enabled=True,
            rate_limit_tier="standard",
        )

        # Create user through repository
        from infrastructure.adapters.user_repository_impl import ConflictError

        try:
            user = await user_repository.create_user(user_data)
        except ConflictError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

        logger.info(
            f"User '{request.username}' registered by admin '{security_context.username}'"
        )

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            client_id=user.client_id,
            status=user.status,
            created_at=user.created_at.isoformat(),
            last_login_at=(
                user.last_login_at.isoformat() if user.last_login_at else None
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during user registration",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    security_context: Annotated[SecurityContext, Depends(require_auth)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
):
    """Get current user information."""
    try:
        user = await user_repository.find_by_id(int(security_context.user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            client_id=user.client_id,
            status=user.status,
            created_at=user.created_at.isoformat(),
            last_login_at=(
                user.last_login_at.isoformat() if user.last_login_at else None
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put("/me/password")
async def change_password(
    request: PasswordChangeRequest,
    security_context: Annotated[SecurityContext, Depends(require_auth)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Change current user password."""
    try:
        user = await user_repository.find_by_id(int(security_context.user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Verify current password
        if not auth_service.verify_password(
            request.current_password, user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        # Update password
        new_password_hash = auth_service.hash_password(request.new_password)
        await user_repository.update_password(user.id, new_password_hash)

        # Revoke all existing tokens for security
        await auth_service.revoke_all_user_tokens(user.id, "password_change")

        logger.info(f"Password changed for user '{security_context.username}'")

        return {"message": "Password changed successfully. Please log in again."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during password change",
        )


# =============================================================================
# ADMIN USER MANAGEMENT
# =============================================================================


@router.get("/users", response_model=UserListResponse)
async def list_users(
    security_context: Annotated[SecurityContext, Depends(require_auth)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    pagination: Annotated[PaginationParams, Depends(user_pagination_parameters)],
    filters: Annotated[UserFilterParams, Depends(user_filter_parameters)],
):
    """
    List users with pagination, sorting, and filtering (admin only).

    Supports:
    - Pagination: offset, limit
    - Sorting: sort_by (username, email, created_at, etc.), sort_order (asc/desc)
    - Filtering: search (username/email/name), role, status, client_id
    - Access control: Only returns users the authenticated user has permission to see
    """
    try:
        # Check permissions
        if not security_context.has_permission("users:read"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: users:read",
            )

        # Determine client filter based on user permissions
        filter_client_id = filters.client_id
        if not security_context.is_super_admin:
            # Non-super admins can only see users from their own client
            filter_client_id = security_context.client_id

        # Get paginated users
        users, total_count = await user_repository.list_users(
            limit=pagination.limit,
            offset=pagination.offset,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order,
            search=filters.search,
            client_id=filter_client_id,
            role=filters.role,
            status=filters.status,
        )

        # Convert to response models
        user_responses = [
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                client_id=user.client_id,
                status=user.status,
                created_at=user.created_at.isoformat(),
                last_login_at=(
                    user.last_login_at.isoformat() if user.last_login_at else None
                ),
            )
            for user in users
        ]

        # Create pagination metadata
        pagination_metadata = PaginationMetadata(
            total=total_count,
            limit=pagination.limit,
            offset=pagination.offset,
            has_more=(pagination.offset + len(users)) < total_count,
        )

        return UserListResponse(
            users=user_responses,
            pagination=pagination_metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    security_context: Annotated[SecurityContext, Depends(require_auth)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Delete user (super admin only)."""
    try:
        # Check permissions - only super admin can delete users
        if not security_context.has_permission("users:delete"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: users:delete",
            )

        if not security_context.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admin can delete users",
            )

        # Prevent self-deletion
        if user_id == int(security_context.user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account",
            )

        user = await user_repository.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Revoke all user tokens
        await auth_service.revoke_all_user_tokens(user_id, "account_deleted")

        # Delete user
        deleted = await user_repository.delete_user(user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        logger.info(
            f"User '{user.username}' deleted by super admin '{security_context.username}'"
        )

        return {"message": f"User '{user.username}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during user deletion",
        )


# =============================================================================
# TOKEN MANAGEMENT
# =============================================================================


@router.get("/sessions")
async def list_active_sessions(
    security_context: Annotated[SecurityContext, Depends(require_auth)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
):
    """List active sessions for current user."""
    try:
        sessions = await user_repository.list_user_sessions(
            int(security_context.user_id), active_only=True
        )

        return {
            "sessions": [
                {
                    "session_id": session.session_id,
                    "token_type": session.token_type,
                    "issued_at": session.issued_at.isoformat(),
                    "last_used_at": (
                        session.last_used_at.isoformat()
                        if session.last_used_at
                        else None
                    ),
                    "expires_at": session.expires_at.isoformat(),
                    "ip_address": session.ip_address,
                    "user_agent": session.user_agent,
                }
                for session in sessions
            ]
        }

    except Exception as e:
        logger.error(f"List sessions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    security_context: Annotated[SecurityContext, Depends(require_auth)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Revoke a specific session."""
    try:
        # Verify session belongs to current user
        session = await user_repository.find_session(session_id)
        if not session or session.user_id != int(security_context.user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )

        # Revoke session
        success = await auth_service.revoke_token(session_id, "user_revoked")
        if success:
            return {"message": "Session revoked successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke session",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
