"""Picker agent setup."""

import logging

from common.models.api import AgentType
from sql_agents.agent_base import BaseSQLAgent
from sql_agents.picker.response import PickerResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PickerAgent(BaseSQLAgent[PickerResponse]):
    """Picker agent for selecting the best SQL translation candidate."""

    @property
    def response_schema(self) -> type:
        """Get the response schema for the picker agent."""
        return PickerResponse

    @property
    def num_candidates(self) -> int:
        """Get the number of candidates for the picker agent."""
        return 3

    @property
    def deployment_name(self) -> str:
        """Get the name of the model to use for the picker agent."""
        return self.config.model_type[AgentType.PICKER]
