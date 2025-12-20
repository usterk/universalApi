"""Audio Transcription plugin models."""

from uuid import UUID

from sqlalchemy import String, Float, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.database.base import Base, TimestampMixin, UUIDMixin


class Transcription(Base, UUIDMixin, TimestampMixin):
    """Transcription result for an audio document."""

    __tablename__ = "transcriptions"

    # Reference to source audio document
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        unique=True,
    )

    # Reference to output transcription document (if created)
    output_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
    )

    # Transcription data
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    language_probability: Mapped[float | None] = mapped_column(Float)
    duration_seconds: Mapped[float | None] = mapped_column(Float)

    # Model info
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    processing_time_seconds: Mapped[float | None] = mapped_column(Float)

    # Relationships
    words: Mapped[list["TranscriptionWord"]] = relationship(
        back_populates="transcription",
        order_by="TranscriptionWord.start_time",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_transcriptions_document", "document_id"),
        Index("idx_transcriptions_language", "language"),
    )

    def __repr__(self) -> str:
        return f"<Transcription {self.id} lang={self.language}>"


class TranscriptionWord(Base, UUIDMixin):
    """Individual word with timestamp."""

    __tablename__ = "transcription_words"

    transcription_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("transcriptions.id", ondelete="CASCADE"),
        nullable=False,
    )

    word: Mapped[str] = mapped_column(String(500), nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)  # seconds
    end_time: Mapped[float] = mapped_column(Float, nullable=False)  # seconds
    confidence: Mapped[float | None] = mapped_column(Float)

    # Relationships
    transcription: Mapped["Transcription"] = relationship(back_populates="words")

    # Indexes
    __table_args__ = (
        Index("idx_words_transcription", "transcription_id"),
        Index("idx_words_time", "start_time"),
    )

    def __repr__(self) -> str:
        return f"<Word '{self.word}' at {self.start_time:.2f}s>"
