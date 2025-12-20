"""JWT token utilities."""

from datetime import datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt

from app.config import settings


def create_access_token(
    user_id: UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
    }

    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    user_id: UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """Create JWT refresh token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str, token_type: str = "access") -> UUID | None:
    """
    Verify JWT token and return user_id.
    Returns None if token is invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        # Check token type
        if payload.get("type") != token_type:
            return None

        return UUID(user_id)

    except JWTError:
        return None
