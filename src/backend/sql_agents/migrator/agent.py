"""module for setting up the migrator agent."""

import logging

from common.models.api import AgentType
from helpers.sk_utils import create_kernel_with_chat_completion
from helpers.utils import get_prompt
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.functions import KernelArguments
from sql_agents.agent_config import AgentModelDeployment, AgentsConfigDialect
from sql_agents.migrator.response import MigratorResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def setup_migrator_agent(
    name: AgentType, config: AgentsConfigDialect, deployment_name: AgentModelDeployment
) -> ChatCompletionAgent:
    """Setup the migrator agent."""
    _deployment_name = deployment_name.value
    _name = name.value
    NUM_CANDIDATES = 3

    kernel = create_kernel_with_chat_completion(_name, _deployment_name)

    try:
        template_content = get_prompt(_name)
    except FileNotFoundError as exc:
        logger.error("Prompt file for %s not found.", _name)
        raise ValueError(f"Prompt file for {_name} not found.") from exc

    settings = kernel.get_prompt_execution_settings_from_service_id(
        service_id="migrator"
    )
    settings.response_format = MigratorResponse
    settings.temperature = 0.0

    kernel_args = KernelArguments(
        target=config.sql_dialect_out,
        numCandidates=str(NUM_CANDIDATES),
        source=config.sql_dialect_in,
        settings=settings,
    )

    migrator_agent = ChatCompletionAgent(
        kernel=kernel,
        name=name,
        instructions=template_content,
        arguments=kernel_args,
    )

    return migrator_agent
