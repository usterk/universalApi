"""Documents API endpoints."""

from datetime import datetime
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
from app.core.events.bus import get_event_bus
from app.core.events.types import EventType, EventSeverity
from app.core.plugins.models import ProcessingJob
from app.core.events.models import SystemEvent

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


class DocumentTreeNode(BaseModel):
    """Recursive document tree node with children."""

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
    children: list["DocumentTreeNode"] = []

    class Config:
        from_attributes = True


class DocumentTreeResponse(BaseModel):
    """Response for tree endpoint with pagination."""

    items: list[DocumentTreeNode]
    total: int
    page: int
    page_size: int


class ProcessingJobResponse(BaseModel):
    """Processing job information."""

    id: str
    plugin_name: str
    status: str
    progress: int
    progress_message: str | None
    result: dict | None
    error_message: str | None
    started_at: str | None
    completed_at: str | None
    created_at: str

    class Config:
        from_attributes = True


class SystemEventResponse(BaseModel):
    """System event information."""

    id: str
    event_type: str
    source: str
    severity: str
    payload: dict
    created_at: str

    class Config:
        from_attributes = True


class DocumentDetailsResponse(BaseModel):
    """Comprehensive document details with relationships."""

    document: DocumentResponse
    parent: DocumentResponse | None
    children: list[DocumentResponse]
    processing_jobs: list[ProcessingJobResponse]
    system_events: list[SystemEventResponse]


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


@router.get("/tree", response_model=DocumentTreeResponse)
async def get_documents_tree(
    auth: CurrentUserOrSource,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type_name: str | None = None,
    source_id: UUID | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> DocumentTreeResponse:
    """Get documents in hierarchical tree structure with filtering."""
    # Determine owner
    if isinstance(auth, User):
        owner_id = auth.id
    else:
        owner_id = auth.owner_id

    # Build query - only root documents (parent_id == None)
    query = (
        select(Document)
        .where(Document.owner_id == owner_id, Document.parent_id == None)
        .options(
            selectinload(Document.document_type),
            selectinload(Document.children).selectinload(Document.document_type),
            selectinload(Document.children).selectinload(Document.children),  # 2 levels deep
        )
    )

    # Apply filters
    if type_name:
        query = query.join(DocumentType).where(DocumentType.name == type_name)
    if source_id:
        query = query.where(Document.source_id == source_id)
    if created_after:
        query = query.where(Document.created_at >= created_after)
    if created_before:
        query = query.where(Document.created_at <= created_before)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Sort
    if sort_order == "asc":
        query = query.order_by(getattr(Document, sort_by).asc())
    else:
        query = query.order_by(getattr(Document, sort_by).desc())

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    documents = result.scalars().all()

    # Convert to tree nodes (recursive)
    def to_tree_node(doc: Document) -> DocumentTreeNode:
        return DocumentTreeNode(
            id=str(doc.id),
            type_name=doc.document_type.name,
            type_display_name=doc.document_type.display_name,
            owner_id=str(doc.owner_id),
            source_id=str(doc.source_id) if doc.source_id else None,
            parent_id=str(doc.parent_id) if doc.parent_id else None,
            storage_plugin=doc.storage_plugin,
            filepath=doc.filepath,
            content_type=doc.content_type,
            size_bytes=doc.size_bytes,
            properties=doc.properties or {},
            created_at=doc.created_at.isoformat(),
            updated_at=doc.updated_at.isoformat(),
            children=[to_tree_node(child) for child in doc.children],
        )

    return DocumentTreeResponse(
        items=[to_tree_node(doc) for doc in documents],
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

    # Store document info before deletion
    doc_type_name = document.document_type.name

    # TODO: Also delete file from storage plugin

    await db.delete(document)

    # Emit document.deleted event
    event_bus = get_event_bus()
    await event_bus.emit(
        event_type=EventType.DOCUMENT_DELETED,
        source="api:documents",
        payload={
            "document_id": str(document_id),
            "document_type": doc_type_name,
            "owner_id": str(current_user.id),
        },
        user_id=current_user.id,
        severity=EventSeverity.INFO,
        persist=True,
    )

    await db.commit()


@router.get("/{document_id}/details", response_model=DocumentDetailsResponse)
async def get_document_details(
    document_id: UUID,
    auth: CurrentUserOrSource,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentDetailsResponse:
    """Get comprehensive document details with all relationships."""
    if isinstance(auth, User):
        owner_id = auth.id
    else:
        owner_id = auth.owner_id

    # Fetch main document
    result = await db.execute(
        select(Document)
        .options(
            selectinload(Document.document_type),
            selectinload(Document.parent).selectinload(Document.document_type),
            selectinload(Document.children).selectinload(Document.document_type),
        )
        .where(Document.id == document_id, Document.owner_id == owner_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Fetch processing jobs
    jobs_result = await db.execute(
        select(ProcessingJob)
        .where(ProcessingJob.document_id == document_id)
        .order_by(ProcessingJob.created_at.desc())
    )
    jobs = jobs_result.scalars().all()

    # Fetch system events
    events_result = await db.execute(
        select(SystemEvent)
        .where(
            SystemEvent.payload["document_id"].astext == str(document_id)
        )
        .order_by(SystemEvent.created_at.desc())
        .limit(50)
    )
    events = events_result.scalars().all()

    # Helper function to convert Document to DocumentResponse
    def to_document_response(doc: Document) -> DocumentResponse:
        return DocumentResponse(
            id=str(doc.id),
            type_name=doc.document_type.name,
            type_display_name=doc.document_type.display_name,
            owner_id=str(doc.owner_id),
            source_id=str(doc.source_id) if doc.source_id else None,
            parent_id=str(doc.parent_id) if doc.parent_id else None,
            storage_plugin=doc.storage_plugin,
            filepath=doc.filepath,
            content_type=doc.content_type,
            size_bytes=doc.size_bytes,
            properties=doc.properties or {},
            created_at=doc.created_at.isoformat(),
            updated_at=doc.updated_at.isoformat(),
        )

    return DocumentDetailsResponse(
        document=to_document_response(document),
        parent=to_document_response(document.parent) if document.parent else None,
        children=[to_document_response(child) for child in document.children],
        processing_jobs=[
            ProcessingJobResponse(
                id=str(job.id),
                plugin_name=job.plugin_name,
                status=job.status,
                progress=job.progress,
                progress_message=job.progress_message,
                result=job.result or {},
                error_message=job.error_message,
                started_at=job.started_at.isoformat() if job.started_at else None,
                completed_at=job.completed_at.isoformat() if job.completed_at else None,
                created_at=job.created_at.isoformat(),
            )
            for job in jobs
        ],
        system_events=[
            SystemEventResponse(
                id=str(event.id),
                event_type=event.event_type,
                source=event.source,
                severity=event.severity,
                payload=event.payload or {},
                created_at=event.created_at.isoformat(),
            )
            for event in events
        ],
    )
