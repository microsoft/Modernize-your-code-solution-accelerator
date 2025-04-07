"""This module contains the setup for the semantic verifier agent."""

import logging
from typing import Any, Dict, Optional

from common.models.api import AgentType
from sql_agents.agent_base import BaseSQLAgent
from sql_agents.agent_config import AgentBaseConfig
from sql_agents.semantic_verifier.response import SemanticVerifierResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SemanticVerifierAgent(BaseSQLAgent[SemanticVerifierResponse]):
    """Semantic verifier agent for checking semantic equivalence between SQL queries."""

    def __init__(
        self,
        config: AgentBaseConfig,
        temperature: float = 0.0,
        source_query: Optional[str] = None,
        target_query: Optional[str] = None,
        **kwargs
    ):
        """Initialize the semantic verifier agent.

        Args:
            agent_type: The type of agent to create.
            config: The dialect configuration for the agent.
            deployment_name: The model deployment to use.
            temperature: The temperature parameter for the model.
            source_query: The source SQL query to verify.
            target_query: The target SQL query to verify against.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(AgentType.SEMANTIC_VERIFIER, config, temperature)
        self.source_query = source_query
        self.target_query = target_query
        self.extra_kwargs = kwargs

    @property
    def response_schema(self) -> type:
        """Get the response schema for the semantic verifier agent."""
        return SemanticVerifierResponse

    @property
    def deployment_name(self) -> str:
        """Get the name of the model to use for the picker agent."""
        return self.config.model_type[AgentType.SEMANTIC_VERIFIER]

    def get_kernel_arguments(self) -> Dict[str, Any]:
        """Get the kernel arguments for this agent.

        Returns:
            A dictionary with the necessary arguments.
        """
        args = super().get_kernel_arguments()

        # Add source and target queries if provided
        if self.source_query is not None:
            args["source_query"] = self.source_query
        if self.target_query is not None:
            args["target_query"] = self.target_query

        return args
