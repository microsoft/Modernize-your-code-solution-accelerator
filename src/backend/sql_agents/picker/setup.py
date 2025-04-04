"""Picker agent setup."""

import logging

from common.models.api import AgentType
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
from sql_agents.agent_config import AgentBaseConfig
from sql_agents.agent_factory import SQLAgentFactory

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def setup_picker_agent(config: AgentBaseConfig) -> AzureAIAgent:
    """Setup the picker agent using the factory."""
    return await SQLAgentFactory.create_agent(AgentType.PICKER, config)
