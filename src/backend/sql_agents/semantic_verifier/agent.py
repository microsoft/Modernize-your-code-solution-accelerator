"""This module contains the setup for the semantic verifier agent."""

import logging

from sql_agents.agent_base import BaseSQLAgent
from sql_agents.helpers.models import AgentType
from sql_agents.semantic_verifier.response import SemanticVerifierResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SemanticVerifierAgent(BaseSQLAgent[SemanticVerifierResponse]):
    """Semantic verifier agent for checking semantic equivalence between SQL queries."""

    @property
    def response_object(self) -> type:
        """Get the response schema for the semantic verifier agent."""
        return SemanticVerifierResponse

    @property
    def deployment_name(self) -> str:
        """Get the name of the model to use for the picker agent."""
        return self.config.model_type[AgentType.SEMANTIC_VERIFIER]
