"""This module contains the syntax checker agent."""

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
from sql_agents.syntax_checker.plug_ins import SyntaxCheckerPlugin
from sql_agents.syntax_checker.response import SyntaxCheckerResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def setup_syntax_checker_agent(
    name: AgentType, config: AgentsConfigDialect, deployment_name: AgentModelDeployment
) -> AzureAIAgent:
    """Setup the syntax checker agent using the factory."""
    return await SQLAgentFactory.create_agent(name, config, deployment_name)


class SyntaxCheckerAgent(BaseSQLAgent[SyntaxCheckerResponse]):
    """Syntax checker agent for validating SQL syntax."""

    @property
    def response_schema(self) -> type:
        """Get the response schema for the syntax checker agent."""
        return SyntaxCheckerResponse

    @property
    def plugins(self):
        """Get the plugins for the syntax checker agent."""
        return ["check_syntax", SyntaxCheckerPlugin()]


# async def setup_syntax_checker_agent(
#     name: AgentType, config: AgentsConfigDialect, deployment_name: AgentModelDeployment
# ) -> AzureAIAgent:
#     """Setup the syntax checker agent."""
#     _deployment_name = deployment_name.value
#     _name = name.value

#     try:
#         template_content = get_prompt(_name)
#     except FileNotFoundError as exc:
#         logger.error("Prompt file for %s not found.", _name)
#         raise ValueError(f"Prompt file for {_name} not found.") from exc

#     # Configure the function choice behavior to auto invoke kernel functions
#     # settings.function_choice_behavior = FunctionChoiceBehavior.Required()

#     kernel_args = KernelArguments(target=config.sql_dialect_out)

#     # Define an agent on the Azure AI agent service
#     agent_definition = await app_config.ai_project_client.agents.create_agent(
#         model=_deployment_name,
#         name=_name,
#         instructions=template_content,
#         temperature=0.0,
#         response_format=ResponseFormatJsonSchemaType(
#             json_schema=ResponseFormatJsonSchema(
#                 name="SyntaxCheckerResponse",
#                 description="respond with SyntaxChecker response",
#                 schema=SyntaxCheckerResponse.model_json_schema(),
#             )
#         ),
#     )

#     # Create a Semantic Kernel agent based on the agent definition.
#     # Add RAG with docs programmatically for this one
#     syntax_checker_agent = AzureAIAgent(
#         client=app_config.ai_project_client,
#         definition=agent_definition,
#         arguments=kernel_args,
#         plugins=["check_syntax", SyntaxCheckerPlugin()],
#     )
#     return syntax_checker_agent
