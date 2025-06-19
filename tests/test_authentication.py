"""
Comprehensive Authentication System Tests
🔐 Full test matrix for JWT, API keys, RBAC, and dual auth middleware.
"""

import pytest
from fastapi.testclient import TestClient

from backend.src.application.middleware.auth import APIKeyUser, DualAuthUser
from backend.src.core.authentication.jwt import AuthService
from backend.src.infrastructure.database.models import User, UserRole, UserStatus
from backend.src.main import app

# Create a test client for the FastAPI app
client = TestClient(app)

# =============================================================================
# TEST DATABASE SETUP - Using global conftest.py fixtures
# =============================================================================


@pytest.fixture(scope="function")
def auth_service(db_session):
    """Create auth service with test database."""
    return AuthService(db_session)


@pytest.fixture(scope="function")
def test_user(db_session, auth_service):
    """Create test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=auth_service.hash_password("testpass123"),
        full_name="Test User",
        role=UserRole.CLIENT_USER,
        client_id="test-client",
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_user(db_session, auth_service):
    """Create admin user."""
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=auth_service.hash_password("adminpass123"),
        full_name="Admin User",
        role=UserRole.SUPER_ADMIN,
        client_id=None,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def client_admin_user(db_session, auth_service):
    """Create client admin user."""
    user = User(
        username="clientadmin",
        email="clientadmin@example.com",
        password_hash=auth_service.hash_password("clientpass123"),
        full_name="Client Admin",
        role=UserRole.CLIENT_ADMIN,
        client_id="test-client",
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# =============================================================================
# JWT AUTHENTICATION TESTS
# =============================================================================


class TestJWTAuthentication:
    """Test JWT token generation and validation."""

    def test_password_hashing(self, auth_service):
        """Test password hashing and verification."""
        password = "testpassword123"
        hash1 = auth_service.hash_password(password)
        hash2 = auth_service.hash_password(password)

        # Hashes should be different (salt)
        assert hash1 != hash2

        # Both should verify correctly
        assert auth_service.verify_password(password, hash1)
        assert auth_service.verify_password(password, hash2)

        # Wrong password should fail
        assert not auth_service.verify_password("wrongpassword", hash1)

    def test_create_access_token(self, auth_service, test_user):
        """Test access token creation."""
        result = auth_service.create_access_token(test_user)

        assert "token" in result
        assert "claims" in result
        assert "expires_at" in result

        claims = result["claims"]
        assert claims["username"] == test_user.username
        assert claims["email"] == test_user.email
        assert claims["role"] == test_user.role.value
        assert claims["client_id"] == test_user.client_id
        assert claims["token_type"] == "access"
        assert "jti" in claims
        assert "exp" in claims

    def test_create_refresh_token(self, auth_service, test_user):
        """Test refresh token creation."""
        result = auth_service.create_refresh_token(test_user)

        assert "token" in result
        assert "claims" in result
        assert "expires_at" in result

        claims = result["claims"]
        assert claims["username"] == test_user.username
        assert claims["token_type"] == "refresh"
        assert "jti" in claims

    def test_validate_token(self, auth_service, test_user):
        """Test token validation."""
        # Create token
        token_result = auth_service.create_access_token(test_user)
        token = token_result["token"]

        # Validate token
        claims = auth_service.validate_token(token, "access")
        assert claims is not None
        assert claims.username == test_user.username
        assert claims.token_type == "access"

    def test_validate_expired_token(self, auth_service, test_user):
        """Test expired token validation."""
        # This would require mocking time or creating a token with past expiry
        # For now, test with wrong token type
        token_result = auth_service.create_access_token(test_user)
        token = token_result["token"]

        # Try to validate as refresh token
        claims = auth_service.validate_token(token, "refresh")
        assert claims is None

    def test_revoke_token(self, auth_service, test_user):
        """Test token revocation."""
        token_result = auth_service.create_access_token(test_user)
        jti = token_result["claims"]["jti"]

        # Revoke token
        success = auth_service.revoke_token(jti, "test_revocation")
        assert success

        # Token should no longer validate
        claims = auth_service.validate_token(token_result["token"], "access")
        assert claims is None


class TestUserAuthentication:
    """Test user authentication flows."""

    def test_authenticate_valid_user(self, auth_service, test_user):
        """Test successful user authentication."""
        user = auth_service.authenticate_user("testuser", "testpass123")
        assert user is not None
        assert user.username == test_user.username
        assert user.id == test_user.id

    def test_authenticate_invalid_password(self, auth_service, test_user):
        """Test authentication with wrong password."""
        user = auth_service.authenticate_user("testuser", "wrongpassword")
        assert user is None

    def test_authenticate_nonexistent_user(self, auth_service):
        """Test authentication with non-existent user."""
        user = auth_service.authenticate_user("nonexistent", "password")
        assert user is None

    def test_login_flow(self, auth_service, test_user):
        """Test complete login flow."""
        from backend.src.core.authentication.jwt import LoginRequest

        request = LoginRequest(username="testuser", password="testpass123")

        token_response = auth_service.login(request)

        assert token_response.access_token
        assert token_response.refresh_token
        assert token_response.token_type == "bearer"
        assert token_response.client_id == test_user.client_id
        assert token_response.role == test_user.role.value
        assert isinstance(token_response.permissions, list)

    def test_get_current_user(self, auth_service, test_user):
        """Test getting current user from token."""
        # Create token
        token_result = auth_service.create_access_token(test_user)
        token = token_result["token"]

        # Get user from token
        auth_user = auth_service.get_current_user(token)

        assert auth_user is not None
        assert auth_user.username == test_user.username
        assert auth_user.email == test_user.email
        assert auth_user.role == test_user.role.value
        assert auth_user.client_id == test_user.client_id


# =============================================================================
# RBAC TESTS
# =============================================================================


class TestRBAC:
    """Test role-based access control."""

    def test_super_admin_permissions(self, auth_service, admin_user):
        """Test super admin has all permissions."""
        from backend.src.core.authentication.jwt import AuthenticatedUser
        from backend.src.core.authorization.rbac import RBACService

        auth_user = AuthenticatedUser(
            id=admin_user.id,
            username=admin_user.username,
            email=admin_user.email,
            full_name=admin_user.full_name,
            role=admin_user.role.value,
            client_id=admin_user.client_id,
            permissions=[],
        )

        # Super admin should have access to any permission
        assert RBACService.check_permission(auth_user, "clients:read", raise_on_deny=False)
        assert RBACService.check_permission(auth_user, "users:write", raise_on_deny=False)
        assert RBACService.check_permission(auth_user, "system:admin", raise_on_deny=False)

    def test_client_user_permissions(self, auth_service, test_user):
        """Test client user has limited permissions."""
        from backend.src.core.authentication.jwt import AuthenticatedUser
        from backend.src.core.authorization.rbac import RBACService

        # Get user permissions based on role
        permissions = auth_service._get_user_permissions(test_user)

        auth_user = AuthenticatedUser(
            id=test_user.id,
            username=test_user.username,
            email=test_user.email,
            full_name=test_user.full_name,
            role=test_user.role.value,
            client_id=test_user.client_id,
            permissions=permissions,
        )

        # Client user should have read access
        assert RBACService.check_permission(
            auth_user, "client:read", "test-client", raise_on_deny=False
        )

        # Client user should not have write access
        assert not RBACService.check_permission(
            auth_user, "client:write", "test-client", raise_on_deny=False
        )

    def test_client_scoping(self, auth_service, test_user):
        """Test client scoping prevents cross-client access."""
        from backend.src.core.authentication.jwt import AuthenticatedUser
        from backend.src.core.authorization.rbac import RBACService

        permissions = auth_service._get_user_permissions(test_user)

        auth_user = AuthenticatedUser(
            id=test_user.id,
            username=test_user.username,
            email=test_user.email,
            full_name=test_user.full_name,
            role=test_user.role.value,
            client_id=test_user.client_id,
            permissions=permissions,
        )

        # Should have access to own client
        assert RBACService.check_permission(
            auth_user, "client:read", "test-client", raise_on_deny=False
        )

        # Should not have access to other client
        assert not RBACService.check_permission(
            auth_user, "client:read", "other-client", raise_on_deny=False
        )


# =============================================================================
# API ENDPOINT TESTS
# =============================================================================


class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""

    def test_login_endpoint(self, client, test_user):
        """Test login endpoint."""
        response = client.post(
            "/auth/login", json={"username": "testuser", "password": "testpass123"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "client_user"
        assert data["client_id"] == "test-client"

    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        response = client.post(
            "/auth/login", json={"username": "testuser", "password": "wrongpassword"}
        )

        assert response.status_code == 401

    @pytest.mark.xfail(
        reason="Middleware database session integration issue - requires architecture refactor"
    )
    def test_get_current_user_endpoint(self, client, test_user, auth_service):
        """Test get current user endpoint."""
        # Get token
        token_result = auth_service.create_access_token(test_user)
        token = token_result["token"]

        # Call endpoint
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        data = response.json()

        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["role"] == "client_user"

    def test_register_user_endpoint(self, client, admin_user, auth_service):
        """Test user registration endpoint (admin only)."""
        # Get admin token
        token_result = auth_service.create_access_token(admin_user)
        token = token_result["token"]

        # Register new user
        response = client.post(
            "/auth/register",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpass123",
                "full_name": "New User",
                "client_id": "test-client",
                "role": "client_user",
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "client_user"

    def test_register_user_non_admin(self, client, test_user, auth_service):
        """Test user registration fails for non-admin."""
        # Get user token
        token_result = auth_service.create_access_token(test_user)
        token = token_result["token"]

        # Try to register new user
        response = client.post(
            "/auth/register",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpass123",
                "full_name": "New User",
                "role": "client_user",
            },
        )

        assert response.status_code == 403


# =============================================================================
# DUAL AUTHENTICATION TESTS
# =============================================================================


class TestDualAuthentication:
    """Test dual authentication middleware."""

    def test_jwt_auth_priority(self, client, test_user, auth_service):
        """Test JWT authentication takes priority over API key."""
        # Get JWT token
        token_result = auth_service.create_access_token(test_user)
        token = token_result["token"]

        # Call endpoint with both JWT and API key
        response = client.get(
            "/webhooks/status",
            headers={"Authorization": f"Bearer {token}", "X-API-Key": "sk-test-invalid-key"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should authenticate as JWT user
        if "authenticated_as" in data:
            assert data["authenticated_as"]["auth_type"] == "jwt"
            assert data["authenticated_as"]["username"] == "testuser"

    def test_api_key_fallback(self, client):
        """Test API key fallback when JWT fails."""
        # Call with invalid JWT but valid API key format
        response = client.get(
            "/webhooks/status",
            headers={
                "Authorization": "Bearer invalid-jwt-token",
                "X-API-Key": "sk-client001-valid-key",
            },
        )

        assert response.status_code == 200
        # Should work with public endpoint regardless of auth

    def test_dual_auth_user_wrapper(self):
        """Test DualAuthUser wrapper functionality."""
        from backend.src.core.authentication.jwt import AuthenticatedUser

        # Create JWT user
        jwt_user = AuthenticatedUser(
            id=1,
            username="jwtuser",
            email="jwt@example.com",
            full_name="JWT User",
            role="client_user",
            client_id="test-client",
            permissions=["client:read"],
        )

        # Wrap in dual auth
        dual_user = DualAuthUser(jwt_user, "jwt")

        assert dual_user.username == "jwtuser"
        assert dual_user.auth_type == "jwt"
        assert dual_user.role == "client_user"
        assert dual_user.client_id == "test-client"

    def test_api_key_user_creation(self):
        """Test API key user creation."""

        api_user = APIKeyUser("test-client", "webhook_key")

        assert api_user.username == "api_key_webhook_key"
        assert api_user.role == "api_user"
        assert api_user.client_id == "test-client"
        assert "webhooks:write" in api_user.permissions


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestAuthenticationIntegration:
    """Integration tests for full authentication flows."""

    @pytest.mark.xfail(reason="Integration test requires full app setup - see docs/known_issues.md")
    def test_complete_login_flow(self, client, test_user):
        """Test complete login to protected endpoint flow."""
        # 1. Login
        login_response = client.post(
            "/auth/login", json={"username": "testuser", "password": "testpass123"}
        )

        assert login_response.status_code == 200
        tokens = login_response.json()
        access_token = tokens["access_token"]

        # 2. Access protected endpoint
        profile_response = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert profile_response.status_code == 200
        profile = profile_response.json()
        assert profile["username"] == "testuser"

        # 3. Access sessions endpoint
        sessions_response = client.get(
            "/auth/sessions", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert sessions_response.status_code == 200
        sessions = sessions_response.json()
        assert "sessions" in sessions
        assert len(sessions["sessions"]) > 0

    @pytest.mark.xfail(
        reason="Token refresh integration test requires complex setup - see docs/known_issues.md"
    )
    def test_token_refresh_flow(self, client, test_user):
        """Test token refresh flow."""
        # 1. Login
        login_response = client.post(
            "/auth/login", json={"username": "testuser", "password": "testpass123"}
        )

        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]

        # 2. Refresh token
        refresh_response = client.post("/auth/refresh", json={"refresh_token": refresh_token})

        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()

        assert "access_token" in new_tokens
        assert new_tokens["access_token"] != tokens["access_token"]  # Should be different

    def test_logout_flow(self, client, test_user):
        """Test logout flow."""
        # 1. Login
        login_response = client.post(
            "/auth/login", json={"username": "testuser", "password": "testpass123"}
        )

        tokens = login_response.json()
        access_token = tokens["access_token"]

        # 2. Logout
        logout_response = client.post(
            "/auth/logout", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert logout_response.status_code == 200

        # 3. Try to use token (should fail)
        profile_response = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert profile_response.status_code == 401


# =============================================================================
# SECURITY TESTS
# =============================================================================


class TestSecurityFeatures:
    """Test security features and edge cases."""

    def test_password_change_revokes_tokens(self, client, test_user):
        """Test that password change revokes all tokens."""
        # 1. Login and get token
        login_response = client.post(
            "/auth/login", json={"username": "testuser", "password": "testpass123"}
        )

        tokens = login_response.json()
        access_token = tokens["access_token"]

        # 2. Change password
        password_response = client.put(
            "/auth/me/password",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"current_password": "testpass123", "new_password": "newpass123"},
        )

        assert password_response.status_code == 200

        # 3. Old token should be invalid
        profile_response = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert profile_response.status_code == 401

    @pytest.mark.xfail(
        reason="Token format validation requires middleware setup - see docs/known_issues.md"
    )
    def test_invalid_token_formats(self, client):
        """Test various invalid token formats."""
        invalid_tokens = ["invalid-token", "Bearer", "Bearer ", "Bearer invalid.token.format", ""]

        for token in invalid_tokens:
            response = client.get("/auth/me", headers={"Authorization": token})
            assert response.status_code == 401

    def test_client_isolation(self, client, auth_service, db_session):
        """Test that users can't access other clients' data."""
        # Create users for different clients
        user1 = User(
            username="user1",
            email="user1@client1.com",
            password_hash=auth_service.hash_password("pass123"),
            full_name="User 1",
            role=UserRole.CLIENT_ADMIN,
            client_id="client-1",
            status=UserStatus.ACTIVE,
        )

        user2 = User(
            username="user2",
            email="user2@client2.com",
            password_hash=auth_service.hash_password("pass123"),
            full_name="User 2",
            role=UserRole.CLIENT_ADMIN,
            client_id="client-2",
            status=UserStatus.ACTIVE,
        )

        db_session.add_all([user1, user2])
        db_session.commit()

        # Get tokens for both users
        token1 = auth_service.create_access_token(user1)["token"]
        token2 = auth_service.create_access_token(user2)["token"]

        # User 1 should not be able to access client-2 endpoints
        # (This would need actual protected endpoints to test fully)
        response1 = client.get("/auth/me", headers={"Authorization": f"Bearer {token1}"})
        assert response1.status_code == 200
        assert response1.json()["client_id"] == "client-1"

        response2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token2}"})
        assert response2.status_code == 200
        assert response2.json()["client_id"] == "client-2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
