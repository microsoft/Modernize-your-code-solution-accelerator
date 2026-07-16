"""
Patch for Azure AI telemetry instrumentors.

Fixes GitHub issue: https://github.com/microsoft/semantic-kernel/issues/13715

The bug: agent_api_response_to_str() in both azure.ai.agents and azure.ai.projects
raises ValueError when response_format is a dict (e.g. from Semantic Kernel's AzureAIAgent).
It only handles str and None types.

The fix: Monkey-patch that method to convert dict/other types to JSON string instead of raising.
Must be called BEFORE configure_azure_monitor() triggers any instrumentation.
"""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _fixed_response_to_str(response_format: Any) -> Optional[str]:
    """Convert response_format to string, handling dict types."""
    if response_format is None:
        return None
    if isinstance(response_format, str):
        return response_format
    try:
        return json.dumps(response_format, default=str)
    except (TypeError, ValueError):
        return str(response_format)


def _patch_fastapi_route_details():
    """
    Patch opentelemetry-instrumentation-fastapi's _get_route_details.

    The bug: _get_route_details() iterates over app.routes and reads
    `starlette_route.path`. With FastAPI >= 0.119.0, app.include_router()
    leaves an `_IncludedRouter` object in app.routes that has no `.path`
    attribute. This raises:
        AttributeError: '_IncludedRouter' object has no attribute 'path'

    It is triggered on requests where no concrete route matches FULL,
    most notably CORS preflight `OPTIONS` requests from the frontend,
    causing a 500 on the preflight and blocking the real request.

    The fix: replace the module-level _get_route_details with a version
    that uses getattr(..., "path", None) and ignores routes whose
    matches() raises. _get_default_span_details references this function
    as a module global, so patching the module attribute is sufficient.
    """
    try:
        import opentelemetry.instrumentation.fastapi as fastapi_instr
        from starlette.routing import Match
    except ImportError:
        logger.debug("opentelemetry.instrumentation.fastapi not installed, skipping patch")
        return

    try:
        def _safe_get_route_details(scope: Any) -> Optional[str]:
            app = scope["app"]
            route = None
            for starlette_route in app.routes:
                try:
                    match, _ = starlette_route.matches(scope)
                except Exception:  # noqa: BLE001
                    continue
                if match == Match.FULL:
                    route = getattr(starlette_route, "path", None)
                    break
                if match == Match.PARTIAL:
                    route = getattr(starlette_route, "path", None)
            return route

        fastapi_instr._get_route_details = _safe_get_route_details
        logger.info("Patched opentelemetry.instrumentation.fastapi._get_route_details")
    except Exception:  # noqa: BLE001
        logger.exception("Failed to patch opentelemetry.instrumentation.fastapi route details")


def patch_instrumentors():
    """
    Patch Azure AI telemetry instrumentors to handle dict response_format.

    This fixes the ValueError: "Unknown response format <class 'dict'>" error
    that occurs when Semantic Kernel's AzureAIAgent passes a dict as response_format
    and Azure Monitor telemetry instrumentor tries to serialize it.

    Patches both azure.ai.agents and azure.ai.projects packages.
    Must be called BEFORE configure_azure_monitor().
    """
    # Patch azure.ai.agents (primary package with the bug)
    try:
        from azure.ai.agents.telemetry._ai_agents_instrumentor import (
            _AIAgentsInstrumentorPreview as _AgentsPreview,
        )
        _AgentsPreview.agent_api_response_to_str = staticmethod(_fixed_response_to_str)
        logger.info("Patched azure.ai.agents instrumentor")
    except ImportError:
        logger.debug("azure.ai.agents telemetry not installed, skipping patch")

    # Patch azure.ai.projects (in case it exists in the environment)
    try:
        from azure.ai.projects.telemetry._ai_project_instrumentor import (
            _AIAgentsInstrumentorPreview as _ProjectsPreview,
        )
        _ProjectsPreview.agent_api_response_to_str = staticmethod(_fixed_response_to_str)
        logger.info("Patched azure.ai.projects instrumentor")
    except ImportError:
        logger.debug("azure.ai.projects telemetry not installed, skipping patch")

    # Patch opentelemetry-instrumentation-fastapi to tolerate routes without a
    # `.path` attribute (e.g. FastAPI >= 0.119.0 `_IncludedRouter`), which
    # otherwise crashes span-name resolution on CORS preflight OPTIONS requests.
    _patch_fastapi_route_details()
