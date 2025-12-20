"""Source model - external data sources with API keys."""

from uuid import UUID
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.core.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.core.users.models import User
    from app.core.documents.models import Document


class Source(Base, UUIDMixin, TimestampMixin):
    """
    Source model representing an external data source (device, service, etc.).

    Each source has its own API key for authentication.
    Documents uploaded via this source will reference it.
    """

    __tablename__ = "sources"

    owner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))

    # API key hash (the actual key is only shown once at creation)
    api_key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    api_key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)  # First few chars for identification

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Additional properties of the source
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="sources")
    documents: Mapped[list["Document"]] = relationship(back_populates="source")

    def __repr__(self) -> str:
        return f"<Source {self.name} ({self.api_key_prefix}...)>"
