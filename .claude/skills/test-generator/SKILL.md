---
name: test-generator
description: Generate comprehensive tests for UniversalAPI. Creates backend e2e/unit tests (pytest) and frontend tests (Vitest/RTL/MSW). Use when asked to generate tests, add test coverage, create test files, or write tests for endpoints/components.
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion]
---

# Test Generator Skill

You are an intelligent test generator for the UniversalAPI project. You create comprehensive, well-structured tests following project conventions.

**Trigger**: Use when user asks to:
- Generate tests for an endpoint, component, or plugin
- Add test coverage
- Create test files
- Write unit/e2e/integration tests

## Project Testing Architecture

### Backend (pytest)
- **Core tests**: `backend/tests/` - shared fixtures, core API tests
- **Plugin tests**: `backend/plugins/{name}/tests/` - plugin-specific tests
- **Fixtures**: `backend/tests/conftest.py` - all shared fixtures

### Frontend (Vitest + RTL + MSW)
- **Config**: `frontend/vitest.config.ts`
- **Setup**: `frontend/src/test/setup.ts`
- **Mocks**: `frontend/src/test/mocks/` - MSW handlers (generated from OpenAPI)
- **Tests**: `frontend/src/**/*.test.tsx`

---

## Workflow

### Phase 1: Identify Test Target

1. Determine what user wants to test:
   - **Backend endpoint** → integration test in `backend/tests/integration/`
   - **Backend function** → unit test in `backend/tests/unit/`
   - **Plugin** → tests in `backend/plugins/{name}/tests/`
   - **Frontend component** → test in `frontend/src/**/*.test.tsx`
   - **Frontend hook/util** → unit test nearby

2. Read the source file to understand:
   - Function signatures and parameters
   - Expected inputs/outputs
   - Error cases
   - Dependencies to mock

### Phase 2: Check Prerequisites

**For Backend:**
```bash
# Verify test database is available
make test-db-up
```

**For Frontend:**
```bash
# Check if Vitest is installed
grep -q "vitest" frontend/package.json
```

If frontend testing not set up, offer to run:
```bash
cd frontend && npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom msw tsx
```

### Phase 3: Generate Tests

#### Backend Integration Tests (API Endpoints)

**Location**: `backend/tests/integration/test_api_{module}.py`

**Pattern**:
```python
"""Integration tests for {module} API."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
class Test{EndpointName}:
    """Tests for /api/v1/{path} endpoint."""

    async def test_{action}_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Description of success case."""
        response = await async_client.{method}(
            "/api/v1/{path}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Add specific assertions

    async def test_{action}_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        response = await async_client.{method}("/api/v1/{path}")
        assert response.status_code == 401

    async def test_{action}_forbidden(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """User without permission should get 403."""
        # Test case for forbidden access
        pass
```

**Available Fixtures** (from conftest.py):
- `async_client` - Async HTTP client
- `auth_headers` - JWT auth headers for test_user
- `admin_auth_headers` - JWT auth headers for admin
- `test_user` - Dict with user credentials
- `test_admin` - Dict with admin credentials
- `db_session` - Database session (auto-rollback)
- `mock_event_bus` - Mocked EventBus
- `sample_audio_file`, `sample_image_file`, `sample_text_file` - File fixtures

#### Backend Unit Tests

**Location**: `backend/tests/unit/test_{module}.py`

**Pattern**:
```python
"""Unit tests for {module}."""

import pytest
from unittest.mock import Mock, patch


class Test{FunctionName}:
    """Tests for {function_name} function."""

    def test_{case}_success(self):
        """Description."""
        result = function_name(input)
        assert result == expected

    def test_{case}_with_invalid_input(self):
        """Should raise error for invalid input."""
        with pytest.raises(ValueError):
            function_name(invalid_input)
```

#### Plugin Tests

**Location**: `backend/plugins/{plugin_name}/tests/`

**Required files**:
1. `conftest.py`:
```python
"""Plugin-specific fixtures."""

import pytest
from tests.conftest import *  # noqa: F401, F403


@pytest.fixture
def plugin_specific_fixture():
    """Fixture specific to this plugin."""
    return ...
```

2. `test_unit.py`:
```python
"""Unit tests for {plugin_name} plugin."""

import pytest


@pytest.mark.plugin
class TestPluginMetadata:
    """Test plugin metadata."""

    def test_plugin_has_required_metadata(self):
        from plugins.{plugin_name}.plugin import {PluginClass}

        plugin = {PluginClass}()
        metadata = plugin.metadata

        assert metadata["name"] == "{plugin_name}"
        assert "version" in metadata
        assert "description" in metadata
```

