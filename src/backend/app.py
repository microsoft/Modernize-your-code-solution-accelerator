"""Create and configure the FastAPI application."""
import logging
import os
from contextlib import asynccontextmanager

from api.api_routes import router as backend_router

from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter, AzureMonitorTraceExporter

from common.config.config import app_config
from common.logger.app_logger import AppLogger

from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from helper.azure_credential_utils import get_azure_credential

from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

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

# Suppress noisy OpenTelemetry and Azure Monitor logs
# logging.getLogger("opentelemetry.sdk").setLevel(logging.ERROR)
# logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
# logging.getLogger("azure.monitor.opentelemetry.exporter.export._base").setLevel(logging.WARNING)

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

    # Configure Azure Monitor and instrument FastAPI for OpenTelemetry
    # This must happen AFTER app creation but BEFORE route registration
    instrumentation_key = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if instrumentation_key:
        # SOLUTION: Use manual telemetry setup instead of configure_azure_monitor
        # This gives us precise control over what gets instrumented, avoiding interference
        # with Semantic Kernel's async generators while still tracking Azure SDK calls

        # Set up Azure Monitor exporter for traces
        azure_trace_exporter = AzureMonitorTraceExporter(connection_string=instrumentation_key)

        # Create a tracer provider and add the Azure Monitor exporter
        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(BatchSpanProcessor(azure_trace_exporter))

        # Set the global tracer provider
        trace.set_tracer_provider(tracer_provider)

        # Set up Azure Monitor exporter for logs (appears in traces table)
        azure_log_exporter = AzureMonitorLogExporter(connection_string=instrumentation_key)

        # Create a logger provider and add the Azure Monitor exporter
        logger_provider = LoggerProvider()
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(azure_log_exporter))
        set_logger_provider(logger_provider)

        # Attach OpenTelemetry handler to Python's root logger
        handler = LoggingHandler(logger_provider=logger_provider)
        logging.getLogger().addHandler(handler)

        # Instrument ONLY FastAPI for HTTP request/response tracing
        # This is safe because it only wraps HTTP handlers, not internal async operations
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="socket,ws",  # Exclude WebSocket URLs to reduce noise
            tracer_provider=tracer_provider
        )

        # Optional: Add manual spans in your code for Azure SDK operations using:
        # from opentelemetry import trace
        # tracer = trace.get_tracer(__name__)
        # with tracer.start_as_current_span("operation_name"):
        #     # your Azure SDK call here

        logger.logger.info("Application Insights configured with selective instrumentation")
        logger.logger.info("✓ FastAPI HTTP tracing enabled")
        logger.logger.info("✓ Python logging export to Application Insights enabled")
        logger.logger.info("✓ Manual span support enabled for Azure SDK operations")
        logger.logger.info("✓ Custom events via OpenTelemetry enabled")
        logger.logger.info("✓ Semantic Kernel async generators unaffected")
    else:
        logger.logger.warning("No Application Insights connection string found. Telemetry disabled.")

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
