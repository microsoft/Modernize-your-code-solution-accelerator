"""Tests for sql_agents/agents/picker/ (agent, response, setup)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from sql_agents.agents.agent_factory import SQLAgentFactory
from sql_agents.agents.picker.agent import PickerAgent
from sql_agents.agents.picker.response import PickerResponse
from sql_agents.agents.picker.setup import setup_picker_agent
from sql_agents.helpers.models import AgentType


# ---------------------------------------------------------------------------
# PickerResponse
# ---------------------------------------------------------------------------

class TestPickerResponse:
    def test_instantiation_with_all_fields(self):
        resp = PickerResponse(conclusion="best", picked_query="SELECT 1", summary="done")
        assert resp.conclusion == "best"
        assert resp.picked_query == "SELECT 1"
        assert resp.summary == "done"

    def test_summary_is_optional(self):
        resp = PickerResponse(conclusion="c", picked_query="SELECT 1", summary=None)
        assert resp.summary is None

    def test_required_fields_enforced(self):
        with pytest.raises(Exception):
            PickerResponse(conclusion="only conclusion")


# ---------------------------------------------------------------------------
# PickerAgent
# ---------------------------------------------------------------------------

class TestPickerAgent:
    def _make_agent(self) -> PickerAgent:
        mock_config = MagicMock()
        mock_config.model_type = {AgentType.PICKER: "picker-deployment"}
        return PickerAgent(agent_type=AgentType.PICKER, config=mock_config)

    def test_response_object_is_picker_response(self):
        assert self._make_agent().response_object is PickerResponse

    def test_deployment_name_uses_picker_key(self):
        assert self._make_agent().deployment_name == "picker-deployment"

    def test_num_candidates_is_three(self):
        assert self._make_agent().num_candidates == 3

    def test_agent_type_stored_on_init(self):
        assert self._make_agent().agent_type is AgentType.PICKER


# ---------------------------------------------------------------------------
# setup_picker_agent
# ---------------------------------------------------------------------------

class TestSetupPickerAgent:
    def test_delegates_to_factory_with_picker_type(self):
        mock_config = MagicMock()
        mock_result = MagicMock()

        with pytest.MonkeyPatch.context() as mp:
            mock_create = AsyncMock(return_value=mock_result)
            mp.setattr(SQLAgentFactory, "create_agent", mock_create)
            result = asyncio.run(setup_picker_agent(mock_config))

        mock_create.assert_called_once_with(
            agent_type=AgentType.PICKER,
            config=mock_config,
            temperature=0.0,
        )
        assert result is mock_result
