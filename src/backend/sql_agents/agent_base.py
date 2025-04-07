"""Base classes for SQL migration agents."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, TypeVar, Union

from azure.ai.projects.models import (
    ResponseFormatJsonSchema,
    ResponseFormatJsonSchemaType,
)
from common.models.api import AgentType
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
from semantic_kernel.functions import KernelArguments
from sql_agents.agent_config import AgentBaseConfig
from sql_agents.helpers.utils import get_prompt

# Type variable for response models
T = TypeVar("T")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BaseSQLAgent(Generic[T], ABC):
    """Base class for all SQL migration agents."""

    def __init__(
        self,
        agent_type: AgentType,
        config: AgentBaseConfig,
        temperature: float = 0.0,
    ):
        """Initialize the base SQL agent.

        Args:
            agent_type: The type of agent to create.
            config: The dialect configuration for the agent.
            deployment_name: The model deployment to use.
            temperature: The temperature parameter for the model.
        """
        self.agent_type = agent_type
        self.config = config
        self.temperature = temperature
        self.agent: AzureAIAgent = None

    @property
    @abstractmethod
    def response_schema(self) -> type:
        """Get the response schema for this agent."""
        pass

    @property
    def num_candidates(self) -> Optional[int]:
        """Get the number of candidates for this agent.

        Returns:
            The number of candidates, or None if not applicable.
        """
        return None

    @property
    def deployment_name(self) -> Optional[str]:
        """Get the name of the model to be used for this agent.

        Returns:
            The model name, or None if not applicable.
        """
        return None

    @property
    def plugins(self) -> Optional[List[Union[str, Any]]]:
        """Get the plugins for this agent.

        Returns:
            A list of plugins, or None if not applicable.
        """
        return None

    def get_kernel_arguments(self) -> KernelArguments:
        """Get the kernel arguments for this agent.

        Returns:
            A KernelArguments object with the necessary arguments.
        """
        args = {
            "target": self.config.sql_to,
            "source": self.config.sql_from,
        }

        if self.num_candidates is not None:
            args["numCandidates"] = str(self.num_candidates)

        return KernelArguments(**args)

    async def setup(self) -> AzureAIAgent:
        """Setup the agent with Azure AI."""
        _name = self.agent_type.value
        _deployment_name = self.config.model_type.get(self.agent_type)

        try:
            template_content = get_prompt(_name)
        except FileNotFoundError as exc:
            logger.error("Prompt file for %s not found.", _name)
            raise ValueError(f"Prompt file for {_name} not found.") from exc

        kernel_args = self.get_kernel_arguments()

        # Define an agent on the Azure AI agent service
        agent_definition = await self.config.ai_project_client.agents.create_agent(
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
        agent_kwargs = {
            "client": self.config.ai_project_client,
            "definition": agent_definition,
            "arguments": kernel_args,
        }

        # Add plugins if specified
        if self.plugins:
            agent_kwargs["plugins"] = self.plugins

        self.agent = AzureAIAgent(**agent_kwargs)

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
