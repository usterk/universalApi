# CLAUDE.md

## Meta: 5 Zasad tego pliku

1. **Krótki > Długi** - Każda linia zużywa context window. Trzymaj tylko to, co używasz w >50% interakcji.

2. **Referencje > Snippety** - Zamiast kopiować kod, wskaż plik: `backend/app/core/plugins/base.py:15-30`.

3. **Progresywne ujawnianie** - Ten plik = overview. Szczegóły w `.claude/docs/`. Pisz "Przeczytaj X dla szczegółów".

4. **Iteruj** - Użyj `#` aby Claude dodawał przydatne rzeczy. Regularnie przeglądaj i usuwaj nieużywane.

5. **Nie lintuj przez LLM** - Style guidelines zostawiaj dla ruff/eslint. CLAUDE.md = intencje i kontekst.

---

## WHAT: UniversalAPI

**Cel:** Uniwersalny interfejs dla dokumentów + orkiestrator agentów AI (styl n8n zarządzany przez Claude Code).

**Kluczowe koncepcje:**
- **Plugin System** - serce aplikacji, każda funkcjonalność to plugin (nawet upload)
- **Documents** - uniwersalny kontener danych, tworzą drzewa (parent → children)
- **Events** - komunikacja między pluginami (document.created → handler → task → job.completed)
- **Workflows** - orkiestracja przetwarzania dokumentów

**Tech Stack:**
- Backend: FastAPI, SQLAlchemy (async), PostgreSQL, Celery, Redis
- Frontend: React, TypeScript, TanStack Query, Zustand, Radix UI

**Struktura projektu:**
```
backend/
├── app/core/           # Rdzeń: auth, database, events, plugins
├── plugins/            # Wszystkie pluginy
└── tests/              # Core tests + shared fixtures

frontend/src/
├── core/               # API client, stores, hooks
├── pages/              # Route components
└── components/         # UI components
```

---

## WHY: Architektura

| Decyzja | Dlaczego |
|---------|----------|
| Pluginy | Loose coupling, łatwe dodawanie funkcji bez zmiany core |
| Events | Chain processing, async, każdy plugin reaguje na swoje typy |
| Documents | Uniwersalny format, parent-child trees (audio → transcription → analysis) |
| Celery | Background processing, retry, rate limiting per plugin |

**Kluczowe pliki** (przeczytaj dla kontekstu architektury):
- `backend/app/core/plugins/base.py` - BasePlugin interface
- `backend/app/core/events/bus.py` - EventBus (pub/sub)
- `backend/plugins/upload/` - wzorcowy prosty plugin
- `backend/plugins/audio_transcription/` - wzorcowy plugin z dependencies

---

## HOW: Praca z Projektem

### Start / Stop / Restart

```bash
make start-all        # Start wszystkiego (RECOMMENDED)
make stop-all         # Stop
make restart-all      # Restart po zmianach (~8s)
make status           # Sprawdź status
make logs             # Zobacz logi
```

### Testowanie

```bash
make test-all                      # Wszystkie testy
make test-plugin PLUGIN=upload     # Testy konkretnego pluginu
make test-e2e                      # Tylko E2E
```

### Database

```bash
make db-migrate                           # Zastosuj migracje
make db-migrate-create NAME="opis"        # Utwórz migrację
make restart-all                          # Po zmianach w modelach
```

**Pełna lista komend:** `.claude/docs/commands-reference.md`

---

## Krytyczne Wzorce (MUST KNOW)

### ZAWSZE

- **`properties` NIE `metadata`** - SQLAlchemy rezerwuje `metadata`. Wszystkie JSONB fields nazywamy `properties`.
- **`make restart-all` po zmianach** - pluginy, modele, event handlers wymagają restartu.
- **Async/await dla DB** - wszystkie operacje bazodanowe są async.
- **bcrypt 4.0+** - NIE passlib.

### NIGDY

- Nie commituj `.env` (secrets!)
- Nie używaj `metadata` jako nazwy pola
- Nie zapominaj o `await` przy operacjach DB

### Document → Plugin Flow

```
Upload → document.created event
       → Plugin handler (sprawdza input_types)
       → Celery task (background)
       → Nowy document (child)
       → document.created event (chain)
```

### Universal Document Pattern

**WSZYSTKIE dane to Documents.** Brak specjalnych tabel dla wyników pluginów.

**ZAWSZE:**
- Plugin output → child Document (parent_id wskazuje na input)
- Dane wynikowe w Document.properties (JSONB)
- Używaj `/documents` API (brak specjalnych endpoints)
- Jedna funkcjonalność = jeden plugin

**NIGDY:**
- Osobne tabele dla wyników pluginu (np. `transcriptions`)
- Specjalne API endpoints per typ (np. `/transcriptions/{id}`)
- Dedykowane strony frontend per typ
- Plugin z wieloma wariantami (użyj osobnych pluginów)

**Szczegóły:** `.claude/docs/document-pattern.md`

---

## Dokumentacja Szczegółowa

| Potrzebujesz | Przeczytaj |
|--------------|------------|
| Universal Document Pattern | `.claude/docs/document-pattern.md` |
| Nowy plugin | `.claude/docs/plugin-development.md` |
| Testowanie | `.claude/docs/testing-guide.md` |
| Baza danych | `.claude/docs/database-patterns.md` |
| Troubleshooting | `.claude/docs/troubleshooting.md` |
| Make commands | `.claude/docs/commands-reference.md` |

---

## Quick Reference

### Ports

| Service | Port |
|---------|------|
| Backend | 8000 |
| Frontend | 5173 |
| PostgreSQL | 5432 (dev), 5433 (test) |
| Redis | 6379 |

### Auth

- **JWT tokens** (web): `Authorization: Bearer {token}`
- **API keys** (external): `X-API-Key: uapi_...`
- **Admin:** `admin@example.com` / `admin123`

### API Docs

- Swagger: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

---

## Instrukcje dla Claude

**Po zakończeniu pracy z kodem: ZAWSZE `make restart-all`**

Zmiany w pluginach, modelach i event handlers wymagają restartu aby zostały załadowane.
