"""
SQLAlchemy-based UserRepository Implementation
🔌 Concrete implementation of UserRepository interface using SQLAlchemy ORM.

This adapter provides database persistence for user operations while implementing
the clean architecture repository pattern.
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from core.models.schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UserPermission,
    UserSession,
    UserWithPermissions,
)
from core.ports.user_repository import UserRepository
from infrastructure.database.models import User
from infrastructure.database.models import UserPermission as DBUserPermission
from infrastructure.database.models import UserRole
from infrastructure.database.models import UserSession as DBUserSession
from infrastructure.database.models import UserStatus

logger = logging.getLogger(__name__)


class ConflictError(Exception):
    """Raised when a resource conflict occurs (e.g., username already exists)."""

    pass


class SQLAlchemyUserRepository(UserRepository):
    """
    SQLAlchemy-based implementation of UserRepository.

    This adapter translates between core domain models and database models,
    providing persistence while keeping the core logic database-agnostic.
    """

    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def _user_to_domain_model(self, user: User) -> UserWithPermissions:
        """
        Convert database User model to domain UserWithPermissions model.

        Args:
            user: Database user model

        Returns:
            Domain user model with permissions
        """
        # Convert permissions
        permissions = []
        for perm in user.permissions:
            permissions.append(
                UserPermission(
                    id=perm.id,
                    user_id=perm.user_id,
                    resource=perm.resource,
                    action=perm.action,
                    client_id=perm.client_id,
                    conditions=perm.conditions,
                    granted_at=perm.granted_at,
                    granted_by=perm.granted_by,
                )
            )

        return UserWithPermissions(
            id=user.id,
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            client_id=user.client_id,
            last_login_at=user.last_login_at,
            login_attempts=user.login_attempts,
            locked_until=user.locked_until,
            jwt_refresh_token_hash=user.jwt_refresh_token_hash,
            jwt_token_version=user.jwt_token_version,
            created_at=user.created_at,
            updated_at=user.updated_at,
            created_by=user.created_by,
            api_access_enabled=user.api_access_enabled,
            rate_limit_tier=user.rate_limit_tier,
            permissions=permissions,
        )

    def _session_to_domain_model(self, session: DBUserSession) -> UserSession:
        """
        Convert database UserSession model to domain UserSession model.

        Args:
            session: Database session model

        Returns:
            Domain session model
        """
        return UserSession(
            id=session.id,
            user_id=session.user_id,
            session_id=session.session_id,
            token_type=session.token_type,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            location=session.location,
            issued_at=session.issued_at,
            expires_at=session.expires_at,
            last_used_at=session.last_used_at,
            is_active=session.is_active,
            revoked_at=session.revoked_at,
            revoked_reason=session.revoked_reason,
        )

    # =========================================================================
    # USER LOOKUP OPERATIONS
    # =========================================================================

    async def find_by_username(self, username: str) -> Optional[UserWithPermissions]:
        """Find user by username."""
        try:
            user = self.db.query(User).filter(User.username == username).first()
            return self._user_to_domain_model(user) if user else None
        except Exception as e:
            logger.error(f"Error finding user by username {username}: {e}")
            return None

    async def find_by_id(self, user_id: int) -> Optional[UserWithPermissions]:
        """Find user by ID."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            return self._user_to_domain_model(user) if user else None
        except Exception as e:
            logger.error(f"Error finding user by ID {user_id}: {e}")
            return None

    async def find_by_email(self, email: str) -> Optional[UserWithPermissions]:
        """Find user by email address."""
        try:
            user = self.db.query(User).filter(User.email == email).first()
            return self._user_to_domain_model(user) if user else None
        except Exception as e:
            logger.error(f"Error finding user by email {email}: {e}")
            return None

    async def find_by_client_id(self, client_id: str) -> List[UserWithPermissions]:
        """Find all users belonging to a specific client."""
        try:
            users = self.db.query(User).filter(User.client_id == client_id).all()
            return [self._user_to_domain_model(user) for user in users]
        except Exception as e:
            logger.error(f"Error finding users by client_id {client_id}: {e}")
            return []

    # =========================================================================
    # USER CRUD OPERATIONS
    # =========================================================================

    async def create_user(self, user_data: CreateUserRequest) -> UserWithPermissions:
        """Create a new user."""
        try:
            # Check for existing username/email
            existing_user = (
                self.db.query(User)
                .filter(
                    (User.username == user_data.username)
                    | (User.email == user_data.email)
                )
                .first()
            )

            if existing_user:
                if existing_user.username == user_data.username:
                    raise ConflictError(
                        f"Username '{user_data.username}' already exists"
                    )
                else:
                    raise ConflictError(f"Email '{user_data.email}' already exists")

            # Map string role to enum
            role_mapping = {
                "super_admin": UserRole.SUPER_ADMIN,
                "client_admin": UserRole.CLIENT_ADMIN,
                "client_user": UserRole.CLIENT_USER,
            }
            role = role_mapping.get(user_data.role, UserRole.CLIENT_USER)

            # Map string status to enum
            status_mapping = {
                "active": UserStatus.ACTIVE,
                "pending": UserStatus.PENDING,
                "suspended": UserStatus.SUSPENDED,
                "inactive": UserStatus.INACTIVE,
            }
            status = status_mapping.get(user_data.status, UserStatus.PENDING)

            # Create new user
            new_user = User(
                username=user_data.username,
                email=user_data.email,
                password_hash=user_data.password,  # Assuming already hashed
                full_name=user_data.full_name,
                role=role,
                status=status,
                client_id=user_data.client_id,
                api_access_enabled=user_data.api_access_enabled,
                rate_limit_tier=user_data.rate_limit_tier,
            )

            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)

            logger.info(f"Created new user: {user_data.username}")
            return self._user_to_domain_model(new_user)

        except ConflictError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user {user_data.username}: {e}")
            raise ValueError(f"Failed to create user: {e}")

    async def update_user(
        self, user_id: int, user_data: UpdateUserRequest
    ) -> Optional[UserWithPermissions]:
        """Update an existing user."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            # Update fields if provided
            if user_data.email is not None:
                # Check for email conflicts
                existing = (
                    self.db.query(User)
                    .filter(User.email == user_data.email, User.id != user_id)
                    .first()
                )
                if existing:
                    raise ConflictError(f"Email '{user_data.email}' already exists")
                user.email = user_data.email

            if user_data.full_name is not None:
                user.full_name = user_data.full_name

            if user_data.role is not None:
                role_mapping = {
                    "super_admin": UserRole.SUPER_ADMIN,
                    "client_admin": UserRole.CLIENT_ADMIN,
                    "client_user": UserRole.CLIENT_USER,
                }
                user.role = role_mapping.get(user_data.role, user.role)

            if user_data.client_id is not None:
                user.client_id = user_data.client_id

            if user_data.status is not None:
                status_mapping = {
                    "active": UserStatus.ACTIVE,
                    "pending": UserStatus.PENDING,
                    "suspended": UserStatus.SUSPENDED,
                    "inactive": UserStatus.INACTIVE,
                }
                user.status = status_mapping.get(user_data.status, user.status)

            if user_data.api_access_enabled is not None:
                user.api_access_enabled = user_data.api_access_enabled

            if user_data.rate_limit_tier is not None:
                user.rate_limit_tier = user_data.rate_limit_tier

            user.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)

            logger.info(f"Updated user: {user.username}")
            return self._user_to_domain_model(user)

        except ConflictError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user {user_id}: {e}")
            raise ValueError(f"Failed to update user: {e}")

    async def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            self.db.delete(user)
            self.db.commit()

            logger.info(f"Deleted user: {user.username}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting user {user_id}: {e}")
            return False

    def _build_user_filter_query(
        self,
        query,
        search: Optional[str] = None,
        client_id: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ):
        """Build query with filtering conditions."""
        if client_id:
            query = query.filter(User.client_id == client_id)

        if role:
            role_mapping = {
                "super_admin": UserRole.SUPER_ADMIN,
                "client_admin": UserRole.CLIENT_ADMIN,
                "client_user": UserRole.CLIENT_USER,
            }
            if role in role_mapping:
                query = query.filter(User.role == role_mapping[role])

        if status:
            status_mapping = {
                "active": UserStatus.ACTIVE,
                "pending": UserStatus.PENDING,
                "suspended": UserStatus.SUSPENDED,
                "inactive": UserStatus.INACTIVE,
            }
            if status in status_mapping:
                query = query.filter(User.status == status_mapping[status])

        if search:
            # Search across username, email, and full_name
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.full_name.ilike(search_pattern),
                )
            )

        return query

    def _apply_user_sorting(self, query, sort_by: str, sort_order: str):
        """Apply sorting to the query."""
        # Map sort fields to actual database columns
        sort_field_mapping = {
            "created_at": User.created_at,
            "updated_at": User.updated_at,
            "username": User.username,
            "email": User.email,
            "full_name": User.full_name,
            "role": User.role,
            "status": User.status,
            "last_login_at": User.last_login_at,
            "client_id": User.client_id,
        }

        # Get the column to sort by
        sort_column = sort_field_mapping.get(sort_by, User.created_at)

        # Apply sorting
        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        return query

    async def list_users(
        self,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        search: Optional[str] = None,
        client_id: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[UserWithPermissions], int]:
        """List users with pagination, sorting, and filtering."""
        try:
            # Build base query
            query = self.db.query(User)

            # Apply filters
            query = self._build_user_filter_query(
                query, search, client_id, role, status
            )

            # Get total count before pagination
            total_count = query.count()

            # Apply sorting
            query = self._apply_user_sorting(query, sort_by, sort_order)

            # Apply pagination
            users = query.offset(offset).limit(limit).all()

            # Convert to domain models
            user_models = [self._user_to_domain_model(user) for user in users]

            return user_models, total_count

        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return [], 0

    async def count_users(
        self,
        search: Optional[str] = None,
        client_id: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count users matching the filter criteria."""
        try:
            query = self.db.query(func.count(User.id))

            # Apply the same filters as list_users
            query = self._build_user_filter_query(
                query, search, client_id, role, status
            )

            return query.scalar() or 0

        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0

    # =========================================================================
    # AUTHENTICATION OPERATIONS
    # =========================================================================

    async def update_login_attempt(
        self, username: str, success: bool, ip_address: Optional[str] = None
    ) -> None:
        """Update login attempt tracking."""
        try:
            user = self.db.query(User).filter(User.username == username).first()
            if not user:
                return

            if success:
                user.login_attempts = 0
                user.locked_until = None
                user.last_login_at = datetime.utcnow()
            else:
                user.login_attempts = (user.login_attempts or 0) + 1

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating login attempt for {username}: {e}")

    async def lock_user_account(
        self, user_id: int, lock_until: datetime, reason: str
    ) -> None:
        """Lock user account until specified time."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.locked_until = lock_until
                user.status = UserStatus.SUSPENDED
                self.db.commit()
                logger.info(
                    f"Locked user account {user.username} until {lock_until}: {reason}"
                )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error locking user account {user_id}: {e}")

    async def unlock_user_account(self, user_id: int) -> None:
        """Unlock user account."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.locked_until = None
                user.login_attempts = 0
                if user.status == UserStatus.SUSPENDED:
                    user.status = UserStatus.ACTIVE
                self.db.commit()
                logger.info(f"Unlocked user account {user.username}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error unlocking user account {user_id}: {e}")

    async def update_password(self, user_id: int, password_hash: str) -> bool:
        """Update user password."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            user.password_hash = password_hash
            user.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Updated password for user {user.username}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating password for user {user_id}: {e}")
            return False

    async def update_last_login(
        self, user_id: int, login_time: Optional[datetime] = None
    ) -> None:
        """Update user's last login timestamp."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.last_login_at = login_time or datetime.utcnow()
                self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating last login for user {user_id}: {e}")

    # =========================================================================
    # TOKEN & SESSION OPERATIONS
    # =========================================================================

    async def create_user_session(
        self,
        user_id: int,
        session_id: str,
        token_type: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserSession:
        """Create a new user session."""
        try:
            session = DBUserSession(
                user_id=user_id,
                session_id=session_id,
                token_type=token_type,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            logger.debug(f"Created session {session_id} for user {user_id}")
            return self._session_to_domain_model(session)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user session: {e}")
            raise

    async def find_session(self, session_id: str) -> Optional[UserSession]:
        """Find user session by session ID."""
        try:
            session = (
                self.db.query(DBUserSession)
                .filter(DBUserSession.session_id == session_id)
                .first()
            )
            return self._session_to_domain_model(session) if session else None

        except Exception as e:
            logger.error(f"Error finding session {session_id}: {e}")
            return None

    async def update_session_activity(
        self, session_id: str, last_used: Optional[datetime] = None
    ) -> None:
        """Update session last used timestamp."""
        try:
            session = (
                self.db.query(DBUserSession)
                .filter(DBUserSession.session_id == session_id)
                .first()
            )
            if session:
                session.last_used_at = last_used or datetime.utcnow()
                self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating session activity {session_id}: {e}")

    async def revoke_session(self, session_id: str, reason: str) -> bool:
        """Revoke a user session."""
        try:
            session = (
                self.db.query(DBUserSession)
                .filter(DBUserSession.session_id == session_id)
                .first()
            )
            if not session:
                return False

            session.is_active = False
            session.revoked_at = datetime.utcnow()
            session.revoked_reason = reason
            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error revoking session {session_id}: {e}")
            return False

    async def revoke_all_user_sessions(self, user_id: int, reason: str) -> int:
        """Revoke all sessions for a user."""
        try:
            count = (
                self.db.query(DBUserSession)
                .filter(DBUserSession.user_id == user_id, DBUserSession.is_active)
                .update(
                    {
                        "is_active": False,
                        "revoked_at": datetime.utcnow(),
                        "revoked_reason": reason,
                    }
                )
            )
            self.db.commit()
            return count

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error revoking all sessions for user {user_id}: {e}")
            return 0

    async def list_user_sessions(
        self, user_id: int, active_only: bool = True
    ) -> List[UserSession]:
        """List sessions for a user."""
        try:
            query = self.db.query(DBUserSession).filter(
                DBUserSession.user_id == user_id
            )

            if active_only:
                query = query.filter(DBUserSession.is_active)

            sessions = query.all()
            return [self._session_to_domain_model(session) for session in sessions]

        except Exception as e:
            logger.error(f"Error listing sessions for user {user_id}: {e}")
            return []

    async def update_refresh_token_hash(
        self, user_id: int, token_hash: Optional[str]
    ) -> None:
        """Update user's refresh token hash."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.jwt_refresh_token_hash = token_hash
                self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating refresh token hash for user {user_id}: {e}")

    async def increment_token_version(self, user_id: int) -> int:
        """Increment user's token version (for global logout)."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return 0

            user.jwt_token_version += 1
            new_version = user.jwt_token_version
            self.db.commit()

            return new_version

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error incrementing token version for user {user_id}: {e}")
            return 0

    # =========================================================================
    # PERMISSION OPERATIONS
    # =========================================================================

    async def get_user_permissions(
        self, user_id: int, client_id: Optional[str] = None
    ) -> List[str]:
        """Get user permissions with optional client scoping."""
        try:
            query = self.db.query(DBUserPermission).filter(
                DBUserPermission.user_id == user_id
            )

            if client_id:
                query = query.filter(
                    (DBUserPermission.client_id == client_id)
                    | (DBUserPermission.client_id.is_(None))
                )

            permissions = query.all()
            return [f"{perm.resource}:{perm.action}" for perm in permissions]

        except Exception as e:
            logger.error(f"Error getting permissions for user {user_id}: {e}")
            return []

    async def grant_permission(
        self,
        user_id: int,
        resource: str,
        action: str,
        client_id: Optional[str] = None,
        granted_by: Optional[int] = None,
    ) -> None:
        """Grant permission to user."""
        try:
            # Check if permission already exists
            existing = (
                self.db.query(DBUserPermission)
                .filter(
                    DBUserPermission.user_id == user_id,
                    DBUserPermission.resource == resource,
                    DBUserPermission.action == action,
                    DBUserPermission.client_id == client_id,
                )
                .first()
            )

            if existing:
                return  # Permission already exists

            permission = DBUserPermission(
                user_id=user_id,
                resource=resource,
                action=action,
                client_id=client_id,
                granted_by=granted_by,
            )

            self.db.add(permission)
            self.db.commit()

            logger.info(f"Granted permission {resource}:{action} to user {user_id}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error granting permission to user {user_id}: {e}")

    async def revoke_permission(
        self, user_id: int, resource: str, action: str, client_id: Optional[str] = None
    ) -> bool:
        """Revoke permission from user."""
        try:
            permission = (
                self.db.query(DBUserPermission)
                .filter(
                    DBUserPermission.user_id == user_id,
                    DBUserPermission.resource == resource,
                    DBUserPermission.action == action,
                    DBUserPermission.client_id == client_id,
                )
                .first()
            )

            if not permission:
                return False

            self.db.delete(permission)
            self.db.commit()

            logger.info(f"Revoked permission {resource}:{action} from user {user_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error revoking permission from user {user_id}: {e}")
            return False
