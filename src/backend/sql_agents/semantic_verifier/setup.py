"""This module contains the setup for the semantic verifier agent."""

import logging

from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent

from sql_agents.agent_config import AgentBaseConfig
from sql_agents.agent_factory import SQLAgentFactory
from sql_agents.helpers.models import AgentType

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def setup_semantic_verifier_agent(config: AgentBaseConfig) -> AzureAIAgent:
    """Setup the semantic verifier agent using the factory."""
    return await SQLAgentFactory.create_agent(
        agent_type=AgentType.SEMANTIC_VERIFIER,
        config=config,
        temperature=0.0,
    )
