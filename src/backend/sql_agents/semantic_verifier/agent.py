"""This module contains the setup for the semantic verifier agent."""

import logging
from typing import Any, Dict, Optional

from azure.ai.projects.models import (
    ResponseFormatJsonSchema,
    ResponseFormatJsonSchemaType,
)
from backend.sql_agents.agent_base import BaseSQLAgent
from backend.sql_agents.agent_factory import SQLAgentFactory
from common.config.config import app_config
from common.models.api import AgentType
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
from semantic_kernel.kernel import KernelArguments
from sql_agents.agent_config import AgentModelDeployment, AgentsConfigDialect
from sql_agents.helpers.utils import get_prompt
from sql_agents.semantic_verifier.response import SemanticVerifierResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def setup_semantic_verifier_agent(
    name: AgentType,
    config: AgentsConfigDialect,
    deployment_name: AgentModelDeployment,
    source_query: str,
    target_query: str,
) -> AzureAIAgent:
    """Setup the semantic verifier agent using the factory."""
    return await SQLAgentFactory.create_agent(
        name,
        config,
        deployment_name,
        source_query=source_query,
        target_query=target_query,
    )


class SemanticVerifierAgent(BaseSQLAgent[SemanticVerifierResponse]):
    """Semantic verifier agent for checking semantic equivalence between SQL queries."""

    def __init__(
        self,
        agent_type: AgentType,
        config: AgentsConfigDialect,
        deployment_name: AgentModelDeployment,
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
        super().__init__(agent_type, config, deployment_name, temperature)
        self.source_query = source_query
        self.target_query = target_query
        self.extra_kwargs = kwargs

    @property
    def response_schema(self) -> type:
        """Get the response schema for the semantic verifier agent."""
        return SemanticVerifierResponse

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


# async def setup_semantic_verifier_agent(
#     name: AgentType,
#     config: AgentsConfigDialect,
#     deployment_name: AgentModelDeployment,
#     source_query: str,
#     target_query: str,
# ) -> AzureAIAgent:
#     """Setup the semantic verifier agent."""
#     _deployment_name = deployment_name.value
#     _name = name.value

#     try:
#         template_content = get_prompt(_name)
#     except FileNotFoundError as exc:
#         logger.error("Prompt file for %s not found.", _name)
#         raise ValueError(f"Prompt file for {_name} not found.") from exc

#     kernel_args = KernelArguments(
#         target=config.sql_dialect_out,
#         source=config.sql_dialect_in,
#         source_query=source_query,
#         target_query=target_query,
#     )

#     # Define an agent on the Azure AI agent service
#     agent_definition = await app_config.ai_project_client.agents.create_agent(
#         model=_deployment_name,
#         name=_name,
#         instructions=template_content,
#         temperature=0.0,
#         response_format=ResponseFormatJsonSchemaType(
#             json_schema=ResponseFormatJsonSchema(
#                 name="SemanticVerifierResponse",
#                 description="respond with SemanticVerifier response",
#                 schema=SemanticVerifierResponse.model_json_schema(),
#             )
#         ),
#     )

#     # Create a Semantic Kernel agent based on the agent definition.
#     # Add RAG with docs programmatically for this one
#     semantic_verifier_agent = AzureAIAgent(
#         client=app_config.ai_project_client,
#         definition=agent_definition,
#         arguments=kernel_args,
#     )

#     return semantic_verifier_agent
