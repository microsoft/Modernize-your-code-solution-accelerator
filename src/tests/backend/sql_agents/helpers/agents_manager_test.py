"""Tests for sql_agents/helpers/agents_manager.py module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.sql_agents.helpers.agents_manager import SqlAgents
from backend.sql_agents.helpers.models import AgentType


class TestSqlAgents:
    """Tests for SqlAgents class."""

    def test_init(self):
        """Test SqlAgents initialization."""
        agents = SqlAgents()
        
        assert agents.agent_fixer is None
        assert agents.agent_migrator is None
        assert agents.agent_picker is None
        assert agents.agent_syntax_checker is None
        assert agents.agent_semantic_verifier is None
        assert agents.agent_config is None

    @pytest.mark.asyncio
    async def test_create_success(self):
        """Test successful SqlAgents creation."""
        mock_config = MagicMock()
        
        with patch("backend.sql_agents.helpers.agents_manager.setup_fixer_agent", new_callable=AsyncMock) as mock_fixer:
            with patch("backend.sql_agents.helpers.agents_manager.setup_migrator_agent", new_callable=AsyncMock) as mock_migrator:
                with patch("backend.sql_agents.helpers.agents_manager.setup_picker_agent", new_callable=AsyncMock) as mock_picker:
                    with patch("backend.sql_agents.helpers.agents_manager.setup_syntax_checker_agent", new_callable=AsyncMock) as mock_syntax:
                        with patch("backend.sql_agents.helpers.agents_manager.setup_semantic_verifier_agent", new_callable=AsyncMock) as mock_semantic:
                            mock_fixer.return_value = MagicMock()
                            mock_migrator.return_value = MagicMock()
                            mock_picker.return_value = MagicMock()
                            mock_syntax.return_value = MagicMock()
                            mock_semantic.return_value = MagicMock()
                            
                            agents = await SqlAgents.create(mock_config)
                            
                            assert agents.agent_config == mock_config
                            assert agents.agent_fixer is not None
                            assert agents.agent_migrator is not None

    @pytest.mark.asyncio
    async def test_create_failure(self):
        """Test SqlAgents creation failure."""
        mock_config = MagicMock()
        
        with patch("backend.sql_agents.helpers.agents_manager.setup_fixer_agent", new_callable=AsyncMock) as mock_fixer:
            mock_fixer.side_effect = ValueError("Setup failed")
            
            with pytest.raises(ValueError, match="Setup failed"):
                await SqlAgents.create(mock_config)

    def test_agents_property(self):
        """Test agents property returns list of agents."""
        agents = SqlAgents()
        agents.agent_migrator = MagicMock()
        agents.agent_picker = MagicMock()
        agents.agent_syntax_checker = MagicMock()
        agents.agent_fixer = MagicMock()
        agents.agent_semantic_verifier = MagicMock()
        
        result = agents.agents
        
        assert len(result) == 5

    def test_idx_agents_property(self):
        """Test idx_agents property returns dictionary of agents."""
        agents = SqlAgents()
        mock_migrator = MagicMock()
        mock_picker = MagicMock()
        mock_syntax = MagicMock()
        mock_fixer = MagicMock()
        mock_semantic = MagicMock()
        
        agents.agent_migrator = mock_migrator
        agents.agent_picker = mock_picker
        agents.agent_syntax_checker = mock_syntax
        agents.agent_fixer = mock_fixer
        agents.agent_semantic_verifier = mock_semantic
        
        result = agents.idx_agents
        
        # idx_agents uses AgentType from sql_agents.helpers.models (internal path)
        # which might differ from backend.sql_agents.helpers.models
        # So we check by string values instead
        result_by_value = {k.value: v for k, v in result.items()}
        
        assert result_by_value["migrator"] == mock_migrator
        assert result_by_value["picker"] == mock_picker
        assert result_by_value["syntax_checker"] == mock_syntax
        assert result_by_value["fixer"] == mock_fixer
        assert result_by_value["semantic_verifier"] == mock_semantic

    @pytest.mark.asyncio
    async def test_delete_agents_success(self):
        """Test successful agent deletion."""
        mock_agent1 = MagicMock()
        mock_agent1.id = "agent-1"
        mock_agent2 = MagicMock()
        mock_agent2.id = "agent-2"
        
        mock_client = MagicMock()
        mock_client.agents = MagicMock()
        mock_client.agents.delete_agent = AsyncMock()
        
        mock_config = MagicMock()
        mock_config.ai_project_client = mock_client
        
        agents = SqlAgents()
        agents.agent_config = mock_config
        agents.agent_migrator = mock_agent1
        agents.agent_picker = mock_agent2
        agents.agent_syntax_checker = None
        agents.agent_fixer = None
        agents.agent_semantic_verifier = None
        
        await agents.delete_agents()
        
        # Should have called delete for each non-None agent
        assert mock_client.agents.delete_agent.call_count >= 2

    @pytest.mark.asyncio
    async def test_delete_agents_with_error(self):
        """Test agent deletion handles errors gracefully."""
        mock_agent = MagicMock()
        mock_agent.id = "agent-1"
        
        mock_client = MagicMock()
        mock_client.agents = MagicMock()
        mock_client.agents.delete_agent = AsyncMock(side_effect=Exception("Delete failed"))
        
        mock_config = MagicMock()
        mock_config.ai_project_client = mock_client
        
        agents = SqlAgents()
        agents.agent_config = mock_config
        agents.agent_migrator = mock_agent
        agents.agent_picker = None
        agents.agent_syntax_checker = None
        agents.agent_fixer = None
        agents.agent_semantic_verifier = None
        
        # Should not raise an exception
        await agents.delete_agents()
