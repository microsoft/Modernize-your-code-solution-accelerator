"""Create and configure the FastAPI application."""
from api.api_routes import router as backend_router

from common.logger.app_logger import AppLogger

from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import uvicorn
# from agent_services.agents_routes import router as agents_router

# Load environment variables
load_dotenv()

# Configure logging
logger = AppLogger("app")


def create_app() -> FastAPI:
    """Create and return the FastAPI application instance."""
    app = FastAPI(title="Code Gen Accelerator", version="1.0.0")

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
