"""Configuration for the agents module."""

import os
from enum import Enum

from dotenv import load_dotenv

load_dotenv()


class AgentModelDeployment(Enum):
    """Agent model deployment names."""

    MIGRATOR_AGENT_MODEL_DEPLOY = os.getenv("MIGRATOR_AGENT_MODEL_DEPLOY")
    PICKER_AGENT_MODEL_DEPLOY = os.getenv("PICKER_AGENT_MODEL_DEPLOY")
    FIXER_AGENT_MODEL_DEPLOY = os.getenv("FIXER_AGENT_MODEL_DEPLOY")
    SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY = os.getenv(
        "SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY"
    )
    SYNTAX_CHECKER_AGENT_MODEL_DEPLOY = os.getenv("SYNTAX_CHECKER_AGENT_MODEL_DEPLOY")
    SELECTION_MODEL_DEPLOY = os.getenv("SELECTION_MODEL_DEPLOY")
    TERMINATION_MODEL_DEPLOY = os.getenv("TERMINATION_MODEL_DEPLOY")


class AgentsConfigDialect:
    """Configuration for the agents module."""

    def __init__(self, sql_dialect_in, sql_dialect_out):
        self.sql_dialect_in = sql_dialect_in
        self.sql_dialect_out = sql_dialect_out


def create_config(sql_dialect_in, sql_dialect_out):
    """Create and return a new AgentConfig object."""
    return AgentsConfigDialect(sql_dialect_in, sql_dialect_out)
