"""Document and DocumentType models."""

from uuid import UUID
from typing import TYPE_CHECKING

from sqlalchemy import String, BigInteger, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, ARRAY

from app.core.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.core.users.models import User
    from app.core.sources.models import Source


class DocumentType(Base, UUIDMixin, TimestampMixin):
    """
    Dynamic document type registered by plugins.

    Examples: "audio", "transcription", "analysis", "image", etc.
    Plugins can register new types when they're installed.
    """

    __tablename__ = "document_types"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))

    # Which plugin registered this type
    registered_by: Mapped[str] = mapped_column(String(100), nullable=False)

    # Associated MIME types (e.g., ["audio/mpeg", "audio/wav"])
    mime_types: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    # Optional JSON Schema for document metadata validation
    metadata_schema: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    documents: Mapped[list["Document"]] = relationship(back_populates="document_type")

    def __repr__(self) -> str:
        return f"<DocumentType {self.name}>"


class Document(Base, UUIDMixin, TimestampMixin):
    """
    Universal document model for all data types.

    A document can be:
    - Uploaded from an external source (source_id is set)
    - Generated from another document (parent_id is set)
    """

    __tablename__ = "documents"

    # Type reference (dynamic)
    type_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_types.id"),
        nullable=False,
    )

    # Owner
    owner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    # Origin (one of these should be set):
    # - source_id: External source (upload)
    # - parent_id: Generated from another document
    source_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sources.id"),
        nullable=True,
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
    )

    # Storage info
    storage_plugin: Mapped[str] = mapped_column(String(100), nullable=False)  # Plugin handling storage
    filepath: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)  # MIME type
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256

    # Additional properties
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    document_type: Mapped["DocumentType"] = relationship(back_populates="documents")
    owner: Mapped["User"] = relationship()
    source: Mapped["Source | None"] = relationship(back_populates="documents")
    parent: Mapped["Document | None"] = relationship(
        remote_side="Document.id",
        back_populates="children",
    )
    children: Mapped[list["Document"]] = relationship(back_populates="parent")

    # Indexes
    __table_args__ = (
        Index("idx_documents_owner_type", "owner_id", "type_id"),
        Index("idx_documents_source", "source_id"),
        Index("idx_documents_parent", "parent_id"),
        Index("idx_documents_created", "created_at"),
    )

    @property
    def is_uploaded(self) -> bool:
        """Check if document was uploaded from external source."""
        return self.source_id is not None

    @property
    def is_generated(self) -> bool:
        """Check if document was generated from another document."""
        return self.parent_id is not None

    def __repr__(self) -> str:
        return f"<Document {self.id} ({self.content_type})>"
