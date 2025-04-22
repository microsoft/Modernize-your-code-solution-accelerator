"""Picker agent setup."""

import logging

from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent

from sql_agents.agents.agent_config import AgentBaseConfig
from sql_agents.agents.agent_factory import SQLAgentFactory
from sql_agents.helpers.models import AgentType

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def setup_picker_agent(config: AgentBaseConfig) -> AzureAIAgent:
    """Setup the picker agent using the factory."""
    return await SQLAgentFactory.create_agent(
        agent_type=AgentType.PICKER,
        config=config,
        temperature=0.0,
    )
