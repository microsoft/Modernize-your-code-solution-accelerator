"""Fixer agent class."""

import logging

from sql_agents.agent_base import (
    BaseSQLAgent,
)  # Ensure this import is correct and the module exists
from sql_agents.fixer.response import FixerResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FixerAgent(BaseSQLAgent[FixerResponse]):
    """Fixer agent for correcting SQL syntax errors."""

    @property
    def response_schema(self) -> type:
        """Get the response schema for the fixer agent."""
        return FixerResponse
