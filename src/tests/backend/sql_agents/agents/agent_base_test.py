"""Tests for sql_agents/agents/agent_base.py module."""

from unittest.mock import AsyncMock, MagicMock, patch

from backend.sql_agents.agents.agent_base import BaseSQLAgent
from backend.sql_agents.helpers.models import AgentType

import pytest


class ConcreteAgent(BaseSQLAgent):
    """Concrete implementation of BaseSQLAgent for testing."""

    @property
    def response_object(self):
        return MagicMock

    @property
    def num_candidates(self):
        return 3

    @property
    def deployment_name(self):
        return "test-deployment"

    @property
    def plugins(self):
        return ["plugin1", "plugin2"]


class MinimalConcreteAgent(BaseSQLAgent):
    """Minimal concrete implementation of BaseSQLAgent for testing."""

    @property
    def response_object(self):
        return MagicMock


class TestBaseSQLAgent:
    """Tests for BaseSQLAgent class."""

    def test_init(self):
        """Test BaseSQLAgent initialization."""
        mock_config = MagicMock()

        agent = ConcreteAgent(
            agent_type=AgentType.MIGRATOR,
            config=mock_config,
            temperature=0.5
        )

        assert agent.agent_type == AgentType.MIGRATOR
        assert agent.config == mock_config
        assert agent.temperature == 0.5
        assert agent.agent is None

    def test_response_object_property(self):
        """Test response_object property."""
        mock_config = MagicMock()
        agent = ConcreteAgent(
            agent_type=AgentType.MIGRATOR,
            config=mock_config
        )

        assert agent.response_object is not None

    def test_num_candidates_property(self):
        """Test num_candidates property."""
        mock_config = MagicMock()
        agent = ConcreteAgent(
            agent_type=AgentType.MIGRATOR,
            config=mock_config
        )

        assert agent.num_candidates == 3

    def test_num_candidates_default(self):
        """Test num_candidates default value."""
        mock_config = MagicMock()
        agent = MinimalConcreteAgent(
            agent_type=AgentType.MIGRATOR,
            config=mock_config
        )

        assert agent.num_candidates is None

    def test_deployment_name_property(self):
        """Test deployment_name property."""
        mock_config = MagicMock()
        agent = ConcreteAgent(
            agent_type=AgentType.MIGRATOR,
            config=mock_config
        )

        assert agent.deployment_name == "test-deployment"

    def test_deployment_name_default(self):
        """Test deployment_name default value."""
        mock_config = MagicMock()
        agent = MinimalConcreteAgent(
            agent_type=AgentType.MIGRATOR,
            config=mock_config
        )

        assert agent.deployment_name is None

    def test_plugins_property(self):
        """Test plugins property."""
        mock_config = MagicMock()
        agent = ConcreteAgent(
            agent_type=AgentType.MIGRATOR,
            config=mock_config
        )

        assert agent.plugins == ["plugin1", "plugin2"]

    def test_plugins_default(self):
        """Test plugins default value."""
        mock_config = MagicMock()
        agent = MinimalConcreteAgent(
            agent_type=AgentType.MIGRATOR,
            config=mock_config
        )

        assert agent.plugins is None

    def test_get_kernel_arguments(self):
        """Test get_kernel_arguments method."""
        mock_config = MagicMock()
        mock_config.sql_from = "informix"
        mock_config.sql_to = "tsql"

        agent = ConcreteAgent(
            agent_type=AgentType.MIGRATOR,
            config=mock_config
        )

        result = agent.get_kernel_arguments()

        # Check that the arguments were set correctly
        assert result is not None

    def test_get_kernel_arguments_without_candidates(self):
        """Test get_kernel_arguments without num_candidates."""
        mock_config = MagicMock()
        mock_config.sql_from = "informix"
        mock_config.sql_to = "tsql"

        agent = MinimalConcreteAgent(
            agent_type=AgentType.MIGRATOR,
            config=mock_config
        )

        result = agent.get_kernel_arguments()

        assert result is not None

    @pytest.mark.asyncio
    async def test_setup_prompt_not_found(self):
        """Test setup when prompt file not found."""
        mock_config = MagicMock()
        mock_config.model_type = MagicMock()
        mock_config.model_type.get = MagicMock(return_value="gpt-4")

        agent = ConcreteAgent(
            agent_type=AgentType.MIGRATOR,
            config=mock_config
        )

        with patch("sql_agents.agents.agent_base.get_prompt", side_effect=FileNotFoundError()):
            with pytest.raises(ValueError, match="Prompt file.*not found"):
                await agent.setup()

    @pytest.mark.asyncio
    async def test_get_agent_when_already_initialized(self):
        """Test get_agent returns existing agent if initialized."""
        mock_config = MagicMock()

        agent = ConcreteAgent(
            agent_type=AgentType.MIGRATOR,
            config=mock_config
        )

        mock_existing_agent = MagicMock()
        agent.agent = mock_existing_agent

        result = await agent.get_agent()

        assert result == mock_existing_agent

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test execute method."""
        mock_config = MagicMock()

        agent = ConcreteAgent(
            agent_type=AgentType.MIGRATOR,
            config=mock_config
        )

        mock_azure_agent = MagicMock()
        mock_azure_agent.invoke = AsyncMock(return_value="test response")
        agent.agent = mock_azure_agent

        result = await agent.execute("test input")

        assert result == "test response"
        mock_azure_agent.invoke.assert_called_once_with("test input")
