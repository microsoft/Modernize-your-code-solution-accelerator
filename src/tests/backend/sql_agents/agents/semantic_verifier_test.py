"""Tests for sql_agents/agents/semantic_verifier/ (agent, response, setup)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from sql_agents.agents.agent_factory import SQLAgentFactory
from sql_agents.agents.semantic_verifier.agent import SemanticVerifierAgent
from sql_agents.agents.semantic_verifier.response import SemanticVerifierResponse
from sql_agents.agents.semantic_verifier.setup import setup_semantic_verifier_agent
from sql_agents.helpers.models import AgentType


# ---------------------------------------------------------------------------
# SemanticVerifierResponse
# ---------------------------------------------------------------------------

class TestSemanticVerifierResponse:
    def test_instantiation_with_all_fields(self):
        resp = SemanticVerifierResponse(
            judgement="equivalent",
            differences=["no differences"],
            summary="queries match",
        )
        assert resp.judgement == "equivalent"
        assert resp.differences == ["no differences"]
        assert resp.summary == "queries match"

    def test_empty_differences_list(self):
        resp = SemanticVerifierResponse(
            judgement="different", differences=[], summary="mismatch"
        )
        assert resp.differences == []

    def test_multiple_differences(self):
        diffs = ["col A missing", "col B renamed"]
        resp = SemanticVerifierResponse(judgement="different", differences=diffs, summary="s")
        assert len(resp.differences) == 2

    def test_required_fields_enforced(self):
        with pytest.raises(Exception):
            SemanticVerifierResponse(judgement="j")  # missing differences and summary


# ---------------------------------------------------------------------------
# SemanticVerifierAgent
# ---------------------------------------------------------------------------

class TestSemanticVerifierAgent:
    def _make_agent(self) -> SemanticVerifierAgent:
        mock_config = MagicMock()
        mock_config.model_type = {AgentType.SEMANTIC_VERIFIER: "sv-deployment"}
        return SemanticVerifierAgent(
            agent_type=AgentType.SEMANTIC_VERIFIER, config=mock_config
        )

    def test_response_object_is_semantic_verifier_response(self):
        assert self._make_agent().response_object is SemanticVerifierResponse

    def test_deployment_name_uses_semantic_verifier_key(self):
        assert self._make_agent().deployment_name == "sv-deployment"

    def test_num_candidates_is_none(self):
        """SemanticVerifierAgent does not override num_candidates."""
        assert self._make_agent().num_candidates is None

    def test_agent_type_stored_on_init(self):
        assert self._make_agent().agent_type is AgentType.SEMANTIC_VERIFIER


# ---------------------------------------------------------------------------
# setup_semantic_verifier_agent
# ---------------------------------------------------------------------------

class TestSetupSemanticVerifierAgent:
    def test_delegates_to_factory_with_semantic_verifier_type(self):
        mock_config = MagicMock()
        mock_result = MagicMock()

        with pytest.MonkeyPatch.context() as mp:
            mock_create = AsyncMock(return_value=mock_result)
            mp.setattr(SQLAgentFactory, "create_agent", mock_create)
            result = asyncio.run(setup_semantic_verifier_agent(mock_config))

        mock_create.assert_called_once_with(
            agent_type=AgentType.SEMANTIC_VERIFIER,
            config=mock_config,
            temperature=0.0,
        )
        assert result is mock_result
