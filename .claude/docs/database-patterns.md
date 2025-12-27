# Database Patterns Guide

Ten plik zawiera wzorce pracy z bazą danych w UniversalAPI.

## Podstawy

- **Driver:** asyncpg (async PostgreSQL)
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Extensions:** pgvector (embeddings)

## CRITICAL: `properties` nie `metadata`

SQLAlchemy rezerwuje atrybut `metadata`. Wszystkie pola JSON nazywamy `properties`:

```python
# POPRAWNIE
class Document(Base):
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)

# NIEPOPRAWNIE - spowoduje konflikt
class Document(Base):
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)  # ERROR!
```

## Async Session Patterns

### Pattern 1: FastAPI Dependency (RECOMMENDED)

```python
from app.core.database.session import AsyncSessionDep

@router.post("/documents/")
async def create_document(
    data: DocumentCreate,
    db: AsyncSessionDep  # Auto-inject session
):
    doc = Document(**data.model_dump())
    db.add(doc)
    # Commit happens automatically when function returns
    # Rollback happens automatically on exception
    return doc
```

### Pattern 2: Manual Session

```python
from app.core.database.session import async_session_factory

async def process_in_background():
    async with async_session_factory() as session:
        try:
            doc = Document(name="test")
            session.add(doc)
            await session.commit()
            await session.refresh(doc)
            return doc
        except Exception:
            await session.rollback()
            raise
```

### Pattern 3: W Celery Tasks

```python
import asyncio
from app.core.database.session import async_session_factory

@shared_task
def process_document(doc_id: str):
    async def _process():
        async with async_session_factory() as session:
            doc = await session.get(Document, UUID(doc_id))
            doc.status = "processed"
            await session.commit()

    asyncio.run(_process())
```

## Query Patterns

### Basic Queries

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Get by ID
doc = await session.get(Document, doc_id)

# Get or 404
doc = await session.get(Document, doc_id)
if not doc:
    raise HTTPException(status_code=404, detail="Document not found")

# Select with filter
stmt = select(Document).where(Document.owner_id == user.id)
result = await session.execute(stmt)
docs = result.scalars().all()

# Select one or none
stmt = select(Document).where(Document.checksum == checksum)
result = await session.execute(stmt)
doc = result.scalar_one_or_none()
```

### Eager Loading (avoid N+1)

```python
# Load with relationships
stmt = (
    select(Document)
    .where(Document.owner_id == user.id)
    .options(selectinload(Document.children))
    .options(selectinload(Document.document_type))
)
result = await session.execute(stmt)
docs = result.scalars().all()
```

### Pagination

```python
from sqlalchemy import func

stmt = (
    select(Document)
    .where(Document.owner_id == user.id)
    .order_by(Document.created_at.desc())
    .offset(skip)
    .limit(limit)
)
result = await session.execute(stmt)
docs = result.scalars().all()

# Count
count_stmt = select(func.count()).select_from(Document).where(Document.owner_id == user.id)
total = (await session.execute(count_stmt)).scalar()
```

### JSONB Queries (properties field)

```python
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import JSONB

# Filter by JSONB field
stmt = select(Document).where(
    Document.properties["status"].astext == "active"
)

# Check if key exists
stmt = select(Document).where(
    Document.properties.has_key("original_filename")
)

# Contains value
stmt = select(Document).where(
    Document.properties.contains({"mime_type": "audio/mpeg"})
)
```

## Transaction Management

### Nested Transactions (Savepoints)

```python
async with session.begin_nested():
    # This creates a savepoint
    doc = Document(name="test")
    session.add(doc)
    # If exception here, only this savepoint rolls back
```

### Explicit Transaction Control

```python
async with session.begin():
    # Explicit transaction
    doc1 = Document(name="test1")
    doc2 = Document(name="test2")
    session.add_all([doc1, doc2])
    # Commit at end of block
```

## Migrations

### Workflow

```bash
# 1. Zmień model w kodzie

# 2. Wygeneruj migrację
make db-migrate-create NAME="add_new_field_to_documents"

# 3. Przejrzyj wygenerowany plik w alembic/versions/

# 4. Zastosuj migrację
make db-migrate

# 5. Restart backend (models nie hot-reloadują)
make restart-all
```

### Core vs Plugin Migrations

**Core migrations:** `backend/alembic/versions/`
- users, documents, sources, plugins
- Named: `{hash}_{description}.py`

**Plugin migrations:** też w `alembic/versions/`
- Named: `{hash}_add_{plugin_name}_tables.py`
- Przykład: `0b5913df4a79_add_audio_transcription_tables.py`

### Migration Template

```python
"""Add new field to documents

Revision ID: abc123
Revises: def456
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'abc123'
down_revision = 'def456'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('documents',
        sa.Column('new_field', sa.String(100), nullable=True)
    )

def downgrade():
    op.drop_column('documents', 'new_field')
```

### Seeding Data in Migrations

```python
def upgrade():
    # Create table
    op.create_table('document_types', ...)

    # Seed data
    op.execute("""
        INSERT INTO document_types (name, display_name, mime_types)
        VALUES
            ('audio', 'Audio File', ARRAY['audio/mpeg', 'audio/wav']),
            ('document', 'Document', ARRAY['application/pdf', 'text/plain'])
    """)
```

## Model Patterns

### Base Model

```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, func
from app.core.database.base import Base
import uuid

class MyModel(Base):
    __tablename__ = "my_models"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[DateTime] = mapped_column(default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(default=func.now(), onupdate=func.now())

    # JSONB field - ALWAYS use 'properties', not 'metadata'
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)
```

### Relationships

```python
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

class Document(Base):
    # Parent relationship
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True
    )
    parent: Mapped["Document"] = relationship(
        back_populates="children",
        remote_side="Document.id"
    )

    # Children relationship
    children: Mapped[list["Document"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan"
    )

    # Many-to-one
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    owner: Mapped["User"] = relationship(back_populates="documents")
```

## Common Pitfalls

### 1. Brakujący await

```python
# NIEPOPRAWNIE - brakuje await
def get_doc(db, doc_id):
    result = db.execute(select(Document))  # Missing await!
    return result.scalar()

# POPRAWNIE
async def get_doc(db, doc_id):
    result = await db.execute(select(Document))
    return result.scalar()
```

### 2. Session scope

```python
# NIEPOPRAWNIE - session poza scope
async def bad_pattern():
    async with async_session_factory() as session:
        doc = await session.get(Document, id)
    # Session closed here!
    return doc.name  # May fail - detached object

# POPRAWNIE
async def good_pattern():
    async with async_session_factory() as session:
        doc = await session.get(Document, id)
        name = doc.name  # Access inside scope
    return name
```

### 3. Lazy loading w async

```python
# NIEPOPRAWNIE - lazy loading nie działa w async
doc = await session.get(Document, id)
children = doc.children  # Error! Lazy load w async

# POPRAWNIE - eager loading
stmt = select(Document).options(selectinload(Document.children))
result = await session.execute(stmt.where(Document.id == id))
doc = result.scalar_one()
children = doc.children  # OK - already loaded
```

## Referencje

- `backend/app/core/database/session.py` - Session factory
- `backend/app/core/database/base.py` - Base model
- `backend/alembic/` - Migrations
- `backend/app/core/documents/models.py` - Document model example
