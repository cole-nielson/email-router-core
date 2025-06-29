"""
JWT Authentication Service for multi-tenant email router.
🔐 Secure token generation and validation with client scoping and RBAC.
Optimized for agentic workflows with fine-grained permissions.

This is the unified JWT service that replaces app/services/auth_service.py.
All JWT token operations, user authentication, and session management are handled here.
"""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import jwt
from fastapi import HTTPException, status
from jwt.exceptions import PyJWTError as JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Import database models and connection dynamically to avoid circular imports

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

# =============================================================================
# PYDANTIC MODELS
# =============================================================================


class TokenResponse(BaseModel):
    """JWT token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until access token expires
    client_id: Optional[str] = None
    role: str
    permissions: List[str] = []


class UserTokenClaims(BaseModel):
    """JWT token claims for validation."""

    sub: str  # User ID
    username: str
    email: str
    role: str
    client_id: Optional[str] = None
    permissions: List[str] = []
    jti: str  # JWT ID for revocation
    iat: int  # Issued at
    exp: int  # Expires at
    token_type: str  # access or refresh


class LoginRequest(BaseModel):
    """User login request."""

    username: str
    password: str
    client_id: Optional[str] = None  # Optional client context


class AuthenticatedUser(BaseModel):
    """Authenticated user information."""

    id: int
    username: str
    email: str
    full_name: str
    role: str  # Changed from UserRole enum to string to avoid circular import
    client_id: Optional[str] = None
    permissions: List[str] = []
    rate_limit_tier: str = "standard"


# =============================================================================
# JWT AUTHENTICATION SERVICE
# =============================================================================


class AuthService:
    """Comprehensive JWT authentication service with RBAC."""

    def __init__(self, db: Session):
        if not db:
            logger.error("AuthService initialized with a null database session.")
            raise ValueError("Database session cannot be None for AuthService.")
        self.db = db

        # Import models dynamically to avoid circular imports
        try:
            from infrastructure.database.models import (
                User,
                UserRole,
                UserSession,
                UserStatus,
            )

            self.User = User
            self.UserRole = UserRole
            self.UserSession = UserSession
            self.UserStatus = UserStatus
        except ImportError as e:
            logger.critical(f"Failed to import database models for AuthService: {e}")
            raise RuntimeError(
                "Could not initialize AuthService due to missing database models."
            ) from e

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

    def authenticate_user(
        self, username: str, password: str, client_id: Optional[str] = None
    ) -> Optional[Any]:
        """Authenticate user credentials and check account status."""
        try:
            # Get user by username using raw SQL to bypass enum issues
            from sqlalchemy import text

            result = self.db.execute(
                text(
                    """
                    SELECT id, username, email, password_hash, full_name, role, status,
                           client_id, last_login_at, login_attempts, locked_until,
                           jwt_refresh_token_hash, jwt_token_version, created_at, updated_at,
                           created_by, api_access_enabled, rate_limit_tier
                    FROM users WHERE username = :username
                """
                ),
                {"username": username},
            ).fetchone()

            if not result:
                logger.warning(f"Authentication failed: user '{username}' not found")
                return None

            # Create a user-like object from the raw data
            user_data = {
                "id": result[0],
                "username": result[1],
                "email": result[2],
                "password_hash": result[3],
                "full_name": result[4],
                "role_str": result[5],
                "status_str": result[6],
                "client_id": result[7],
                "last_login_at": result[8],
                "login_attempts": result[9] or 0,
                "locked_until": result[10],
                "jwt_refresh_token_hash": result[11],
                "jwt_token_version": result[12] or 1,
                "created_at": result[13],
                "updated_at": result[14],
                "created_by": result[15],
                "api_access_enabled": (
                    bool(result[16]) if result[16] is not None else True
                ),
                "rate_limit_tier": result[17] or "standard",
            }

            # Map string roles to enum values for compatibility (handle both values and names)
            role_mapping = {
                "super_admin": self.UserRole.SUPER_ADMIN,
                "client_admin": self.UserRole.CLIENT_ADMIN,
                "client_user": self.UserRole.CLIENT_USER,
                "SUPER_ADMIN": self.UserRole.SUPER_ADMIN,
                "CLIENT_ADMIN": self.UserRole.CLIENT_ADMIN,
                "CLIENT_USER": self.UserRole.CLIENT_USER,
            }
            user_data["role"] = role_mapping.get(
                user_data["role_str"], self.UserRole.CLIENT_USER
            )

            # Map string status to enum values (handle both values and names)
            status_mapping = {
                "active": self.UserStatus.ACTIVE,
                "pending": self.UserStatus.PENDING,
                "suspended": self.UserStatus.SUSPENDED,
                "inactive": self.UserStatus.INACTIVE,
                "ACTIVE": self.UserStatus.ACTIVE,
                "PENDING": self.UserStatus.PENDING,
                "SUSPENDED": self.UserStatus.SUSPENDED,
                "INACTIVE": self.UserStatus.INACTIVE,
            }
            user_data["status"] = status_mapping.get(
                user_data["status_str"], self.UserStatus.PENDING
            )

            # Create a simple user object
            class SimpleUser:
                pass

            user = SimpleUser()
            for key, value in user_data.items():
                setattr(user, key, value)

            # Add missing attributes for compatibility
            user.permissions = []  # Empty permissions list for now

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
            if user.status != self.UserStatus.ACTIVE:
                logger.warning(
                    f"Authentication failed: account '{username}' is {user.status.value}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Account is {user.status.value}",
                )

            # Verify password
            if not self.verify_password(password, user.password_hash):
                # Increment failed login attempts using raw SQL
                new_attempts = user.login_attempts + 1

                # Lock account if too many attempts
                if new_attempts >= MAX_LOGIN_ATTEMPTS:
                    lock_until = datetime.utcnow() + timedelta(
                        minutes=LOCKOUT_DURATION_MINUTES
                    )
                    self.db.execute(
                        text(
                            "UPDATE users SET login_attempts = :attempts, locked_until = :locked WHERE username = :username"
                        ),
                        {
                            "attempts": new_attempts,
                            "locked": lock_until,
                            "username": username,
                        },
                    )
                    logger.warning(
                        f"Account '{username}' locked due to {MAX_LOGIN_ATTEMPTS} failed attempts"
                    )
                else:
                    self.db.execute(
                        text(
                            "UPDATE users SET login_attempts = :attempts WHERE username = :username"
                        ),
                        {"attempts": new_attempts, "username": username},
                    )

                self.db.commit()
                logger.warning(
                    f"Authentication failed: invalid password for user '{username}'"
                )
                return None

            # Check client scope for non-super-admin users
            if user.role != self.UserRole.SUPER_ADMIN and client_id:
                if user.client_id != client_id:
                    logger.warning(
                        f"Authentication failed: user '{username}' not authorized for client '{client_id}'"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="User not authorized for this client",
                    )

            # Reset login attempts on successful authentication using raw SQL
            self.db.execute(
                text(
                    "UPDATE users SET login_attempts = 0, locked_until = NULL, last_login_at = datetime('now') WHERE username = :username"
                ),
                {"username": username},
            )
            self.db.commit()

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

    def create_access_token(
        self, user: Any, permissions: List[str] = None
    ) -> Dict[str, Any]:
        """Create JWT access token with user claims."""
        import time

        now = int(time.time())  # Use time.time() for proper UTC timestamps
        exp = now + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)  # Convert minutes to seconds
        jti = secrets.token_urlsafe(32)

        # Build token claims
        claims = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "client_id": user.client_id,
            "permissions": permissions or self._get_user_permissions(user),
            "jti": jti,
            "iat": now,
            "exp": exp,
            "token_type": "access",
        }

        # Create JWT token
        token = jwt.encode(claims, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        # Convert timestamp back to datetime for database storage
        exp_datetime = datetime.fromtimestamp(exp)

        # Store session for tracking
        session = self.UserSession(
            user_id=user.id,
            session_id=jti,
            token_type="access",
            expires_at=exp_datetime,
        )
        self.db.add(session)
        self.db.commit()

        return {"token": token, "claims": claims, "expires_at": exp_datetime}

    def create_refresh_token(self, user: Any) -> Dict[str, Any]:
        """Create JWT refresh token for long-term sessions."""
        import time

        now = int(time.time())  # Use time.time() for proper UTC timestamps
        exp = now + (
            REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )  # Convert days to seconds
        jti = secrets.token_urlsafe(32)

        claims = {
            "sub": str(user.id),
            "username": user.username,
            "jti": jti,
            "iat": now,
            "exp": exp,
            "token_type": "refresh",
        }

        token = jwt.encode(claims, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        # Store refresh token hash for revocation
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        user.jwt_refresh_token_hash = token_hash

        # Convert timestamp back to datetime for database storage
        exp_datetime = datetime.fromtimestamp(exp)

        # Store session
        session = self.UserSession(
            user_id=user.id,
            session_id=jti,
            token_type="refresh",
            expires_at=exp_datetime,
        )
        self.db.add(session)
        self.db.commit()

        return {"token": token, "claims": claims, "expires_at": exp_datetime}

    @staticmethod
    def validate_token_stateless(
        token: str, token_type: str = "access"
    ) -> Optional[UserTokenClaims]:
        """Validate JWT token signature and expiration without database access."""
        try:
            # Decode token with signature and expiration validation
            # Add leeway to handle clock skew (required for newer PyJWT versions)
            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
                leeway=timedelta(seconds=10),
            )
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

    def validate_token(
        self, token: str, token_type: str = "access"
    ) -> Optional[UserTokenClaims]:
        """Validate JWT token and return claims with database session check."""
        try:
            # First do stateless validation
            claims = self.validate_token_stateless(token, token_type)
            if not claims:
                return None

            # Check if session is still active
            session = (
                self.db.query(self.UserSession)
                .filter(
                    self.UserSession.session_id == claims.jti,
                    self.UserSession.is_active,
                )
                .first()
            )

            if not session:
                logger.warning(f"Token session not found or inactive: {claims.jti}")
                return None

            # Update last used time
            session.last_used_at = datetime.utcnow()
            self.db.commit()

            return claims

        except JWTError as e:
            logger.warning(f"JWT validation error: {e}")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[TokenResponse]:
        """Generate new access token from valid refresh token."""
        claims = self.validate_token(refresh_token, "refresh")
        if not claims:
            return None

        # Get user
        user = self.db.query(self.User).filter(self.User.id == int(claims.sub)).first()
        if not user or user.status != self.UserStatus.ACTIVE:
            return None

        # Verify refresh token hash
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        if user.jwt_refresh_token_hash != token_hash:
            logger.warning(f"Refresh token hash mismatch for user {user.username}")
            return None

        # Create new access token
        access_result = self.create_access_token(user)

        return TokenResponse(
            access_token=access_result["token"],
            refresh_token=refresh_token,  # Keep existing refresh token
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            client_id=user.client_id,
            role=user.role.value,
            permissions=self._get_user_permissions(user),
        )

    def revoke_token(self, jti: str, reason: str = "user_logout") -> bool:
        """Revoke a specific token session."""
        session = (
            self.db.query(self.UserSession)
            .filter(self.UserSession.session_id == jti)
            .first()
        )
        if session:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            session.revoked_reason = reason
            self.db.commit()
            return True
        return False

    def revoke_all_user_tokens(
        self, user_id: int, reason: str = "security_action"
    ) -> int:
        """Revoke all active tokens for a user."""
        count = (
            self.db.query(self.UserSession)
            .filter(self.UserSession.user_id == user_id, self.UserSession.is_active)
            .update(
                {
                    "is_active": False,
                    "revoked_at": datetime.utcnow(),
                    "revoked_reason": reason,
                }
            )
        )

        # Increment token version to invalidate any cached tokens
        user = self.db.query(self.User).filter(self.User.id == user_id).first()
        if user:
            user.jwt_token_version += 1
            user.jwt_refresh_token_hash = None

        self.db.commit()
        return count

    # =========================================================================
    # PERMISSION MANAGEMENT
    # =========================================================================

    def _get_user_permissions(self, user: Any) -> List[str]:
        """Get user permissions based on role and explicit grants."""
        permissions = []

        # Role-based permissions
        if user.role == self.UserRole.SUPER_ADMIN:
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
        elif user.role == self.UserRole.CLIENT_ADMIN:
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
        elif user.role == self.UserRole.CLIENT_USER:
            permissions.extend(
                ["client:read", "routing:read", "branding:read", "response_times:read"]
            )

        # Add explicit permissions from database
        for perm in user.permissions:
            permission_str = f"{perm.resource}:{perm.action}"
            if permission_str not in permissions:
                permissions.append(permission_str)

        return permissions

    def check_permission(
        self,
        user_claims: UserTokenClaims,
        resource: str,
        action: str,
        client_id: str = None,
    ) -> bool:
        """Check if user has permission for resource:action."""
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

    def login(
        self, request: LoginRequest, ip_address: str = None, user_agent: str = None
    ) -> TokenResponse:
        """Complete login flow with token generation."""
        # Authenticate user
        user = self.authenticate_user(
            request.username, request.password, request.client_id
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        # Generate tokens
        access_result = self.create_access_token(user)
        refresh_result = self.create_refresh_token(user)

        # Update session metadata
        for session in [access_result, refresh_result]:
            session_record = (
                self.db.query(self.UserSession)
                .filter(self.UserSession.session_id == session["claims"]["jti"])
                .first()
            )
            if session_record:
                session_record.ip_address = ip_address
                session_record.user_agent = user_agent

        self.db.commit()

        return TokenResponse(
            access_token=access_result["token"],
            refresh_token=refresh_result["token"],
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            client_id=user.client_id,
            role=user.role.value,
            permissions=self._get_user_permissions(user),
        )

    def logout(self, token: str) -> bool:
        """Logout user by revoking current token."""
        claims = self.validate_token(token)
        if claims:
            return self.revoke_token(claims.jti, "user_logout")
        return False

    def get_current_user(self, token: str) -> Optional[AuthenticatedUser]:
        """Get current user from valid token."""
        claims = self.validate_token(token)
        if not claims:
            return None

        user = self.db.query(self.User).filter(self.User.id == int(claims.sub)).first()
        if not user or user.status != self.UserStatus.ACTIVE:
            return None

        return AuthenticatedUser(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,  # Convert enum to string
            client_id=user.client_id,
            permissions=claims.permissions,
            rate_limit_tier=user.rate_limit_tier,
        )


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================


def get_auth_service(db: Session) -> AuthService:
    """Dependency for AuthService, requires a DB session."""
    if not db:
        raise ValueError("AuthService requires a valid database session.")
    return AuthService(db)
