"""
Authentication-specific test fixtures.
"""

import pytest

from core.authentication.jwt import AuthService
from infrastructure.database.models import User, UserRole, UserStatus


@pytest.fixture(scope="function")
def auth_service(isolated_db_session):
    """Provide an AuthService instance for testing."""
    return AuthService(isolated_db_session)


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
def jwt_tokens(auth_service, super_admin_user):
    """Generate JWT tokens for testing."""
    access_token = auth_service.create_access_token(super_admin_user)
    refresh_token = auth_service.create_refresh_token(super_admin_user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": super_admin_user,
    }


@pytest.fixture(scope="function")
def auth_headers(jwt_tokens):
    """Generate authentication headers for API testing."""
    return {
        "Authorization": f"Bearer {jwt_tokens['access_token']}",
        "X-API-Key": "test-api-key-for-testing",
    }
