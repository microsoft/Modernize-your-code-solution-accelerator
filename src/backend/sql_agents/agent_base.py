"""Base classes for SQL migration agents."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from azure.ai.projects.models import (
    ResponseFormatJsonSchema,
    ResponseFormatJsonSchemaType,
)
from common.config.config import app_config
from common.models.api import AgentType
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
from semantic_kernel.functions import KernelArguments
from sql_agents.agent_config import AgentModelDeployment, AgentsConfigDialect
from sql_agents.helpers.utils import get_prompt

# Type variable for response models
T = TypeVar('T')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BaseSQLAgent(Generic[T], ABC):
    """Base class for all SQL migration agents."""

    def __init__(
        self,
        agent_type: AgentType,
        config: AgentsConfigDialect,
        deployment_name: AgentModelDeployment,

    ):
        """Initialize the base SQL agent."""
        self.agent_type = agent_type
        self.config = config
        self.deployment_name = deployment_name
        self.agent: AzureAIAgent = None


    @property
    @abstractmethod
    def response_schema(self) -> type:
        """Get the response schema for this agent."""
        pass

    @property
    @abstractmethod
    def num_candidates(self) -> int:
        """Get the number of candidates for this agent."""
        pass

    async def setup(self) -> AzureAIAgent:
        """Setup the agent with Azure AI."""
        _deployment_name = self.deployment_name.value
        _name = self.agent_type.value

        try:
            template_content = get_prompt(_name)
        except FileNotFoundError as exc:
            logger.error("Prompt file for %s not found.", _name)
            raise ValueError(f"Prompt file for {_name} not found.") from exc

        kernel_args = KernelArguments(
            target=self.config.sql_dialect_out,
            numCandidates=str(self.num_candidates),
            source=self.config.sql_dialect_in,
        )

        # Define an agent on the Azure AI agent service
        agent_definition = await app_config.ai_project_client.agents.create_agent(
            model=_deployment_name,
            name=_name,
            instructions=template_content,
            temperature=self.temperature,
            response_format=ResponseFormatJsonSchemaType(
                json_schema=ResponseFormatJsonSchema(
                    name=self.response_schema.__name__,
                    description=f"respond with {self.response_schema.__name__.lower()}",
                    schema=self.response_schema.model_json_schema(),
                )
            ),
        )

        # Create a Semantic Kernel agent based on the agent definition
        self.agent = AzureAIAgent(
            client=app_config.ai_project_client,
            definition=agent_definition,
            arguments=kernel_args,
        )

        return self.agent

    async def get_agent(self) -> AzureAIAgent:
        """Get the agent, setting it up if needed."""
        if self.agent is None:
            await self.setup()
        return self.agent

    async def execute(self, inputs: Any) -> T:
        """Execute the agent with the given inputs."""
        agent = await self.get_agent()
        response = await agent.invoke(inputs)
        return response  # Type will be inferred from T