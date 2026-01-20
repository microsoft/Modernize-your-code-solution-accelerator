"""Tests for sql_agents/agents/agent_factory.py module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.sql_agents.agents.agent_factory import SQLAgentFactory
from backend.sql_agents.helpers.models import AgentType


class TestSQLAgentFactory:
    """Tests for SQLAgentFactory class."""

    @pytest.mark.asyncio
    async def test_create_agent_picker(self):
        """Test creating a picker agent."""
        mock_config = MagicMock()
        mock_config.model_type = {AgentType.PICKER: "gpt-4"}
        
        mock_agent = MagicMock()
        mock_agent.setup = AsyncMock(return_value=MagicMock())
        
        with patch.object(SQLAgentFactory, '_agent_classes', {AgentType.PICKER: MagicMock(return_value=mock_agent)}):
            result = await SQLAgentFactory.create_agent(
                AgentType.PICKER,
                mock_config,
                temperature=0.5
            )
            
            mock_agent.setup.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_agent_migrator(self):
        """Test creating a migrator agent."""
        mock_config = MagicMock()
        
        mock_agent = MagicMock()
        mock_agent.setup = AsyncMock(return_value=MagicMock())
        
        with patch.object(SQLAgentFactory, '_agent_classes', {AgentType.MIGRATOR: MagicMock(return_value=mock_agent)}):
            result = await SQLAgentFactory.create_agent(
                AgentType.MIGRATOR,
                mock_config
            )
            
            mock_agent.setup.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_agent_syntax_checker(self):
        """Test creating a syntax checker agent."""
        mock_config = MagicMock()
        
        mock_agent = MagicMock()
        mock_agent.setup = AsyncMock(return_value=MagicMock())
        
        with patch.object(SQLAgentFactory, '_agent_classes', {AgentType.SYNTAX_CHECKER: MagicMock(return_value=mock_agent)}):
            result = await SQLAgentFactory.create_agent(
                AgentType.SYNTAX_CHECKER,
                mock_config
            )
            
            mock_agent.setup.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_agent_fixer(self):
        """Test creating a fixer agent."""
        mock_config = MagicMock()
        
        mock_agent = MagicMock()
        mock_agent.setup = AsyncMock(return_value=MagicMock())
        
        with patch.object(SQLAgentFactory, '_agent_classes', {AgentType.FIXER: MagicMock(return_value=mock_agent)}):
            result = await SQLAgentFactory.create_agent(
                AgentType.FIXER,
                mock_config
            )
            
            mock_agent.setup.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_agent_semantic_verifier(self):
        """Test creating a semantic verifier agent."""
        mock_config = MagicMock()
        
        mock_agent = MagicMock()
        mock_agent.setup = AsyncMock(return_value=MagicMock())
        
        with patch.object(SQLAgentFactory, '_agent_classes', {AgentType.SEMANTIC_VERIFIER: MagicMock(return_value=mock_agent)}):
            result = await SQLAgentFactory.create_agent(
                AgentType.SEMANTIC_VERIFIER,
                mock_config
            )
            
            mock_agent.setup.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_agent_unknown_type(self):
        """Test creating agent with unknown type raises error."""
        mock_config = MagicMock()
    def test_create_agent_unknown_type(self):
        """Test creating agent with unknown type raises error."""
        mock_config = MagicMock()
        
        # Test with completely unknown type - use an empty _agent_classes dict
        with patch.object(SQLAgentFactory, '_agent_classes', {}):
            with pytest.raises(ValueError, match="Unknown agent type"):
                # Run the synchronous part - we need to handle this differently
                import asyncio
                asyncio.get_event_loop().run_until_complete(
                    SQLAgentFactory.create_agent("unknown_type", mock_config)
                )

    @pytest.mark.asyncio
    async def test_create_agent_with_kwargs(self):
        """Test creating agent with additional kwargs."""
        mock_config = MagicMock()
        
        mock_agent = MagicMock()
        mock_agent.setup = AsyncMock(return_value=MagicMock())
        mock_agent_class = MagicMock(return_value=mock_agent)
        
        with patch.object(SQLAgentFactory, '_agent_classes', {AgentType.MIGRATOR: mock_agent_class}):
            result = await SQLAgentFactory.create_agent(
                AgentType.MIGRATOR,
                mock_config,
                temperature=0.7,
                custom_param="value"
            )
            
            # Verify custom kwargs were passed
            call_kwargs = mock_agent_class.call_args[1]
            assert call_kwargs["temperature"] == 0.7
            assert call_kwargs["custom_param"] == "value"

    def test_get_agent_class_valid(self):
        """Test getting a valid agent class."""
        # Use a mock to avoid actual import issues
        mock_class = MagicMock()
        with patch.object(SQLAgentFactory, '_agent_classes', {AgentType.MIGRATOR: mock_class}):
            result = SQLAgentFactory.get_agent_class(AgentType.MIGRATOR)
            assert result == mock_class

    def test_get_agent_class_invalid(self):
        """Test getting an invalid agent class raises error."""
        with patch.object(SQLAgentFactory, '_agent_classes', {}):
            with pytest.raises(ValueError, match="Unknown agent type"):
                SQLAgentFactory.get_agent_class("invalid_type")

    def test_register_agent_class(self):
        """Test registering a new agent class."""
        mock_agent_class = MagicMock()
        mock_agent_class.__name__ = "MockAgent"
        
        # Create a mock AgentType
        mock_type = MagicMock()
        mock_type.value = "custom_agent"
        
        # Backup original
        original_classes = SQLAgentFactory._agent_classes.copy()
        
        SQLAgentFactory.register_agent_class(mock_type, mock_agent_class)
        
        result = SQLAgentFactory._agent_classes.get(mock_type)
        assert result == mock_agent_class
        
        # Clean up - restore original
        SQLAgentFactory._agent_classes = original_classes

    @pytest.mark.asyncio
    async def test_create_agent_type_error(self):
        """Test creating agent handles TypeError."""
        mock_config = MagicMock()
        
        mock_agent_class = MagicMock(side_effect=TypeError("Invalid parameter"))
        
        with patch.object(SQLAgentFactory, '_agent_classes', {AgentType.MIGRATOR: mock_agent_class}):
            with pytest.raises(TypeError):
                await SQLAgentFactory.create_agent(
                    AgentType.MIGRATOR,
                    mock_config
                )
