"""
Authentication-specific test fixtures.
"""

import pytest

from core.authentication.auth_service import AuthService
from infrastructure.adapters.user_repository_impl import SQLAlchemyUserRepository
from infrastructure.database.models import User, UserRole, UserStatus


@pytest.fixture(scope="function")
def user_repository(isolated_db_session):
    """Provide a UserRepository instance for testing."""
    return SQLAlchemyUserRepository(isolated_db_session)


@pytest.fixture(scope="function")
def auth_service(user_repository):
    """Provide an AuthService instance for testing."""
    return AuthService(user_repository)


@pytest.fixture(scope="function")
def super_admin_user(isolated_db_session, auth_service):
    """Create a super admin user for testing."""
    user = User(
        username="test_super_admin",
        email="super_admin@test.com",
        full_name="Test Super Admin",
        password_hash=auth_service.hash_password("supersecret123"),
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
    )
    isolated_db_session.add(user)
    isolated_db_session.commit()

    # Store password for test access
    user.password = "supersecret123"
    return user


@pytest.fixture(scope="function")
def client_admin_user(isolated_db_session, auth_service):
    """Create a client admin user for testing."""
    user = User(
        username="test_client_admin",
        email="client_admin@test.com",
        full_name="Test Client Admin",
        password_hash=auth_service.hash_password("adminpass123"),
        role=UserRole.CLIENT_ADMIN,
        status=UserStatus.ACTIVE,
        client_id="test-client",
    )
    isolated_db_session.add(user)
    isolated_db_session.commit()

    user.password = "adminpass123"
    return user


@pytest.fixture(scope="function")
def client_user(isolated_db_session, auth_service):
    """Create a standard client user for testing."""
    user = User(
        username="test_client_user",
        email="client_user@test.com",
        full_name="Test Client User",
        password_hash=auth_service.hash_password("userpass123"),
        role=UserRole.CLIENT_USER,
        status=UserStatus.ACTIVE,
        client_id="test-client",
    )
    isolated_db_session.add(user)
    isolated_db_session.commit()

    user.password = "userpass123"
    return user


@pytest.fixture(scope="function")
async def jwt_tokens(auth_service, super_admin_user, user_repository):
    """Generate JWT tokens for testing."""
    # Convert database user to domain model first
    domain_user = await user_repository.find_by_id(super_admin_user.id)

    access_result = await auth_service.create_access_token(domain_user)
    refresh_result = await auth_service.create_refresh_token(domain_user)

    return {
        "access_token": access_result["token"],
        "refresh_token": refresh_result["token"],
        "user": super_admin_user,
    }


@pytest.fixture(scope="function")
async def auth_headers(jwt_tokens):
    """Generate authentication headers for API testing."""
    tokens = await jwt_tokens if hasattr(jwt_tokens, "__await__") else jwt_tokens
    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-API-Key": "test-api-key-for-testing",
    }
