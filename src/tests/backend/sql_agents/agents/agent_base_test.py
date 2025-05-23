from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import pytest_asyncio

from semantic_kernel.functions import KernelArguments

from sql_agents.agents.agent_base import BaseSQLAgent
from sql_agents.helpers.models import AgentType


# Concrete subclass for testing
class DummyResponse:
    @classmethod
    def model_json_schema(cls):
        return {"type": "object"}


class DummySQLAgent(BaseSQLAgent):
    @property
    def response_object(self) -> type:
        return DummyResponse

    @property
    def deployment_name(self) -> str:
        return self.config.model_type.get(self.agent_type)


class FakeAgentModel:
    def __init__(self):
        self.name = "test-agent"
        self.description = "test-description"
        self.id = "agent-id"
        self.instructions = "some instructions"


@pytest.fixture
def mock_config():
    mock = MagicMock()
    mock.sql_to = "TSQL"
    mock.sql_from = "MySQL"
    mock.model_type = {AgentType.FIXER: "test-model"}
    mock.ai_project_client.agents.create_agent = AsyncMock()
    return mock


@pytest_asyncio.fixture
async def dummy_agent(mock_config):
    return DummySQLAgent(agent_type=AgentType.FIXER, config=mock_config)


def test_properties(dummy_agent):
    assert dummy_agent.agent_type == AgentType.FIXER
    assert dummy_agent.config.sql_to == "TSQL"
    assert dummy_agent.num_candidates is None
    assert dummy_agent.plugins is None
    assert dummy_agent.deployment_name == "test-model"


def test_get_kernel_arguments(dummy_agent):
    args = dummy_agent.get_kernel_arguments()
    assert isinstance(args, KernelArguments)
    assert args["target"] == "TSQL"
    assert args["source"] == "MySQL"


@pytest.mark.asyncio
async def test_setup_file_not_found(dummy_agent):
    with patch("sql_agents.agents.agent_base.get_prompt", side_effect=FileNotFoundError):
        with pytest.raises(ValueError, match="Prompt file for fixer not found."):
            await dummy_agent.setup()


@pytest.mark.asyncio
async def test_get_agent_sets_up(dummy_agent):
    dummy_agent.agent = None

    async def mock_setup():
        dummy_agent.agent = "mocked_agent"

    with patch.object(dummy_agent, "setup", new=AsyncMock(side_effect=mock_setup)) as mock_setup_fn, \
         patch("sql_agents.agents.agent_base.get_prompt", return_value="prompt content"):

        await dummy_agent.get_agent()

        mock_setup_fn.assert_awaited_once()
        assert dummy_agent.agent == "mocked_agent"


@pytest.mark.asyncio
async def test_execute_invokes_agent(dummy_agent):
    dummy_agent.agent = MagicMock()
    dummy_agent.agent.invoke = AsyncMock(return_value={"result": "ok"})

    result = await dummy_agent.execute("input query")
    dummy_agent.agent.invoke.assert_awaited_once_with("input query")
    assert result == {"result": "ok"}
