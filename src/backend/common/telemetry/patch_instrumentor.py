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
