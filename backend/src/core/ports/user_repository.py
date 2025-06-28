"""
User Repository Interface (Port) for Clean Architecture
🏗️ Abstract interface for user data access operations.

This interface defines the contract for user data operations without
depending on any specific database technology or ORM.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Tuple

from core.models.schemas import (
    AuthenticatedUser,
    CreateUserRequest,
    UpdateUserRequest,
    UserSession,
    UserWithPermissions,
)


class UserRepository(ABC):
    """
    Abstract repository interface for user data operations.

    This interface defines all user-related data operations needed by
    the core business logic. Concrete implementations will be provided
    in the infrastructure layer.
    """

    # =========================================================================
    # USER LOOKUP OPERATIONS
    # =========================================================================

    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[UserWithPermissions]:
        """
        Find user by username.

        Args:
            username: Username to search for

        Returns:
            User with permissions if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_id(self, user_id: int) -> Optional[UserWithPermissions]:
        """
        Find user by ID.

        Args:
            user_id: User ID to search for

        Returns:
            User with permissions if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[UserWithPermissions]:
        """
        Find user by email address.

        Args:
            email: Email address to search for

        Returns:
            User with permissions if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_client_id(self, client_id: str) -> List[UserWithPermissions]:
        """
        Find all users belonging to a specific client.

        Args:
            client_id: Client ID to search for

        Returns:
            List of users with permissions
        """
        pass

    # =========================================================================
    # USER CRUD OPERATIONS
    # =========================================================================

    @abstractmethod
    async def create_user(self, user_data: CreateUserRequest) -> UserWithPermissions:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user with permissions

        Raises:
            ValueError: If user data is invalid
            ConflictError: If username/email already exists
        """
        pass

    @abstractmethod
    async def update_user(
        self, user_id: int, user_data: UpdateUserRequest
    ) -> Optional[UserWithPermissions]:
        """
        Update an existing user.

        Args:
            user_id: ID of user to update
            user_data: Updated user data

        Returns:
            Updated user with permissions if found, None otherwise

        Raises:
            ValueError: If user data is invalid
            ConflictError: If username/email conflicts with another user
        """
        pass

    @abstractmethod
    async def delete_user(self, user_id: int) -> bool:
        """
        Delete a user.

        Args:
            user_id: ID of user to delete

        Returns:
            True if user was deleted, False if not found
        """
        pass

    @abstractmethod
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
        """
        List users with pagination, sorting, and filtering.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            sort_by: Field to sort by (e.g., 'created_at', 'username', 'email')
            sort_order: Sort order - 'asc' or 'desc'
            search: Search term for username, email, or full name
            client_id: Filter by client ID
            role: Filter by role
            status: Filter by account status

        Returns:
            Tuple of (users list, total count)
        """
        pass

    @abstractmethod
    async def count_users(
        self,
        search: Optional[str] = None,
        client_id: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """
        Count users matching the filter criteria.

        Args:
            search: Search term for username, email, or full name
            client_id: Filter by client ID
            role: Filter by role
            status: Filter by account status

        Returns:
            Total count of users matching criteria
        """
        pass

    # =========================================================================
    # AUTHENTICATION OPERATIONS
    # =========================================================================

    @abstractmethod
    async def update_login_attempt(
        self, username: str, success: bool, ip_address: Optional[str] = None
    ) -> None:
        """
        Update login attempt tracking.

        Args:
            username: Username that attempted login
            success: Whether login was successful
            ip_address: IP address of login attempt
        """
        pass

    @abstractmethod
    async def lock_user_account(
        self, user_id: int, lock_until: datetime, reason: str
    ) -> None:
        """
        Lock user account until specified time.

        Args:
            user_id: ID of user to lock
            lock_until: When to unlock the account
            reason: Reason for locking
        """
        pass

    @abstractmethod
    async def unlock_user_account(self, user_id: int) -> None:
        """
        Unlock user account.

        Args:
            user_id: ID of user to unlock
        """
        pass

    @abstractmethod
    async def update_password(self, user_id: int, password_hash: str) -> bool:
        """
        Update user password.

        Args:
            user_id: ID of user to update
            password_hash: New password hash

        Returns:
            True if password was updated, False if user not found
        """
        pass

    @abstractmethod
    async def update_last_login(
        self, user_id: int, login_time: Optional[datetime] = None
    ) -> None:
        """
        Update user's last login timestamp.

        Args:
            user_id: ID of user that logged in
            login_time: Login timestamp (defaults to now)
        """
        pass

    # =========================================================================
    # TOKEN & SESSION OPERATIONS
    # =========================================================================

    @abstractmethod
    async def create_user_session(
        self,
        user_id: int,
        session_id: str,
        token_type: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserSession:
        """
        Create a new user session.

        Args:
            user_id: ID of user
            session_id: Unique session identifier
            token_type: Type of token (access, refresh)
            expires_at: When session expires
            ip_address: IP address of session
            user_agent: User agent string

        Returns:
            Created session
        """
        pass

    @abstractmethod
    async def find_session(self, session_id: str) -> Optional[UserSession]:
        """
        Find user session by session ID.

        Args:
            session_id: Session ID to find

        Returns:
            Session if found, None otherwise
        """
        pass

    @abstractmethod
    async def update_session_activity(
        self, session_id: str, last_used: Optional[datetime] = None
    ) -> None:
        """
        Update session last used timestamp.

        Args:
            session_id: Session ID to update
            last_used: Last used timestamp (defaults to now)
        """
        pass

    @abstractmethod
    async def revoke_session(self, session_id: str, reason: str) -> bool:
        """
        Revoke a user session.

        Args:
            session_id: Session ID to revoke
            reason: Reason for revocation

        Returns:
            True if session was revoked, False if not found
        """
        pass

    @abstractmethod
    async def revoke_all_user_sessions(self, user_id: int, reason: str) -> int:
        """
        Revoke all sessions for a user.

        Args:
            user_id: ID of user whose sessions to revoke
            reason: Reason for revocation

        Returns:
            Number of sessions revoked
        """
        pass

    @abstractmethod
    async def list_user_sessions(
        self, user_id: int, active_only: bool = True
    ) -> List[UserSession]:
        """
        List sessions for a user.

        Args:
            user_id: ID of user
            active_only: Whether to return only active sessions

        Returns:
            List of user sessions
        """
        pass

    @abstractmethod
    async def update_refresh_token_hash(
        self, user_id: int, token_hash: Optional[str]
    ) -> None:
        """
        Update user's refresh token hash.

        Args:
            user_id: ID of user
            token_hash: New refresh token hash (None to clear)
        """
        pass

    @abstractmethod
    async def increment_token_version(self, user_id: int) -> int:
        """
        Increment user's token version (for global logout).

        Args:
            user_id: ID of user

        Returns:
            New token version number
        """
        pass

    # =========================================================================
    # PERMISSION OPERATIONS
    # =========================================================================

    @abstractmethod
    async def get_user_permissions(
        self, user_id: int, client_id: Optional[str] = None
    ) -> List[str]:
        """
        Get user permissions with optional client scoping.

        Args:
            user_id: ID of user
            client_id: Optional client ID for scoped permissions

        Returns:
            List of permission strings (e.g., "routing:write")
        """
        pass

    @abstractmethod
    async def grant_permission(
        self,
        user_id: int,
        resource: str,
        action: str,
        client_id: Optional[str] = None,
        granted_by: Optional[int] = None,
    ) -> None:
        """
        Grant permission to user.

        Args:
            user_id: ID of user to grant permission to
            resource: Resource name (e.g., "routing")
            action: Action name (e.g., "write")
            client_id: Optional client scoping
            granted_by: ID of user granting permission
        """
        pass

    @abstractmethod
    async def revoke_permission(
        self, user_id: int, resource: str, action: str, client_id: Optional[str] = None
    ) -> bool:
        """
        Revoke permission from user.

        Args:
            user_id: ID of user to revoke permission from
            resource: Resource name
            action: Action name
            client_id: Optional client scoping

        Returns:
            True if permission was revoked, False if not found
        """
        pass
