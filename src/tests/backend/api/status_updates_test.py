import asyncio
import uuid
from unittest.mock import AsyncMock, patch

from api import status_updates

from common.models.api import AgentType, FileProcessUpdate, FileResult, ProcessStatus

import pytest


@pytest.fixture
def file_process_update():
    return FileProcessUpdate(
        batch_id=uuid.uuid4(),
        file_id=uuid.uuid4(),
        process_status=ProcessStatus.IN_PROGRESS,
        agent_type=AgentType.MIGRATOR,
        agent_message="Processing in progress",
        file_result=FileResult.INFO
    )


@pytest.fixture
def mock_websocket():
    return AsyncMock()


@pytest.mark.asyncio
async def test_send_status_update_async_success(file_process_update):
    mock_websocket = AsyncMock()
    status_updates.app_connection_manager.add_connection(file_process_update.batch_id, mock_websocket)

    with patch("api.status_updates.json.dumps", return_value='{"batch_id": "test_batch", "status": "Processing", "progress": 50}'):
        await status_updates.send_status_update_async(file_process_update)

    mock_websocket.send_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_status_update_async_no_connection(file_process_update):
    # No connection added
    with patch("api.status_updates.logger") as mock_logger:
        await status_updates.send_status_update_async(file_process_update)
        mock_logger.warning.assert_called_once_with(
            "No connection found for batch ID: %s", file_process_update.batch_id
        )


def test_send_status_update_success(file_process_update):
    mock_websocket = AsyncMock()
    loop = asyncio.new_event_loop()

    with patch("api.status_updates.asyncio.get_event_loop", return_value=loop):
        with patch("api.status_updates.asyncio.run_coroutine_threadsafe") as mock_run:
            status_updates.app_connection_manager.add_connection(str(file_process_update.batch_id), mock_websocket)

            with patch("api.status_updates.json.dumps", return_value='{}'):
                status_updates.send_status_update(file_process_update)

            mock_run.assert_called_once()


def test_send_status_update_no_connection(file_process_update):
    with patch("api.status_updates.logger") as mock_logger:
        status_updates.send_status_update(file_process_update)

        mock_logger.warning.assert_called()
        args, kwargs = mock_logger.warning.call_args
        assert "No connection found for batch ID" in args[0]


@pytest.mark.asyncio
async def test_close_connection_success(file_process_update, mock_websocket):
    status_updates.app_connection_manager.add_connection(file_process_update.batch_id, mock_websocket)
    loop = asyncio.new_event_loop()

    with patch("api.status_updates.asyncio.get_event_loop", return_value=loop):
        with patch("api.status_updates.asyncio.run_coroutine_threadsafe") as mock_run:
            with patch("api.status_updates.logger") as mock_logger:
                await status_updates.close_connection(file_process_update.batch_id)

                mock_run.assert_called_once()
                mock_logger.info.assert_any_call("Connection closed for batch ID: %s", file_process_update.batch_id)
                mock_logger.info.assert_any_call("Connection removed for batch ID: %s", file_process_update.batch_id)


@pytest.mark.asyncio
async def test_close_connection_no_connection(file_process_update):
    with patch("api.status_updates.logger") as mock_logger:
        await status_updates.close_connection(file_process_update.batch_id)

        mock_logger.warning.assert_called_once_with(
            "No connection found for batch ID: %s", file_process_update.batch_id
        )
        mock_logger.info.assert_called_once_with(
            "Connection removed for batch ID: %s", file_process_update.batch_id
        )


# Test the connection manager directly
def test_connection_manager_methods():
    # Get the actual connection manager instance
    manager = status_updates.app_connection_manager

    # Test the get_connection method
    batch_id = uuid.uuid4()
    assert manager.get_connection(batch_id) is None

    # Test add_connection method
    mock_websocket = AsyncMock()
    manager.add_connection(batch_id, mock_websocket)
    assert manager.get_connection(batch_id) == mock_websocket

    # Test overwriting an existing connection
    new_mock_websocket = AsyncMock()
    manager.add_connection(batch_id, new_mock_websocket)
    assert manager.get_connection(batch_id) == new_mock_websocket

    # Test remove_connection method
    manager.remove_connection(batch_id)
    assert manager.get_connection(batch_id) is None

    # Test removing a non-existent connection (should not raise an error)
    manager.remove_connection(uuid.uuid4())


def test_send_status_update_exception(file_process_update):
    mock_websocket = AsyncMock()
    status_updates.app_connection_manager.add_connection(str(file_process_update.batch_id), mock_websocket)

    with patch("api.status_updates.asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value = asyncio.new_event_loop()
        with patch("api.status_updates.json.dumps", return_value='{}'):
            with patch("api.status_updates.asyncio.run_coroutine_threadsafe", side_effect=Exception("send error")):
                with patch("api.status_updates.logger") as mock_logger:
                    status_updates.send_status_update(file_process_update)
                    mock_logger.error.assert_called_once()
                    assert "Failed to send message" in mock_logger.error.call_args[0][0]
