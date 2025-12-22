"""UniversalAPI Test Suite.

This package contains tests for the UniversalAPI application.

Test Structure:
    tests/
    ├── conftest.py          # Shared fixtures for all tests
    ├── unit/                # Unit tests (no external dependencies)
    ├── integration/         # Integration tests (with database)
    └── fixtures/            # Test data factories

Plugin tests are located within each plugin directory:
    plugins/{plugin_name}/tests/

Run all tests:
    make test

Run specific test categories:
    make test-core       # Core tests only
    make test-plugins    # Plugin tests only
    make test-plugin PLUGIN=upload  # Specific plugin
"""
