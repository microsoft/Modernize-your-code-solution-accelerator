# Test Plan

## Phase 1 — `common/telemetry`
**Target:** `src/backend/common/telemetry/patch_instrumentor.py`  
**Output:** `src/tests/backend/common/telemetry/patch_instrumentor_test.py`

- [x] `_fixed_response_to_str` — None, str, empty str, dict, nested dict, non-JSON-serialisable, int, list
- [x] `_patch_fastapi_route_details` — ImportError path, success replaces attribute, exception inside try caught
- [x] `patch_instrumentors` — agents patch, projects patch, both ImportError paths, delegates to `_patch_fastapi_route_details`

## Phase 2 — `sql_agents/helpers/models.py`
**Target:** `src/backend/sql_agents/helpers/models.py`  
**Output:** `src/tests/backend/sql_agents/helpers/models_test.py`

- [x] All `AgentType` member values
- [x] `__new__` lowercases string input
- [x] `_missing_` returns `AgentType.ALL` for unknown string

## Phase 3 — Sub-agent classes and responses
**Targets:** `sql_agents/agents/{fixer,migrator,picker,semantic_verifier,syntax_checker}/`  
**Outputs:** `src/tests/backend/sql_agents/agents/{fixer,migrator,picker,semantic_verifier,syntax_checker}_test.py`

For each agent: response_object, deployment_name, num_candidates (where applicable), plugins (syntax_checker)  
For each setup function: calls `SQLAgentFactory.create_agent` with correct `AgentType` and kwargs  
For each response model: field instantiation and field presence
