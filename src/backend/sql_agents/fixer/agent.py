"""Fixer agent setup."""

import logging

from azure.ai.projects.models import (
    ResponseFormatJsonSchema,
    ResponseFormatJsonSchemaType,
)
from backend.sql_agents.agent_base import (
    BaseSQLAgent,
)  # Ensure this import is correct and the module exists
from backend.sql_agents.agent_factory import SQLAgentFactory
from common.config.config import app_config
from common.models.api import AgentType
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
from semantic_kernel.kernel import KernelArguments
from sql_agents.agent_config import AgentModelDeployment, AgentsConfigDialect
from sql_agents.fixer.response import FixerResponse
from sql_agents.helpers.utils import get_prompt

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FixerAgent(BaseSQLAgent[FixerResponse]):
    """Fixer agent for correcting SQL syntax errors."""

    @property
    def response_schema(self) -> type:
        """Get the response schema for the fixer agent."""
        return FixerResponse


# async def setup_fixer_agent(
#     name: AgentType, config: AgentsConfigDialect, deployment_name: AgentModelDeployment
# ) -> AzureAIAgent:
#     """Setup the fixer agent."""
#     _deployment_name = deployment_name.value
#     _name = name.value

#     try:
#         template_content = get_prompt(_name)
#     except FileNotFoundError as exc:
#         logger.error("Prompt file for %s not found.", _name)
#         raise ValueError(f"Prompt file for {_name} not found.") from exc

#     kernel_args = KernelArguments(target=config.sql_dialect_out)

#     # Define an agent on the Azure AI agent service
#     agent_definition = await app_config.ai_project_client.agents.create_agent(
#         model=_deployment_name,
#         name=_name,
#         instructions=template_content,
#         temperature=0.0,
#         response_format=ResponseFormatJsonSchemaType(
#             json_schema=ResponseFormatJsonSchema(
#                 name="FixerResponse",
#                 description="respond with fixer response",
#                 schema=FixerResponse.model_json_schema(),
#             )
#         ),
#     )

#     # Create a Semantic Kernel agent based on the agent definition.
#     # Add RAG with docs programmatically for this one
#     fixer_agent = AzureAIAgent(
#         client=app_config.ai_project_client,
#         definition=agent_definition,
#         arguments=kernel_args,
#     )

#     return fixer_agent


async def setup_fixer_agent(
    name: AgentType, config: AgentsConfigDialect, deployment_name: AgentModelDeployment
) -> AzureAIAgent:
    """Setup the fixer agent using the factory."""
    return await SQLAgentFactory.create_agent(name, config, deployment_name)
