from backend.app import create_app

from fastapi import FastAPI

from httpx import ASGITransport
from httpx import AsyncClient

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
