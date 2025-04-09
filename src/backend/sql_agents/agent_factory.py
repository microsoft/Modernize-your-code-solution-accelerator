"""Factory for creating SQL migration agents."""

import logging
from typing import Any, Dict, Optional, Type, TypeVar

from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent

from sql_agents.agent_base import BaseSQLAgent
from sql_agents.agent_config import AgentBaseConfig
from sql_agents.fixer.agent import FixerAgent
from sql_agents.helpers.models import AgentType
from sql_agents.migrator.agent import MigratorAgent
from sql_agents.picker.agent import PickerAgent
from sql_agents.semantic_verifier.agent import SemanticVerifierAgent
from sql_agents.syntax_checker.agent import SyntaxCheckerAgent

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Type variable for agent response types
T = TypeVar("T")


class SQLAgentFactory:
    """Factory for creating SQL migration agents."""

    _agent_classes = {
        AgentType.PICKER: PickerAgent,
        AgentType.MIGRATOR: MigratorAgent,
        AgentType.SYNTAX_CHECKER: SyntaxCheckerAgent,
        AgentType.FIXER: FixerAgent,
        AgentType.SEMANTIC_VERIFIER: SemanticVerifierAgent,
    }

    @classmethod
    async def create_agent(
        cls,
        agent_type: AgentType,
        config: AgentBaseConfig,
        temperature: float = 0.0,
        **kwargs,
    ) -> AzureAIAgent:
        """Create and setup an agent of the specified type.

        Args:
            agent_type: The type of agent to create.
            config: The dialect configuration for the agent.
            deployment_name: The model deployment to use.
            temperature: The temperature parameter for the model.
            **kwargs: Additional parameters to pass to the agent constructor.

        Returns:
            A configured AzureAIAgent instance.
        """
        agent_class = cls._agent_classes.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")

        # Prepare constructor parameters
        params = {
            "agent_type": agent_type,
            "config": config,
            "temperature": temperature,
            **kwargs,
        }
        try:
            agent = agent_class(**params)
        except TypeError as e:
            logger.error(
                "Error creating agent of type %s with parameters %s: %s",
                agent_type,
                params,
                e,
            )
            raise
        return await agent.setup()

    @classmethod
    def get_agent_class(cls, agent_type: AgentType) -> Type[BaseSQLAgent]:
        """Get the agent class for the specified type."""
        agent_class = cls._agent_classes.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return agent_class

    @classmethod
    def register_agent_class(
        cls, agent_type: AgentType, agent_class: Type[BaseSQLAgent]
    ) -> None:
        """Register a new agent class with the factory."""
        cls._agent_classes[agent_type] = agent_class
        logger.info(
            "Registered agent class %s for type %s",
            agent_class.__name__,
            agent_type.value,
        )
