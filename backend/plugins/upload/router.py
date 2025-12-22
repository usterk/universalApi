"""Upload plugin router."""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database.session import get_db
from app.core.auth.dependencies import CurrentSource, CurrentUserOrSource
from app.core.documents.models import Document, DocumentType
from app.core.events.bus import get_event_bus, EventBus
from app.core.events.types import EventType
from app.core.users.models import User
from app.core.sources.models import Source

router = APIRouter()


class UploadResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    document_type: str
    created_at: str


def get_document_type_for_mime(mime_type: str, doc_types: list[DocumentType]) -> DocumentType | None:
    """Find document type matching MIME type."""
    for dt in doc_types:
        if mime_type in (dt.mime_types or []):
            return dt
    return None


def calculate_checksum(file_content: bytes) -> str:
    """Calculate SHA-256 checksum."""
    return hashlib.sha256(file_content).hexdigest()


@router.post("/files", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    auth: CurrentUserOrSource,
    db: Annotated[AsyncSession, Depends(get_db)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    file: UploadFile = File(...),
) -> UploadResponse:
    """
    Upload a file.

    Authentication:
    - API key (X-API-Key header) for source devices
    - JWT Bearer token for users

    The file will be stored and a Document record created.
    This triggers DOCUMENT_CREATED event for processing plugins.
    """
    # Determine owner and source based on auth type
    if isinstance(auth, Source):
        owner_id = auth.owner_id
        source_id = auth.id
    else:  # User
        owner_id = auth.id
        source_id = None

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Check file size (100MB default limit)
    max_size = 100 * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {max_size // (1024*1024)}MB",
        )

    # Get document types
    result = await db.execute(select(DocumentType))
    doc_types = list(result.scalars().all())

    # Find matching document type
    content_type = file.content_type or "application/octet-stream"
    doc_type = get_document_type_for_mime(content_type, doc_types)

    if doc_type is None:
        # Create a generic "file" type if doesn't exist
        result = await db.execute(select(DocumentType).where(DocumentType.name == "file"))
        doc_type = result.scalar_one_or_none()

        if doc_type is None:
            doc_type = DocumentType(
                name="file",
                display_name="Generic File",
                registered_by="upload",
                mime_types=[],
            )
            db.add(doc_type)
            await db.flush()

    # Calculate checksum
    checksum = calculate_checksum(content)

    # Generate storage path
    now = datetime.utcnow()
    file_id = uuid4()
    file_ext = Path(file.filename or "file").suffix
    storage_path = f"{now.year}/{now.month:02d}/{now.day:02d}/{file_id}{file_ext}"

    # Save file to storage
    full_path = Path(settings.storage_local_path) / storage_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(content)

    # Create document record
    document = Document(
        id=file_id,
        type_id=doc_type.id,
        owner_id=owner_id,
        source_id=source_id,
        parent_id=None,
        storage_plugin="upload",
        filepath=storage_path,
        content_type=content_type,
        size_bytes=file_size,
        checksum=checksum,
        properties={
            "original_filename": file.filename,
        },
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Emit document created event
    await event_bus.emit(
        event_type=EventType.DOCUMENT_CREATED,
        source="plugin:upload",
        payload={
            "document_id": str(document.id),
            "document_type": doc_type.name,
            "content_type": content_type,
            "size_bytes": file_size,
            "source_id": str(source_id) if source_id else None,
        },
        user_id=owner_id,
    )

    return UploadResponse(
        id=str(document.id),
        filename=file.filename or "unknown",
        content_type=content_type,
        size_bytes=file_size,
        document_type=doc_type.name,
        created_at=document.created_at.isoformat(),
    )


@router.get("/files/{document_id}")
async def get_file_info(
    document_id: str,
    auth: CurrentUserOrSource,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get file/document information."""
    if isinstance(auth, User):
        owner_id = auth.id
    else:
        owner_id = auth.owner_id

    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.owner_id == owner_id)
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return {
        "document_id": str(document.id),
        "type": document.document_type.name if document.document_type else "unknown",
        "content_type": document.content_type,
        "size_bytes": document.size_bytes,
        "filepath": document.filepath,
        "checksum": document.checksum,
        "properties": document.properties,
        "created_at": document.created_at.isoformat(),
    }
