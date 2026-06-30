"""Tests for sql_agents/agents/agent_config.py module."""
# pylint: disable=redefined-outer-name,import-outside-toplevel,invalid-name

import importlib
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_project_client():
    """Create a mock AI project client."""
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
    """Test agent model type mapping and instance creation."""
    # Re-import to re-evaluate class variable with patched env
    from backend.sql_agents.agents import agent_config
    importlib.reload(agent_config)

    agent_type = agent_config.AgentType
    agent_base_config = agent_config.AgentBaseConfig

    # Test model_type mapping
    assert agent_base_config.model_type[agent_type.MIGRATOR] == "migrator-model"
    assert agent_base_config.model_type[agent_type.PICKER] == "picker-model"
    assert agent_base_config.model_type[agent_type.FIXER] == "fixer-model"
    assert agent_base_config.model_type[agent_type.SEMANTIC_VERIFIER] == "semantic-verifier-model"
    assert agent_base_config.model_type[agent_type.SYNTAX_CHECKER] == "syntax-checker-model"
    assert agent_base_config.model_type[agent_type.SELECTION] == "selection-model"
    assert agent_base_config.model_type[agent_type.TERMINATION] == "termination-model"

    # Test __init__ stores params correctly
    config = agent_base_config(mock_project_client, sql_from="sql1", sql_to="sql2")
    assert config.ai_project_client == mock_project_client
    assert config.sql_from == "sql1"
    assert config.sql_to == "sql2"
