"""FastAPI dependencies for authentication."""

from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.auth.jwt import verify_token
from app.core.auth.api_keys import hash_api_key
from app.core.users.models import User
from app.core.sources.models import Source

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> User:
    """
    Get current user from JWT token.
    Raises 401 if not authenticated.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = verify_token(credentials.credentials, token_type="access")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current user if active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Get current user if superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


async def get_source_from_api_key(
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[str | None, Depends(api_key_header)] = None,
) -> Source:
    """
    Get source from API key.
    Raises 401 if not authenticated.
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    key_hash = hash_api_key(api_key)

    result = await db.execute(
        select(Source).where(
            Source.api_key_hash == key_hash,
            Source.is_active == True,
        )
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return source


async def get_user_or_source(
    db: Annotated[AsyncSession, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    api_key: Annotated[str | None, Depends(api_key_header)] = None,
) -> User | Source:
    """
    Get either user (from JWT) or source (from API key).
    Allows both authentication methods.
    """
    # Try JWT first
    if credentials is not None:
        user_id = verify_token(credentials.credentials, token_type="access")
        if user_id is not None:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user is not None and user.is_active:
                return user

    # Try API key
    if api_key is not None:
        key_hash = hash_api_key(api_key)
        result = await db.execute(
            select(Source).where(
                Source.api_key_hash == key_hash,
                Source.is_active == True,
            )
        )
        source = result.scalar_one_or_none()
        if source is not None:
            return source

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )


async def get_user_from_query_token(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: str | None = Query(None, description="JWT access token"),
) -> User:
    """
    Get current user from query parameter token.
    Used for SSE endpoints where EventSource doesn't support custom headers.
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token required",
        )

    user_id = verify_token(token, token_type="access")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentSuperuser = Annotated[User, Depends(get_current_superuser)]
CurrentSource = Annotated[Source, Depends(get_source_from_api_key)]
CurrentUserOrSource = Annotated[User | Source, Depends(get_user_or_source)]
CurrentUserFromQueryToken = Annotated[User, Depends(get_user_from_query_token)]
