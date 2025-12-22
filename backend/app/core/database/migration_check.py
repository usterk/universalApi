"""Migration status checker.

This module provides functions to check if database migrations are up to date.
It's designed to be called during application startup to prevent cryptic runtime
errors when migrations haven't been run.
"""

import logging
from pathlib import Path
from typing import Any

from alembic import script
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


async def check_migration_status(engine: AsyncEngine) -> dict[str, Any]:
    """Check if database migrations are up to date.

    Args:
        engine: SQLAlchemy async engine

    Returns:
        Dictionary with migration status information:
        - alembic_table_exists: bool - whether alembic_version table exists
        - current_revision: Optional[str] - current database revision
        - head_revision: str - latest available revision
        - is_up_to_date: bool - whether database is at latest revision
        - pending_migrations: list[str] - list of pending migration IDs (future feature)
    """
    result: dict[str, Any] = {
        "alembic_table_exists": False,
        "current_revision": None,
        "head_revision": None,
        "is_up_to_date": False,
        "pending_migrations": [],
    }

    # Check if alembic_version table exists
    async with engine.begin() as conn:
        query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'alembic_version'
            )
        """)
        table_exists = await conn.scalar(query)
        result["alembic_table_exists"] = bool(table_exists)

        if not table_exists:
            logger.warning(
                "alembic_version table does not exist - migrations have never been run!"
            )
            return result

        # Get current revision
        current_query = text("SELECT version_num FROM alembic_version")
        current_rev = await conn.scalar(current_query)
        result["current_revision"] = current_rev

    # Get head revision from alembic config
    # Look for alembic.ini in the backend directory
    alembic_ini_path = Path(__file__).parent.parent.parent.parent / "alembic.ini"

    if not alembic_ini_path.exists():
        logger.error(f"alembic.ini not found at {alembic_ini_path}")
        return result

    alembic_cfg = Config(str(alembic_ini_path))
    script_dir = script.ScriptDirectory.from_config(alembic_cfg)
    head_revision = script_dir.get_current_head()
    result["head_revision"] = head_revision

    # Check if up to date
    if current_rev == head_revision:
        result["is_up_to_date"] = True
        logger.info(
            f"Database migrations are up to date (revision: {current_rev})"
        )
    else:
        result["is_up_to_date"] = False
        logger.warning(
            f"Database migrations are OUT OF DATE! "
            f"Current: {current_rev}, Head: {head_revision}"
        )

    return result


async def require_migrations(
    engine: AsyncEngine, fail_on_outdated: bool = True
) -> None:
    """Check migration status and optionally fail if not up to date.

    This function is designed to be called during application startup to ensure
    the database schema is properly initialized and up to date.

    Args:
        engine: SQLAlchemy async engine
        fail_on_outdated: If True, raises RuntimeError when migrations are outdated
                         If False, only logs a warning

    Raises:
        RuntimeError: If migrations are not up to date and fail_on_outdated=True
    """
    status = await check_migration_status(engine)

    if not status["alembic_table_exists"]:
        error_msg = (
            "❌ DATABASE NOT INITIALIZED!\n"
            "The alembic_version table does not exist.\n"
            "Migrations have never been run.\n\n"
            "To fix this, run:\n"
            "  cd backend && poetry run alembic upgrade head\n"
            "Or:\n"
            "  make db-migrate\n"
        )
        logger.error(error_msg)
        if fail_on_outdated:
            raise RuntimeError(error_msg)
        return

    if not status["is_up_to_date"]:
        error_msg = (
            f"❌ DATABASE MIGRATIONS OUT OF DATE!\n"
            f"Current revision: {status['current_revision']}\n"
            f"Head revision: {status['head_revision']}\n\n"
            f"To fix this, run:\n"
            f"  cd backend && poetry run alembic upgrade head\n"
            f"Or:\n"
            f"  make db-migrate\n"
        )
        logger.error(error_msg)
        if fail_on_outdated:
            raise RuntimeError(error_msg)
