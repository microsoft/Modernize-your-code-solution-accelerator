# pylint: disable=redefined-outer-name
"""Tests for the FastAPI application."""

import logging
import os

from backend.app import create_app

from fastapi import FastAPI

from httpx import ASGITransport
from httpx import AsyncClient

from opentelemetry.sdk._logs import LoggingHandler

import pytest


@pytest.fixture
def app() -> FastAPI:
    """Fixture to create a test app instance."""
    return create_app()


@pytest.mark.asyncio
async def test_health_check(app: FastAPI):
    """Test the /health endpoint returns a healthy status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_backend_routes_exist(app: FastAPI):
    """Ensure /api routes are available (smoke test)."""
    # Check available routes include /api prefix from backend_router
    routes = [route.path for route in app.router.routes]
    backend_routes = [r for r in routes if r.startswith("/api")]
    assert backend_routes, "No backend routes found under /api prefix"


def test_logging_handler_deduplication():
    """Test that creating multiple apps doesn't accumulate LoggingHandler instances."""
    # Set up Application Insights connection string to trigger telemetry setup
    connection_string = "InstrumentationKey=test-key;IngestionEndpoint=https://test.com"
    original_env = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")

    try:
        os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"] = connection_string

        # Get root logger and count existing LoggingHandlers
        root_logger = logging.getLogger()
        initial_handler_count = sum(1 for h in root_logger.handlers if isinstance(h, LoggingHandler))

        # Create first app
        app1 = create_app()
        handler_count_after_first = sum(1 for h in root_logger.handlers if isinstance(h, LoggingHandler))

        # Create second app
        app2 = create_app()
        handler_count_after_second = sum(1 for h in root_logger.handlers if isinstance(h, LoggingHandler))

        # Assert only one LoggingHandler exists after multiple create_app() calls
        assert handler_count_after_first == initial_handler_count + 1, \
            "First create_app() should add one LoggingHandler"
        assert handler_count_after_second == handler_count_after_first, \
            "Second create_app() should not add another LoggingHandler (de-duplication should work)"

        # Clean up - remove the handler we added
        for handler in list(root_logger.handlers):
            if isinstance(handler, LoggingHandler):
                root_logger.removeHandler(handler)
                try:
                    handler.close()
                except Exception:
                    pass
    finally:
        # Restore original environment
        if original_env is not None:
            os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"] = original_env
        else:
            os.environ.pop("APPLICATIONINSIGHTS_CONNECTION_STRING", None)
