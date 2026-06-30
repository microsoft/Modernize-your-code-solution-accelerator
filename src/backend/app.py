"""Create and configure the FastAPI application."""
import logging
import os
from contextlib import asynccontextmanager

from api.api_routes import router as backend_router

from azure.monitor.opentelemetry import configure_azure_monitor

from common.config.config import app_config
from common.logger.app_logger import AppLogger
from common.telemetry import patch_instrumentors

from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from helper.azure_credential_utils import get_azure_credential

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

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

# Suppress noisy Azure SDK and OpenTelemetry internal loggers.
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies._universal").setLevel(logging.WARNING)
logging.getLogger("azure.cosmos").setLevel(logging.WARNING)
logging.getLogger("opentelemetry.sdk").setLevel(logging.WARNING)
logging.getLogger("azure.monitor.opentelemetry.exporter.export._base").setLevel(logging.WARNING)

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
        logger.info("Initializing SQL agents...")

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
        logger.info("SQL agents initialized successfully.")

    except Exception:  # noqa: BLE001
        logger.error("Failed to initialize SQL agents")
        # Don't raise the exception to allow the app to start even if agents fail

    yield  # Application runs here

    # Shutdown
    try:
        if sql_agents:
            logger.info("Application shutting down - cleaning up SQL agents...")
            await sql_agents.delete_agents()
            logger.info("SQL agents cleaned up successfully.")

            # Clear the global agents instance
            await clear_sql_agents()

        if azure_client:
            await azure_client.close()

    except Exception:  # noqa: BLE001
        logger.error("Error during agent cleanup")


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

    # Configure Azure Monitor and instrument FastAPI for OpenTelemetry
    # This must happen AFTER app creation but BEFORE route registration
    instrumentation_key = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if instrumentation_key:
        # Patch azure.ai.agents, azure.ai.projects instrumentor to handle dict response_format (prevents ValueError)
        patch_instrumentors()

        # Configure Azure Monitor with FULL auto-instrumentation
        configure_azure_monitor(
            connection_string=instrumentation_key,
            enable_live_metrics=True
        )

        # Instrument FastAPI for HTTP request/response tracing
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="health,socket,ws",
        )

        logger.info("Application Insights configured with full auto-instrumentation")
    else:
        logger.warning("No Application Insights connection string found. Telemetry disabled.")

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
