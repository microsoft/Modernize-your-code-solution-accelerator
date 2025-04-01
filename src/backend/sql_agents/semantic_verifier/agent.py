"""This module contains the setup for the semantic verifier agent."""

import logging

from azure.ai.projects.models import (
    ResponseFormatJsonSchema,
    ResponseFormatJsonSchemaType,
)
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
    """Setup the semantic verifier agent."""
    _deployment_name = deployment_name.value
    _name = name.value

    try:
        template_content = get_prompt(_name)
    except FileNotFoundError as exc:
        logger.error("Prompt file for %s not found.", _name)
        raise ValueError(f"Prompt file for {_name} not found.") from exc

    kernel_args = KernelArguments(
        target=config.sql_dialect_out,
        source=config.sql_dialect_in,
        source_query=source_query,
        target_query=target_query,
    )

    # Define an agent on the Azure AI agent service
    agent_definition = await app_config.ai_project_client.agents.create_agent(
        model=_deployment_name,
        name=_name,
        instructions=template_content,
        temperature=0.0,
        response_format=ResponseFormatJsonSchemaType(
            json_schema=ResponseFormatJsonSchema(
                name="SemanticVerifierResponse",
                description="respond with SemanticVerifier response",
                schema=SemanticVerifierResponse.model_json_schema(),
            )
        ),
    )

    # Create a Semantic Kernel agent based on the agent definition.
    # Add RAG with docs programmatically for this one
    semantic_verifier_agent = AzureAIAgent(
        client=app_config.ai_project_client,
        definition=agent_definition,
        arguments=kernel_args,
    )

    return semantic_verifier_agent
