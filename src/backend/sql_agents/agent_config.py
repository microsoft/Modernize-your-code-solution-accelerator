"""Configuration class for the agents.
This class loads configuration values from environment variables and provides
properties to access them. It also stores an Azure AI client and SQL dialect
configuration for the agents, that will be set per batch.
Access to .env variables requires adding the `python-dotenv` package to, or
configuration of the env python path through the IDE. For example, in VSCode, the
settings.json file in the .vscode folder should include the following:
{
    "python.envFile": "${workspaceFolder}/.env"
}
"""

import os
from enum import Enum

from azure.ai.projects.aio import AIProjectClient
from common.models.api import AgentType


class AgentBaseConfig:
    """Agent model deployment names."""

    def __init__(self, project_client: AIProjectClient, sql_from: str, sql_to: str):

        self.ai_project_client: AIProjectClient = project_client
        self.sql_from = sql_from
        self.sql_to = sql_to

    model_type = {
        AgentType.MIGRATOR: os.getenv("MIGRATOR_AGENT_MODEL_DEPLOY"),
        AgentType.PICKER: os.getenv("PICKER_AGENT_MODEL_DEPLOY"),
        AgentType.FIXER: os.getenv("FIXER_AGENT_MODEL_DEPLOY"),
        AgentType.SEMANTIC_VERIFIER: os.getenv("SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY"),
        AgentType.SYNTAX_CHECKER: os.getenv("SYNTAX_CHECKER_AGENT_MODEL_DEPLOY"),
        AgentType.SELECTION: os.getenv("SELECTION_MODEL_DEPLOY"),
        AgentType.TERMINATION: os.getenv("TERMINATION_MODEL_DEPLOY"),
    }
