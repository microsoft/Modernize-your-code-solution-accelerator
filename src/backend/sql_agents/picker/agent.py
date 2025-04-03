"""Picker agent setup."""

import logging

from sql_agents.picker.response import PickerResponse

from backend.sql_agents.agent_base import BaseSQLAgent

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
