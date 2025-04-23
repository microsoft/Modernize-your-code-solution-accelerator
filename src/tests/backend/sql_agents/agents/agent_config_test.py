import importlib
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_project_client():
    return AsyncMock()


@patch.dict("os.environ", {
    "MIGRATOR_AGENT_MODEL_DEPLOY": "migrator-model",
    "PICKER_AGENT_MODEL_DEPLOY": "picker-model",
    "FIXER_AGENT_MODEL_DEPLOY": "fixer-model",
    "SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY": "semantic-verifier-model",
    "SYNTAX_CHECKER_AGENT_MODEL_DEPLOY": "syntax-checker-model",
    "SELECTION_MODEL_DEPLOY": "selection-model",
    "TERMINATION_MODEL_DEPLOY": "termination-model",
})
def test_agent_model_type_mapping_and_instance(mock_project_client):
    # Re-import to re-evaluate class variable with patched env
    from sql_agents.agents import agent_config
    importlib.reload(agent_config)

    AgentType = agent_config.AgentType
    AgentBaseConfig = agent_config.AgentBaseConfig

    # Test model_type mapping
    assert AgentBaseConfig.model_type[AgentType.MIGRATOR] == "migrator-model"
    assert AgentBaseConfig.model_type[AgentType.PICKER] == "picker-model"
    assert AgentBaseConfig.model_type[AgentType.FIXER] == "fixer-model"
    assert AgentBaseConfig.model_type[AgentType.SEMANTIC_VERIFIER] == "semantic-verifier-model"
    assert AgentBaseConfig.model_type[AgentType.SYNTAX_CHECKER] == "syntax-checker-model"
    assert AgentBaseConfig.model_type[AgentType.SELECTION] == "selection-model"
    assert AgentBaseConfig.model_type[AgentType.TERMINATION] == "termination-model"

    # Test __init__ stores params correctly
    config = AgentBaseConfig(mock_project_client, sql_from="sql1", sql_to="sql2")
    assert config.ai_project_client == mock_project_client
    assert config.sql_from == "sql1"
    assert config.sql_to == "sql2"
