# Testing Guide

Ten plik zawiera szczegółowe informacje o testowaniu w UniversalAPI.

## Struktura Testów

```
backend/
├── tests/                        # Core tests
│   ├── conftest.py               # SHARED FIXTURES (critical!)
│   ├── unit/                     # Unit tests (mocked dependencies)
│   ├── integration/              # Tests with database
│   ├── e2e/                      # End-to-end tests
│   │   └── conftest.py           # E2E-specific fixtures
│   └── fixtures/
│       └── factories.py          # Test data factories
│
└── plugins/
    └── {plugin_name}/
        └── tests/                # Plugin tests CLOSE to code
            ├── conftest.py       # Imports from tests.conftest
            ├── test_unit.py
            └── test_e2e.py       # REQUIRED
```

## Test Database

Testy używają osobnej bazy danych na **porcie 5433** (nie 5432).

### Uruchomienie test database

```bash
# Start test PostgreSQL
make test-db-up

# Stop test database
make test-db-stop
```

### Docker Compose Test Config

Plik: `docker-compose.test.yml`
- PostgreSQL na porcie **5433**
- Redis na porcie **6380**
- Używa **tmpfs** dla szybkości (brak persystencji)

## Shared Fixtures (tests/conftest.py)

### Kluczowe fixtures

| Fixture | Opis |
|---------|------|
| `test_settings` | Ustawienia testowe |
| `test_engine` | SQLAlchemy async engine |
| `db_session` | Async database session (auto-rollback) |
| `async_client` | httpx AsyncClient dla API tests |
| `test_user` | Test user fixture |
| `test_admin` | Admin user fixture |
| `auth_headers` | JWT authentication headers |
| `mock_event_bus` | Mocked EventBus |

### Użycie w testach

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_documents(async_client: AsyncClient, auth_headers: dict):
    response = await async_client.get(
        "/api/v1/documents/",
        headers=auth_headers
    )
    assert response.status_code == 200
```

## Plugin Test Pattern

### conftest.py

```python
# plugins/my_plugin/tests/conftest.py
import pytest
from tests.conftest import *  # noqa: Import all shared fixtures
from tests.e2e.conftest import *  # noqa

@pytest.fixture
def sample_audio_file():
    """Plugin-specific fixture."""
    return Path(__file__).parent / "fixtures" / "sample.mp3"

@pytest.fixture
def processed_document(db_session, test_user):
    """Create test document for plugin tests."""
    doc = Document(
        owner_id=test_user.id,
        type_name="audio",
        properties={"original_filename": "test.mp3"}
    )
    db_session.add(doc)
    return doc
```

### Unit tests

```python
# plugins/my_plugin/tests/test_unit.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_process_audio(sample_audio_file):
    """Test audio processing logic."""
    with patch('plugins.my_plugin.tasks.transcribe') as mock_transcribe:
        mock_transcribe.return_value = {"text": "Hello world"}
        result = await process_audio(sample_audio_file)
        assert result["text"] == "Hello world"
```

### E2E tests

```python
# plugins/my_plugin/tests/test_e2e.py
import pytest
from httpx import AsyncClient

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_upload_and_process(async_client: AsyncClient, auth_headers: dict):
    """Full flow: upload -> process -> verify result."""
    # Upload file
    with open("tests/fixtures/sample.mp3", "rb") as f:
        response = await async_client.post(
            "/api/v1/plugins/upload/files",
            headers=auth_headers,
            files={"file": ("sample.mp3", f, "audio/mpeg")}
        )
    assert response.status_code == 201
    doc_id = response.json()["id"]

    # Wait for processing (in real tests use polling or events)
    # ...

    # Verify result
    response = await async_client.get(
        f"/api/v1/documents/{doc_id}/children",
        headers=auth_headers
    )
    assert response.status_code == 200
```

## Pytest Configuration

Plik: `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests", "plugins"]   # Discovers tests in both locations
asyncio_mode = "auto"              # Auto async test support
markers = [
    "slow: slow tests",
    "integration: integration tests",
    "e2e: end-to-end tests",
    "plugin: plugin-specific tests",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]
```

## Test Commands

### Podstawowe komendy

```bash
# Wszystkie testy
make test-all

# Z coverage report
make test-with-coverage

# Core tests only (backend/tests/)
make test-core

# Wszystkie plugin tests
make test-plugins

# Konkretny plugin
make test-plugin PLUGIN=upload
make test-plugin PLUGIN=audio_transcription

# Tylko E2E tests
make test-e2e
```

### Zaawansowane

```bash
# Konkretny test file
cd backend && poetry run pytest tests/unit/test_auth.py -v

# Konkretny test
cd backend && poetry run pytest tests/unit/test_auth.py::test_login -v

# Z outputem print statements
cd backend && poetry run pytest -s

# Tylko failed tests
cd backend && poetry run pytest --lf

# Parallel execution
cd backend && poetry run pytest -n auto
```

## Test Markers

### Używanie markerów

```python
import pytest

@pytest.mark.slow
def test_heavy_processing():
    """Marked as slow - can be skipped with -m "not slow"."""
    pass

@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_integration(db_session):
    """Integration test requiring database."""
    pass

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_flow(async_client):
    """End-to-end test."""
    pass
```

### Filtrowanie po markerach

```bash
# Tylko E2E
cd backend && poetry run pytest -m e2e

# Wszystko oprócz slow
cd backend && poetry run pytest -m "not slow"

# Integration i E2E
cd backend && poetry run pytest -m "integration or e2e"
```

## Async Testing

### Pattern dla async tests

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_document(db_session: AsyncSession):
    """Async test with database session."""
    doc = Document(name="test")
    db_session.add(doc)
    await db_session.flush()

    result = await db_session.get(Document, doc.id)
    assert result.name == "test"
    # Session auto-rollbacks after test
```

### Mocking async functions

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_with_mock():
    mock_service = AsyncMock()
    mock_service.process.return_value = {"status": "ok"}

    result = await mock_service.process("data")
    assert result["status"] == "ok"
```

## Coverage

### Generowanie raportu

```bash
# HTML report
make test-with-coverage
# Otwórz: backend/htmlcov/index.html

# Console report
cd backend && poetry run pytest --cov=app --cov=plugins --cov-report=term-missing
```

### Coverage requirements

- Minimum: 70% dla core
- Minimum: 60% dla plugins
- E2E tests: REQUIRED dla każdego pluginu

## Debugging Tests

### VSCode launch.json

```json
{
    "name": "Pytest: Current File",
    "type": "python",
    "request": "launch",
    "module": "pytest",
    "args": ["${file}", "-v", "-s"],
    "cwd": "${workspaceFolder}/backend",
    "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
    }
}
```

### pdb debugging

```python
def test_with_debugger():
    import pdb; pdb.set_trace()  # Breakpoint
    result = some_function()
    assert result == expected
```

## Referencje

- `backend/tests/conftest.py` - Shared fixtures
- `backend/tests/e2e/conftest.py` - E2E fixtures
- `backend/tests/fixtures/factories.py` - Test factories
- `backend/pyproject.toml` - Pytest configuration
