from unittest.mock import MagicMock

import pytest

from sql_agents.agents.fixer.agent import FixerAgent
from sql_agents.agents.fixer.response import FixerResponse
from sql_agents.helpers.models import AgentType


@pytest.fixture
def mock_config():
    """Fixture to mock the config for FixerAgent."""
    mock_config = MagicMock()
    mock_config.model_type = {
        AgentType.FIXER: "fixer_model_name"
    }
    return mock_config


@pytest.fixture
def fixer_agent(mock_config):
    """Fixture to create an instance of FixerAgent with a mocked config."""
    agent = FixerAgent(config=mock_config, agent_type=AgentType.FIXER)
    return agent


def test_response_object(fixer_agent):
    """Test the response_object property."""
    assert fixer_agent.response_object == FixerResponse


def test_deployment_name(fixer_agent):
    """Test the deployment_name property."""
    assert fixer_agent.deployment_name == "fixer_model_name"
