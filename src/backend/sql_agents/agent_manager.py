"""
Global agent manager for SQL agents.
This module manages the global SQL agents instance to avoid circular imports.
"""

import logging
from typing import Optional

from sql_agents.helpers.agents_manager import SqlAgents

logger = logging.getLogger(__name__)

# Global variable to store the SQL agents instance
_sql_agents: Optional[SqlAgents] = None


def set_sql_agents(agents: SqlAgents) -> None:
    """Set the global SQL agents instance."""
    global _sql_agents
    _sql_agents = agents
    logger.info("Global SQL agents instance has been set")


def get_sql_agents() -> Optional[SqlAgents]:
    """Get the global SQL agents instance."""
    return _sql_agents


async def update_agent_config(convert_from: str, convert_to: str) -> None:
    """Update the global agent configuration for different SQL conversion types."""
    if _sql_agents and _sql_agents.agent_config:
        _sql_agents.agent_config.sql_from = convert_from
        _sql_agents.agent_config.sql_to = convert_to
        logger.info(f"Updated agent configuration: {convert_from} -> {convert_to}")
    else:
        logger.warning("SQL agents not initialized, cannot update configuration")


async def clear_sql_agents() -> None:
    """Clear the global SQL agents instance."""
    global _sql_agents
    await _sql_agents.delete_agents()
    _sql_agents = None
    logger.info("Global SQL agents instance has been cleared")
