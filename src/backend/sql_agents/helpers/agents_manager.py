"""Module to manage the SQL agents for migration."""

import logging

from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent  # pylint: disable=E0611

from sql_agents.agents.agent_config import AgentBaseConfig
from sql_agents.agents.fixer.setup import setup_fixer_agent
from sql_agents.agents.migrator.setup import setup_migrator_agent
from sql_agents.agents.picker.setup import setup_picker_agent
from sql_agents.agents.semantic_verifier.setup import setup_semantic_verifier_agent
from sql_agents.agents.syntax_checker.setup import setup_syntax_checker_agent
from sql_agents.helpers.models import AgentType

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SqlAgents:
    """Class to setup the SQL agents for migration."""

    # List of agents in the solution
    agent_fixer: AzureAIAgent = None
    agent_migrator: AzureAIAgent = None
    agent_picker: AzureAIAgent = None
    agent_syntax_checker: AzureAIAgent = None
    agent_semantic_verifier: AzureAIAgent = None
    agent_config: AgentBaseConfig = None

    def __init__(self):
        pass

    @classmethod
    async def create(cls, config: AgentBaseConfig):
        """Create the SQL agents for migration.
        Required as init cannot be async
        """
        self = cls()  # Create an instance
        try:
            self.agent_config = config
            self.agent_fixer = await setup_fixer_agent(config)
            self.agent_migrator = await setup_migrator_agent(config)
            self.agent_picker = await setup_picker_agent(config)
            self.agent_syntax_checker = await setup_syntax_checker_agent(config)
            self.agent_semantic_verifier = await setup_semantic_verifier_agent(config)
        except ValueError as exc:
            logger.error("Error setting up agents.")
            raise exc

        return self

    @property
    def agents(self):
        """Return a list of the agents."""
        return [
            self.agent_migrator,
            self.agent_picker,
            self.agent_syntax_checker,
            self.agent_fixer,
            self.agent_semantic_verifier,
        ]

    @property
    def idx_agents(self):
        """Return a list of the main agents."""
        return {
            AgentType.MIGRATOR: self.agent_migrator,
            AgentType.PICKER: self.agent_picker,
            AgentType.SYNTAX_CHECKER: self.agent_syntax_checker,
            AgentType.FIXER: self.agent_fixer,
            AgentType.SEMANTIC_VERIFIER: self.agent_semantic_verifier,
        }

    async def delete_agents(self):
        """Cleans up the agents from Azure Foundry"""
        try:
            for agent in self.agents:
                await self.agent_config.ai_project_client.agents.delete_agent(agent.id)
        except Exception as exc:
            logger.error("Error deleting agents: %s", exc)
