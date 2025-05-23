from unittest.mock import MagicMock

import pytest

from sql_agents.agents.semantic_verifier.agent import SemanticVerifierAgent
from sql_agents.agents.semantic_verifier.response import SemanticVerifierResponse
from sql_agents.helpers.models import AgentType


@pytest.fixture
def mock_config():
    """Fixture to create a mock configuration."""
    mock_config = MagicMock()
    mock_config.model_type = {
        AgentType.SEMANTIC_VERIFIER: "semantic_verifier_model"
    }
    return mock_config


@pytest.fixture
def semantic_verifier_agent(mock_config):
    """Fixture to create a SemanticVerifierAgent instance."""
    agent = SemanticVerifierAgent(
        agent_type=AgentType.SEMANTIC_VERIFIER,
        config=mock_config
    )
    return agent


def test_response_object(semantic_verifier_agent):
    """Test that the response_object property returns SemanticVerifierResponse."""
    assert semantic_verifier_agent.response_object == SemanticVerifierResponse


def test_deployment_name(semantic_verifier_agent):
    """Test that the deployment_name property returns the correct model name."""
    assert semantic_verifier_agent.deployment_name == "semantic_verifier_model"


def test_missing_deployment_name(mock_config):
    """Test that accessing deployment_name raises a KeyError if the model type is missing."""
    mock_config.model_type = {}
    agent = SemanticVerifierAgent(
        agent_type=AgentType.SEMANTIC_VERIFIER,
        config=mock_config
    )
    with pytest.raises(KeyError):
        _ = agent.deployment_name
