"""module for setting up the migrator agent."""

import logging

from azure.ai.projects.models import (
    ResponseFormatJsonSchema,
    ResponseFormatJsonSchemaType,
)
from common.config.config import app_config
from common.models.api import AgentType
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
from semantic_kernel.functions import KernelArguments
from sql_agents.agent_config import AgentModelDeployment, AgentsConfigDialect
from sql_agents.helpers.utils import get_prompt
from sql_agents.migrator.response import MigratorResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def setup_migrator_agent(
    name: AgentType, config: AgentsConfigDialect, deployment_name: AgentModelDeployment
) -> AzureAIAgent:
    """Setup the migrator agent."""
    _deployment_name = deployment_name.value
    _name = name.value
    num_candidates = 3

    try:
        template_content = get_prompt(_name)
    except FileNotFoundError as exc:
        logger.error("Prompt file for %s not found.", _name)
        raise ValueError(f"Prompt file for {_name} not found.") from exc

    kernel_args = KernelArguments(
        target=config.sql_dialect_out,
        numCandidates=str(num_candidates),
        source=config.sql_dialect_in,
    )

    # Define an agent on the Azure AI agent service
    agent_definition = await app_config.ai_project_client.agents.create_agent(
        model=_deployment_name,
        name=_name,
        instructions=template_content,
        temperature=0.0,
        response_format=ResponseFormatJsonSchemaType(
            json_schema=ResponseFormatJsonSchema(
                name="MigratorResponse",
                description="respond with migrator response",
                schema=MigratorResponse.model_json_schema(),
            )
        ),
    )

    # Create a Semantic Kernel agent based on the agent definition.
    # Add RAG with docs programmatically for this one
    migrator_agent = AzureAIAgent(
        client=app_config.ai_project_client,
        definition=agent_definition,
        arguments=kernel_args,
    )

    return migrator_agent
