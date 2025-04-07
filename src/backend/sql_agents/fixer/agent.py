"""Fixer agent class."""

import logging

from common.models.api import AgentType
from sql_agents.agent_base import BaseSQLAgent
from sql_agents.fixer.response import FixerResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FixerAgent(BaseSQLAgent[FixerResponse]):
    """Fixer agent for correcting SQL syntax errors."""

    @property
    def response_schema(self) -> type:
        """Get the response schema for the fixer agent."""
        return FixerResponse

    @property
    def deployment_name(self) -> str:
        """Get the name of the model to use for the picker agent."""
        return self.config.model_type[AgentType.FIXER]
