"""Set up the syntax checker agent."""

import logging

from common.models.api import AgentType

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.kernel import KernelArguments

from sql_agents.agent_config import AgentModelDeployment, AgentsConfigDialect
from sql_agents.helpers.sk_utils import create_kernel_with_chat_completion
from sql_agents.helpers.utils import get_prompt
from sql_agents.syntax_checker.plug_ins import SyntaxCheckerPlugin
from sql_agents.syntax_checker.response import SyntaxCheckerResponse


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def setup_syntax_checker_agent(
    name: AgentType, config: AgentsConfigDialect, deployment_name: AgentModelDeployment
) -> ChatCompletionAgent:
    """Set up the syntax checker agent."""
    _deployment_name = deployment_name.value
    _name = name.value
    kernel = create_kernel_with_chat_completion(_name, _deployment_name)

    try:
        template_content = get_prompt(_name)
    except FileNotFoundError as exc:
        logger.error("Prompt file for %s not found.", _name)
        raise ValueError(f"Prompt file for {_name} not found.") from exc

    settings = kernel.get_prompt_execution_settings_from_service_id(
        service_id="syntax_checker"
    )
    settings.response_format = SyntaxCheckerResponse
    settings.temperature = 0.0

    # Configure the function choice behavior to auto invoke kernel functions
    settings.function_choice_behavior = FunctionChoiceBehavior.Required()

    kernel_args = KernelArguments(target=config.sql_dialect_out, settings=settings)

    kernel.add_plugin(SyntaxCheckerPlugin(), plugin_name="check_syntax")

    syntax_checker_agent = ChatCompletionAgent(
        kernel=kernel,
        name=_name,
        instructions=template_content,
        arguments=kernel_args,
    )
    return syntax_checker_agent
