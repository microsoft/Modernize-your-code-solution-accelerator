"""Tests for sql_agents/helpers/comms_manager.py module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.sql_agents.helpers.comms_manager import CommsManager
from backend.sql_agents.helpers.models import AgentType


class MockChatMessageContent:
    """Mock for ChatMessageContent."""
    
    def __init__(self, name, content="", role="assistant"):
        self.name = name
        self.content = content
        self.role = role


class TestSelectionStrategy:
    """Tests for SelectionStrategy class."""

    @pytest.mark.asyncio
    async def test_select_agent_after_migrator(self):
        """Test agent selection after migrator."""
        strategy = CommsManager.SelectionStrategy()
        
        mock_picker = MagicMock()
        mock_picker.name = AgentType.PICKER.value
        mock_migrator = MagicMock()
        mock_migrator.name = AgentType.MIGRATOR.value
        
        agents = [mock_picker, mock_migrator]
        history = [MockChatMessageContent(AgentType.MIGRATOR.value)]
        
        result = await strategy.select_agent(agents, history)
        
        assert result.name == AgentType.PICKER.value

    @pytest.mark.asyncio
    async def test_select_agent_after_picker(self):
        """Test agent selection after picker."""
        strategy = CommsManager.SelectionStrategy()
        
        mock_syntax = MagicMock()
        mock_syntax.name = AgentType.SYNTAX_CHECKER.value
        
        agents = [mock_syntax]
        history = [MockChatMessageContent(AgentType.PICKER.value)]
        
        result = await strategy.select_agent(agents, history)
        
        assert result.name == AgentType.SYNTAX_CHECKER.value

    @pytest.mark.asyncio
    async def test_select_agent_after_syntax_checker(self):
        """Test agent selection after syntax checker."""
        strategy = CommsManager.SelectionStrategy()
        
        mock_fixer = MagicMock()
        mock_fixer.name = AgentType.FIXER.value
        
        agents = [mock_fixer]
        history = [MockChatMessageContent(AgentType.SYNTAX_CHECKER.value)]
        
        result = await strategy.select_agent(agents, history)
        
        assert result.name == AgentType.FIXER.value

    @pytest.mark.asyncio
    async def test_select_agent_after_fixer(self):
        """Test agent selection after fixer."""
        strategy = CommsManager.SelectionStrategy()
        
        mock_syntax = MagicMock()
        mock_syntax.name = AgentType.SYNTAX_CHECKER.value
        
        agents = [mock_syntax]
        history = [MockChatMessageContent(AgentType.FIXER.value)]
        
        result = await strategy.select_agent(agents, history)
        
        assert result.name == AgentType.SYNTAX_CHECKER.value

    @pytest.mark.asyncio
    async def test_select_agent_candidate(self):
        """Test agent selection after candidate message."""
        strategy = CommsManager.SelectionStrategy()
        
        mock_semantic = MagicMock()
        mock_semantic.name = AgentType.SEMANTIC_VERIFIER.value
        
        agents = [mock_semantic]
        history = [MockChatMessageContent("candidate")]
        
        result = await strategy.select_agent(agents, history)
        
        assert result.name == AgentType.SEMANTIC_VERIFIER.value

    @pytest.mark.asyncio
    async def test_select_agent_default(self):
        """Test default agent selection (no history match)."""
        strategy = CommsManager.SelectionStrategy()
        
        mock_migrator = MagicMock()
        mock_migrator.name = AgentType.MIGRATOR.value
        
        agents = [mock_migrator]
        history = [MockChatMessageContent("unknown")]
        
        result = await strategy.select_agent(agents, history)
        
        assert result.name == AgentType.MIGRATOR.value


class TestApprovalTerminationStrategy:
    """Tests for ApprovalTerminationStrategy class."""

    @pytest.mark.asyncio
    async def test_should_terminate_after_migrator_with_input_error(self):
        """Test termination when migrator returns input error."""
        strategy = CommsManager.ApprovalTerminationStrategy()
        
        mock_agent = MagicMock()
        # Provide all required fields for MigratorResponse
        content = '{"input_summary": "test", "candidates": [], "input_error": "Invalid input", "rai_error": null}'
        history = [MockChatMessageContent(AgentType.MIGRATOR.value, content)]
        
        result = await strategy.should_agent_terminate(mock_agent, history)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_should_terminate_after_migrator_with_rai_error(self):
        """Test termination when migrator returns RAI error."""
        strategy = CommsManager.ApprovalTerminationStrategy()
        
        mock_agent = MagicMock()
        content = '{"input_summary": "test", "candidates": [], "input_error": null, "rai_error": "RAI violation"}'
        history = [MockChatMessageContent(AgentType.MIGRATOR.value, content)]
        
        result = await strategy.should_agent_terminate(mock_agent, history)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_should_not_terminate_migrator_no_error(self):
        """Test no termination when migrator has no errors."""
        strategy = CommsManager.ApprovalTerminationStrategy()
        
        mock_agent = MagicMock()
        content = '{"input_summary": "test", "candidates": [], "input_error": null, "rai_error": null}'
        history = [MockChatMessageContent(AgentType.MIGRATOR.value, content)]
        
        result = await strategy.should_agent_terminate(mock_agent, history)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_should_terminate_after_semantic_verifier(self):
        """Test termination after semantic verifier."""
        strategy = CommsManager.ApprovalTerminationStrategy()
        
        mock_agent = MagicMock()
        history = [MockChatMessageContent(AgentType.SEMANTIC_VERIFIER.value, "{}")]
        
        result = await strategy.should_agent_terminate(mock_agent, history)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_should_not_terminate_other_agents(self):
        """Test no termination for other agents."""
        strategy = CommsManager.ApprovalTerminationStrategy()
        
        mock_agent = MagicMock()
        history = [MockChatMessageContent(AgentType.FIXER.value, "{}")]
        
        result = await strategy.should_agent_terminate(mock_agent, history)
        
        assert result is False



