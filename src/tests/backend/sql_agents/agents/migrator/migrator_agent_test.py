from unittest.mock import MagicMock

import pytest

from sql_agents.agents.migrator.agent import MigratorAgent
from sql_agents.agents.migrator.response import MigratorResponse
from sql_agents.helpers.models import AgentType


@pytest.fixture
def mock_config():
    mock = MagicMock()
    mock.model_type = {
        AgentType.MIGRATOR: "migrator-model-name"
    }
    return mock


@pytest.fixture
def migrator_agent(mock_config):
    return MigratorAgent(config=mock_config, agent_type=AgentType.MIGRATOR)


def test_response_object(migrator_agent):
    """Test that the response_object returns MigratorResponse."""
    assert migrator_agent.response_object is MigratorResponse


def test_num_candidates(migrator_agent):
    """Test that the num_candidates property returns 3."""
    assert migrator_agent.num_candidates == 3


def test_deployment_name(migrator_agent):
    """Test that the correct model name is returned from config."""
    assert migrator_agent.deployment_name == "migrator-model-name"
