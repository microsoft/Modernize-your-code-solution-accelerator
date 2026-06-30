"""Setup module for the syntax checker agent."""

import logging

from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent

from sql_agents.agents.agent_config import AgentBaseConfig
from sql_agents.agents.agent_factory import SQLAgentFactory
from sql_agents.helpers.models import AgentType

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def setup_syntax_checker_agent(
    config: AgentBaseConfig,
) -> AzureAIAgent:
    """Setup the syntax checker agent using the factory."""
    return await SQLAgentFactory.create_agent(AgentType.SYNTAX_CHECKER, config)
