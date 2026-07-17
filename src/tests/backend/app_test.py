# pylint: disable=redefined-outer-name
"""Tests for the FastAPI application."""

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
    # Use the OpenAPI schema rather than walking `app.router.routes`, because
    # newer FastAPI versions wrap included routers in an `_IncludedRouter`
    # object (no `.path` attribute) which makes direct route iteration fragile.
    # The OpenAPI `paths` mapping is the stable public surface and always
    # contains the fully-resolved paths including the `/api` prefix added by
    # `app.include_router(backend_router, prefix="/api", ...)`.
    paths = app.openapi().get("paths", {})
    backend_paths = [p for p in paths if p.startswith("/api")]
    assert backend_paths, "No backend routes found under /api prefix"
