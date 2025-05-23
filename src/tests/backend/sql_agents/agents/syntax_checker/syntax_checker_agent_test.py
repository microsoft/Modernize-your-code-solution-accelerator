from unittest.mock import MagicMock

import pytest

from sql_agents.agents.syntax_checker.agent import SyntaxCheckerAgent
from sql_agents.agents.syntax_checker.plug_ins import SyntaxCheckerPlugin
from sql_agents.agents.syntax_checker.response import SyntaxCheckerResponse
from sql_agents.helpers.models import AgentType


@pytest.fixture
def mock_config():
    """Fixture to create a mock configuration."""
    mock_config = MagicMock()
    mock_config.model_type = {
        AgentType.SYNTAX_CHECKER: "syntax_checker_model"
    }
    return mock_config


@pytest.fixture
def syntax_checker_agent(mock_config):
    """Fixture to create a SyntaxCheckerAgent instance."""
    agent = SyntaxCheckerAgent(
        agent_type=AgentType.SYNTAX_CHECKER,
        config=mock_config
    )
    return agent


def test_response_object(syntax_checker_agent):
    """Test that the response_object property returns SyntaxCheckerResponse."""
    assert syntax_checker_agent.response_object == SyntaxCheckerResponse


def test_plugins(syntax_checker_agent):
    """Test that the plugins property returns the correct plugins."""
    plugins = syntax_checker_agent.plugins
    assert isinstance(plugins, list)
    assert plugins[0] == "check_syntax"
    assert isinstance(plugins[1], SyntaxCheckerPlugin)


def test_deployment_name(syntax_checker_agent):
    """Test that the deployment_name property returns the correct model name."""
    assert syntax_checker_agent.deployment_name == "syntax_checker_model"


def test_missing_deployment_name(mock_config):
    """Test that accessing deployment_name raises a KeyError if the model type is missing."""
    mock_config.model_type = {}  # Simulate missing AgentType in model_type
    agent = SyntaxCheckerAgent(
        agent_type=AgentType.SYNTAX_CHECKER,
        config=mock_config
    )
    with pytest.raises(KeyError):
        _ = agent.deployment_name
