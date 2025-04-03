"""module for setting up the migrator agent."""

import logging

from sql_agents.migrator.response import MigratorResponse

from backend.sql_agents.agent_base import BaseSQLAgent

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MigratorAgent(BaseSQLAgent[MigratorResponse]):
    """Migrator agent for translating SQL from one dialect to another."""

    @property
    def response_schema(self) -> type:
        """Get the response schema for the migrator agent."""
        return MigratorResponse

    @property
    def num_candidates(self) -> int:
        """Get the number of candidates for the migrator agent."""
        return 3
