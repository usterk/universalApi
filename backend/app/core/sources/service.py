"""Source service functions."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.sources.models import Source
from app.core.constants import MANUAL_SOURCE_DESCRIPTION, MANUAL_SOURCE_NAME
from app.core.plugins.models import SourceWorkflowStep
from app.core.auth.api_keys import generate_api_key


async def get_or_create_manual_source(db: AsyncSession, owner_id: UUID) -> Source:
    """
    Get or create the system 'Manual' source for a user.

    This source is used for all manual web uploads. If the source doesn't exist,
    it creates it along with a default workflow: audio → transcription.

    Args:
        db: Database session
        owner_id: User ID who owns the source

    Returns:
        Source: The Manual source for the user
    """
    # Try to find existing Manual source for this user
    result = await db.execute(
        select(Source).where(
            Source.owner_id == owner_id, Source.name == MANUAL_SOURCE_NAME
        )
    )
    source = result.scalar_one_or_none()

    if source:
        return source

    # Create new Manual source
    # Generate API key (even though it won't be used for auth)
    _, key_hash, key_prefix = generate_api_key()

    source = Source(
        owner_id=owner_id,
        name=MANUAL_SOURCE_NAME,
        description=MANUAL_SOURCE_DESCRIPTION,
        api_key_hash=key_hash,
        api_key_prefix=key_prefix,
        is_active=True,
        properties={"is_system_source": True, "created_automatically": True},
    )
    db.add(source)
    await db.flush()  # Get source.id

    # Create default workflow: audio → transcription
    workflow_step = SourceWorkflowStep(
        source_id=source.id,
        document_type="audio",
        sequence_number=1,
        plugin_name="audio_transcription",
        is_enabled=True,
        settings={},
    )
    db.add(workflow_step)

    await db.commit()
    await db.refresh(source)

    return source
