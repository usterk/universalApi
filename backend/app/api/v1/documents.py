"""Documents API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database.session import get_db
from app.core.auth.dependencies import CurrentActiveUser, CurrentUserOrSource
from app.core.documents.models import Document, DocumentType
from app.core.users.models import User
from app.core.sources.models import Source

router = APIRouter()


class DocumentTypeResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: str | None
    registered_by: str
    mime_types: list[str]

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: str
    type_name: str
    type_display_name: str
    owner_id: str
    source_id: str | None
    parent_id: str | None
    storage_plugin: str
    filepath: str
    content_type: str
    size_bytes: int
    properties: dict
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int


@router.get("/types", response_model=list[DocumentTypeResponse])
async def list_document_types(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DocumentTypeResponse]:
    """List all document types."""
    result = await db.execute(select(DocumentType).order_by(DocumentType.name))
    types = result.scalars().all()

    return [
        DocumentTypeResponse(
            id=str(t.id),
            name=t.name,
            display_name=t.display_name,
            description=t.description,
            registered_by=t.registered_by,
            mime_types=t.mime_types or [],
        )
        for t in types
    ]


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    auth: CurrentUserOrSource,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type_name: str | None = None,
    source_id: UUID | None = None,
) -> DocumentListResponse:
    """List documents for current user/source."""
    # Determine owner_id based on auth type
    if isinstance(auth, User):
        owner_id = auth.id
    else:  # Source
        owner_id = auth.owner_id

    # Build query
    query = select(Document).where(Document.owner_id == owner_id)

    if type_name:
        query = query.join(DocumentType).where(DocumentType.name == type_name)

    if source_id:
        query = query.where(Document.source_id == source_id)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = (
        query.options(selectinload(Document.document_type))
        .order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=str(d.id),
                type_name=d.document_type.name,
                type_display_name=d.document_type.display_name,
                owner_id=str(d.owner_id),
                source_id=str(d.source_id) if d.source_id else None,
                parent_id=str(d.parent_id) if d.parent_id else None,
                storage_plugin=d.storage_plugin,
                filepath=d.filepath,
                content_type=d.content_type,
                size_bytes=d.size_bytes,
                properties=d.properties or {},
                created_at=d.created_at.isoformat(),
                updated_at=d.updated_at.isoformat(),
            )
            for d in documents
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    auth: CurrentUserOrSource,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentResponse:
    """Get document by ID."""
    if isinstance(auth, User):
        owner_id = auth.id
    else:
        owner_id = auth.owner_id

    result = await db.execute(
        select(Document)
        .options(selectinload(Document.document_type))
        .where(Document.id == document_id, Document.owner_id == owner_id)
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return DocumentResponse(
        id=str(document.id),
        type_name=document.document_type.name,
        type_display_name=document.document_type.display_name,
        owner_id=str(document.owner_id),
        source_id=str(document.source_id) if document.source_id else None,
        parent_id=str(document.parent_id) if document.parent_id else None,
        storage_plugin=document.storage_plugin,
        filepath=document.filepath,
        content_type=document.content_type,
        size_bytes=document.size_bytes,
        properties=document.properties or {},
        created_at=document.created_at.isoformat(),
        updated_at=document.updated_at.isoformat(),
    )


@router.get("/{document_id}/children", response_model=list[DocumentResponse])
async def get_document_children(
    document_id: UUID,
    auth: CurrentUserOrSource,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DocumentResponse]:
    """Get documents generated from this document."""
    if isinstance(auth, User):
        owner_id = auth.id
    else:
        owner_id = auth.owner_id

    # First check if parent document exists and belongs to user
    parent_result = await db.execute(
        select(Document).where(Document.id == document_id, Document.owner_id == owner_id)
    )
    if parent_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Get children
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.document_type))
        .where(Document.parent_id == document_id)
        .order_by(Document.created_at.desc())
    )
    children = result.scalars().all()

    return [
        DocumentResponse(
            id=str(d.id),
            type_name=d.document_type.name,
            type_display_name=d.document_type.display_name,
            owner_id=str(d.owner_id),
            source_id=str(d.source_id) if d.source_id else None,
            parent_id=str(d.parent_id) if d.parent_id else None,
            storage_plugin=d.storage_plugin,
            filepath=d.filepath,
            content_type=d.content_type,
            size_bytes=d.size_bytes,
            properties=d.properties or {},
            created_at=d.created_at.isoformat(),
            updated_at=d.updated_at.isoformat(),
        )
        for d in children
    ]


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete document."""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.owner_id == current_user.id)
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # TODO: Also delete file from storage plugin

    await db.delete(document)
    await db.commit()
