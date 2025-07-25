"""Create and configure the FastAPI application."""
from contextlib import asynccontextmanager

from api.api_routes import router as backend_router

from azure.identity.aio import DefaultAzureCredential

from common.config.config import app_config
from common.logger.app_logger import AppLogger

from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent  # pylint: disable=E0611

from sql_agents.agents.agent_config import AgentBaseConfig
from sql_agents.helpers.agents_manager import SqlAgents

import uvicorn
# from agent_services.agents_routes import router as agents_router

# Load environment variables
load_dotenv()

# Configure logging
logger = AppLogger("app")

# Global variables for agents
sql_agents: SqlAgents = None
azure_client = None


def get_sql_agents() -> SqlAgents:
    """Get the global SQL agents instance."""
    return sql_agents


async def update_agent_config(convert_from: str, convert_to: str):
    """Update the global agent configuration for different SQL conversion types."""
    global sql_agents
    if sql_agents and sql_agents.agent_config:
        sql_agents.agent_config.sql_from = convert_from
        sql_agents.agent_config.sql_to = convert_to
        logger.logger.info(f"Updated agent configuration: {convert_from} -> {convert_to}")
    else:
        logger.logger.warning("SQL agents not initialized, cannot update configuration")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    global sql_agents, azure_client
    
    # Startup
    try:
        logger.logger.info("Initializing SQL agents...")
        
        # Create Azure credentials and client
        creds = DefaultAzureCredential()
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
        logger.logger.info("SQL agents initialized successfully.")
        
    except Exception as exc:
        logger.logger.error("Failed to initialize SQL agents: %s", exc)
        # Don't raise the exception to allow the app to start even if agents fail
    
    yield  # Application runs here
    
    # Shutdown
    try:
        if sql_agents:
            logger.logger.info("Cleaning up SQL agents...")
            await sql_agents.delete_agents()
            logger.logger.info("SQL agents cleaned up successfully.")
        
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
