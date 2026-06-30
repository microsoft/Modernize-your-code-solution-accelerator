"""
Holds collection of websocket connections.

from clients registering for status updates.
These socket references are used to send updates to
registered clients from the backend processing code.
"""

import asyncio
import json
import logging
from typing import Dict

from common.models.api import FileProcessUpdate, FileProcessUpdateJSONEncoder

from fastapi import WebSocket

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ConnectionManager:
    """Connection manager for WebSocket connections."""

    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}

    def add_connection(self, batch_id, connection):
        """Add a new connection."""
        self.connections[batch_id] = connection

    def remove_connection(self, batch_id):
        """Remove a connection."""
        if batch_id in self.connections:
            del self.connections[batch_id]

    def get_connection(self, batch_id):
        """Get a connection."""
        return self.connections.get(batch_id)


app_connection_manager = ConnectionManager()


async def send_status_update_async(status: FileProcessUpdate):
    """Send a status update to a specific client."""
    connection = app_connection_manager.get_connection(status.batch_id)
    if connection:
        await connection.send_text(json.dumps(status))
    else:
        logger.warning("No connection found for batch ID: %s", status.batch_id)


def send_status_update(status: FileProcessUpdate):
    """Send a status update to a specific client."""
    connection = app_connection_manager.get_connection(str(status.batch_id))
    if connection:
        try:
            # Directly send the message using the connection object
            asyncio.run_coroutine_threadsafe(
                connection.send_text(
                    json.dumps(status, cls=FileProcessUpdateJSONEncoder)
                ),
                asyncio.get_event_loop(),
            )
        except Exception as e:
            logger.error("Failed to send message: %s", e)
    else:
        logger.warning("No connection found for batch ID: %s", status.batch_id)


async def close_connection(batch_id):
    """Remove a connection."""
    connection = app_connection_manager.get_connection(batch_id)
    if connection:
        asyncio.run_coroutine_threadsafe(connection.close(), asyncio.get_event_loop())
        logger.info("Connection closed for batch ID: %s", batch_id)
    else:
        logger.warning("No connection found for batch ID: %s", batch_id)
    app_connection_manager.remove_connection(batch_id)
    logger.info("Connection removed for batch ID: %s", batch_id)
