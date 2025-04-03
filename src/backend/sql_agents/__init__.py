# """This module initializes the agents and helpers for the"""

# from common.models.api import AgentType
from sql_agents.fixer.agent import FixerAgent, setup_fixer_agent
from sql_agents.migrator.agent import MigratorAgent, setup_migrator_agent
from sql_agents.picker.agent import PickerAgent, setup_picker_agent
from sql_agents.semantic_verifier.agent import (
    SemanticVerifierAgent,
    setup_semantic_verifier_agent,
)
from sql_agents.syntax_checker.agent import (
    SyntaxCheckerAgent,
    setup_syntax_checker_agent,
)

# from sql_agents.agent_config import AgentBaseConfig
# from sql_agents.agent_factory import SQLAgentFactory

__all__ = [
    "setup_migrator_agent",
    "MigratorAgent",
    "setup_fixer_agent",
    "FixerAgent",
    "setup_picker_agent",
    "PickerAgent",
    "setup_syntax_checker_agent",
    "SyntaxCheckerAgent",
    "setup_semantic_verifier_agent",
    "SemanticVerifierAgent",
]
