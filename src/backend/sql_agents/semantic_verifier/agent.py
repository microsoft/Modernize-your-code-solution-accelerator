"""This module contains the setup for the semantic verifier agent."""

import logging

from common.models.api import AgentType
from helpers.sk_utils import create_kernel_with_chat_completion
from helpers.utils import get_prompt
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.kernel import KernelArguments
from sql_agents.agent_config import AgentModelDeployment, AgentsConfigDialect
from sql_agents.semantic_verifier.response import SemanticVerifierResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def setup_semantic_verifier_agent(
    name: AgentType,
    config: AgentsConfigDialect,
    deployment_name: AgentModelDeployment,
    source_query: str,
    target_query: str,
) -> ChatCompletionAgent:
    """Setup the semantic verifier agent."""
    _deployment_name = deployment_name.value
    _name = name.value
    kernel = create_kernel_with_chat_completion(_name, _deployment_name)

    try:
        template_content = get_prompt(_name)
    except FileNotFoundError as exc:
        logger.error("Prompt file for %s not found.", _name)
        raise ValueError(f"Prompt file for {_name} not found.") from exc

    settings = kernel.get_prompt_execution_settings_from_service_id(
        service_id="semantic_verifier"
    )
    settings.response_format = SemanticVerifierResponse
    settings.temperature = 0.0

    kernel_args = KernelArguments(
        target=config.sql_dialect_out,
        source=config.sql_dialect_in,
        source_query=source_query,
        target_query=target_query,
        settings=settings,
    )

    semantic_verifier_agent = ChatCompletionAgent(
        kernel=kernel,
        name=_name,
        instructions=template_content,
        arguments=kernel_args,
    )

    return semantic_verifier_agent
