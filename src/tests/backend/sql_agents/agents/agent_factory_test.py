from unittest.mock import AsyncMock, MagicMock

import pytest

from sql_agents.agents.agent_base import BaseSQLAgent
from sql_agents.agents.agent_factory import SQLAgentFactory
from sql_agents.helpers.models import AgentType


# Mock agent class for registration test
class DummyAgent(BaseSQLAgent):
    def __init__(self, **kwargs):
        pass

    async def setup(self):
        return "dummy-agent"


@pytest.mark.asyncio
@pytest.mark.parametrize("agent_type", [
    AgentType.FIXER,
    AgentType.MIGRATOR,
    AgentType.PICKER,
    AgentType.SEMANTIC_VERIFIER,
    AgentType.SYNTAX_CHECKER,
])
async def test_create_agent_success(agent_type):
    mock_config = MagicMock()

    # Patch the actual agent class with a mock
    mock_agent_class = MagicMock()
    mock_agent_instance = MagicMock()
    mock_agent_instance.setup = AsyncMock(return_value=f"{agent_type.value}-mock-agent")
    mock_agent_class.return_value = mock_agent_instance

    SQLAgentFactory._agent_classes[agent_type] = mock_agent_class

    agent = await SQLAgentFactory.create_agent(agent_type, mock_config)
    assert agent == f"{agent_type.value}-mock-agent"
    mock_agent_class.assert_called_once()
    mock_agent_instance.setup.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_agent_invalid_type():
    with pytest.raises(ValueError, match="Unknown agent type: dummy"):
        await SQLAgentFactory.create_agent("dummy", MagicMock())


def test_get_agent_class_success():
    for agent_type in SQLAgentFactory._agent_classes:
        cls = SQLAgentFactory.get_agent_class(agent_type)
        assert cls == SQLAgentFactory._agent_classes[agent_type]


def test_get_agent_class_failure():
    with pytest.raises(ValueError, match="Unknown agent type: dummy"):
        SQLAgentFactory.get_agent_class("dummy")


# def test_register_agent_class(caplog):
#     agent_type = "dummy_type"
#     SQLAgentFactory.register_agent_class(agent_type, DummyAgent)

#     assert SQLAgentFactory._agent_classes[agent_type] == DummyAgent
#     assert any("Registered agent class DummyAgent" in message for message in caplog.text.splitlines())
