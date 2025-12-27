# Plugin Development Guide

Ten plik zawiera szczegółowe informacje o tworzeniu pluginów dla UniversalAPI.

## Struktura Pluginu

Każdy plugin znajduje się w `/backend/plugins/{plugin_name}/`:

```
plugins/my_plugin/
├── __init__.py           # REQUIRED: Eksportuje klasę pluginu
├── plugin.py             # REQUIRED: Główna klasa (dziedziczy z BasePlugin)
├── README.md             # REQUIRED: Dokumentacja pluginu
├── models.py             # OPTIONAL: SQLAlchemy models
├── router.py             # OPTIONAL: FastAPI routes
├── tasks.py              # OPTIONAL: Celery background tasks
├── handlers.py           # OPTIONAL: Event handlers
└── tests/                # REQUIRED: Testy
    ├── conftest.py       # Import shared fixtures
    ├── test_unit.py      # Unit tests
    └── test_e2e.py       # REQUIRED: E2E tests
```

## BasePlugin Interface

Klasa bazowa: `backend/app/core/plugins/base.py`

### Wymagane właściwości

```python
from app.core.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    @property
    def metadata(self) -> dict:
        return {
            "name": "my_plugin",           # Unikalna nazwa (slug)
            "version": "1.0.0",
            "description": "Opis pluginu",
            "author": "Your Name",
            "priority": 50,                # Niższy = wcześniej ładowany
            "dependencies": ["upload"],    # Lista zależności od innych pluginów
            "input_types": ["audio"],      # Jakie typy dokumentów przetwarza
            "output_type": "transcription" # Jaki typ tworzy
        }

    @property
    def capabilities(self) -> dict:
        return {
            "has_routes": True,            # Ma FastAPI router
            "has_models": True,            # Ma modele bazodanowe
            "has_tasks": True,             # Ma Celery tasks
            "has_event_handlers": True,    # Subskrybuje eventy
            "has_frontend": False,         # Ma komponenty frontend
            "has_document_types": True     # Rejestruje nowe typy dokumentów
        }
```

### Metody opcjonalne

```python
class MyPlugin(BasePlugin):
    # Zwraca FastAPI router
    def get_router(self) -> APIRouter:
        from .router import router
        return router

    # Zwraca listę SQLAlchemy models
    def get_models(self) -> list:
        from .models import MyModel
        return [MyModel]

    # Zwraca dict Celery tasks
    def get_tasks(self) -> dict:
        from .tasks import process_document
        return {"process": process_document}

    # Zwraca dict event handlers
    def get_event_handlers(self) -> dict:
        return {
            "document.created": self._on_document_created
        }

    # Rejestruje nowe typy dokumentów
    def get_document_types(self) -> list:
        return [{
            "name": "my_type",
            "display_name": "My Document Type",
            "mime_types": ["application/x-my-type"]
        }]

    # Hook uruchamiany przy starcie aplikacji
    async def on_startup(self):
        pass

    # Hook uruchamiany przy zamknięciu
    async def on_shutdown(self):
        pass
```

## Plugin Priority Guidelines

| Priority | Typ pluginu | Przykład |
|----------|-------------|----------|
| 10-19 | Storage/upload | `upload` |
| 20-39 | Primary processing | `audio_transcription`, `ocr` |
| 40-69 | Secondary processing | `analysis`, `enrichment` |
| 70-99 | Indexing/search | `vector_search`, `elasticsearch` |
| 100+ | Automation | `notifications`, `webhooks` |

## Event Handlers

### Subskrybowanie eventów

```python
async def on_startup(self):
    from app.core.events.bus import get_event_bus
    event_bus = get_event_bus()
    event_bus.subscribe("document.created", self._handle_document)

async def _handle_document(self, event):
    document_id = event.payload["document_id"]
    document_type = event.payload.get("type_name")

    # Sprawdź czy plugin powinien przetwarzać ten dokument
    if document_type not in self.metadata["input_types"]:
        return

    # Kolejkuj task
    from .tasks import process_document
    process_document.delay(str(document_id))
```

### Emitowanie eventów

```python
from app.core.events.bus import get_event_bus

event_bus = get_event_bus()
await event_bus.emit(
    event_type="document.created",
    source="my_plugin",
    payload={"document_id": str(doc.id), "type_name": "my_type"},
    severity="info",
    persist=True
)
```

## Celery Tasks

```python
from celery import shared_task
import asyncio

@shared_task(
    bind=True,
    name="my_plugin.process",      # Format: {plugin}.{task}
    queue="my_plugin",              # Osobna kolejka
    max_retries=3,
    default_retry_delay=60
)
def process_document(self, document_id: str):
    """
    WAŻNE:
    1. Importy wewnątrz funkcji (unikaj circular imports)
    2. Wrap async code with asyncio.run()
    3. Emituj eventy dla progress tracking
    """
    from app.core.events.bus import get_event_bus
    from app.core.database.session import async_session_factory

    async def _process():
        event_bus = get_event_bus()

        # Emit job.started
        await event_bus.emit(
            event_type="job.started",
            source="my_plugin",
            payload={"document_id": document_id}
        )

        async with async_session_factory() as session:
            # Process document...
            pass

        # Emit job.completed
        await event_bus.emit(
            event_type="job.completed",
            source="my_plugin",
            payload={"document_id": document_id}
        )

    asyncio.run(_process())
```

## Plugin Testing Requirements

### Wymagane testy

Każdy plugin MUSI mieć:
- `tests/conftest.py` - import shared fixtures
- `tests/test_unit.py` - unit tests
- `tests/test_e2e.py` - end-to-end tests

### conftest.py pattern

```python
# plugins/my_plugin/tests/conftest.py
import pytest
from tests.conftest import *  # noqa: Import wszystkich shared fixtures
from tests.e2e.conftest import *  # noqa

@pytest.fixture
def my_plugin_fixture():
    """Plugin-specific fixture."""
    return ...
```

### Uruchamianie testów

```bash
# Wszystkie testy pluginu
make test-plugin PLUGIN=my_plugin

# Tylko E2E
make test-e2e

# Konkretny test file
cd backend && poetry run pytest plugins/my_plugin/tests/test_e2e.py -v
```

## Checklist Tworzenia Pluginu

1. [ ] Utworzyć katalog `/backend/plugins/{plugin_name}/`
2. [ ] Utworzyć `__init__.py` eksportujący klasę pluginu
3. [ ] Zaimplementować `plugin.py` z BasePlugin
4. [ ] Utworzyć `README.md` (użyj `plugins/PLUGIN_TEMPLATE.md`)
5. [ ] Utworzyć `tests/` z conftest.py, test_unit.py, test_e2e.py
6. [ ] Jeśli plugin ma modele: utworzyć migration
   ```bash
   make db-migrate-create NAME="add_{plugin_name}_tables"
   ```
7. [ ] Dodać plugin do `PLUGINS_ENABLED` w `.env`
8. [ ] Uruchomić testy: `make test-plugin PLUGIN={plugin_name}`
9. [ ] Zrestartować backend: `make restart-all`

## Referencje

- `backend/app/core/plugins/base.py` - BasePlugin class
- `backend/app/core/plugins/loader.py` - Plugin discovery
- `backend/plugins/upload/` - Wzorcowy prosty plugin
- `backend/plugins/audio_transcription/` - Wzorcowy plugin z dependencies
- `backend/plugins/PLUGIN_TEMPLATE.md` - Template README
