"""This module contains the syntax checker agent."""

import logging

from sql_agents.agent_base import BaseSQLAgent
from sql_agents.syntax_checker.plug_ins import SyntaxCheckerPlugin
from sql_agents.syntax_checker.response import SyntaxCheckerResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SyntaxCheckerAgent(BaseSQLAgent[SyntaxCheckerResponse]):
    """Syntax checker agent for validating SQL syntax."""

    @property
    def response_schema(self) -> type:
        """Get the response schema for the syntax checker agent."""
        return SyntaxCheckerResponse

    @property
    def plugins(self):
        """Get the plugins for the syntax checker agent."""
        return ["check_syntax", SyntaxCheckerPlugin()]
