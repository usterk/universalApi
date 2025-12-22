"""Unit tests for authentication module."""

import pytest
from datetime import timedelta


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_string(self):
        """Password hash should be a string."""
        from app.core.auth.password import hash_password

        hashed = hash_password("mypassword")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_different_each_time(self):
        """Same password should produce different hashes (salt)."""
        from app.core.auth.password import hash_password

        hash1 = hash_password("mypassword")
        hash2 = hash_password("mypassword")
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Correct password should verify successfully."""
        from app.core.auth.password import hash_password, verify_password

        password = "mypassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Incorrect password should fail verification."""
        from app.core.auth.password import hash_password, verify_password

        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty(self):
        """Empty password should fail verification."""
        from app.core.auth.password import hash_password, verify_password

        hashed = hash_password("somepassword")
        assert verify_password("", hashed) is False

    def test_hash_password_with_special_characters(self):
        """Password with special characters should hash correctly."""
        from app.core.auth.password import hash_password, verify_password

        password = "p@$$w0rd!#%^&*()"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Tests for JWT token creation and validation."""

    def test_create_access_token(self):
        """Access token should be created successfully."""
        from uuid import UUID
        from app.core.auth.jwt import create_access_token

        user_id = UUID("12345678-1234-5678-1234-567812345678")
        token = create_access_token(user_id=user_id)
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT format: header.payload.signature
        assert token.count(".") == 2

    def test_create_access_token_with_expiry(self):
        """Access token with custom expiry should work."""
        from uuid import UUID
        from app.core.auth.jwt import create_access_token

        user_id = UUID("12345678-1234-5678-1234-567812345678")
        token = create_access_token(
            user_id=user_id,
            expires_delta=timedelta(hours=1),
        )
        assert isinstance(token, str)

    def test_decode_access_token(self):
        """Access token should decode correctly."""
        from uuid import UUID
        from app.core.auth.jwt import create_access_token, verify_token

        user_id = UUID("12345678-1234-5678-1234-567812345678")
        token = create_access_token(user_id=user_id)
        decoded_user_id = verify_token(token, token_type="access")

        assert decoded_user_id is not None
        assert decoded_user_id == user_id

    def test_decode_expired_token_returns_none(self):
        """Expired token should return None."""
        from uuid import UUID
        from app.core.auth.jwt import create_access_token, verify_token

        user_id = UUID("12345678-1234-5678-1234-567812345678")
        # Create already expired token
        token = create_access_token(
            user_id=user_id,
            expires_delta=timedelta(seconds=-1),
        )
        decoded_user_id = verify_token(token, token_type="access")

        assert decoded_user_id is None

    def test_decode_invalid_token_returns_none(self):
        """Invalid token should return None."""
        from app.core.auth.jwt import verify_token

        decoded_user_id = verify_token("invalid.token.here", token_type="access")
        assert decoded_user_id is None

    def test_create_refresh_token(self):
        """Refresh token should be created successfully."""
        from uuid import UUID
        from app.core.auth.jwt import create_refresh_token

        user_id = UUID("12345678-1234-5678-1234-567812345678")
        token = create_refresh_token(user_id=user_id)
        assert isinstance(token, str)
        assert token.count(".") == 2
