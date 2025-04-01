"""Picker agent setup."""

import logging

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
from sql_agents.picker.response import PickerResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# NUM_CANDIDATES = 3


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


async def setup_picker_agent(
    name: AgentType, config: AgentsConfigDialect, deployment_name: AgentModelDeployment
) -> AzureAIAgent:
    """Setup the picker agent using the factory."""
    return await SQLAgentFactory.create_agent(name, config, deployment_name)


# async def setup_picker_agent(
#     name: AgentType, config: AgentsConfigDialect, deployment_name: AgentModelDeployment
# ) -> AzureAIAgent:
#     """Setup the picker agent."""
#     _deployment_name = deployment_name.value
#     _name = name.value

#     try:
#         template_content = get_prompt(_name)
#     except FileNotFoundError as exc:
#         logger.error("Prompt file for %s not found.", _name)
#         raise ValueError(f"Prompt file for {_name} not found.") from exc

#     kernel_args = KernelArguments(
#         target=config.sql_dialect_out,
#         numCandidates=str(NUM_CANDIDATES),
#         source=config.sql_dialect_in,
#     )

#     # Define an agent on the Azure AI agent service
#     agent_definition = await app_config.ai_project_client.agents.create_agent(
#         model=_deployment_name,
#         name=_name,
#         instructions=template_content,
#         temperature=0.0,
#         response_format=ResponseFormatJsonSchemaType(
#             json_schema=ResponseFormatJsonSchema(
#                 name="PickerResponse",
#                 description="respond with picker response",
#                 schema=PickerResponse.model_json_schema(),
#             )
#         ),
#     )

#     # Create a Semantic Kernel agent based on the agent definition.
#     # Add RAG with docs programmatically for this one
#     picker_agent = AzureAIAgent(
#         client=app_config.ai_project_client,
#         definition=agent_definition,
#         arguments=kernel_args,
#     )

#     return picker_agent
