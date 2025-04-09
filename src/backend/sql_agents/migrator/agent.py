"""module for setting up the migrator agent."""

import logging

from sql_agents.agent_base import BaseSQLAgent
from sql_agents.helpers.models import AgentType
from sql_agents.migrator.response import MigratorResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MigratorAgent(BaseSQLAgent[MigratorResponse]):
    """Migrator agent for translating SQL from one dialect to another."""

    @property
    def response_object(self) -> type:
        """Get the response schema for the migrator agent."""
        return MigratorResponse

    @property
    def num_candidates(self) -> int:
        """Get the number of candidates for the migrator agent."""
        return 3

    @property
    def deployment_name(self) -> str:
        """Get the name of the model to use for the picker agent."""
        return self.config.model_type[AgentType.MIGRATOR]
