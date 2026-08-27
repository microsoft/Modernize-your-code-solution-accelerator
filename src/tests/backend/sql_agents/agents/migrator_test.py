"""Tests for sql_agents/agents/migrator/ (agent, response, setup)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from sql_agents.agents.agent_factory import SQLAgentFactory
from sql_agents.agents.migrator.agent import MigratorAgent
from sql_agents.agents.migrator.response import MigratorCandidate, MigratorResponse
from sql_agents.agents.migrator.setup import setup_migrator_agent
from sql_agents.helpers.models import AgentType


# ---------------------------------------------------------------------------
# MigratorCandidate
# ---------------------------------------------------------------------------

class TestMigratorCandidate:
    def test_instantiation(self):
        cand = MigratorCandidate(plan="use CTE", candidate_query="WITH cte AS (...) SELECT *")
        assert cand.plan == "use CTE"
        assert cand.candidate_query == "WITH cte AS (...) SELECT *"

    def test_required_fields_enforced(self):
        with pytest.raises(Exception):
            MigratorCandidate(plan="only plan")  # missing candidate_query


# ---------------------------------------------------------------------------
# MigratorResponse
# ---------------------------------------------------------------------------

class TestMigratorResponse:
    def _make_response(self, **overrides):
        defaults = dict(
            input_summary="original summary",
            candidates=[
                MigratorCandidate(plan="p1", candidate_query="SELECT 1"),
                MigratorCandidate(plan="p2", candidate_query="SELECT 2"),
            ],
        )
        defaults.update(overrides)
        return MigratorResponse(**defaults)

    def test_instantiation_with_required_fields(self):
        resp = self._make_response()
        assert resp.input_summary == "original summary"
        assert len(resp.candidates) == 2

    def test_optional_fields_default_to_none(self):
        resp = self._make_response()
        assert resp.input_error is None
        assert resp.summary is None
        assert resp.rai_error is None

    def test_optional_fields_accepted(self):
        resp = self._make_response(input_error="bad input", summary="done", rai_error="rai")
        assert resp.input_error == "bad input"
        assert resp.summary == "done"
        assert resp.rai_error == "rai"

    def test_candidates_list(self):
        cands = [MigratorCandidate(plan="p", candidate_query="SELECT 1")]
        resp = self._make_response(candidates=cands)
        assert resp.candidates[0].plan == "p"


# ---------------------------------------------------------------------------
# MigratorAgent
# ---------------------------------------------------------------------------

class TestMigratorAgent:
    def _make_agent(self) -> MigratorAgent:
        mock_config = MagicMock()
        mock_config.model_type = {AgentType.MIGRATOR: "migrator-deployment"}
        return MigratorAgent(agent_type=AgentType.MIGRATOR, config=mock_config)

    def test_response_object_is_migrator_response(self):
        assert self._make_agent().response_object is MigratorResponse

    def test_deployment_name_uses_migrator_key(self):
        assert self._make_agent().deployment_name == "migrator-deployment"

    def test_num_candidates_is_three(self):
        assert self._make_agent().num_candidates == 3

    def test_agent_type_stored_on_init(self):
        assert self._make_agent().agent_type is AgentType.MIGRATOR


# ---------------------------------------------------------------------------
# setup_migrator_agent
# ---------------------------------------------------------------------------

class TestSetupMigratorAgent:
    def test_delegates_to_factory_with_migrator_type(self):
        mock_config = MagicMock()
        mock_result = MagicMock()

        with pytest.MonkeyPatch.context() as mp:
            mock_create = AsyncMock(return_value=mock_result)
            mp.setattr(SQLAgentFactory, "create_agent", mock_create)
            result = asyncio.run(setup_migrator_agent(mock_config))

        mock_create.assert_called_once_with(AgentType.MIGRATOR, mock_config)
        assert result is mock_result
