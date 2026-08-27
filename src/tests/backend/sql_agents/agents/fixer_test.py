"""Tests for sql_agents/agents/fixer/ (agent, response, setup)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from sql_agents.agents.agent_factory import SQLAgentFactory
from sql_agents.agents.fixer.agent import FixerAgent
from sql_agents.agents.fixer.response import FixerResponse
from sql_agents.agents.fixer.setup import setup_fixer_agent
from sql_agents.helpers.models import AgentType


# ---------------------------------------------------------------------------
# FixerResponse
# ---------------------------------------------------------------------------

class TestFixerResponse:
    def test_instantiation_with_all_fields(self):
        resp = FixerResponse(thought="think", fixed_query="SELECT 1", summary="ok")
        assert resp.thought == "think"
        assert resp.fixed_query == "SELECT 1"
        assert resp.summary == "ok"

    def test_summary_accepts_none(self):
        resp = FixerResponse(thought="t", fixed_query="SELECT 1", summary=None)
        assert resp.summary is None

    def test_required_thought_field_enforced(self):
        with pytest.raises(Exception):
            FixerResponse(fixed_query="SELECT 1", summary=None)  # missing thought


# ---------------------------------------------------------------------------
# FixerAgent
# ---------------------------------------------------------------------------

class TestFixerAgent:
    def _make_agent(self) -> FixerAgent:
        mock_config = MagicMock()
        mock_config.model_type = {AgentType.FIXER: "fixer-deployment"}
        return FixerAgent(agent_type=AgentType.FIXER, config=mock_config)

    def test_response_object_is_fixer_response(self):
        assert self._make_agent().response_object is FixerResponse

    def test_deployment_name_uses_fixer_key(self):
        assert self._make_agent().deployment_name == "fixer-deployment"

    def test_num_candidates_is_none(self):
        """FixerAgent does not override num_candidates."""
        assert self._make_agent().num_candidates is None

    def test_agent_type_stored_on_init(self):
        assert self._make_agent().agent_type is AgentType.FIXER


# ---------------------------------------------------------------------------
# setup_fixer_agent
# ---------------------------------------------------------------------------

class TestSetupFixerAgent:
    def test_delegates_to_factory_with_fixer_type(self):
        mock_config = MagicMock()
        mock_result = MagicMock()

        with pytest.MonkeyPatch.context() as mp:
            mock_create = AsyncMock(return_value=mock_result)
            mp.setattr(SQLAgentFactory, "create_agent", mock_create)
            result = asyncio.run(setup_fixer_agent(mock_config))

        mock_create.assert_called_once_with(AgentType.FIXER, mock_config)
        assert result is mock_result
