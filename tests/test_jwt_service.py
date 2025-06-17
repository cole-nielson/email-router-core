"""
JWT Service Focused Tests
🔐 Detailed testing of JWT token generation, validation, and security.
"""

import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.database.models import User, UserRole, UserStatus
from app.services.auth_service import AuthService, UserTokenClaims


class TestJWTTokenSecurity:
    """Test JWT token security and edge cases."""

    @pytest.fixture
    def mock_user(self):
        """Mock user for testing."""
        user = MagicMock()
        user.id = 1
        user.username = "testuser"
        user.email = "test@example.com"
        user.role = UserRole.CLIENT_USER
        user.client_id = "test-client"
        user.status = UserStatus.ACTIVE
        return user

    @pytest.fixture
    def auth_service(self):
        """Mock auth service."""
        db = MagicMock()
        service = AuthService(db)
        return service

    def test_token_contains_required_claims(self, auth_service, mock_user):
        """Test that tokens contain all required claims."""
        result = auth_service.create_access_token(mock_user)
        claims = result["claims"]

        required_claims = [
            "sub",
            "username",
            "email",
            "role",
            "client_id",
            "permissions",
            "jti",
            "iat",
            "exp",
            "token_type",
        ]

        for claim in required_claims:
            assert claim in claims, f"Missing required claim: {claim}"

    def test_token_expiration_time(self, auth_service, mock_user):
        """Test token expiration is set correctly."""
        before_creation = datetime.utcnow()
        result = auth_service.create_access_token(mock_user)
        after_creation = datetime.utcnow()

        expires_at = result["expires_at"]

        # Should expire 30 minutes from creation
        expected_min = before_creation + timedelta(minutes=29, seconds=55)
        expected_max = after_creation + timedelta(minutes=30, seconds=5)

        assert expected_min <= expires_at <= expected_max

    def test_jwt_id_uniqueness(self, auth_service, mock_user):
        """Test that each token has a unique JWT ID."""
        token1 = auth_service.create_access_token(mock_user)
        token2 = auth_service.create_access_token(mock_user)

        jti1 = token1["claims"]["jti"]
        jti2 = token2["claims"]["jti"]

        assert jti1 != jti2, "JWT IDs should be unique"
        assert len(jti1) >= 32, "JWT ID should be sufficiently long"
        assert len(jti2) >= 32, "JWT ID should be sufficiently long"

    def test_refresh_token_differences(self, auth_service, mock_user):
        """Test differences between access and refresh tokens."""
        access_result = auth_service.create_access_token(mock_user)
        refresh_result = auth_service.create_refresh_token(mock_user)

        access_claims = access_result["claims"]
        refresh_claims = refresh_result["claims"]

        # Refresh tokens should have different structure
        assert access_claims["token_type"] == "access"
        assert refresh_claims["token_type"] == "refresh"

        # Refresh tokens should have longer expiration
        assert refresh_result["expires_at"] > access_result["expires_at"]

        # Refresh tokens should have minimal claims
        refresh_only_claims = {"sub", "username", "jti", "iat", "exp", "token_type"}
        assert set(refresh_claims.keys()) == refresh_only_claims

    def test_token_validation_with_wrong_type(self, auth_service, mock_user):
        """Test validating access token as refresh token fails."""
        # Mock database session query
        auth_service.db.query.return_value.filter.return_value.first.return_value = MagicMock(
            session_id="test_jti", is_active=True, last_used_at=datetime.utcnow()
        )
        auth_service.db.commit = MagicMock()

        access_result = auth_service.create_access_token(mock_user)
        access_token = access_result["token"]

        # Should validate as access token
        claims = auth_service.validate_token(access_token, "access")
        assert claims is not None

        # Should NOT validate as refresh token
        claims = auth_service.validate_token(access_token, "refresh")
        assert claims is None

    def test_token_validation_with_inactive_session(self, auth_service, mock_user):
        """Test that tokens with inactive sessions are rejected."""
        # Mock database to return no active session
        auth_service.db.query.return_value.filter.return_value.first.return_value = None

        access_result = auth_service.create_access_token(mock_user)
        access_token = access_result["token"]

        claims = auth_service.validate_token(access_token, "access")
        assert claims is None

    def test_malformed_token_handling(self, auth_service):
        """Test handling of malformed tokens."""
        malformed_tokens = ["not.a.jwt", "too.few.parts", "invalid.signature.token", "", None]

        for token in malformed_tokens:
            if token is not None:
                claims = auth_service.validate_token(token, "access")
                assert claims is None

    @patch("app.services.auth_service.jwt.decode")
    def test_token_validation_exception_handling(self, mock_decode, auth_service):
        """Test exception handling during token validation."""
        # Make jwt.decode raise an exception
        mock_decode.side_effect = Exception("Unexpected error")

        claims = auth_service.validate_token("any.token.here", "access")
        assert claims is None


