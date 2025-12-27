"""allow_parallel_workflow_steps

Revision ID: 96b90a9e7415
Revises: c93679a32e05
Create Date: 2025-12-27 20:13:49.326224

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96b90a9e7415'
down_revision: Union[str, None] = 'c93679a32e05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow multiple plugins with the same sequence_number (parallel execution).

    Change unique index from (source_id, document_type, sequence_number)
    to (source_id, document_type, sequence_number, plugin_name).
    """
    # Drop old unique index and create new one (source_workflow_steps)
    op.execute("DROP INDEX IF EXISTS idx_source_workflow_unique;")
    op.execute("""
        CREATE UNIQUE INDEX idx_source_workflow_unique
        ON source_workflow_steps (source_id, document_type, sequence_number, plugin_name);
    """)

    # Drop old unique index and create new one (user_workflow_steps)
    op.execute("DROP INDEX IF EXISTS idx_user_workflow_unique;")
    op.execute("""
        CREATE UNIQUE INDEX idx_user_workflow_unique
        ON user_workflow_steps (user_id, document_type, sequence_number, plugin_name);
    """)


def downgrade() -> None:
    """Revert to original constraint (breaks parallel workflows)."""
    # Revert source_workflow_steps
    op.execute("DROP INDEX IF EXISTS idx_source_workflow_unique;")
    op.execute("""
        CREATE UNIQUE INDEX idx_source_workflow_unique
        ON source_workflow_steps (source_id, document_type, sequence_number);
    """)

    # Revert user_workflow_steps
    op.execute("DROP INDEX IF EXISTS idx_user_workflow_unique;")
    op.execute("""
        CREATE UNIQUE INDEX idx_user_workflow_unique
        ON user_workflow_steps (user_id, document_type, sequence_number);
    """)
