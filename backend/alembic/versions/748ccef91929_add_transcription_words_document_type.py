"""add_transcription_words_document_type

Revision ID: 748ccef91929
Revises: b2c3d4e5f6a7
Create Date: 2025-12-27 19:55:19.199955

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '748ccef91929'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add transcription_words document type for audio_transcription_words plugin."""
    op.execute("""
        INSERT INTO document_types (id, name, display_name, registered_by, mime_types, metadata_schema, created_at, updated_at)
        VALUES (
            gen_random_uuid(),
            'transcription_words',
            'Transcription with Words',
            'audio_transcription_words',
            ARRAY['application/json'],
            '{"type": "object", "required": ["full_text", "words"], "properties": {"full_text": {"type": "string"}, "language": {"type": "string"}, "duration_seconds": {"type": "number"}, "model_used": {"type": "string"}, "word_count": {"type": "integer"}, "words": {"type": "array", "items": {"type": "object", "properties": {"word": {"type": "string"}, "start": {"type": "number"}, "end": {"type": "number"}, "confidence": {"type": "number"}}}}}}',
            NOW(),
            NOW()
        )
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    """Remove transcription_words document type."""
    op.execute("""
        DELETE FROM document_types
        WHERE registered_by = 'audio_transcription_words'
        AND name = 'transcription_words';
    """)