class TestTokenRevocation:
    """Test token revocation functionality."""

    @pytest.fixture
    def auth_service_with_mock_db(self):
        """Auth service with mocked database."""
        db = MagicMock()
        service = AuthService(db)
        return service, db

    def test_revoke_single_token(self, auth_service_with_mock_db):
        """Test revoking a single token."""
        auth_service, mock_db = auth_service_with_mock_db

        # Mock session exists
        mock_session = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session

        success = auth_service.revoke_token("test_jti", "user_logout")

        assert success
        assert mock_session.is_active == False
        assert mock_session.revoked_reason == "user_logout"
        assert mock_session.revoked_at is not None
        mock_db.commit.assert_called_once()

    def test_revoke_nonexistent_token(self, auth_service_with_mock_db):
        """Test revoking a token that doesn't exist."""
        auth_service, mock_db = auth_service_with_mock_db

        # Mock no session found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        success = auth_service.revoke_token("nonexistent_jti", "test")

        assert not success

    def test_revoke_all_user_tokens(self, auth_service_with_mock_db):
        """Test revoking all tokens for a user."""
        auth_service, mock_db = auth_service_with_mock_db

        # Mock user and update query
        mock_user = MagicMock()
        mock_user.jwt_token_version = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value.filter.return_value.update.return_value = 3  # 3 tokens revoked

        count = auth_service.revoke_all_user_tokens(1, "security_action")

        assert count == 3
        assert mock_user.jwt_token_version == 2  # Incremented
        assert mock_user.jwt_refresh_token_hash is None  # Cleared
        mock_db.commit.assert_called_once()


class TestTokenRefreshSecurity:
    """Test refresh token security."""

    @pytest.fixture
    def auth_service_with_user(self):
        """Auth service with mocked user."""
        db = MagicMock()
        service = AuthService(db)

        # Mock user
        user = MagicMock()
        user.id = 1
        user.username = "testuser"
        user.role = UserRole.CLIENT_USER
        user.status = UserStatus.ACTIVE
        user.jwt_refresh_token_hash = None

        db.query.return_value.filter.return_value.first.return_value = user

        return service, user

    def test_refresh_token_hash_verification(self, auth_service_with_user):
        """Test refresh token hash verification."""
        auth_service, mock_user = auth_service_with_user

        # Create refresh token
        refresh_result = auth_service.create_refresh_token(mock_user)
        refresh_token = refresh_result["token"]

        # Mock token validation
        with patch.object(auth_service, "validate_token") as mock_validate:
            mock_validate.return_value = UserTokenClaims(
                sub="1",
                username="testuser",
                email="test@example.com",
                role="client_user",
                jti="test_jti",
                iat=int(datetime.utcnow().timestamp()),
                exp=int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                token_type="refresh",
            )

            # Set the correct hash on user
            import hashlib

            expected_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            mock_user.jwt_refresh_token_hash = expected_hash

            # Should succeed
            result = auth_service.refresh_access_token(refresh_token)
            assert result is not None
            assert result.access_token

    def test_refresh_token_hash_mismatch(self, auth_service_with_user):
        """Test refresh token with wrong hash fails."""
        auth_service, mock_user = auth_service_with_user

        with patch.object(auth_service, "validate_token") as mock_validate:
            mock_validate.return_value = UserTokenClaims(
                sub="1",
                username="testuser",
                email="test@example.com",
                role="client_user",
                jti="test_jti",
                iat=int(datetime.utcnow().timestamp()),
                exp=int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                token_type="refresh",
            )

            # Set wrong hash
            mock_user.jwt_refresh_token_hash = "wrong_hash"

            # Should fail
            result = auth_service.refresh_access_token("any.token.here")
            assert result is None


class TestPasswordSecurity:
    """Test password security features."""

    def test_password_hashing_uniqueness(self):
        """Test that same password produces different hashes."""
        auth_service = AuthService(None)  # No DB needed for hashing

        password = "testpassword123"
        hash1 = auth_service.hash_password(password)
        hash2 = auth_service.hash_password(password)

        assert hash1 != hash2, "Same password should produce different hashes (salt)"
        assert len(hash1) > 50, "Hash should be sufficiently long"
        assert len(hash2) > 50, "Hash should be sufficiently long"

    def test_password_verification_timing(self):
        """Test password verification doesn't leak timing info."""
        auth_service = AuthService(None)

        password = "testpassword123"
        correct_hash = auth_service.hash_password(password)
        wrong_hash = auth_service.hash_password("differentpassword")

        # Both verifications should take similar time (bcrypt property)
        start_time = time.time()
        result1 = auth_service.verify_password(password, correct_hash)
        time1 = time.time() - start_time

        start_time = time.time()
        result2 = auth_service.verify_password(password, wrong_hash)
        time2 = time.time() - start_time

        assert result1 == True
        assert result2 == False

        # Times should be similar (within reasonable bounds)
        # This is a property of bcrypt but timing can vary
        assert abs(time1 - time2) < 0.1, "Verification timing should be similar"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
