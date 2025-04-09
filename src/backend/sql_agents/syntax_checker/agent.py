"""This module contains the syntax checker agent."""

import logging

from sql_agents.agent_base import BaseSQLAgent
from sql_agents.helpers.models import AgentType
from sql_agents.syntax_checker.plug_ins import SyntaxCheckerPlugin
from sql_agents.syntax_checker.response import SyntaxCheckerResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SyntaxCheckerAgent(BaseSQLAgent[SyntaxCheckerResponse]):
    """Syntax checker agent for validating SQL syntax."""

    @property
    def response_object(self) -> type:
        """Get the response schema for the syntax checker agent."""
        return SyntaxCheckerResponse

    @property
    def plugins(self):
        """Get the plugins for the syntax checker agent."""
        return ["check_syntax", SyntaxCheckerPlugin()]

    @property
    def deployment_name(self) -> str:
        """Get the name of the model to use for the picker agent."""
        return self.config.model_type[AgentType.SYNTAX_CHECKER]
