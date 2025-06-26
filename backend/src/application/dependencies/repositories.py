"""
Repository Dependency Injection for Clean Architecture
🔌 Provides concrete repository implementations to the application layer.

This module bridges the infrastructure and core layers by providing
dependency injection for repository interfaces.
"""

import logging
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from core.ports.analytics_repository import AnalyticsRepository
from core.ports.client_repository import ClientRepository
from core.ports.user_repository import UserRepository
from infrastructure.adapters.analytics_repository_impl import SQLAlchemyAnalyticsRepository
from infrastructure.adapters.client_repository_impl import SQLAlchemyClientRepository
from infrastructure.adapters.user_repository_impl import SQLAlchemyUserRepository
from infrastructure.database.connection import get_database_session

logger = logging.getLogger(__name__)


# =============================================================================
# REPOSITORY DEPENDENCIES
# =============================================================================


def get_user_repository(db: Annotated[Session, Depends(get_database_session)]) -> UserRepository:
    """
    Dependency that provides UserRepository implementation.

    Args:
        db: Database session from dependency injection

    Returns:
        UserRepository implementation
    """
    return SQLAlchemyUserRepository(db)


def get_client_repository(
    db: Annotated[Session, Depends(get_database_session)],
) -> ClientRepository:
    """
    Dependency that provides ClientRepository implementation.

    Args:
        db: Database session from dependency injection

    Returns:
        ClientRepository implementation
    """
    return SQLAlchemyClientRepository(db)


def get_analytics_repository(
    db: Annotated[Session, Depends(get_database_session)],
) -> AnalyticsRepository:
    """
    Dependency that provides AnalyticsRepository implementation.

    Args:
        db: Database session from dependency injection

    Returns:
        AnalyticsRepository implementation
    """
    return SQLAlchemyAnalyticsRepository(db)


# =============================================================================
# SERVICE DEPENDENCIES
# =============================================================================


def get_auth_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> "AuthService":
    """
    Dependency that provides AuthService with repository injection.

    Args:
        user_repository: UserRepository implementation

    Returns:
        AuthService instance
    """
    from core.authentication.auth_service import AuthService

    return AuthService(user_repository)


# =============================================================================
# LEGACY COMPATIBILITY DEPENDENCIES
# =============================================================================


def get_legacy_auth_service(
    db: Annotated[Session, Depends(get_database_session)],
) -> "LegacyAuthService":
    """
    Legacy dependency for backward compatibility with existing JWT service.

    This provides the old AuthService that directly uses database sessions.
    This should be phased out in favor of the new repository-based service.

    Args:
        db: Database session

    Returns:
        Legacy AuthService instance
    """
    from core.authentication.jwt import AuthService as LegacyAuthService

    return LegacyAuthService(db)


def get_client_manager(
    client_repository: Annotated[ClientRepository, Depends(get_client_repository)],
) -> "EnhancedClientManager":
    """
    Dependency that provides ClientManager with repository injection.

    This provides the updated ClientManager that uses both file-based configuration
    and database operations through the ClientRepository interface.

    Args:
        client_repository: ClientRepository implementation

    Returns:
        EnhancedClientManager instance with repository injection
    """
    from core.clients.manager import get_client_manager

    return get_client_manager(client_repository)
