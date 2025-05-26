from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sql_agents.agents.agent_config import AgentBaseConfig
from sql_agents.helpers.agents_manager import SqlAgents
from sql_agents.helpers.models import AgentType


@pytest.mark.asyncio
async def test_create_sql_agents_success():
    config = MagicMock(spec=AgentBaseConfig)

    with patch("sql_agents.helpers.agents_manager.setup_fixer_agent", new_callable=AsyncMock) as mock_fixer, \
         patch("sql_agents.helpers.agents_manager.setup_migrator_agent", new_callable=AsyncMock) as mock_migrator, \
         patch("sql_agents.helpers.agents_manager.setup_picker_agent", new_callable=AsyncMock) as mock_picker, \
         patch("sql_agents.helpers.agents_manager.setup_syntax_checker_agent", new_callable=AsyncMock) as mock_syntax, \
         patch("sql_agents.helpers.agents_manager.setup_semantic_verifier_agent", new_callable=AsyncMock) as mock_semantic:

        # Setup mock return values
        mock_fixer.return_value.id = "fixer-id"
        mock_migrator.return_value.id = "migrator-id"
        mock_picker.return_value.id = "picker-id"
        mock_syntax.return_value.id = "syntax-id"
        mock_semantic.return_value.id = "semantic-id"

        agents = await SqlAgents.create(config)

        assert agents.agent_config == config
        assert agents.agent_fixer.id == "fixer-id"
        assert agents.agent_migrator.id == "migrator-id"
        assert agents.agent_picker.id == "picker-id"
        assert agents.agent_syntax_checker.id == "syntax-id"
        assert agents.agent_semantic_verifier.id == "semantic-id"

        assert len(agents.agents) == 5
        assert agents.idx_agents[AgentType.MIGRATOR].id == "migrator-id"


@pytest.mark.asyncio
async def test_create_sql_agents_failure():
    config = MagicMock(spec=AgentBaseConfig)

    with patch("sql_agents.helpers.agents_manager.setup_fixer_agent", new_callable=AsyncMock) as mock_fixer:
        mock_fixer.side_effect = ValueError("Failed to create fixer")

        with pytest.raises(ValueError, match="Failed to create fixer"):
            await SqlAgents.create(config)


@pytest.mark.asyncio
async def test_delete_agents_success():
    # Create a dummy agent with id
    agent_mock = MagicMock()
    agent_mock.id = "agent-id"

    config = MagicMock()
    config.ai_project_client.agents.delete_agent = AsyncMock()

    agents = SqlAgents()
    agents.agent_config = config
    agents.agent_migrator = agent_mock
    agents.agent_picker = agent_mock
    agents.agent_syntax_checker = agent_mock
    agents.agent_fixer = agent_mock
    agents.agent_semantic_verifier = agent_mock

    await agents.delete_agents()

    assert config.ai_project_client.agents.delete_agent.await_count == 5
    config.ai_project_client.agents.delete_agent.assert_called_with("agent-id")


@pytest.mark.asyncio
async def test_delete_agents_with_exception(caplog):
    agent_mock = MagicMock()
    agent_mock.id = "agent-id"

    config = MagicMock()
    config.ai_project_client.agents.delete_agent = AsyncMock(side_effect=Exception("delete failed"))

    agents = SqlAgents()
    agents.agent_config = config
    agents.agent_migrator = agent_mock
    agents.agent_picker = agent_mock
    agents.agent_syntax_checker = agent_mock
    agents.agent_fixer = agent_mock
    agents.agent_semantic_verifier = agent_mock

    await agents.delete_agents()

    assert "Error deleting agents: delete failed" in caplog.text
