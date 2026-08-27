"""Tests for sql_agents/helpers/models.py"""

import pytest

from backend.sql_agents.helpers.models import AgentType


class TestAgentType:
    def test_all_member_values(self):
        assert AgentType.MIGRATOR.value == "migrator"
        assert AgentType.FIXER.value == "fixer"
        assert AgentType.PICKER.value == "picker"
        assert AgentType.SEMANTIC_VERIFIER.value == "semantic_verifier"
        assert AgentType.SYNTAX_CHECKER.value == "syntax_checker"
        assert AgentType.SELECTION.value == "selection"
        assert AgentType.TERMINATION.value == "termination"
        assert AgentType.HUMAN.value == "human"
        assert AgentType.ALL.value == "agents"

    def test_lookup_by_lowercase_string(self):
        assert AgentType("migrator") is AgentType.MIGRATOR
        assert AgentType("fixer") is AgentType.FIXER
        assert AgentType("picker") is AgentType.PICKER

    def test_new_normalises_to_lowercase(self):
        """__new__ stores the value as lowercase regardless of input case."""
        assert AgentType.MIGRATOR.value == "migrator"
        assert AgentType.SYNTAX_CHECKER.value == "syntax_checker"

    def test_missing_value_returns_all(self):
        result = AgentType("unknown_agent_xyz")
        assert result is AgentType.ALL

    def test_missing_empty_string_returns_all(self):
        result = AgentType("")
        assert result is AgentType.ALL

    def test_identity_equality(self):
        assert AgentType("migrator") == AgentType.MIGRATOR

    @pytest.mark.parametrize("member", list(AgentType))
    def test_all_members_are_enum_instances(self, member):
        assert isinstance(member, AgentType)
