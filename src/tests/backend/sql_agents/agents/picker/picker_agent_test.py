from unittest.mock import MagicMock

import pytest

from sql_agents.agents.picker.agent import PickerAgent
from sql_agents.agents.picker.response import PickerResponse
from sql_agents.helpers.models import AgentType


@pytest.fixture
def mock_config():
    return MagicMock(model_type={AgentType.PICKER: "picker-model-v1"})


@pytest.fixture
def picker_agent(mock_config):
    return PickerAgent(config=mock_config, agent_type=AgentType.PICKER)


def test_response_object(picker_agent):
    """Test that the response_object property returns PickerResponse."""
    assert picker_agent.response_object is PickerResponse


def test_num_candidates(picker_agent):
    """Test that the num_candidates property returns 3."""
    assert picker_agent.num_candidates == 3


def test_deployment_name(picker_agent):
    """Test that the deployment_name returns the correct model name."""
    assert picker_agent.deployment_name == "picker-model-v1"
