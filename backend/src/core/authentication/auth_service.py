"""
Clean Architecture Authentication Service
🔐 Domain service for authentication operations using repository pattern.

This service contains the core authentication business logic while depending
only on repository interfaces, making it database-agnostic.
"""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Union

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext

from core.models.schemas import (
    AuthenticatedUser,
    LoginRequest,
    RefreshTokenClaims,
    TokenResponse,
    UserTokenClaims,
    UserWithPermissions,
)
from core.ports.user_repository import UserRepository

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================

# Get unified configuration
try:
    from core import get_app_config

    _app_config = get_app_config()

    # JWT Configuration from unified config
    JWT_SECRET_KEY = _app_config.security.jwt_secret_key
    JWT_ALGORITHM = _app_config.security.jwt_algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES = _app_config.security.access_token_expire_minutes
    REFRESH_TOKEN_EXPIRE_DAYS = _app_config.security.refresh_token_expire_days

    # Rate limiting from unified config
    MAX_LOGIN_ATTEMPTS = _app_config.security.max_login_attempts
    LOCKOUT_DURATION_MINUTES = _app_config.security.lockout_duration_minutes
except Exception:
    # Fallback to environment variables if unified config fails
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 30
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Domain service for authentication operations.

    This service contains the core authentication business logic while depending
    only on repository interfaces, making it database-agnostic and testable.
    """

    def __init__(self, user_repository: UserRepository):
        """
        Initialize the authentication service.

        Args:
            user_repository: Repository for user data operations
        """
        self.user_repository = user_repository

    # =========================================================================
    # PASSWORD MANAGEMENT
    # =========================================================================

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    # =========================================================================
    # USER AUTHENTICATION
    # =========================================================================

    async def authenticate_user(
        self, username: str, password: str, client_id: Optional[str] = None
    ) -> Optional[UserWithPermissions]:
        """
        Authenticate user credentials and check account status.

        Args:
            username: Username to authenticate
            password: Plain text password
            client_id: Optional client context

        Returns:
            Authenticated user if successful, None otherwise

        Raises:
            HTTPException: For account lockout or status issues
        """
        try:
            # Find user by username
            user = await self.user_repository.find_by_username(username)
            if not user:
                logger.warning(f"Authentication failed: user '{username}' not found")
                return None

            # Check if account is locked
            if user.locked_until and user.locked_until > datetime.utcnow():
                logger.warning(
                    f"Authentication failed: account '{username}' is locked until {user.locked_until}"
                )
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"Account locked until {user.locked_until.isoformat()}",
                )

            # Check account status
            if user.status != "active":
                logger.warning(
                    f"Authentication failed: account '{username}' is {user.status}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Account is {user.status}",
                )

            # Verify password
            if not self.verify_password(password, user.password_hash):
                # Track failed login attempt
                await self.user_repository.update_login_attempt(username, success=False)

                # Check if we should lock the account
                if user.login_attempts + 1 >= MAX_LOGIN_ATTEMPTS:
                    lock_until = datetime.utcnow() + timedelta(
                        minutes=LOCKOUT_DURATION_MINUTES
                    )
                    await self.user_repository.lock_user_account(
                        user.id, lock_until, "Too many failed login attempts"
                    )
                    logger.warning(
                        f"Account '{username}' locked due to {MAX_LOGIN_ATTEMPTS} failed attempts"
                    )

                logger.warning(
                    f"Authentication failed: invalid password for user '{username}'"
                )
                return None

            # Check client scope for non-super-admin users
            if user.role != "super_admin" and client_id:
                if user.client_id != client_id:
                    logger.warning(
                        f"Authentication failed: user '{username}' not authorized for client '{client_id}'"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="User not authorized for this client",
                    )

            # Successful authentication - reset login attempts
            await self.user_repository.update_login_attempt(username, success=True)

            logger.info(f"User '{username}' authenticated successfully")
            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error for user '{username}': {e}")
            return None

    # =========================================================================
    # JWT TOKEN MANAGEMENT
    # =========================================================================

    async def create_access_token(
        self, user: UserWithPermissions, permissions: List[str] = None
    ) -> dict:
        """
        Create JWT access token with user claims.

        Args:
            user: Authenticated user
            permissions: Optional custom permissions list

        Returns:
            Dictionary containing token, claims, and expiry information
        """
        now = datetime.utcnow()
        exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        jti = secrets.token_urlsafe(32)

        # Get user permissions if not provided
        if permissions is None:
            permissions = await self._get_user_permissions(user)

        # Build token claims
        claims = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "client_id": user.client_id,
            "permissions": permissions,
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "token_type": "access",
        }

        # Create JWT token
        token = jwt.encode(claims, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        # Store session for tracking
        await self.user_repository.create_user_session(
            user_id=user.id, session_id=jti, token_type="access", expires_at=exp
        )

        return {"token": token, "claims": claims, "expires_at": exp}

    async def create_refresh_token(self, user: UserWithPermissions) -> dict:
        """
        Create JWT refresh token for long-term sessions.

        Args:
            user: Authenticated user

        Returns:
            Dictionary containing token, claims, and expiry information
        """
        now = datetime.utcnow()
        exp = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        jti = secrets.token_urlsafe(32)

        claims = {
            "sub": str(user.id),
            "username": user.username,
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "token_type": "refresh",
        }

        token = jwt.encode(claims, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        # Store refresh token hash for revocation
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        await self.user_repository.update_refresh_token_hash(user.id, token_hash)

        # Store session
        await self.user_repository.create_user_session(
            user_id=user.id, session_id=jti, token_type="refresh", expires_at=exp
        )

        return {"token": token, "claims": claims, "expires_at": exp}

    @staticmethod
    def validate_token_stateless(
        token: str, token_type: str = "access"
    ) -> Optional[Union[UserTokenClaims, RefreshTokenClaims]]:
        """
        Validate JWT token signature and expiration without database access.

        Args:
            token: JWT token to validate
            token_type: Expected token type

        Returns:
            Token claims if valid, None otherwise
        """
        try:
            # Decode token with signature and expiration validation
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

            # Use appropriate claims model based on token type
            if token_type == "refresh":
                claims = RefreshTokenClaims(**payload)
            else:
                claims = UserTokenClaims(**payload)

            # Check token type
            if claims.token_type != token_type:
                logger.warning(
                    f"Invalid token type: expected {token_type}, got {claims.token_type}"
                )
                return None

            return claims

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None

    async def validate_token(
        self, token: str, token_type: str = "access"
    ) -> Optional[Union[UserTokenClaims, RefreshTokenClaims]]:
        """
        Validate JWT token and return claims with database session check.

        Args:
            token: JWT token to validate
            token_type: Expected token type

        Returns:
            Token claims if valid and session active, None otherwise
        """
        try:
            # First do stateless validation
            claims = self.validate_token_stateless(token, token_type)
            if not claims:
                return None

            # Check if session is still active
            session = await self.user_repository.find_session(claims.jti)
            if not session or not session.is_active:
                logger.warning(f"Token session not found or inactive: {claims.jti}")
                return None

            # Update last used time
            await self.user_repository.update_session_activity(claims.jti)

            return claims

        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT validation error: {e}")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None

    async def refresh_access_token(self, refresh_token: str) -> Optional[TokenResponse]:
        """
        Generate new access token from valid refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New token response if successful, None otherwise
        """
        claims = await self.validate_token(refresh_token, "refresh")
        if not claims:
            return None

        # Get user
        user = await self.user_repository.find_by_id(int(claims.sub))
        if not user or user.status != "active":
            return None

        # Verify refresh token hash
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        if user.jwt_refresh_token_hash != token_hash:
            logger.warning(f"Refresh token hash mismatch for user {user.username}")
            return None

        # Create new access token
        access_result = await self.create_access_token(user)

        return TokenResponse(
            access_token=access_result["token"],
            refresh_token=refresh_token,  # Keep existing refresh token
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            client_id=user.client_id,
            role=user.role,
            permissions=await self._get_user_permissions(user),
        )

    async def revoke_token(self, jti: str, reason: str = "user_logout") -> bool:
        """
        Revoke a specific token session.

        Args:
            jti: JWT ID to revoke
            reason: Reason for revocation

        Returns:
            True if session was revoked, False if not found
        """
        return await self.user_repository.revoke_session(jti, reason)

    async def revoke_all_user_tokens(
        self, user_id: int, reason: str = "security_action"
    ) -> int:
        """
        Revoke all active tokens for a user.

        Args:
            user_id: User ID
            reason: Reason for revocation

        Returns:
            Number of sessions revoked
        """
        count = await self.user_repository.revoke_all_user_sessions(user_id, reason)

        # Increment token version to invalidate any cached tokens
        await self.user_repository.increment_token_version(user_id)
        await self.user_repository.update_refresh_token_hash(user_id, None)

        return count

    # =========================================================================
    # PERMISSION MANAGEMENT
    # =========================================================================

    async def _get_user_permissions(self, user: UserWithPermissions) -> List[str]:
        """
        Get user permissions based on role and explicit grants.

        Args:
            user: User to get permissions for

        Returns:
            List of permission strings
        """
        permissions = []

        # Role-based permissions
        if user.role == "super_admin":
            permissions.extend(
                [
                    "clients:read",
                    "clients:write",
                    "clients:delete",
                    "clients:admin",
                    "users:read",
                    "users:write",
                    "users:delete",
                    "users:admin",
                    "system:admin",
                ]
            )
        elif user.role == "client_admin":
            permissions.extend(
                [
                    "client:read",
                    "client:write",
                    "client:admin",
                    "routing:read",
                    "routing:write",
                    "branding:read",
                    "branding:write",
                    "ai_prompts:read",
                    "ai_prompts:write",
                    "response_times:read",
                    "response_times:write",
                    "settings:read",
                    "settings:write",
                ]
            )
        elif user.role == "client_user":
            permissions.extend(
                ["client:read", "routing:read", "branding:read", "response_times:read"]
            )

        # Add explicit permissions from repository
        explicit_permissions = await self.user_repository.get_user_permissions(
            user.id, user.client_id
        )

        for permission in explicit_permissions:
            if permission not in permissions:
                permissions.append(permission)

        return permissions

    def check_permission(
        self,
        user_claims: UserTokenClaims,
        resource: str,
        action: str,
        client_id: str = None,
    ) -> bool:
        """
        Check if user has permission for resource:action.

        Args:
            user_claims: User token claims
            resource: Resource name
            action: Action name
            client_id: Optional client context

        Returns:
            True if permission is granted
        """
        permission = f"{resource}:{action}"

        # Check explicit permissions
        if permission in user_claims.permissions:
            return True

        # Super admin has all permissions
        if user_claims.role == "super_admin":
            return True

        # Check client scoping for non-super-admin
        if user_claims.role != "super_admin" and client_id:
            if user_claims.client_id != client_id:
                return False

        return False

    # =========================================================================
    # LOGIN/LOGOUT FLOWS
    # =========================================================================

    async def login(
        self, request: LoginRequest, ip_address: str = None, user_agent: str = None
    ) -> TokenResponse:
        """
        Complete login flow with token generation.

        Args:
            request: Login request
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Token response

        Raises:
            HTTPException: If authentication fails
        """
        # Authenticate user
        user = await self.authenticate_user(
            request.username, request.password, request.client_id
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        # Generate tokens
        access_result = await self.create_access_token(user)
        refresh_result = await self.create_refresh_token(user)

        # Update session metadata if provided
        if ip_address or user_agent:
            for session_info in [access_result, refresh_result]:
                session = await self.user_repository.find_session(
                    session_info["claims"]["jti"]
                )
                if session:
                    # Note: This would require adding session metadata update to repository
                    pass

        return TokenResponse(
            access_token=access_result["token"],
            refresh_token=refresh_result["token"],
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            client_id=user.client_id,
            role=user.role,
            permissions=await self._get_user_permissions(user),
        )

    async def logout(self, token: str) -> bool:
        """
        Logout user by revoking current token.

        Args:
            token: Current access token

        Returns:
            True if logout was successful
        """
        claims = await self.validate_token(token)
        if claims:
            return await self.revoke_token(claims.jti, "user_logout")
        return False

    async def get_current_user(self, token: str) -> Optional[AuthenticatedUser]:
        """
        Get current user from valid token.

        Args:
            token: Access token

        Returns:
            Authenticated user information if token is valid
        """
        claims = await self.validate_token(token)
        if not claims:
            return None

        user = await self.user_repository.find_by_id(int(claims.sub))
        if not user or user.status != "active":
            return None

        return AuthenticatedUser(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            client_id=user.client_id,
            permissions=claims.permissions,
            rate_limit_tier=user.rate_limit_tier,
            status=user.status,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )
