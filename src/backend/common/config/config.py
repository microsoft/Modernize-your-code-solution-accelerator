"""Configuration class for the application.
This class loads configuration values from environment variables and provides
methods to access them. It also initializes an Azure AI client using the
provided credentials.
It uses the `azure.identity` library to handle authentication and
authorization with Azure services.
Access to .env variables requires adding the `python-dotenv` package to, or
configuration of the env python path through the IDE. For example, in VSCode, the
settings.json file in the .vscode folder should include the following:
{
    "python.envFile": "${workspaceFolder}/.env"
}
"""

import os

from azure.identity.aio import ClientSecretCredential

from helper.azure_credential_utils import get_azure_credential


class Config:
    """Configuration class for the application."""

    def __init__(self):
        self.azure_tenant_id = os.getenv("AZURE_TENANT_ID", "")
        self.azure_client_id = os.getenv("AZURE_CLIENT_ID", "")
        self.azure_client_secret = os.getenv("AZURE_CLIENT_SECRET", "")

        self.cosmosdb_endpoint = os.getenv("COSMOSDB_ENDPOINT")
        self.cosmosdb_database = os.getenv("COSMOSDB_DATABASE")
        self.cosmosdb_batch_container = os.getenv("COSMOSDB_BATCH_CONTAINER")
        self.cosmosdb_file_container = os.getenv("COSMOSDB_FILE_CONTAINER")
        self.cosmosdb_log_container = os.getenv("COSMOSDB_LOG_CONTAINER")

        self.azure_blob_container_name = os.getenv("AZURE_BLOB_CONTAINER_NAME")
        self.azure_blob_account_name = os.getenv("AZURE_BLOB_ACCOUNT_NAME")

        self.azure_service_bus_namespace = os.getenv("AZURE_SERVICE_BUS_NAMESPACE")
        self.azure_queue_name = os.getenv("AZURE_QUEUE_NAME")

        self.ai_project_endpoint = os.getenv("AI_PROJECT_ENDPOINT")
        self.migrator_agent_model_deploy = os.getenv("MIGRATOR_AGENT_MODEL_DEPLOY")
        self.picker_agent_model_deploy = os.getenv("PICKER_AGENT_MODEL_DEPLOY")
        self.fixer_agent_model_deploy = os.getenv("FIXER_AGENT_MODEL_DEPLOY")
        self.semantic_verifier_agent_model_deploy = os.getenv(
            "SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY"
        )
        self.syntax_checker_agent_model_deploy = os.getenv(
            "SYNTAX_CHECKER_AGENT_MODEL_DEPLOY"
        )

        self.__azure_credentials = get_azure_credential(self.azure_client_id)

    def get_azure_credentials(self):
        """Retrieve Azure credentials, either from environment variables or managed identity."""
        if all([self.azure_tenant_id, self.azure_client_id, self.azure_client_secret]):
            return ClientSecretCredential(
                tenant_id=self.azure_tenant_id,
                client_id=self.azure_client_id,
                client_secret=self.azure_client_secret,
            )
        return self.__azure_credentials


app_config = Config()
print(f"[DEBUG] AI_PROJECT_ENDPOINT: '{os.getenv('AI_PROJECT_ENDPOINT')}'")
