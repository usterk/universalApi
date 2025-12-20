"""User, Role, and Permission models."""

from uuid import UUID
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.core.sources.models import Source


# Association table for Role <-> Permission many-to-many
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", PG_UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", PG_UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True),
)


class Permission(Base, UUIDMixin):
    """Permission model for fine-grained access control."""

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    resource: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "documents"
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "read", "write"
    description: Mapped[str | None] = mapped_column(String(500))

    def __repr__(self) -> str:
        return f"<Permission {self.name}>"


class Role(Base, UUIDMixin, TimestampMixin):
    """Role model for grouping permissions."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # Built-in roles

    # Relationships
    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permissions,
        lazy="selectin",
    )
    users: Mapped[list["User"]] = relationship(back_populates="role")

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class User(Base, UUIDMixin, TimestampMixin):
    """User model."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    role_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id"),
        nullable=False,
    )

    # Relationships
    role: Mapped["Role"] = relationship(back_populates="users", lazy="selectin")
    sources: Mapped[list["Source"]] = relationship(back_populates="owner")

    def has_permission(self, resource: str, action: str) -> bool:
        """Check if user has specific permission."""
        if self.is_superuser:
            return True
        return any(
            p.resource == resource and p.action == action for p in self.role.permissions
        )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
