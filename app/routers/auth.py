"""
Authentication API Router for multi-tenant email router.
🔐 User login, logout, registration, and token management endpoints.
"""

import logging
from typing import Annotated, List, Optional
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr

from ..database.connection import get_db
from ..middleware.jwt_auth import require_authenticated_user
from ..services.auth_service import (
    AuthenticatedUser,
    LoginRequest,
    TokenResponse,
    get_auth_service,
)
from ..services.rbac import RBACService

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


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, req: Request, db: Session = Depends(get_db)):
    """User login with JWT token generation."""
    try:
        # Get client metadata
        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get("User-Agent")

        # Get auth service
        auth_service = get_auth_service(db)
        if not auth_service:
            raise HTTPException(status_code=500, detail="Could not initialize authentication service.")

        # Perform login
        token_response = auth_service.login(request, ip_address, user_agent)

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
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    try:
        auth_service = get_auth_service(db)
        if not auth_service:
            raise HTTPException(status_code=500, detail="Could not initialize authentication service.")

        token_response = auth_service.refresh_access_token(request.refresh_token)
        if not token_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
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
    current_user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
    db: Session = Depends(get_db)
):
    """Logout user by revoking current token."""
    try:
        auth_service = get_auth_service(db)
        if not auth_service:
            raise HTTPException(status_code=500, detail="Could not initialize authentication service.")

        # Extract token from request (this would need to be improved)
        # For now, we'll revoke all user tokens as a secure logout
        revoked_count = auth_service.revoke_all_user_tokens(current_user.id, "user_logout")

        logger.info(f"User '{current_user.username}' logged out, {revoked_count} tokens revoked")

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
    current_user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
    db: Session = Depends(get_db)
):
    """Register a new user (admin only)."""
    try:
        # Check permissions - only super admin can create users
        RBACService.check_permission(current_user, "users:write")

        auth_service = get_auth_service(db)
        if not auth_service:
            raise HTTPException(status_code=500, detail="Could not initialize authentication service.")

        # Import User model dynamically
        from ..database.models import User, UserRole, UserStatus

        # Check if user already exists
        existing_user = (
            db.query(User)
            .filter((User.username == request.username) | (User.email == request.email))
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this username or email already exists",
            )

        # Validate role
        try:
            role_enum = UserRole(request.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role: {request.role}"
            )

        # Create user
        hashed_password = auth_service.hash_password(request.password)

        user = User(
            username=request.username,
            email=request.email,
            password_hash=hashed_password,
            full_name=request.full_name,
            role=role_enum,
            client_id=request.client_id,
            status=UserStatus.ACTIVE,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"User '{request.username}' registered by admin '{current_user.username}'")

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            client_id=user.client_id,
            status=user.status.value,
            created_at=user.created_at.isoformat(),
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
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
    current_user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
    db: Session = Depends(get_db)
):
    """Get current user information."""
    try:

        # Import User model dynamically
        from ..database.models import User

        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            client_id=user.client_id,
            status=user.status.value,
            created_at=user.created_at.isoformat(),
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        )


@router.put("/me/password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
    db: Session = Depends(get_db)
):
    """Change current user password."""
    try:
        auth_service = get_auth_service(db)
        if not auth_service:
            raise HTTPException(status_code=500, detail="Could not initialize authentication service.")

        # Import User model dynamically
        from ..database.models import User

        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Verify current password
        if not auth_service.verify_password(request.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect"
            )

        # Update password
        user.password_hash = auth_service.hash_password(request.new_password)

        # Revoke all existing tokens for security
        auth_service.revoke_all_user_tokens(user.id, "password_change")

        db.commit()

        logger.info(f"Password changed for user '{current_user.username}'")

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


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
    client_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List users (admin only)."""
    try:
        # Check permissions
        RBACService.check_permission(current_user, "users:read")

        # Import User model dynamically
        from ..database.models import User

        query = db.query(User)

        # Filter by client if specified and user is not super admin
        if current_user.role != "super_admin":
            query = query.filter(User.client_id == current_user.client_id)
        elif client_id:
            query = query.filter(User.client_id == client_id)

        users = query.offset(offset).limit(limit).all()

        return [
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                client_id=user.client_id,
                status=user.status.value,
                created_at=user.created_at.isoformat(),
                last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
            )
            for user in users
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int, 
    current_user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
    db: Session = Depends(get_db)
):
    """Delete user (super admin only)."""
    try:
        # Check permissions - only super admin can delete users
        RBACService.check_permission(current_user, "users:delete")

        if current_user.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only super admin can delete users"
            )

        # Prevent self-deletion
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account"
            )

        auth_service = get_auth_service(db)
        if not auth_service:
            raise HTTPException(status_code=500, detail="Could not initialize authentication service.")

        # Import User model dynamically
        from ..database.models import User

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Revoke all user tokens
        auth_service.revoke_all_user_tokens(user_id, "account_deleted")

        # Delete user
        db.delete(user)
        db.commit()

        logger.info(f"User '{user.username}' deleted by super admin '{current_user.username}'")

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
    current_user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
    db: Session = Depends(get_db)
):
    """List active sessions for current user."""
    try:

        # Import models dynamically
        from ..database.models import UserSession

        sessions = (
            db.query(UserSession)
            .filter(UserSession.user_id == current_user.id, UserSession.is_active)
            .order_by(UserSession.created_at.desc())
            .all()
        )

        return {
            "sessions": [
                {
                    "session_id": session.session_id,
                    "token_type": session.token_type,
                    "created_at": session.created_at.isoformat(),
                    "last_used_at": (
                        session.last_used_at.isoformat() if session.last_used_at else None
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        )


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str, 
    current_user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
    db: Session = Depends(get_db)
):
    """Revoke a specific session."""
    try:
        auth_service = get_auth_service(db)
        if not auth_service:
            raise HTTPException(status_code=500, detail="Could not initialize authentication service.")

        # Import models dynamically
        from ..database.models import UserSession

        # Verify session belongs to current user
        session = (
            db.query(UserSession)
            .filter(UserSession.session_id == session_id, UserSession.user_id == current_user.id)
            .first()
        )

        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        # Revoke session
        success = auth_service.revoke_token(session_id, "user_revoked")
        if success:
            return {"message": "Session revoked successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to revoke session"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        )
