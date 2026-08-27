"""Tests for sql_agents/agents/syntax_checker/ (agent, response, setup)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from sql_agents.agents.agent_factory import SQLAgentFactory
from sql_agents.agents.syntax_checker.agent import SyntaxCheckerAgent
from sql_agents.agents.syntax_checker.plug_ins import SyntaxCheckerPlugin
from sql_agents.agents.syntax_checker.response import SyntaxCheckerResponse, SyntaxErrorInt
from sql_agents.agents.syntax_checker.setup import setup_syntax_checker_agent
from sql_agents.helpers.models import AgentType


# ---------------------------------------------------------------------------
# SyntaxErrorInt
# ---------------------------------------------------------------------------

class TestSyntaxErrorInt:
    def test_instantiation(self):
        err = SyntaxErrorInt(line=1, column=5, error="unexpected token")
        assert err.line == 1
        assert err.column == 5
        assert err.error == "unexpected token"

    def test_required_fields_enforced(self):
        with pytest.raises(Exception):
            SyntaxErrorInt(line=1)  # missing column and error


# ---------------------------------------------------------------------------
# SyntaxCheckerResponse
# ---------------------------------------------------------------------------

class TestSyntaxCheckerResponse:
    def test_instantiation_with_errors(self):
        errors = [SyntaxErrorInt(line=2, column=10, error="bad syntax")]
        resp = SyntaxCheckerResponse(
            thought="found issues", syntax_errors=errors, summary="1 error"
        )
        assert resp.thought == "found issues"
        assert len(resp.syntax_errors) == 1
        assert resp.syntax_errors[0].error == "bad syntax"
        assert resp.summary == "1 error"

    def test_empty_errors_list(self):
        resp = SyntaxCheckerResponse(thought="ok", syntax_errors=[], summary="no errors")
        assert resp.syntax_errors == []

    def test_required_fields_enforced(self):
        with pytest.raises(Exception):
            SyntaxCheckerResponse(thought="t")  # missing syntax_errors and summary


# ---------------------------------------------------------------------------
# SyntaxCheckerAgent
# ---------------------------------------------------------------------------

class TestSyntaxCheckerAgent:
    def _make_agent(self) -> SyntaxCheckerAgent:
        mock_config = MagicMock()
        mock_config.model_type = {AgentType.SYNTAX_CHECKER: "sc-deployment"}
        return SyntaxCheckerAgent(agent_type=AgentType.SYNTAX_CHECKER, config=mock_config)

    def test_response_object_is_syntax_checker_response(self):
        assert self._make_agent().response_object is SyntaxCheckerResponse

    def test_deployment_name_uses_syntax_checker_key(self):
        assert self._make_agent().deployment_name == "sc-deployment"

    def test_plugins_includes_check_syntax_function_name(self):
        plugins = self._make_agent().plugins
        assert "check_syntax" in plugins

    def test_plugins_includes_syntax_checker_plugin_instance(self):
        plugins = self._make_agent().plugins
        assert any(isinstance(p, SyntaxCheckerPlugin) for p in plugins)

    def test_agent_type_stored_on_init(self):
        assert self._make_agent().agent_type is AgentType.SYNTAX_CHECKER


# ---------------------------------------------------------------------------
# setup_syntax_checker_agent
# ---------------------------------------------------------------------------

class TestSetupSyntaxCheckerAgent:
    def test_delegates_to_factory_with_syntax_checker_type(self):
        mock_config = MagicMock()
        mock_result = MagicMock()

        with pytest.MonkeyPatch.context() as mp:
            mock_create = AsyncMock(return_value=mock_result)
            mp.setattr(SQLAgentFactory, "create_agent", mock_create)
            result = asyncio.run(setup_syntax_checker_agent(mock_config))

        mock_create.assert_called_once_with(AgentType.SYNTAX_CHECKER, mock_config)
        assert result is mock_result
