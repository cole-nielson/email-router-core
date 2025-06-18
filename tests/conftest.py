"""
Global fixtures for the Email Router test suite.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path to allow module imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.models import Base, User, UserRole, UserStatus
from app.main import app
from app.services.auth_service import AuthService
from app.database.connection import get_db

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create the database and tables for the entire test session."""
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
    
    return {
        "Authorization": f"Bearer {access_token}",
        "X-API-Key": api_key
    } 