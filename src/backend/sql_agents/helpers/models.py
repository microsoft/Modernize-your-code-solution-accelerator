"""Models for SQL agents."""

from enum import Enum


class AgentType(Enum):
    """Agent types."""

    MIGRATOR = "migrator"
    FIXER = "fixer"
    PICKER = "picker"
    SEMANTIC_VERIFIER = "semantic_verifier"
    SYNTAX_CHECKER = "syntax_checker"
    SELECTION = "selection"
    TERMINATION = "termination"
    HUMAN = "human"
    ALL = "agents"  # For all agents

    def __new__(cls, value):
        # If value is a string, normalize it to lowercase
        if isinstance(value, str):
            value = value.lower()
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    @classmethod
    def _missing_(cls, value):
        return cls.ALL
