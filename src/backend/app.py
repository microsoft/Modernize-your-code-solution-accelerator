"""Create and configure the FastAPI application."""
import logging
import os
from contextlib import asynccontextmanager

from api.api_routes import router as backend_router

from common.config.config import app_config
from common.logger.app_logger import AppLogger

from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from helper.azure_credential_utils import get_azure_credential

from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent  # pylint: disable=E0611

from sql_agents.agent_manager import clear_sql_agents, set_sql_agents
from sql_agents.agents.agent_config import AgentBaseConfig
from sql_agents.helpers.agents_manager import SqlAgents

import uvicorn
# from agent_services.agents_routes import router as agents_router

# Load environment variables
load_dotenv()

# Configure logging
# Basic application logging (default: INFO level)
AZURE_BASIC_LOGGING_LEVEL = os.getenv("AZURE_BASIC_LOGGING_LEVEL", "INFO").upper()
# Azure package logging (default: WARNING level to suppress INFO)
AZURE_PACKAGE_LOGGING_LEVEL = os.getenv("AZURE_PACKAGE_LOGGING_LEVEL", "WARNING").upper()
# Azure logging packages (default: empty list)
azure_logging_packages_env = os.getenv("AZURE_LOGGING_PACKAGES")
AZURE_LOGGING_PACKAGES = azure_logging_packages_env.split(",") if azure_logging_packages_env else []

# Basic config: logging.basicConfig(level=logging.INFO)
logging.basicConfig(
    level=getattr(logging, AZURE_BASIC_LOGGING_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Package config: Azure loggers set to WARNING to suppress INFO
for logger_name in AZURE_LOGGING_PACKAGES:
    logging.getLogger(logger_name).setLevel(getattr(logging, AZURE_PACKAGE_LOGGING_LEVEL, logging.WARNING))

logger = AppLogger("app")

# Global variables for agents
sql_agents: SqlAgents = None
azure_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    global sql_agents, azure_client

    # Startup
    try:
        logger.logger.info("Initializing SQL agents...")

        # Create Azure credentials and client
        creds = get_azure_credential(app_config.azure_client_id)
        azure_client = AzureAIAgent.create_client(
            credential=creds,
            endpoint=app_config.ai_project_endpoint
        )

        # Setup agent configuration with default conversion settings
        agent_config = AgentBaseConfig(
            project_client=azure_client,
            sql_from="informix",  # Default source dialect
            sql_to="tsql"         # Default target dialect
        )

        # Create SQL agents
        sql_agents = await SqlAgents.create(agent_config)

        # Set the global agents instance
        set_sql_agents(sql_agents)
        logger.logger.info("SQL agents initialized successfully.")

    except Exception as exc:
        logger.logger.error("Failed to initialize SQL agents: %s", exc)
        # Don't raise the exception to allow the app to start even if agents fail

    yield  # Application runs here

    # Shutdown
    try:
        if sql_agents:
            logger.logger.info("Application shutting down - cleaning up SQL agents...")
            await sql_agents.delete_agents()
            logger.logger.info("SQL agents cleaned up successfully.")

            # Clear the global agents instance
            await clear_sql_agents()

        if azure_client:
            await azure_client.close()

    except Exception as exc:
        logger.logger.error("Error during agent cleanup: %s", exc)


def create_app() -> FastAPI:
    """Create and return the FastAPI application instance."""
    app = FastAPI(title="Code Gen Accelerator", version="1.0.0", lifespan=lifespan)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers with /api prefix
    app.include_router(backend_router, prefix="/api", tags=["backend"])
    # app.include_router(agents_router, prefix="/api/agents", tags=["agents"])

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
