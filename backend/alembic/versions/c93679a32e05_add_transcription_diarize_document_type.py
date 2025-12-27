"""add_transcription_diarize_document_type

Revision ID: c93679a32e05
Revises: 748ccef91929
Create Date: 2025-12-27 20:11:26.798718

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c93679a32e05'
down_revision: Union[str, None] = '748ccef91929'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add transcription_diarize document type for speaker identification plugin."""
    op.execute("""
        INSERT INTO document_types (id, name, display_name, registered_by, mime_types, metadata_schema, created_at, updated_at)
        VALUES (
            gen_random_uuid(),
            'transcription_diarize',
            'Transcription with Speaker ID',
            'audio_transcription_diarize',
            ARRAY['application/json'],
            '{"type": "object", "required": ["full_text", "segments"], "properties": {"full_text": {"type": "string"}, "language": {"type": "string"}, "duration_seconds": {"type": "number"}, "model_used": {"type": "string"}, "speaker_count": {"type": "integer"}, "segment_count": {"type": "integer"}, "segments": {"type": "array", "items": {"type": "object", "properties": {"speaker": {"type": "string"}, "text": {"type": "string"}, "start": {"type": "number"}, "end": {"type": "number"}}}}}}',
            NOW(),
            NOW()
        )
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    """Remove transcription_diarize document type."""
    op.execute("""
        DELETE FROM document_types
        WHERE registered_by = 'audio_transcription_diarize'
        AND name = 'transcription_diarize';
    """)
