---
name: python-test-conventions
description: >
  Apply when writing Python tests for this repo. Enforces pytest conventions,
  file naming, class structure, mock style, and coverage requirements.
  USE FOR: generating, reviewing, or extending pytest test files.
  DO NOT USE FOR: non-Python tests, running tests, diagnosing failures.
applyTo: "src/tests/**/*.py"
---

# Python Test Conventions

## Framework
- pytest + pytest-asyncio (`asyncio_mode = "auto"`)
- Use `unittest.mock` — never `pytest-mock`

## File naming
- Files: `*_test.py` (e.g. `agent_manager_test.py`)
- Place under `src/tests/backend/` mirroring the source tree

## Import order (strict)
1. stdlib (`os`, `uuid`, `datetime`)
2. `unittest.mock` (`AsyncMock`, `MagicMock`, `patch`)
3. source imports (`from backend.module import ...`)
4. `pytest`

## Class structure
- One class per function under test: `class TestFunctionName:`
- Each class has a docstring: `"""Tests for function_name function."""`

## Test methods
- Naming: `test_<function>_<scenario>` (e.g. `test_set_sql_agents_replaces_existing`)
- Each method has a one-line docstring

## Async tests
- Decorate with `@pytest.mark.asyncio`
- Use `AsyncMock` for async dependencies

## Fixtures
- Defined at module level with `@pytest.fixture`
- Use `patch` as a context manager inside tests, not as a decorator on classes

## Shared setup
- Use module-level helper functions (e.g. `create_mock_file_data()`) for repeated object construction

## Coverage
- Minimum 80% (`fail_under = 80` in `pyproject.toml`)
- Branch coverage enabled

## sys.path / imports
- `conftest.py` at `src/tests/` adds `src/backend` to `sys.path`
- Always import source as `from backend.module import ...`
