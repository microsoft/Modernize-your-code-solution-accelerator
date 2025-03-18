"""Fixer agent setup."""

import logging

from common.models.api import AgentType
from helpers.sk_utils import create_kernel_with_chat_completion
from helpers.utils import get_prompt
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.kernel import KernelArguments
from semantic_kernel.prompt_template import PromptTemplateConfig
from sql_agents.agent_config import AgentModelDeployment, AgentsConfigDialect
from sql_agents.fixer.response import FixerResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def setup_fixer_agent(
    name: AgentType, config: AgentsConfigDialect, deployment_name: AgentModelDeployment
) -> ChatCompletionAgent:
    """Setup the fixer agent."""
    _deployment_name = deployment_name.value
    _name = name.value
    kernel = create_kernel_with_chat_completion(_name, _deployment_name)

    try:
        template_content = get_prompt(_name)
    except FileNotFoundError as exc:
        logger.error("Prompt file for %s not found.", _name)
        raise ValueError(f"Prompt file for {_name} not found.") from exc

    # prompt = replace_tags(template_content, {"target": config.sql_dialect_out})

    settings = kernel.get_prompt_execution_settings_from_service_id(service_id=_name)
    settings.response_format = FixerResponse
    settings.temperature = 0.0

    kernel_args = KernelArguments(target=config.sql_dialect_out, settings=settings)

    fixer_agent = ChatCompletionAgent(
        kernel=kernel,
        name=_name,
        instructions=template_content,
        arguments=kernel_args,
    )

    return fixer_agent
