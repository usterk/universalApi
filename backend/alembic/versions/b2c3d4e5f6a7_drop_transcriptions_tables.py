"""drop_transcriptions_tables

Universal Document Pattern: Drop old transcription tables after data migration.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-27 12:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Drop old transcription tables.

    Data has been migrated to Documents table in the previous migration.
    """
    # Drop indexes first
    op.drop_index('idx_words_time', table_name='transcription_words')
    op.drop_index('idx_words_transcription', table_name='transcription_words')
    op.drop_table('transcription_words')

    op.drop_index('idx_transcriptions_language', table_name='transcriptions')
    op.drop_index('idx_transcriptions_document', table_name='transcriptions')
    op.drop_table('transcriptions')


def downgrade() -> None:
    """
    Recreate transcription tables.

    Note: This does NOT restore the data - only recreates empty tables.
    Use a database backup to restore data.
    """
    # Recreate transcriptions table
    op.create_table(
        'transcriptions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('output_document_id', sa.UUID(), nullable=True),
        sa.Column('full_text', sa.Text(), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('language_probability', sa.Float(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('model_used', sa.String(length=100), nullable=False),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['output_document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id')
    )
    op.create_index('idx_transcriptions_document', 'transcriptions', ['document_id'], unique=False)
    op.create_index('idx_transcriptions_language', 'transcriptions', ['language'], unique=False)

    # Recreate transcription_words table
    op.create_table(
        'transcription_words',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('transcription_id', sa.UUID(), nullable=False),
        sa.Column('word', sa.String(length=500), nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('end_time', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['transcription_id'], ['transcriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_words_transcription', 'transcription_words', ['transcription_id'], unique=False)
    op.create_index('idx_words_time', 'transcription_words', ['start_time'], unique=False)
