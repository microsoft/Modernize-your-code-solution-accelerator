# Test Research

## Target

`src/backend` — Python/FastAPI backend for the Modernize-your-code accelerator.

## Test conventions (from `src/tests/backend`)

- File naming: `*_test.py`
- Framework: `pytest`, `pytest-asyncio` (`asyncio_mode = "auto"` in `pyproject.toml`), `pytest-mock`
- Imports: either `from backend.module import X` (sql_agents) or `from common.module import X` (common) — both work because `conftest.py` adds `src/backend` to `sys.path`
- Mocking: `unittest.mock.patch`, `AsyncMock`, `MagicMock`; `mocker` fixture from pytest-mock
- Async tests: `@pytest.mark.asyncio` decorator; some tests omit it due to `asyncio_mode = "auto"`
- Test classes: `class TestXxx:` grouping preferred for module-level tests
- Fixtures: function-scoped by default

## Source → test pairing (gaps identified)

| Source file | Test file | Status |
|---|---|---|
| `common/telemetry/patch_instrumentor.py` | (none) | **MISSING** |
| `sql_agents/helpers/models.py` | (none) | **MISSING** |
| `sql_agents/agents/fixer/agent.py` | (none) | **MISSING** |
| `sql_agents/agents/fixer/response.py` | (none) | **MISSING** |
| `sql_agents/agents/fixer/setup.py` | (none) | **MISSING** |
| `sql_agents/agents/migrator/agent.py` | (none) | **MISSING** |
| `sql_agents/agents/migrator/response.py` | (none) | **MISSING** |
| `sql_agents/agents/migrator/setup.py` | (none) | **MISSING** |
| `sql_agents/agents/picker/agent.py` | (none) | **MISSING** |
| `sql_agents/agents/picker/response.py` | (none) | **MISSING** |
| `sql_agents/agents/picker/setup.py` | (none) | **MISSING** |
| `sql_agents/agents/semantic_verifier/agent.py` | (none) | **MISSING** |
| `sql_agents/agents/semantic_verifier/response.py` | (none) | **MISSING** |
| `sql_agents/agents/semantic_verifier/setup.py` | (none) | **MISSING** |
| `sql_agents/agents/syntax_checker/agent.py` | (none) | **MISSING** |
| `sql_agents/agents/syntax_checker/response.py` | (none) | **MISSING** |
| `sql_agents/agents/syntax_checker/setup.py` | (none) | **MISSING** |

## Acceptance checklist

1. `_fixed_response_to_str` handles None / str / dict / non-serializable
2. `_patch_fastapi_route_details` silently returns on ImportError
3. `_patch_fastapi_route_details` replaces `_get_route_details` on success
4. `patch_instrumentors` patches agents/projects instrumentors and calls route-details patch
5. `AgentType` enum: all member values, lowercase normalisation, `_missing_` fallback
6. `FixerAgent.response_object` returns `FixerResponse`; `deployment_name` uses `AgentType.FIXER`
7. `MigratorAgent.response_object`, `deployment_name`, `num_candidates == 3`
8. `PickerAgent.response_object`, `deployment_name`, `num_candidates == 3`
9. `SemanticVerifierAgent.response_object`, `deployment_name`
10. `SyntaxCheckerAgent.response_object`, `deployment_name`, `plugins` includes `SyntaxCheckerPlugin`
11. `setup_fixer_agent` / `setup_migrator_agent` / `setup_picker_agent` / `setup_semantic_verifier_agent` / `setup_syntax_checker_agent` each call `SQLAgentFactory.create_agent` with the right `AgentType`
12. Response model instantiation: `FixerResponse`, `MigratorResponse`/`MigratorCandidate`, `PickerResponse`, `SemanticVerifierResponse`, `SyntaxCheckerResponse`/`SyntaxErrorInt`
