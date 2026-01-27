"""Tests for status_updates module."""

from unittest.mock import AsyncMock, MagicMock, patch

from backend.api.status_updates import (
    ConnectionManager,
    app_connection_manager,
    close_connection,
    send_status_update,
    send_status_update_async,
)

import pytest


class TestConnectionManager:
    """Tests for ConnectionManager class."""

    def test_init(self):
        """Test ConnectionManager initialization."""
        manager = ConnectionManager()
        assert not manager.connections

    def test_add_connection(self):
        """Test adding a connection."""
        manager = ConnectionManager()
        mock_websocket = MagicMock()

        manager.add_connection("batch-1", mock_websocket)

        assert "batch-1" in manager.connections
        assert manager.connections["batch-1"] == mock_websocket

    def test_remove_connection(self):
        """Test removing a connection."""
        manager = ConnectionManager()
        mock_websocket = MagicMock()
        manager.add_connection("batch-1", mock_websocket)

        manager.remove_connection("batch-1")

        assert "batch-1" not in manager.connections

    def test_remove_nonexistent_connection(self):
        """Test removing a connection that doesn't exist."""
        manager = ConnectionManager()

        # Should not raise an error
        manager.remove_connection("nonexistent")

    def test_get_connection(self):
        """Test getting a connection."""
        manager = ConnectionManager()
        mock_websocket = MagicMock()
        manager.add_connection("batch-1", mock_websocket)

        result = manager.get_connection("batch-1")

        assert result == mock_websocket

    def test_get_nonexistent_connection(self):
        """Test getting a connection that doesn't exist."""
        manager = ConnectionManager()

        result = manager.get_connection("nonexistent")

        assert result is None


class TestSendStatusUpdateAsync:
    """Tests for send_status_update_async function."""

    @pytest.mark.asyncio
    async def test_send_status_update_async_with_connection(self):
        """Test sending status update when connection exists."""
        mock_websocket = AsyncMock()

        status = MagicMock()
        status.batch_id = "batch-1"

        with patch.object(app_connection_manager, 'get_connection', return_value=mock_websocket):
            with patch("json.dumps", return_value='{"batch_id": "batch-1"}'):
                await send_status_update_async(status)

                mock_websocket.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_status_update_async_no_connection(self):
        """Test sending status update when no connection exists."""
        status = MagicMock()
        status.batch_id = "batch-1"

        with patch.object(app_connection_manager, 'get_connection', return_value=None):
            # Should not raise an error
            await send_status_update_async(status)


class TestSendStatusUpdate:
    """Tests for send_status_update function."""

    def test_send_status_update_with_connection(self):
        """Test sending status update synchronously when connection exists."""
        mock_websocket = MagicMock()
        mock_loop = MagicMock()

        status = MagicMock()
        status.batch_id = "batch-1"

        with patch.object(app_connection_manager, 'get_connection', return_value=mock_websocket):
            with patch('backend.api.status_updates.asyncio.get_event_loop', return_value=mock_loop):
                with patch('backend.api.status_updates.asyncio.run_coroutine_threadsafe') as mock_run:
                    with patch('backend.api.status_updates.json.dumps', return_value='{"batch_id": "batch-1"}'):
                        send_status_update(status)

                        mock_run.assert_called_once()

    def test_send_status_update_no_connection(self):
        """Test sending status update when no connection exists."""
        status = MagicMock()
        status.batch_id = "batch-1"

        with patch.object(app_connection_manager, 'get_connection', return_value=None):
            # Should not raise an error
            send_status_update(status)

    def test_send_status_update_exception(self):
        """Test sending status update when exception occurs."""
        mock_websocket = MagicMock()

        status = MagicMock()
        status.batch_id = "batch-1"

        with patch.object(app_connection_manager, 'get_connection', return_value=mock_websocket):
            with patch('backend.api.status_updates.asyncio.get_event_loop', side_effect=RuntimeError("No event loop")):
                # Should handle exception gracefully
                send_status_update(status)


class TestCloseConnection:
    """Tests for close_connection function."""

    @pytest.mark.asyncio
    async def test_close_connection_with_connection(self):
        """Test closing a connection that exists."""
        mock_websocket = MagicMock()
        mock_loop = MagicMock()

        with patch.object(app_connection_manager, 'get_connection', return_value=mock_websocket):
            with patch.object(app_connection_manager, 'remove_connection') as mock_remove:
                with patch('asyncio.get_event_loop', return_value=mock_loop):
                    with patch('asyncio.run_coroutine_threadsafe'):
                        await close_connection("batch-1")

                        mock_remove.assert_called_once_with("batch-1")

    @pytest.mark.asyncio
    async def test_close_connection_no_connection(self):
        """Test closing a connection that doesn't exist."""
        with patch.object(app_connection_manager, 'get_connection', return_value=None):
            with patch.object(app_connection_manager, 'remove_connection') as mock_remove:
                await close_connection("batch-1")

                # Should still call remove_connection
                mock_remove.assert_called_once_with("batch-1")
