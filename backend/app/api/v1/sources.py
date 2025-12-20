"""Sources API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.auth.dependencies import CurrentActiveUser
from app.core.auth.api_keys import generate_api_key
from app.core.sources.models import Source

router = APIRouter()


class SourceCreate(BaseModel):
    name: str
    description: str | None = None
    properties: dict | None = None


class SourceResponse(BaseModel):
    id: str
    name: str
    description: str | None
    api_key_prefix: str
    is_active: bool
    properties: dict
    created_at: str

    class Config:
        from_attributes = True


class SourceWithKeyResponse(SourceResponse):
    """Response when creating source - includes full API key (shown once)."""

    api_key: str


class SourceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    properties: dict | None = None
    is_active: bool | None = None


@router.get("", response_model=list[SourceResponse])
async def list_sources(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SourceResponse]:
    """List all sources for current user."""
    result = await db.execute(
        select(Source).where(Source.owner_id == current_user.id).order_by(Source.created_at.desc())
    )
    sources = result.scalars().all()

    return [
        SourceResponse(
            id=str(s.id),
            name=s.name,
            description=s.description,
            api_key_prefix=s.api_key_prefix,
            is_active=s.is_active,
            properties=s.properties or {},
            created_at=s.created_at.isoformat(),
        )
        for s in sources
    ]


@router.post("", response_model=SourceWithKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    data: SourceCreate,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceWithKeyResponse:
    """Create a new source with API key."""
    # Generate API key
    full_key, key_hash, key_prefix = generate_api_key()

    source = Source(
        owner_id=current_user.id,
        name=data.name,
        description=data.description,
        api_key_hash=key_hash,
        api_key_prefix=key_prefix,
        properties=data.properties or {},
    )

    db.add(source)
    await db.commit()
    await db.refresh(source)

    return SourceWithKeyResponse(
        id=str(source.id),
        name=source.name,
        description=source.description,
        api_key_prefix=source.api_key_prefix,
        api_key=full_key,  # Only shown once!
        is_active=source.is_active,
        properties=source.properties or {},
        created_at=source.created_at.isoformat(),
    )


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: UUID,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceResponse:
    """Get source by ID."""
    result = await db.execute(
        select(Source).where(Source.id == source_id, Source.owner_id == current_user.id)
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    return SourceResponse(
        id=str(source.id),
        name=source.name,
        description=source.description,
        api_key_prefix=source.api_key_prefix,
        is_active=source.is_active,
        properties=source.properties or {},
        created_at=source.created_at.isoformat(),
    )


@router.patch("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: UUID,
    data: SourceUpdate,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceResponse:
    """Update source."""
    result = await db.execute(
        select(Source).where(Source.id == source_id, Source.owner_id == current_user.id)
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    if data.name is not None:
        source.name = data.name
    if data.description is not None:
        source.description = data.description
    if data.properties is not None:
        source.properties = data.properties
    if data.is_active is not None:
        source.is_active = data.is_active

    await db.commit()
    await db.refresh(source)

    return SourceResponse(
        id=str(source.id),
        name=source.name,
        description=source.description,
        api_key_prefix=source.api_key_prefix,
        is_active=source.is_active,
        properties=source.properties or {},
        created_at=source.created_at.isoformat(),
    )


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: UUID,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete source."""
    result = await db.execute(
        select(Source).where(Source.id == source_id, Source.owner_id == current_user.id)
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    await db.delete(source)
    await db.commit()


@router.post("/{source_id}/regenerate-key", response_model=SourceWithKeyResponse)
async def regenerate_api_key(
    source_id: UUID,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceWithKeyResponse:
    """Regenerate API key for source."""
    result = await db.execute(
        select(Source).where(Source.id == source_id, Source.owner_id == current_user.id)
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    # Generate new key
    full_key, key_hash, key_prefix = generate_api_key()
    source.api_key_hash = key_hash
    source.api_key_prefix = key_prefix

    await db.commit()
    await db.refresh(source)

    return SourceWithKeyResponse(
        id=str(source.id),
        name=source.name,
        description=source.description,
        api_key_prefix=source.api_key_prefix,
        api_key=full_key,
        is_active=source.is_active,
        properties=source.properties or {},
        created_at=source.created_at.isoformat(),
    )
