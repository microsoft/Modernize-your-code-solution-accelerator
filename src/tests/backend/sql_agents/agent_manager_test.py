"""Tests for sql_agents/agent_manager.py module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.sql_agents.agent_manager import (
    set_sql_agents,
    get_sql_agents,
    update_agent_config,
    clear_sql_agents,
    _sql_agents,
)


class TestSetSqlAgents:
    """Tests for set_sql_agents function."""

    def test_set_sql_agents(self):
        """Test setting the global SQL agents instance."""
        mock_agents = MagicMock()
        
        set_sql_agents(mock_agents)
        
        result = get_sql_agents()
        assert result == mock_agents

    def test_set_sql_agents_replaces_existing(self):
        """Test that setting new agents replaces existing."""
        mock_agents1 = MagicMock()
        mock_agents2 = MagicMock()
        
        set_sql_agents(mock_agents1)
        set_sql_agents(mock_agents2)
        
        result = get_sql_agents()
        assert result == mock_agents2


class TestGetSqlAgents:
    """Tests for get_sql_agents function."""

    def test_get_sql_agents_when_set(self):
        """Test getting agents when they are set."""
        mock_agents = MagicMock()
        set_sql_agents(mock_agents)
        
        result = get_sql_agents()
        
        assert result == mock_agents

    def test_get_sql_agents_when_none(self):
        """Test getting agents when not set."""
        # Clear the global variable by setting to None via a mock
        with patch("backend.sql_agents.agent_manager._sql_agents", None):
            result = get_sql_agents()
            # The patched value should be None
            assert result is None


class TestUpdateAgentConfig:
    """Tests for update_agent_config function."""

    @pytest.mark.asyncio
    async def test_update_agent_config_success(self):
        """Test updating agent configuration successfully."""
        mock_config = MagicMock()
        mock_config.sql_from = "informix"
        mock_config.sql_to = "tsql"
        
        mock_agents = MagicMock()
        mock_agents.agent_config = mock_config
        
        set_sql_agents(mock_agents)
        
        await update_agent_config("mysql", "postgres")
        
        assert mock_config.sql_from == "mysql"
        assert mock_config.sql_to == "postgres"

    @pytest.mark.asyncio
    async def test_update_agent_config_no_agents(self):
        """Test updating config when agents not initialized."""
        with patch("backend.sql_agents.agent_manager._sql_agents", None):
            # Should not raise an error, just log warning
            await update_agent_config("mysql", "postgres")

    @pytest.mark.asyncio
    async def test_update_agent_config_no_config(self):
        """Test updating config when agent_config is None."""
        mock_agents = MagicMock()
        mock_agents.agent_config = None
        
        with patch("backend.sql_agents.agent_manager._sql_agents", mock_agents):
            # Should not raise an error
            await update_agent_config("mysql", "postgres")


class TestClearSqlAgents:
    """Tests for clear_sql_agents function."""

    @pytest.mark.asyncio
    async def test_clear_sql_agents(self):
        """Test clearing the global SQL agents instance."""
        mock_agents = MagicMock()
        mock_agents.delete_agents = AsyncMock()
        
        set_sql_agents(mock_agents)
        
        await clear_sql_agents()
        
        mock_agents.delete_agents.assert_called_once()
