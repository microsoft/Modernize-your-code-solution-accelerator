"""Picker agent setup."""

import logging

from sql_agents.agents.agent_base import BaseSQLAgent
from sql_agents.agents.picker.response import PickerResponse
from sql_agents.helpers.models import AgentType

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PickerAgent(BaseSQLAgent[PickerResponse]):
    """Picker agent for selecting the best SQL translation candidate."""

    @property
    def response_object(self) -> type:
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