3. `test_e2e.py`:
```python
"""End-to-end tests for {plugin_name} plugin."""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.plugin
@pytest.mark.asyncio
class Test{PluginName}E2E:
    """E2E tests for {plugin_name} plugin endpoints."""

    async def test_plugin_endpoint_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test main plugin endpoint."""
        response = await async_client.{method}(
            "/api/v1/plugins/{plugin_name}/{endpoint}",
            headers=auth_headers,
        )
        assert response.status_code in [200, 201]
```

#### Frontend Component Tests

**Location**: Same directory as component or `src/__tests__/`

**Pattern**:
```typescript
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, beforeEach } from 'vitest'
import {ComponentName} from './{ComponentName}'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  )
}

describe('{ComponentName}', () => {
  it('renders correctly', () => {
    render(<{ComponentName} />, { wrapper: createWrapper() })
    expect(screen.getByRole('...')).toBeInTheDocument()
  })

  it('handles user interaction', async () => {
    const user = userEvent.setup()
    render(<{ComponentName} />, { wrapper: createWrapper() })

    await user.click(screen.getByRole('button', { name: /submit/i }))

    await waitFor(() => {
      expect(screen.getByText(/success/i)).toBeInTheDocument()
    })
  })

  it('shows error state', async () => {
    // Test error handling
  })
})
```

### Phase 4: Verify Tests

1. **Run lint**:
```bash
make lint
```

2. **Run specific tests**:
```bash
# Backend
cd backend && poetry run pytest tests/integration/test_api_{module}.py -v

# Plugin
make test-plugin PLUGIN={plugin_name}

# Frontend
cd frontend && npm test -- {test_file}
```

3. **Report results** to user

---

## Test Scenarios Checklist

### For API Endpoints:
- [ ] Success case (authenticated)
- [ ] Unauthenticated (401)
- [ ] Forbidden/no permission (403)
- [ ] Not found (404)
- [ ] Validation error (422)
- [ ] Pagination (if applicable)
- [ ] Filtering (if applicable)
- [ ] Admin-only operations (superuser required)

### For Functions:
- [ ] Happy path with valid input
- [ ] Edge cases (empty, null, boundary values)
- [ ] Error cases (invalid input, exceptions)
- [ ] Mocked dependencies

### For Components:
- [ ] Initial render
- [ ] User interactions (click, type, submit)
- [ ] Loading states
- [ ] Error states
- [ ] Empty states

---

## Important Rules

### DO:
- Read source code before writing tests
- Use existing fixtures from conftest.py
- Follow project naming conventions
- Add appropriate pytest markers (@pytest.mark.integration, etc.)
- Test both success and failure cases
- Use descriptive test names

### DON'T:
- Create tests without reading the source
- Duplicate existing fixtures
- Skip error case testing
- Use hardcoded IDs that may not exist
- Forget to import fixtures properly

---

## Running Tests

```bash
# All backend tests
make test-all

# Core tests only
make test-core

# All plugin tests
make test-plugins

# Specific plugin
make test-plugin PLUGIN=upload

# E2E tests only
make test-e2e

# Frontend tests
make test-frontend

# Everything
make test-full

# With coverage
make test-with-coverage
```

---

## Examples

### Example 1: Generate tests for /api/v1/documents endpoint

User: "Generate tests for documents API"

1. Read `backend/app/api/v1/documents.py`
2. Identify endpoints: GET /documents, GET /documents/{id}, DELETE /documents/{id}
3. Create `backend/tests/integration/test_api_documents.py`
4. Include tests for:
   - List documents (authenticated, unauthenticated, pagination)
   - Get single document (found, not found, forbidden)
   - Delete document (success, not found, forbidden)
5. Run tests: `cd backend && poetry run pytest tests/integration/test_api_documents.py -v`

### Example 2: Generate tests for new plugin

User: "Create tests for my_plugin"

1. Read `backend/plugins/my_plugin/plugin.py`
2. Create test directory structure:
   - `backend/plugins/my_plugin/tests/__init__.py`
   - `backend/plugins/my_plugin/tests/conftest.py`
   - `backend/plugins/my_plugin/tests/test_unit.py`
   - `backend/plugins/my_plugin/tests/test_e2e.py`
3. Run tests: `make test-plugin PLUGIN=my_plugin`

### Example 3: Generate frontend component test

User: "Add tests for Login component"

1. Read `frontend/src/pages/Login.tsx`
2. Check if test infrastructure exists
3. Create `frontend/src/pages/Login.test.tsx`
4. Include tests for render, submit, error states
5. Run: `cd frontend && npm test -- Login.test.tsx`

---

## Communication

- Ask for clarification if target is ambiguous
- Report which tests were generated
- Show how to run the tests
- Warn if prerequisites are missing
