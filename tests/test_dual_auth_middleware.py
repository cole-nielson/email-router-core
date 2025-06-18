"""
Dual Authentication Middleware Tests
🔐 Test JWT + API key dual authentication system.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.middleware.dual_auth import (
    APIKeyUser,
    DualAuthMiddleware,
    DualAuthUser,
    extract_api_key_from_request,
    extract_client_from_api_key,
    get_auth_type_for_endpoint,
    get_dual_auth_user,
    require_api_key_only,
    require_dual_auth,
    require_jwt_only,
)
from app.services.auth_service import AuthenticatedUser


class TestAPIKeyExtraction:
    """Test API key extraction from requests."""

    def test_extract_from_x_api_key_header(self):
        """Test extracting API key from X-API-Key header."""
        request = MagicMock()
        request.headers.get.side_effect = lambda key: {
            "X-API-Key": "sk-test-key-123",
            "Authorization": None,
        }.get(key)

        api_key = extract_api_key_from_request(request)
        assert api_key == "sk-test-key-123"

    def test_extract_from_authorization_header(self):
        """Test extracting API key from Authorization Bearer header."""
        request = MagicMock()
        request.headers.get.side_effect = lambda key: {
            "X-API-Key": None,
            "Authorization": "Bearer sk-test-key-456",
        }.get(key)

        api_key = extract_api_key_from_request(request)
        assert api_key == "sk-test-key-456"

    def test_extract_no_api_key(self):
        """Test when no API key is present."""
        request = MagicMock()
        request.headers.get.return_value = None

        api_key = extract_api_key_from_request(request)
        assert api_key is None

    def test_extract_jwt_token_not_api_key(self):
        """Test that JWT tokens are not extracted as API keys."""
        request = MagicMock()
        request.headers.get.side_effect = lambda key: {
            "X-API-Key": None,
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.jwt.token",
        }.get(key)

        api_key = extract_api_key_from_request(request)
        assert api_key is None


class TestClientExtraction:
    """Test client ID extraction from API keys."""

    def test_extract_valid_client_id(self):
        """Test extracting valid client ID from API key."""
        api_key = "sk-client001-abc123def456"
        client_id = extract_client_from_api_key(api_key)
        assert client_id == "client-001-cole-nielson"

    def test_extract_test_client(self):
        """Test extracting test client ID."""
        api_key = "sk-test-xyz789"
        client_id = extract_client_from_api_key(api_key)
        assert client_id == "test-client"

    def test_extract_invalid_format(self):
        """Test invalid API key format returns None."""
        invalid_keys = ["invalid-key", "sk-", "sk-unknown-client", "not-an-api-key", ""]

        for key in invalid_keys:
            client_id = extract_client_from_api_key(key)
            assert client_id is None


class TestAPIKeyUser:
    """Test APIKeyUser functionality."""

    def test_api_key_user_creation(self):
        """Test creating API key user."""
        user = APIKeyUser("test-client", "webhook_key")

        assert user.id == 0
        assert user.username == "api_key_webhook_key"
        assert user.email == "api_webhook_key@test-client.local"
        assert user.full_name == "API Key (webhook_key)"
        assert user.role == "api_user"
        assert user.client_id == "test-client"
        assert user.auth_type == "api_key"
        assert "webhooks:write" in user.permissions
        assert "client:read" in user.permissions

    def test_api_key_user_rate_limiting(self):
        """Test API key user rate limiting tier."""
        user = APIKeyUser("test-client")
        assert user.rate_limit_tier == "api_standard"


class TestDualAuthUser:
    """Test DualAuthUser wrapper."""

    def test_wrap_jwt_user(self):
        """Test wrapping JWT authenticated user."""
        jwt_user = AuthenticatedUser(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role="client_user",
            client_id="test-client",
            permissions=["client:read"],
        )

        dual_user = DualAuthUser(jwt_user, "jwt")

        assert dual_user.id == 1
        assert dual_user.username == "testuser"
        assert dual_user.email == "test@example.com"
        assert dual_user.role == "client_user"
        assert dual_user.client_id == "test-client"
        assert dual_user.auth_type == "jwt"
        assert dual_user.underlying_user == jwt_user

    def test_wrap_api_key_user(self):
        """Test wrapping API key user."""
        api_user = APIKeyUser("test-client", "webhook")
        dual_user = DualAuthUser(api_user, "api_key")

        assert dual_user.auth_type == "api_key"
        assert dual_user.role == "api_user"
        assert dual_user.client_id == "test-client"
        assert dual_user.underlying_user == api_user


class TestEndpointAuthStrategy:
    """Test authentication strategy selection per endpoint."""

    def test_webhook_endpoints(self):
        """Test webhook endpoints prefer API key auth."""
        webhook_paths = ["/webhooks/mailgun/inbound", "/webhooks/test", "/health", "/metrics"]

        for path in webhook_paths:
            strategy = get_auth_type_for_endpoint(path)
            assert strategy == "api_key_preferred"

    def test_auth_endpoints(self):
        """Test auth endpoints are public."""
        auth_paths = ["/auth/login", "/auth/refresh", "/auth/logout"]

        for path in auth_paths:
            strategy = get_auth_type_for_endpoint(path)
            assert strategy == "public"

    def test_config_endpoints(self):
        """Test config endpoints require JWT."""
        config_paths = ["/api/v2/clients/test", "/api/v2/config/branding"]

        for path in config_paths:
            strategy = get_auth_type_for_endpoint(path)
            assert strategy == "jwt_required"

    def test_default_endpoints(self):
        """Test default endpoints use dual auth."""
        default_paths = ["/api/v1/status", "/some/other/endpoint"]

        for path in default_paths:
            strategy = get_auth_type_for_endpoint(path)
            assert strategy == "dual_auth"


class TestDualAuthDependencies:
    """Test dual authentication dependency functions."""

    @pytest.mark.asyncio
    async def test_get_dual_auth_user_jwt_success(self):
        """Test getting user via JWT authentication."""
        # Mock request
        request = MagicMock()
        request.headers.get.return_value = None

        # Mock credentials
        credentials = MagicMock()
        credentials.scheme = "bearer"
        credentials.credentials = "valid.jwt.token"

        # Mock JWT user
        jwt_user = AuthenticatedUser(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role="client_user",
            client_id="test-client",
            permissions=["client:read"],
        )

        with patch("app.middleware.dual_auth.get_current_user_from_token", return_value=jwt_user):
            user = await get_dual_auth_user(request, credentials)

            assert user is not None
            assert user.auth_type == "jwt"
            assert user.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_dual_auth_user_api_key_fallback(self):
        """Test falling back to API key when JWT fails."""
        # Mock request with API key
        request = MagicMock()
        request.headers.get.side_effect = lambda key: {"X-API-Key": "sk-client001-test123"}.get(key)

        # Mock invalid JWT credentials
        credentials = MagicMock()
        credentials.scheme = "bearer"
        credentials.credentials = "invalid.jwt.token"

        with patch(
            "app.middleware.dual_auth.get_current_user_from_token",
            side_effect=Exception("Invalid JWT"),
        ):
            user = await get_dual_auth_user(request, credentials)

            assert user is not None
            assert user.auth_type == "api_key"
            assert user.role == "api_user"
            assert user.client_id == "client-001-cole-nielson"

    @pytest.mark.asyncio
    async def test_get_dual_auth_user_no_auth(self):
        """Test when no authentication is provided."""
        request = MagicMock()
        request.headers.get.return_value = None

        user = await get_dual_auth_user(request, None)
        assert user is None

    @pytest.mark.asyncio
    async def test_require_dual_auth_success(self):
        """Test require_dual_auth dependency with valid user."""
        user = DualAuthUser(APIKeyUser("test-client"), "api_key")

        result = await require_dual_auth(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_require_dual_auth_failure(self):
        """Test require_dual_auth dependency with no user."""
        with pytest.raises(Exception):  # Should raise HTTPException
            await require_dual_auth(None)

    @pytest.mark.asyncio
    async def test_require_jwt_only_success(self):
        """Test JWT-only requirement with JWT user."""
        jwt_user = AuthenticatedUser(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role="client_user",
            client_id="test-client",
            permissions=["client:read"],
        )
        dual_user = DualAuthUser(jwt_user, "jwt")

        result = await require_jwt_only(dual_user)
        assert result == dual_user

    @pytest.mark.asyncio
    async def test_require_jwt_only_failure_with_api_key(self):
        """Test JWT-only requirement fails with API key user."""
        api_user = APIKeyUser("test-client")
        dual_user = DualAuthUser(api_user, "api_key")

        with pytest.raises(Exception):  # Should raise HTTPException
            await require_jwt_only(dual_user)

    @pytest.mark.asyncio
    async def test_require_api_key_only_success(self):
        """Test API key-only requirement with API key user."""
        api_user = APIKeyUser("test-client")
        dual_user = DualAuthUser(api_user, "api_key")

        result = await require_api_key_only(dual_user)
        assert result == dual_user

    @pytest.mark.asyncio
    async def test_require_api_key_only_failure_with_jwt(self):
        """Test API key-only requirement fails with JWT user."""
        jwt_user = AuthenticatedUser(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role="client_user",
            client_id="test-client",
            permissions=["client:read"],
        )
        dual_user = DualAuthUser(jwt_user, "jwt")

        with pytest.raises(Exception):  # Should raise HTTPException
            await require_api_key_only(dual_user)


class TestDualAuthMiddleware:
    """Test dual authentication middleware."""

    def test_middleware_initialization(self):
        """Test middleware initialization."""
        from unittest.mock import MagicMock

        mock_app = MagicMock()
        middleware = DualAuthMiddleware(mock_app)
        assert middleware.auth_cache == {}

    @pytest.mark.asyncio
    async def test_middleware_public_endpoint(self):
        """Test middleware skips auth for public endpoints."""
        middleware = DualAuthMiddleware()

        # Mock request for public endpoint
        request = MagicMock()
        request.url.path = "/health"

        # Mock call_next
        call_next = AsyncMock()
        response = MagicMock()
        call_next.return_value = response

        result = await middleware(request, call_next)

        assert result == response
        call_next.assert_called_once_with(request)
        # Should not have auth state
        assert not hasattr(request.state, "current_user")

    @pytest.mark.asyncio
    async def test_middleware_jwt_auth_success(self):
        """Test middleware JWT authentication success."""
        middleware = DualAuthMiddleware()

        # Mock request with JWT
        request = MagicMock()
        request.url.path = "/api/v1/status"
        request.headers.get.side_effect = lambda key: {
            "Authorization": "Bearer valid.jwt.token",
            "X-API-Key": None,
        }.get(key)
        request.state = MagicMock()

        # Mock JWT user
        jwt_user = AuthenticatedUser(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role="client_user",
            client_id="test-client",
            permissions=["client:read"],
        )

        # Mock call_next
        call_next = AsyncMock()
        response = MagicMock()
        call_next.return_value = response

        with patch.object(
            middleware, "_try_jwt_auth", return_value=DualAuthUser(jwt_user, "jwt")
        ) as mock_jwt:
            result = await middleware(request, call_next)

            assert result == response
            mock_jwt.assert_called_once_with(request)
            # Should have auth state
            assert request.state.current_user.username == "testuser"
            assert request.state.auth_type == "jwt"

    @pytest.mark.asyncio
    async def test_middleware_api_key_fallback(self):
        """Test middleware API key fallback."""
        middleware = DualAuthMiddleware()

        # Mock request with API key
        request = MagicMock()
        request.url.path = "/webhooks/mailgun/inbound"
        request.state = MagicMock()

        # Mock API key user
        api_user = APIKeyUser("test-client")
        dual_api_user = DualAuthUser(api_user, "api_key")

        # Mock call_next
        call_next = AsyncMock()
        response = MagicMock()
        call_next.return_value = response

        with patch.object(middleware, "_try_jwt_auth", return_value=None) as mock_jwt:
            with patch.object(
                middleware, "_try_api_key_auth", return_value=dual_api_user
            ) as mock_api:
                result = await middleware(request, call_next)

                assert result == response
                mock_jwt.assert_called_once_with(request)
                mock_api.assert_called_once_with(request)
                # Should have auth state
                assert request.state.current_user.role == "api_user"
                assert request.state.auth_type == "api_key"

    @pytest.mark.asyncio
    async def test_middleware_no_auth(self):
        """Test middleware with no authentication."""
        middleware = DualAuthMiddleware()

        # Mock request with no auth
        request = MagicMock()
        request.url.path = "/api/v1/status"
        request.state = MagicMock()

        # Mock call_next
        call_next = AsyncMock()
        response = MagicMock()
        call_next.return_value = response

        with patch.object(middleware, "_try_jwt_auth", return_value=None):
            with patch.object(middleware, "_try_api_key_auth", return_value=None):
                result = await middleware(request, call_next)

                assert result == response
                # Should not have auth state
                assert not hasattr(request.state, "current_user")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
