"""seed_document_types_from_upload_plugin

Revision ID: 5a2e5faec3f2
Revises: 0b5913df4a79
Create Date: 2025-12-24 14:21:04.093317

"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column
from sqlalchemy.dialects.postgresql import UUID, ARRAY


# revision identifiers, used by Alembic.
revision: str = '5a2e5faec3f2'
down_revision: Union[str, None] = '0b5913df4a79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed document types from upload plugin."""
    # Use raw SQL for UUID generation and timestamps
    op.execute("""
        INSERT INTO document_types (id, name, display_name, registered_by, mime_types, created_at, updated_at)
        VALUES
            -- Audio files
            (gen_random_uuid(), 'audio', 'Audio File', 'upload',
             ARRAY['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg', 'audio/webm', 'audio/flac', 'audio/m4a', 'audio/x-m4a'],
             NOW(), NOW()),

            -- Video files
            (gen_random_uuid(), 'video', 'Video File', 'upload',
             ARRAY['video/mp4', 'video/webm', 'video/ogg', 'video/quicktime', 'video/x-msvideo'],
             NOW(), NOW()),

            -- Image files
            (gen_random_uuid(), 'image', 'Image File', 'upload',
             ARRAY['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'],
             NOW(), NOW()),

            -- Code files
            (gen_random_uuid(), 'code', 'Source Code', 'upload',
             ARRAY['text/x-python', 'text/x-script.python', 'application/x-python-code',
                   'text/javascript', 'application/javascript', 'application/x-javascript',
                   'text/x-typescript', 'application/x-typescript',
                   'text/x-java-source', 'text/x-java',
                   'text/x-c', 'text/x-c++', 'text/x-c++src',
                   'text/x-go', 'text/x-rust', 'text/x-ruby', 'text/x-php', 'text/x-csharp', 'text/x-swift', 'text/x-kotlin'],
             NOW(), NOW()),

            -- Markdown files
            (gen_random_uuid(), 'markdown', 'Markdown Document', 'upload',
             ARRAY['text/markdown', 'text/x-markdown'],
             NOW(), NOW()),

            -- Text files
            (gen_random_uuid(), 'text', 'Text File', 'upload',
             ARRAY['text/plain', 'text/html', 'text/css', 'text/csv'],
             NOW(), NOW()),

            -- XML files
            (gen_random_uuid(), 'xml', 'XML Document', 'upload',
             ARRAY['application/xml', 'text/xml'],
             NOW(), NOW()),

            -- YAML files
            (gen_random_uuid(), 'yaml', 'YAML Document', 'upload',
             ARRAY['application/x-yaml', 'text/yaml', 'text/x-yaml'],
             NOW(), NOW()),

            -- Document files
            (gen_random_uuid(), 'document', 'Document', 'upload',
             ARRAY['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
             NOW(), NOW()),

            -- JSON files
            (gen_random_uuid(), 'json', 'JSON Data', 'upload',
             ARRAY['application/json'],
             NOW(), NOW())
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    """Remove seeded document types."""
    # Delete all types registered by upload plugin
    op.execute("""
        DELETE FROM document_types
        WHERE registered_by = 'upload'
        AND name IN ('audio', 'video', 'image', 'code', 'markdown', 'text', 'xml', 'yaml', 'document', 'json');
    """)
