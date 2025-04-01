"""This module initializes the agents and helpers for the"""

from common.models.api import AgentType
from sql_agents.fixer.agent import setup_fixer_agent
from sql_agents.helpers.sk_utils import create_kernel_with_chat_completion
from sql_agents.helpers.utils import get_prompt
from sql_agents.migrator.agent import setup_migrator_agent
from sql_agents.picker.agent import setup_picker_agent
from sql_agents.semantic_verifier.agent import setup_semantic_verifier_agent
from sql_agents.syntax_checker.agent import setup_syntax_checker_agent

# Import the configuration function
from .agent_config import AgentsConfigDialect, create_config

__all__ = [
    "create_kernel_with_chat_completion",
    "setup_migrator_agent",
    "setup_fixer_agent",
    "setup_picker_agent",
    "setup_syntax_checker_agent",
    "setup_semantic_verifier_agent",
    "get_prompt",
    "create_config",
    "AgentType",
]
