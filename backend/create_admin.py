"""Create initial admin user."""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.core.database.base import Base  # noqa: F401
from app.core.users.models import User, Role  # noqa: F401
from app.core.sources.models import Source  # noqa: F401
from app.core.documents.models import Document, DocumentType  # noqa: F401
from app.core.auth.password import hash_password


async def create_admin_user():
    """Create admin user if not exists."""
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if admin role exists
        result = await session.execute(select(Role).where(Role.name == "admin"))
        admin_role = result.scalar_one_or_none()

        if not admin_role:
            admin_role = Role(
                name="admin",
                description="Administrator with full access",
                is_system=False,
            )
            session.add(admin_role)
            await session.commit()
            await session.refresh(admin_role)
            print("✓ Created admin role")

        # Check if admin user exists
        result = await session.execute(select(User).where(User.email == "admin@example.com"))
        admin_user = result.scalar_one_or_none()

        if admin_user:
            print("✓ Admin user already exists")
            print(f"  Email: admin@example.com")
            return

        # Create admin user
        admin_user = User(
            email="admin@example.com",
            full_name="Admin User",
            hashed_password=hash_password("admin123"),
            is_active=True,
            role_id=admin_role.id,
        )
        session.add(admin_user)
        await session.commit()

        print("✓ Created admin user")
        print(f"  Email: admin@example.com")
        print(f"  Password: admin123")
        print(f"  Role: admin")
        print("\n⚠️  IMPORTANT: Change the password after first login!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_admin_user())
