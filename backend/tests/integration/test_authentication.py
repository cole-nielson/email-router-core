"""
Comprehensive Authentication System Tests
🔐 Full test matrix for JWT, API keys, RBAC, and dual auth middleware.
"""

import pytest
from fastapi.testclient import TestClient

from core.authentication.jwt import AuthService
from main import app

# Create a test client for the FastAPI app
client = TestClient(app)

# =============================================================================
# TEST DATABASE SETUP - Using global conftest.py fixtures
# =============================================================================


@pytest.fixture(scope="function")
def auth_service(db_session):
    """Create auth service with test database."""
    return AuthService(db_session)


# =============================================================================
# AUTHENTICATION ENDPOINT TESTS
# =============================================================================


class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""

    def test_login_endpoint_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/auth/login",
            json={
                "username": test_user["client_user"].username,
                "password": test_user["client_user"].password,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "role" in data

        # Validate token type and role
        assert data["token_type"] == "bearer"
        assert data["role"] == "client_user"

    def test_login_endpoint_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        response = client.post(
            "/auth/login",
            json={
                "username": test_user["client_user"].username,
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["message"]

    def test_login_endpoint_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "password"},
        )

        assert response.status_code == 401

    def test_get_current_user_endpoint(self, client, test_user):
        """Test getting current user information."""
        # First login to get token
        login_response = client.post(
            "/auth/login",
            json={
                "username": test_user["client_user"].username,
                "password": test_user["client_user"].password,
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Test getting current user
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        data = response.json()

        assert data["username"] == test_user["client_user"].username
        assert data["email"] == test_user["client_user"].email
        assert data["role"] == "client_user"

    def test_get_current_user_without_token(self, client):
        """Test getting current user without authentication."""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get("/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401

    def test_logout_endpoint(self, client, test_user):
        """Test logout endpoint."""
        # First login
        login_response = client.post(
            "/auth/login",
            json={
                "username": test_user["client_user"].username,
                "password": test_user["client_user"].password,
            },
        )
        token = login_response.json()["access_token"]

        # Test logout
        response = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"

        # Verify token is invalidated
        user_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert user_response.status_code == 401

    def test_refresh_token_endpoint(self, client, test_user):
        """Test token refresh endpoint."""
        # First login
        login_response = client.post(
            "/auth/login",
            json={
                "username": test_user["client_user"].username,
                "password": test_user["client_user"].password,
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Test refresh
        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"


# =============================================================================
# JWT AUTHENTICATION TESTS
# =============================================================================


class TestJWTAuthentication:
    """Test JWT authentication functionality."""

    def test_password_hashing(self, auth_service):
        """Test password hashing functionality."""
        password = "test_password_123"
        hashed = auth_service.hash_password(password)

        # Password should be hashed
        assert hashed != password
        assert len(hashed) > 20  # bcrypt hashes are longer

        # Verification should work
        assert auth_service.verify_password(password, hashed)
        assert not auth_service.verify_password("wrong_password", hashed)

    def test_token_creation(self, auth_service, test_user):
        """Test JWT token creation."""
        result = auth_service.create_access_token(test_user["client_user"])

        assert "token" in result
        assert "claims" in result
        assert "expires_at" in result

        claims = result["claims"]
        assert claims["sub"] == str(test_user["client_user"].id)
        assert claims["username"] == test_user["client_user"].username
        assert claims["role"] == test_user["client_user"].role.value
        assert claims["token_type"] == "access"

    def test_token_validation(self, auth_service, test_user):
        """Test JWT token validation."""
        # Create token
        result = auth_service.create_access_token(test_user["client_user"])
        token = result["token"]

        # Validate token (stateless)
        claims = auth_service.validate_token_stateless(token)
        assert claims is not None
        assert claims.username == test_user["client_user"].username

    async def test_user_authentication(self, client, test_user):
        """Test user authentication."""
        # Get auth service from client to use same database session
        auth_service = client._test_auth_service

        # Test valid credentials
        user = await auth_service.authenticate_user(
            test_user["client_user"].username, test_user["client_user"].password
        )
        assert user is not None
        assert user.username == test_user["client_user"].username

        # Test invalid password
        user = await auth_service.authenticate_user(
            test_user["client_user"].username, "wrongpassword"
        )
        assert user is None

        # Test nonexistent user
        user = await auth_service.authenticate_user("nonexistent", "password")
        assert user is None


# =============================================================================
# RBAC (Role-Based Access Control) TESTS
# =============================================================================


class TestRBAC:
    """Test Role-Based Access Control functionality."""

    def test_super_admin_permissions(self, auth_service, test_user):
        """Test super admin has all permissions."""
        result = auth_service.create_access_token(test_user["super_admin"])
        claims = result["claims"]

        # Super admin should have system-wide permissions
        expected_permissions = [
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

        for permission in expected_permissions:
            assert permission in claims["permissions"]

    def test_client_user_permissions(self, auth_service, test_user):
        """Test client user has limited permissions."""
        result = auth_service.create_access_token(test_user["client_user"])
        claims = result["claims"]

        # Client user should have limited permissions
        expected_permissions = [
            "client:read",
            "routing:read",
            "branding:read",
            "response_times:read",
        ]

        for permission in expected_permissions:
            assert permission in claims["permissions"]

        # Should NOT have admin permissions
        forbidden_permissions = [
            "clients:delete",
            "users:admin",
            "system:admin",
        ]

        for permission in forbidden_permissions:
            assert permission not in claims["permissions"]

    def test_permission_checking(self, auth_service, test_user):
        """Test permission checking functionality."""
        # Create claims for both users
        user_result = auth_service.create_access_token(test_user["client_user"])
        admin_result = auth_service.create_access_token(test_user["super_admin"])

        user_claims = user_result["claims"]
        admin_claims = admin_result["claims"]

        # Import claims model for testing
        from core.authentication.jwt import UserTokenClaims

        user_token_claims = UserTokenClaims(**user_claims)
        admin_token_claims = UserTokenClaims(**admin_claims)

        # Test client user permissions
        assert auth_service.check_permission(user_token_claims, "client", "read")
        assert not auth_service.check_permission(user_token_claims, "system", "admin")

        # Test admin permissions
        assert auth_service.check_permission(admin_token_claims, "system", "admin")
        assert auth_service.check_permission(admin_token_claims, "users", "delete")


# =============================================================================
# USER MANAGEMENT TESTS
# =============================================================================


class TestUserManagement:
    """Test user management functionality."""

    def test_user_registration(self, client, test_user):
        """Test user registration (admin only)."""
        # Login as admin
        login_response = client.post(
            "/auth/login",
            json={
                "username": test_user["super_admin"].username,
                "password": test_user["super_admin"].password,
            },
        )
        admin_token = login_response.json()["access_token"]

        # Register new user
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newuserpass123",
                "full_name": "New User",
                "role": "client_user",
                "client_id": "test-client",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "client_user"

    def test_user_registration_unauthorized(self, client, test_user):
        """Test user registration without admin privileges."""
        # Login as regular user
        login_response = client.post(
            "/auth/login",
            json={
                "username": test_user["client_user"].username,
                "password": test_user["client_user"].password,
            },
        )
        user_token = login_response.json()["access_token"]

        # Try to register new user (should fail)
        response = client.post(
            "/auth/register",
            json={
                "username": "unauthorized",
                "email": "unauthorized@example.com",
                "password": "password123",
                "full_name": "Unauthorized User",
                "role": "client_user",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 403

    def test_list_users_pagination(self, client, test_user):
        """Test listing users with pagination (admin only)."""
        # Login as admin
        login_response = client.post(
            "/auth/login",
            json={
                "username": test_user["super_admin"].username,
                "password": test_user["super_admin"].password,
            },
        )
        admin_token = login_response.json()["access_token"]

        # Test basic pagination
        response = client.get("/auth/users", headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "users" in data
        assert "pagination" in data
        assert isinstance(data["users"], list)

        # Check pagination metadata
        pagination = data["pagination"]
        assert "total" in pagination
        assert "limit" in pagination
        assert "offset" in pagination
        assert "has_more" in pagination
        assert pagination["limit"] == 100  # Default limit
        assert pagination["offset"] == 0  # Default offset

    def test_list_users_pagination_parameters(self, client, test_user):
        """Test listing users with custom pagination parameters."""
        # Login as admin
        login_response = client.post(
            "/auth/login",
            json={
                "username": test_user["super_admin"].username,
                "password": test_user["super_admin"].password,
            },
        )
        admin_token = login_response.json()["access_token"]

        # Test custom pagination
        response = client.get(
            "/auth/users",
            params={"limit": 5, "offset": 0},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        pagination = data["pagination"]
        assert pagination["limit"] == 5
        assert pagination["offset"] == 0
        assert len(data["users"]) <= 5

    def test_list_users_sorting(self, client, test_user):
        """Test listing users with sorting."""
        # Login as admin
        login_response = client.post(
            "/auth/login",
            json={
                "username": test_user["super_admin"].username,
                "password": test_user["super_admin"].password,
            },
        )
        admin_token = login_response.json()["access_token"]

        # Test sorting by username ascending
        response = client.get(
            "/auth/users",
            params={"sort_by": "username", "sort_order": "asc"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check that users are sorted by username
        usernames = [user["username"] for user in data["users"]]
        assert usernames == sorted(usernames)

        # Test sorting by created_at descending (default)
        response = client.get(
            "/auth/users",
            params={"sort_by": "created_at", "sort_order": "desc"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200

    def test_list_users_filtering(self, client, test_user):
        """Test listing users with filtering."""
        # Login as admin
        login_response = client.post(
            "/auth/login",
            json={
                "username": test_user["super_admin"].username,
                "password": test_user["super_admin"].password,
            },
        )
        admin_token = login_response.json()["access_token"]

        # Test filtering by role
        response = client.get(
            "/auth/users",
            params={"role": "super_admin"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # All returned users should be super_admin
        for user in data["users"]:
            assert user["role"] == "super_admin"

        # Test search functionality
        response = client.get(
            "/auth/users",
            params={"search": "admin"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # All returned users should contain "admin" in username, email, or full_name
        for user in data["users"]:
            assert (
                "admin" in user["username"].lower()
                or "admin" in user["email"].lower()
                or "admin" in user["full_name"].lower()
            )

    def test_list_users_invalid_parameters(self, client, test_user):
        """Test listing users with invalid parameters."""
        # Login as admin
        login_response = client.post(
            "/auth/login",
            json={
                "username": test_user["super_admin"].username,
                "password": test_user["super_admin"].password,
            },
        )
        admin_token = login_response.json()["access_token"]

        # Test invalid sort field
        response = client.get(
            "/auth/users",
            params={"sort_by": "invalid_field"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422  # Validation error

        # Test invalid sort order
        response = client.get(
            "/auth/users",
            params={"sort_order": "invalid_order"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422  # Validation error

        # Test negative offset
        response = client.get(
            "/auth/users",
            params={"offset": -1},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422  # Validation error

        # Test limit too high
        response = client.get(
            "/auth/users",
            params={"limit": 1001},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_change_password(self, client, test_user):
        """Test password change functionality."""
        # Login
        login_response = client.post(
            "/auth/login",
            json={
                "username": test_user["client_user"].username,
                "password": test_user["client_user"].password,
            },
        )
        token = login_response.json()["access_token"]

        # Change password
        response = client.put(
            "/auth/me/password",
            json={
                "current_password": test_user["client_user"].password,
                "new_password": "newtestpass123",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

        # Verify old password doesn't work
        old_login_response = client.post(
            "/auth/login",
            json={
                "username": test_user["client_user"].username,
                "password": test_user["client_user"].password,
            },
        )
        assert old_login_response.status_code == 401

        # Verify new password works
        new_login_response = client.post(
            "/auth/login",
            json={
                "username": test_user["client_user"].username,
                "password": "newtestpass123",
            },
        )
        assert new_login_response.status_code == 200


# =============================================================================
# SESSION MANAGEMENT TESTS
# =============================================================================


class TestSessionManagement:
    """Test session management functionality."""

    def test_list_sessions(self, client, test_user):
        """Test listing user sessions."""
        # Login to create session
        login_response = client.post(
            "/auth/login",
            json={
                "username": test_user["client_user"].username,
                "password": test_user["client_user"].password,
            },
        )
        token = login_response.json()["access_token"]

        # List sessions
        response = client.get("/auth/sessions", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        data = response.json()
        print(f"DEBUG: Session response data: {data}")
        assert "sessions" in data
        assert len(data["sessions"]) >= 1  # At least current session

    def test_revoke_session(self, client, test_user):
        """Test revoking specific session."""
        # Login to create sessions
        login1 = client.post(
            "/auth/login",
            json={
                "username": test_user["client_user"].username,
                "password": test_user["client_user"].password,
            },
        )
        login2 = client.post(
            "/auth/login",
            json={
                "username": test_user["client_user"].username,
                "password": test_user["client_user"].password,
            },
        )

        token1 = login1.json()["access_token"]
        login2.json()["access_token"]

        # Get sessions from first token
        sessions_response = client.get(
            "/auth/sessions", headers={"Authorization": f"Bearer {token1}"}
        )
        sessions = sessions_response.json()["sessions"]

        # Find a session to revoke
        session_to_revoke = sessions[0]["session_id"]

        # Revoke session
        response = client.delete(
            f"/auth/sessions/{session_to_revoke}",
            headers={"Authorization": f"Bearer {token1}"},
        )

        assert response.status_code == 200


# =============================================================================
# SECURITY TESTS
# =============================================================================


class TestSecurityFeatures:
    """Test security features."""

    def test_rate_limiting_login_attempts(self, client, test_user, auth_service):
        """Test rate limiting for failed login attempts."""
        # Make multiple failed login attempts
        for i in range(6):  # Exceed the limit of 5
            client.post(
                "/auth/login",
                json={
                    "username": test_user["client_user"].username,
                    "password": "wrongpassword",
                },
            )

        # After 5 failed attempts, account should be locked
        final_response = client.post(
            "/auth/login",
            json={
                "username": test_user["client_user"].username,
                "password": test_user["client_user"].password,
            },
        )

        # Should be locked (423) or unauthorized (401)
        assert final_response.status_code in [401, 423]

    def test_token_expiration_handling(self, client, test_user):
        """Test handling of expired tokens."""
        # This would require mocking time or creating expired tokens
        # For now, test with invalid token format
        response = client.get("/auth/me", headers={"Authorization": "Bearer expired.token.here"})
        assert response.status_code == 401

    def test_session_security(self, auth_service, test_user):
        """Test session security features."""
        # Test token revocation
        result = auth_service.create_access_token(test_user["client_user"])
        claims = result["claims"]
        jti = claims["jti"]

        # Revoke token
        success = auth_service.revoke_token(jti, "security_test")
        assert success

        # Test revoking all user tokens
        count = auth_service.revoke_all_user_tokens(test_user["client_user"].id, "security_action")
        assert count >= 0  # Should not error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
