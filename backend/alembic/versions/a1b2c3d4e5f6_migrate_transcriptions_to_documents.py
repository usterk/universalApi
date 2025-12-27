"""migrate_transcriptions_to_documents

Universal Document Pattern: Migrate existing transcriptions to child documents.

Revision ID: a1b2c3d4e5f6
Revises: 0269b1b38152
Create Date: 2025-12-27 12:00:00.000000

"""
from typing import Sequence, Union
from uuid import uuid4
from datetime import datetime
import hashlib
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '0269b1b38152'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Migrate existing transcriptions to child Documents.

    For each transcription:
    1. Get the transcription document type ID
    2. Create a child Document with parent_id = transcription.document_id
    3. Put all transcription data in properties (including words)
    """
    connection = op.get_bind()

    # Get or create transcription document type
    transcription_type = connection.execute(
        sa.text("SELECT id FROM document_types WHERE name = 'transcription'")
    ).fetchone()

    if transcription_type is None:
        # Create transcription document type if it doesn't exist
        type_id = str(uuid4())
        connection.execute(
            sa.text("""
                INSERT INTO document_types (id, name, display_name, description, registered_by, mime_types, created_at, updated_at)
                VALUES (:id, 'transcription', 'Transcription', 'Audio transcription output', 'audio_transcription', ARRAY['application/json'], now(), now())
            """),
            {"id": type_id}
        )
        transcription_type_id = type_id
    else:
        transcription_type_id = str(transcription_type[0])

    # Get all transcriptions with their parent document info
    transcriptions = connection.execute(
        sa.text("""
            SELECT
                t.id,
                t.document_id,
                t.full_text,
                t.language,
                t.language_probability,
                t.duration_seconds,
                t.model_used,
                t.processing_time_seconds,
                t.created_at,
                d.owner_id,
                d.source_id,
                d.properties as parent_properties
            FROM transcriptions t
            JOIN documents d ON t.document_id = d.id
        """)
    ).fetchall()

    for t in transcriptions:
        # Get words for this transcription
        words = connection.execute(
            sa.text("""
                SELECT word, start_time, end_time, confidence
                FROM transcription_words
                WHERE transcription_id = :transcription_id
                ORDER BY start_time
            """),
            {"transcription_id": str(t[0])}
        ).fetchall()

        # Build words array
        words_list = [
            {
                "word": w[0],
                "start": w[1],
                "end": w[2],
                "confidence": w[3],
            }
            for w in words
        ]

        # Build properties
        parent_props = t[11] or {}
        properties = {
            "full_text": t[2],
            "language": t[3],
            "language_probability": t[4],
            "duration_seconds": t[5],
            "model_used": t[6],
            "processing_time_seconds": t[7],
            "original_filename": parent_props.get("original_filename", "audio.mp3"),
            "word_count": len(words_list),
            "words": words_list,
        }

        # Create JSON content for checksum
        json_content = json.dumps(properties, ensure_ascii=False)
        json_bytes = json_content.encode("utf-8")
        checksum = hashlib.sha256(json_bytes).hexdigest()

        # Generate filepath
        created_at = t[8]
        child_id = str(uuid4())
        filepath = f"{created_at.year}/{created_at.month:02d}/{created_at.day:02d}/{child_id}.json"

        # Insert child document
        connection.execute(
            sa.text("""
                INSERT INTO documents (
                    id, type_id, owner_id, source_id, parent_id,
                    storage_plugin, filepath, content_type, size_bytes, checksum,
                    properties, created_at, updated_at
                )
                VALUES (
                    :id, :type_id, :owner_id, :source_id, :parent_id,
                    'audio_transcription', :filepath, 'application/json', :size_bytes, :checksum,
                    :properties, :created_at, now()
                )
            """),
            {
                "id": child_id,
                "type_id": transcription_type_id,
                "owner_id": str(t[9]),
                "source_id": str(t[10]) if t[10] else None,
                "parent_id": str(t[1]),  # document_id from transcription
                "filepath": filepath,
                "size_bytes": len(json_bytes),
                "checksum": checksum,
                "properties": json.dumps(properties),
                "created_at": created_at,
            }
        )

    print(f"Migrated {len(transcriptions)} transcriptions to child documents")


def downgrade() -> None:
    """
    Rollback: Delete child documents created from transcriptions.

    Note: Original transcriptions table still exists, so we just delete the migrated documents.
    """
    connection = op.get_bind()

    # Get transcription type id
    transcription_type = connection.execute(
        sa.text("SELECT id FROM document_types WHERE name = 'transcription'")
    ).fetchone()

    if transcription_type:
        # Delete documents with storage_plugin = 'audio_transcription' and type = transcription
        connection.execute(
            sa.text("""
                DELETE FROM documents
                WHERE storage_plugin = 'audio_transcription'
                AND type_id = :type_id
            """),
            {"type_id": str(transcription_type[0])}
        )
