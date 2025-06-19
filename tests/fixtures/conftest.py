"""
Global fixtures for the Email Router test suite.
"""

# Add project root to path to allow module imports
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

backend_path = str(Path(__file__).parent.parent / "backend")
sys.path.insert(0, backend_path)
# Ensure tests can find the src module
import sys

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Set up test environment variables before any imports
TEST_ENV_VARS = {
    "JWT_SECRET_KEY": "test-secret-key-for-testing-minimum-32-characters",
    "ANTHROPIC_API_KEY": "sk-ant-test-key-for-testing",
    "MAILGUN_API_KEY": "key-test-key-for-testing",
    "MAILGUN_DOMAIN": "test.example.com",
    "ENVIRONMENT": "test",
    "EMAIL_ROUTER_DEBUG": "false",
    "LOG_LEVEL": "WARNING",  # Reduce noise in tests
    "DATABASE_URL": "sqlite:///:memory:",
}

# Apply test environment variables
for key, value in TEST_ENV_VARS.items():
    os.environ.setdefault(key, value)

from src.core.authentication.jwt import AuthService
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models import Base, User, UserRole, UserStatus
from src.main import app

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create the database and run Alembic migrations for the entire test session."""
    # For testing, we'll use direct table creation since Alembic with in-memory is complex
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Yield a new database session for each test function."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Yield a TestClient with a database override for each test function."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a standard test user and a super_admin and add them to the session."""
    auth_service = AuthService(db_session)

    # Create super_admin
    super_admin_password = "supersecretpassword"
    super_admin = User(
        username="test_super_admin",
        email="test_super_admin@example.com",
        full_name="Test Super Admin",
        password_hash=auth_service.hash_password(super_admin_password),
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
    )

    # Create standard user
    user_password = "a_secure_password"
    user = User(
        username="testuser",
        email="testuser@example.com",
        full_name="Test User",
        client_id="test-client",
        password_hash=auth_service.hash_password(user_password),
        role=UserRole.CLIENT_USER,
        status=UserStatus.ACTIVE,
    )

    db_session.add(super_admin)
    db_session.add(user)
    db_session.commit()

    # Store passwords on the object for tests to use
    super_admin.password = super_admin_password
    user.password = user_password

    return {"super_admin": super_admin, "client_user": user}


@pytest.fixture(scope="function")
def auth_headers(client, test_user):
    """
    Authenticate as the test super_admin and return valid auth headers.
    """
    login_data = {
        "username": test_user["super_admin"].username,
        "password": test_user["super_admin"].password,
    }

    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    tokens = response.json()

    access_token = tokens["access_token"]

    # This is a mock API key for testing webhook endpoints
    # In a real scenario, this would also be generated and stored
    api_key = "sk-test-client-dummy-key-for-testing"

    return {"Authorization": f"Bearer {access_token}", "X-API-Key": api_key}


# =============================================================================
# EXTERNAL SERVICE MOCKING FIXTURES
# =============================================================================


@pytest.fixture(scope="function", autouse=True)
def mock_external_services():
    """Mock all external services for test isolation."""

    # Mock requests (used by Mailgun and other HTTP APIs)
    with patch("requests.post") as mock_requests_post, patch("requests.get") as mock_requests_get:

        # Set up default responses for requests
        mock_requests_post.return_value.status_code = 200
        mock_requests_post.return_value.json.return_value = {"id": "test-message-id"}
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {"status": "success"}

        yield {
            "requests_post": mock_requests_post,
            "requests_get": mock_requests_get,
        }


@pytest.fixture(scope="function")
def mock_anthropic_response():
    """Mock Anthropic API with customizable responses."""

    def _mock_response(classification="general", confidence=0.9):
        # Only patch if anthropic module is imported in the application
        try:
            import sys

            if "anthropic" in sys.modules:
                with patch("anthropic.Anthropic") as mock_anthropic:
                    mock_client = mock_anthropic.return_value
                    mock_response = mock_client.messages.create.return_value
                    mock_response.content = [type("obj", (object,), {"text": classification})]
                    yield mock_client
            else:
                # Mock through application-specific imports instead
                with patch("app.services.ai_classifier.anthropic", create=True) as mock_anthropic:
                    mock_client = mock_anthropic.Anthropic.return_value
                    mock_response = mock_client.messages.create.return_value
                    mock_response.content = [type("obj", (object,), {"text": classification})]
                    yield mock_client
        except ImportError:
            # Create a simple mock if anthropic not available
            from unittest.mock import MagicMock

            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [type("obj", (object,), {"text": classification})]
            mock_client.messages.create.return_value = mock_response
            yield mock_client

    return _mock_response


@pytest.fixture(scope="function")
def mock_mailgun_response():
    """Mock Mailgun API with customizable responses."""

    def _mock_response(success=True, message_id="test-message-id"):
        with patch("requests.post") as mock_mailgun:
            if success:
                mock_mailgun.return_value.status_code = 200
                mock_mailgun.return_value.json.return_value = {"id": message_id}
            else:
                mock_mailgun.return_value.status_code = 400
                mock_mailgun.return_value.json.return_value = {"error": "API Error"}
            yield mock_mailgun

    return _mock_response


@pytest.fixture(scope="function")
def isolated_db_session():
    """
    Provide a completely isolated database session for unit tests.

    This fixture creates a fresh in-memory database for each test,
    ensuring complete isolation.
    """
    # Create a unique engine for this test
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        test_engine.dispose()


# =============================================================================
# IMPORT SPECIALIZED FIXTURES
# =============================================================================

# Import all specialized fixtures to make them available globally
from tests.fixtures.auth_fixtures import *  # noqa: F401, F403
from tests.fixtures.client_fixtures import *  # noqa: F401, F403

# =============================================================================
# LEGACY COMPATIBILITY FIXTURES
# =============================================================================


@pytest.fixture(scope="function")
def user_factory(isolated_db_session):
    """Factory for creating test users with different roles."""

    def _create_user(
        username="testuser",
        email="test@example.com",
        role=UserRole.CLIENT_USER,
        client_id="test-client",
        password="testpass123",
    ):
        auth_service = AuthService(isolated_db_session)
        user = User(
            username=username,
            email=email,
            full_name=f"Test User {username}",
            password_hash=auth_service.hash_password(password),
            role=role,
            status=UserStatus.ACTIVE,
            client_id=client_id if role != UserRole.SUPER_ADMIN else None,
        )
        isolated_db_session.add(user)
        isolated_db_session.commit()

        # Store password for test access
        user.password = password
        return user

    return _create_user
