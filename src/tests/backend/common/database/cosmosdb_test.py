import os
import sys
# Add backend directory to sys.path
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..", "backend")),
)
from datetime import datetime, timezone  # noqa: E402
from unittest import mock  # noqa: E402
from unittest.mock import AsyncMock  # noqa: E402
from uuid import uuid4  # noqa: E402

from azure.cosmos.aio import CosmosClient  # noqa: E402
from azure.cosmos.exceptions import CosmosResourceExistsError  # noqa: E402

from common.database.cosmosdb import (  # noqa: E402
    CosmosDBClient,
)
from common.models.api import (  # noqa: E402
    AgentType,
    AuthorRole,
    BatchRecord,
    FileRecord,
    LogType,
    ProcessStatus,
)  # noqa: E402

import pytest  # noqa: E402

# Mocked data for the test
endpoint = "https://fake.cosmosdb.azure.com"
credential = "fake_credential"
database_name = "test_database"
batch_container = "batch_container"
file_container = "file_container"
log_container = "log_container"


@pytest.fixture
def cosmos_db_client():
    return CosmosDBClient(
        endpoint=endpoint,
        credential=credential,
        database_name=database_name,
        batch_container=batch_container,
        file_container=file_container,
        log_container=log_container,
    )


@pytest.mark.asyncio
async def test_initialize_cosmos(cosmos_db_client, mocker):
    # Mocking CosmosClient and its methods
    mock_client = mocker.patch.object(CosmosClient, 'get_database_client', return_value=mock.MagicMock())
    mock_database = mock_client.return_value

    # Use AsyncMock for asynchronous methods
    mock_batch_container = mock.MagicMock()
    mock_file_container = mock.MagicMock()
    mock_log_container = mock.MagicMock()

    # Mock get_container_client method (since _get_container uses this)
    mock_database.get_container_client = mock.MagicMock(side_effect=[
        mock_batch_container,
        mock_file_container,
        mock_log_container
    ])

    # Call the initialize_cosmos method
    await cosmos_db_client.initialize_cosmos()

    # Assert that the containers were fetched successfully
    mock_database.get_container_client.assert_any_call(batch_container)
    mock_database.get_container_client.assert_any_call(file_container)
    mock_database.get_container_client.assert_any_call(log_container)

    # Check the client and containers were set
    assert cosmos_db_client.client is not None
    assert cosmos_db_client.batch_container == mock_batch_container
    assert cosmos_db_client.file_container == mock_file_container
    assert cosmos_db_client.log_container == mock_log_container


@pytest.mark.asyncio
async def test_initialize_cosmos_with_error(cosmos_db_client, mocker):
    # Mocking CosmosClient and its methods
    mock_client = mocker.patch.object(CosmosClient, 'get_database_client', return_value=mock.MagicMock())
    mock_database = mock_client.return_value

    # Simulate a general exception during container access
    mock_database.get_container_client = mock.MagicMock(side_effect=Exception("Failed to get container"))

    # Call the initialize_cosmos method and expect it to raise an error
    with pytest.raises(Exception) as exc_info:
        await cosmos_db_client.initialize_cosmos()

    # Assert that the exception message matches the expected message
    assert str(exc_info.value) == "Failed to get container"


@pytest.mark.asyncio
async def test_initialize_cosmos_container_exists_error(cosmos_db_client, mocker):
    # Mocking CosmosClient and its methods
    mock_client = mocker.patch.object(CosmosClient, 'get_database_client', return_value=mock.MagicMock())
    mock_database = mock_client.return_value

    # Use AsyncMock for asynchronous methods
    mock_batch_container = mock.MagicMock()
    mock_file_container = mock.MagicMock()
    mock_log_container = mock.MagicMock()

    # Mock get_container_client method to return existing containers
    mock_database.get_container_client = mock.MagicMock(side_effect=[
        mock_batch_container,
        mock_file_container,
        mock_log_container
    ])

    # Call the initialize_cosmos method
    await cosmos_db_client.initialize_cosmos()

    # Assert that the container access method was called with the correct arguments
    mock_database.get_container_client.assert_any_call('batch_container')
    mock_database.get_container_client.assert_any_call('file_container')
    mock_database.get_container_client.assert_any_call('log_container')

    # Check that existing containers are returned (mocked containers)
    assert cosmos_db_client.batch_container == mock_batch_container
    assert cosmos_db_client.file_container == mock_file_container
    assert cosmos_db_client.log_container == mock_log_container


@pytest.mark.asyncio
async def test_create_batch_new(cosmos_db_client, mocker):
    user_id = "user_1"
    batch_id = uuid4()

    # Mock container creation
    mock_batch_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'batch_container', mock_batch_container)

    # Mock the method to return the batch
    mock_batch_container.create_item = AsyncMock(return_value=None)

    # Call the method
    batch = await cosmos_db_client.create_batch(user_id, batch_id)

    # Assert that the batch is created
    assert batch.batch_id == batch_id
    assert batch.user_id == user_id
    assert batch.status == ProcessStatus.READY_TO_PROCESS

    mock_batch_container.create_item.assert_called_once_with(body=batch.dict())


@pytest.mark.asyncio
async def test_create_batch_exists(cosmos_db_client, mocker):
    user_id = "user_1"
    batch_id = uuid4()

    # Mock container creation and get_batch
    mock_batch_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'batch_container', mock_batch_container)
    mock_batch_container.create_item = AsyncMock(side_effect=CosmosResourceExistsError)

    # Mock the get_batch method
    mock_get_batch = AsyncMock(return_value=BatchRecord(
        batch_id=batch_id,
        user_id=user_id,
        file_count=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        status=ProcessStatus.READY_TO_PROCESS
    ))
    mocker.patch.object(cosmos_db_client, 'get_batch', mock_get_batch)

    # Call the method
    batch = await cosmos_db_client.create_batch(user_id, batch_id)

    # Assert that batch was fetched (not created) due to already existing
    assert batch.batch_id == batch_id
    assert batch.user_id == user_id
    assert batch.status == ProcessStatus.READY_TO_PROCESS

    mock_get_batch.assert_called_once_with(user_id, str(batch_id))


@pytest.mark.asyncio
async def test_create_batch_exception(cosmos_db_client, mocker):
    user_id = "user_1"
    batch_id = uuid4()

    # Mock the batch_container and make create_item raise a general Exception
    mock_batch_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'batch_container', mock_batch_container)
    mock_batch_container.create_item = AsyncMock(side_effect=Exception("Unexpected Error"))

    # Mock the logger to verify logging
    mock_logger = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'logger', mock_logger)

    # Call the method and assert it raises the exception
    with pytest.raises(Exception, match="Unexpected Error"):
        await cosmos_db_client.create_batch(user_id, batch_id)

    # Ensure logger.error was called with expected message and error
    mock_logger.error.assert_called_once()
    called_args, called_kwargs = mock_logger.error.call_args
    assert called_args[0] == "Failed to create batch"
    assert "error" in called_kwargs
    assert "Unexpected Error" in called_kwargs["error"]


@pytest.mark.asyncio
async def test_add_file(cosmos_db_client, mocker):
    batch_id = uuid4()
    file_id = uuid4()
    file_name = "file.txt"
    storage_path = "/path/to/storage"

    # Mock file container creation
    mock_file_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'file_container', mock_file_container)

    # Mock the create_item method
    mock_file_container.create_item = AsyncMock(return_value=None)

    # Call the method
    file_record = await cosmos_db_client.add_file(batch_id, file_id, file_name, storage_path)

    # Assert that the file record is created
    assert file_record.file_id == file_id
    assert file_record.batch_id == batch_id
    assert file_record.original_name == file_name
    assert file_record.blob_path == storage_path
    assert file_record.status == ProcessStatus.READY_TO_PROCESS

    mock_file_container.create_item.assert_called_once_with(body=file_record.dict())


@pytest.mark.asyncio
async def test_add_file_exception(cosmos_db_client, mocker):
    batch_id = uuid4()
    file_id = uuid4()
    file_name = "document.pdf"
    storage_path = "/files/document.pdf"

    # Mock file_container.create_item to raise a general exception
    mock_file_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'file_container', mock_file_container)
    mock_file_container.create_item = AsyncMock(side_effect=Exception("Insert failed"))

    # Mock logger to capture error logs
    mock_logger = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'logger', mock_logger)

    # Expect an exception when calling add_file
    with pytest.raises(Exception, match="Insert failed"):
        await cosmos_db_client.add_file(batch_id, file_id, file_name, storage_path)

    # Check that logger.error was called properly
    called_args, called_kwargs = mock_logger.error.call_args
    assert called_args[0] == "Failed to add file"
    assert "error" in called_kwargs
    assert "Insert failed" in called_kwargs["error"]


@pytest.mark.asyncio
async def test_update_file(cosmos_db_client, mocker):
    file_id = uuid4()
    file_record = FileRecord(
        file_id=file_id,
        batch_id=uuid4(),
        original_name="file.txt",
        blob_path="/path/to/storage",
        translated_path="",
        status=ProcessStatus.READY_TO_PROCESS,
        error_count=0,
        syntax_count=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    # Mock file container replace_item method
    mock_file_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'file_container', mock_file_container)
    mock_file_container.replace_item = AsyncMock(return_value=None)

    # Call the method
    updated_file_record = await cosmos_db_client.update_file(file_record)

    # Assert that the file record is updated
    assert updated_file_record.file_id == file_id

    mock_file_container.replace_item.assert_called_once_with(item=str(file_id), body=file_record.dict())


@pytest.mark.asyncio
async def test_update_file_exception(cosmos_db_client, mocker):
    # Create a sample FileRecord
    file_record = FileRecord(
        file_id=uuid4(),
        batch_id=uuid4(),
        original_name="file.txt",
        blob_path="/storage/file.txt",
        translated_path="",
        status=ProcessStatus.READY_TO_PROCESS,
        error_count=0,
        syntax_count=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # Mock file_container.replace_item to raise an exception
    mock_file_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'file_container', mock_file_container)
    mock_file_container.replace_item = AsyncMock(side_effect=Exception("Update failed"))

    # Mock logger
    mock_logger = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'logger', mock_logger)

    # Expect an exception when update_file is called
    with pytest.raises(Exception, match="Update failed"):
        await cosmos_db_client.update_file(file_record)

    called_args, called_kwargs = mock_logger.error.call_args
    assert called_args[0] == "Failed to update file"
    assert "error" in called_kwargs
    assert "Update failed" in called_kwargs["error"]


@pytest.mark.asyncio
async def test_update_batch(cosmos_db_client, mocker):
    batch_record = BatchRecord(
        batch_id=uuid4(),
        user_id="user_1",
        file_count=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        status=ProcessStatus.READY_TO_PROCESS
    )

    # Mock batch container replace_item method
    mock_batch_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'batch_container', mock_batch_container)
    mock_batch_container.replace_item = AsyncMock(return_value=None)

    # Call the method
    updated_batch_record = await cosmos_db_client.update_batch(batch_record)

    # Assert that the batch record is updated
    assert updated_batch_record.batch_id == batch_record.batch_id

    mock_batch_container.replace_item.assert_called_once_with(item=str(batch_record.batch_id), body=batch_record.dict())


@pytest.mark.asyncio
async def test_update_batch_exception(cosmos_db_client, mocker):
    # Create a sample BatchRecord
    batch_record = BatchRecord(
        batch_id=uuid4(),
        user_id="user_1",
        file_count=3,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        status=ProcessStatus.READY_TO_PROCESS,
    )

    # Mock batch_container.replace_item to raise an exception
    mock_batch_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'batch_container', mock_batch_container)
    mock_batch_container.replace_item = AsyncMock(side_effect=Exception("Update batch failed"))

    # Mock logger to verify logging
    mock_logger = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'logger', mock_logger)

    # Expect an exception when update_batch is called
    with pytest.raises(Exception, match="Update batch failed"):
        await cosmos_db_client.update_batch(batch_record)

    called_args, called_kwargs = mock_logger.error.call_args
    assert called_args[0] == "Failed to update batch"
    assert "error" in called_kwargs
    assert "Update batch failed" in called_kwargs["error"]


@pytest.mark.asyncio
async def test_get_batch(cosmos_db_client, mocker):
    user_id = "user_1"
    batch_id = str(uuid4())

    # Mock batch container query_items method
    mock_batch_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, "batch_container", mock_batch_container)

    # Simulate the query result
    expected_batch = {
        "batch_id": batch_id,
        "user_id": user_id,
        "file_count": 0,
        "status": ProcessStatus.READY_TO_PROCESS,
    }

    # We define the async generator function that will yield the expected batch
    async def mock_query_items(query, parameters):
        yield expected_batch

    # Assign the async generator to query_items mock
    mock_batch_container.query_items.side_effect = mock_query_items
    # Call the method
    batch = await cosmos_db_client.get_batch(user_id, batch_id)

    # Assert the batch is returned correctly
    assert batch["batch_id"] == batch_id
    assert batch["user_id"] == user_id

    mock_batch_container.query_items.assert_called_once_with(
        query="SELECT * FROM c WHERE c.batch_id = @batch_id and c.user_id = @user_id",
        parameters=[
            {"name": "@batch_id", "value": batch_id},
            {"name": "@user_id", "value": user_id},
        ],
    )


@pytest.mark.asyncio
async def test_get_batch_exception(cosmos_db_client, mocker):
    user_id = "user_1"
    batch_id = str(uuid4())

    # Mock batch_container.query_items to raise an exception
    mock_batch_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'batch_container', mock_batch_container)
    mock_batch_container.query_items = mock.MagicMock(
        side_effect=Exception("Get batch failed")
    )

    # Patch logger
    mock_logger = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'logger', mock_logger)

    # Call get_batch and expect it to raise an exception
    with pytest.raises(Exception, match="Get batch failed"):
        await cosmos_db_client.get_batch(user_id, batch_id)

    # Ensure logger.error was called with the expected error message
    called_args, called_kwargs = mock_logger.error.call_args
    assert called_args[0] == "Failed to get batch"
    assert "error" in called_kwargs
    assert "Get batch failed" in called_kwargs["error"]


@pytest.mark.asyncio
async def test_get_file(cosmos_db_client, mocker):
    file_id = str(uuid4())

    # Mock file container query_items method
    mock_file_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'file_container', mock_file_container)

    # Simulate the query result
    expected_file = {
        "file_id": file_id,
        "status": ProcessStatus.READY_TO_PROCESS,
        "original_name": "file.txt",
        "blob_path": "/path/to/file"
    }

    # We define the async generator function that will yield the expected batch
    async def mock_query_items(query, parameters):
        yield expected_file

    # Assign the async generator to query_items mock
    mock_file_container.query_items.side_effect = mock_query_items

    # Call the method
    file = await cosmos_db_client.get_file(file_id)

    # Assert the file is returned correctly
    assert file["file_id"] == file_id
    assert file["status"] == ProcessStatus.READY_TO_PROCESS

    mock_file_container.query_items.assert_called_once()


@pytest.mark.asyncio
async def test_get_file_exception(cosmos_db_client, mocker):
    file_id = str(uuid4())

    # Mock file_container.query_items to raise an exception
    mock_file_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'file_container', mock_file_container)
    mock_file_container.query_items = mock.MagicMock(
        side_effect=Exception("Get file failed")
    )

    # Mock logger to verify logging
    mock_logger = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'logger', mock_logger)

    # Call get_file and expect an exception
    with pytest.raises(Exception, match="Get file failed"):
        await cosmos_db_client.get_file(file_id)

    called_args, called_kwargs = mock_logger.error.call_args
    assert called_args[0] == "Failed to get file"
    assert "error" in called_kwargs
    assert "Get file failed" in called_kwargs["error"]


@pytest.mark.asyncio
async def test_get_batch_files(cosmos_db_client, mocker):
    batch_id = str(uuid4())

    # Mock file container query_items method
    mock_file_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'file_container', mock_file_container)

    # Simulate the query result for multiple files
    expected_files = [
        {
            "file_id": str(uuid4()),
            "status": ProcessStatus.READY_TO_PROCESS,
            "original_name": "file1.txt",
            "blob_path": "/path/to/file1"
        },
        {
            "file_id": str(uuid4()),
            "status": ProcessStatus.IN_PROGRESS,
            "original_name": "file2.txt",
            "blob_path": "/path/to/file2"
        }
    ]

    # Define the async generator function to yield the expected files
    async def mock_query_items(query, parameters):
        for file in expected_files:
            yield file

    # Set the side_effect of query_items to simulate async iteration
    mock_file_container.query_items.side_effect = mock_query_items

    # Call the method
    files = await cosmos_db_client.get_batch_files(batch_id)

    # Assert the files list contains the correct files
    assert len(files) == len(expected_files)
    assert files[0]["file_id"] == expected_files[0]["file_id"]
    assert files[1]["file_id"] == expected_files[1]["file_id"]

    mock_file_container.query_items.assert_called_once()


@pytest.mark.asyncio
async def test_get_batch_files_exception(cosmos_db_client, mocker):
    batch_id = str(uuid4())

    # Mock file_container.query_items to raise an exception
    mock_file_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'file_container', mock_file_container)
    mock_file_container.query_items = mock.MagicMock(
        side_effect=Exception("Get batch file failed")
    )

    # Mock logger to verify logging
    mock_logger = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'logger', mock_logger)

    # Expect the exception to be raised
    with pytest.raises(Exception, match="Get batch file failed"):
        await cosmos_db_client.get_batch_files(batch_id)

    called_args, called_kwargs = mock_logger.error.call_args
    assert called_args[0] == "Failed to get files"
    assert "error" in called_kwargs
    assert "Get batch file failed" in called_kwargs["error"]


@pytest.mark.asyncio
async def test_get_batch_from_id(cosmos_db_client, mocker):
    batch_id = str(uuid4())

    # Mock batch container query_items method
    mock_batch_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'batch_container', mock_batch_container)

    # Simulate the query result
    expected_batch = {
        "batch_id": batch_id,
        "status": ProcessStatus.READY_TO_PROCESS,
        "user_id": "user_123",
    }

    # Define the async generator function that will yield the expected batch
    async def mock_query_items(query, parameters):
        yield expected_batch

    # Assign the async generator to query_items mock
    mock_batch_container.query_items.side_effect = mock_query_items

    # Call the method
    batch = await cosmos_db_client.get_batch_from_id(batch_id)

    # Assert the batch is returned correctly
    assert batch["batch_id"] == batch_id
    assert batch["status"] == ProcessStatus.READY_TO_PROCESS

    mock_batch_container.query_items.assert_called_once()


@pytest.mark.asyncio
async def test_get_batch_from_id_exception(cosmos_db_client, mocker):
    batch_id = str(uuid4())

    # Mock batch_container.query_items to raise an exception
    mock_batch_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'batch_container', mock_batch_container)
    mock_batch_container.query_items = mock.MagicMock(
        side_effect=Exception("Get batch from id failed")
    )

    # Mock logger to verify logging
    mock_logger = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'logger', mock_logger)

    # Call the method and expect it to raise an exception
    with pytest.raises(Exception, match="Get batch from id failed"):
        await cosmos_db_client.get_batch_from_id(batch_id)

    called_args, called_kwargs = mock_logger.error.call_args
    assert called_args[0] == "Failed to get batch from ID"
    assert "error" in called_kwargs
    assert "Get batch from id failed" in called_kwargs["error"]


@pytest.mark.asyncio
async def test_get_user_batches(cosmos_db_client, mocker):
    user_id = "user_123"

    # Mock batch container query_items method
    mock_batch_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'batch_container', mock_batch_container)

    # Simulate the query result
    expected_batches = [
        {"batch_id": str(uuid4()), "status": ProcessStatus.READY_TO_PROCESS, "user_id": user_id},
        {"batch_id": str(uuid4()), "status": ProcessStatus.IN_PROGRESS, "user_id": user_id}
    ]

    # Define the async generator function that will yield the expected batches
    async def mock_query_items(query, parameters):
        for batch in expected_batches:
            yield batch

    # Assign the async generator to query_items mock
    mock_batch_container.query_items.side_effect = mock_query_items

    # Call the method
    batches = await cosmos_db_client.get_user_batches(user_id)

    # Assert the batches are returned correctly
    assert len(batches) == 2
    assert batches[0]["status"] == ProcessStatus.READY_TO_PROCESS
    assert batches[1]["status"] == ProcessStatus.IN_PROGRESS

    mock_batch_container.query_items.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_batches_exception(cosmos_db_client, mocker):
    user_id = "user_" + str(uuid4())

    # Mock batch_container.query_items to raise an exception
    mock_batch_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'batch_container', mock_batch_container)
    mock_batch_container.query_items = mock.MagicMock(
        side_effect=Exception("Get user batch failed")
    )

    # Mock logger to capture the error
    mock_logger = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'logger', mock_logger)

    # Call the method and expect it to raise the exception
    with pytest.raises(Exception, match="Get user batch failed"):
        await cosmos_db_client.get_user_batches(user_id)

    # Ensure logger.error was called with the expected message and error
    called_args, called_kwargs = mock_logger.error.call_args
    assert called_args[0] == "Failed to get user batches"
    assert "error" in called_kwargs
    assert "Get user batch failed" in called_kwargs["error"]


@pytest.mark.asyncio
async def test_get_file_logs(cosmos_db_client, mocker):
    file_id = str(uuid4())

    # Mock log container query_items method
    mock_log_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'log_container', mock_log_container)

    # Simulate the query result with new log structure
    expected_logs = [
        {
            "log_id": str(uuid4()),
            "file_id": file_id,
            "description": "Log entry 1",
            "last_candidate": "candidate_1",
            "log_type": LogType.INFO,
            "agent_type": AgentType.FIXER,
            "author_role": AuthorRole.ASSISTANT,
            "timestamp": datetime(2025, 4, 7, 12, 0, 0)
        },
        {
            "log_id": str(uuid4()),
            "file_id": file_id,
            "description": "Log entry 2",
            "last_candidate": "candidate_2",
            "log_type": LogType.ERROR,
            "agent_type": AgentType.HUMAN,
            "author_role": AuthorRole.USER,
            "timestamp": datetime(2025, 4, 7, 12, 5, 0)
        }
    ]

    # Define the async generator function that will yield the expected logs
    async def mock_query_items(query, parameters):
        for log in expected_logs:
            yield log

    # Assign the async generator to query_items mock
    mock_log_container.query_items.side_effect = mock_query_items

    # Call the method
    logs = await cosmos_db_client.get_file_logs(file_id)

    # Assert the logs are returned correctly
    assert len(logs) == 2
    assert logs[0]["description"] == "Log entry 1"
    assert logs[1]["description"] == "Log entry 2"
    assert logs[0]["log_type"] == LogType.INFO
    assert logs[1]["log_type"] == LogType.ERROR
    assert logs[0]["timestamp"] == datetime(2025, 4, 7, 12, 0, 0)
    assert logs[1]["timestamp"] == datetime(2025, 4, 7, 12, 5, 0)

    mock_log_container.query_items.assert_called_once()


@pytest.mark.asyncio
async def test_get_file_logs_exception(cosmos_db_client, mocker):
    file_id = str(uuid4())

    # Mock log_container.query_items to raise an exception
    mock_log_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'log_container', mock_log_container)
    mock_log_container.query_items = mock.MagicMock(
        side_effect=Exception("Get file log failed")
    )

    # Mock logger to verify error logging
    mock_logger = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'logger', mock_logger)

    # Call the method and expect it to raise the exception
    with pytest.raises(Exception, match="Get file log failed"):
        await cosmos_db_client.get_file_logs(file_id)

    # Assert logger.error was called with correct arguments
    called_args, called_kwargs = mock_logger.error.call_args
    assert called_args[0] == "Failed to get file logs"
    assert "error" in called_kwargs
    assert "Get file log failed" in called_kwargs["error"]


@pytest.mark.asyncio
async def test_delete_all(cosmos_db_client, mocker):
    user_id = str(uuid4())

    # Mock containers with AsyncMock
    mock_batch_container = AsyncMock()
    mock_file_container = AsyncMock()
    mock_log_container = AsyncMock()

    # Patching the containers with mock objects
    mocker.patch.object(cosmos_db_client, 'batch_container', mock_batch_container)
    mocker.patch.object(cosmos_db_client, 'file_container', mock_file_container)
    mocker.patch.object(cosmos_db_client, 'log_container', mock_log_container)

    # Mock the delete_item method for all containers
    mock_batch_container.delete_item = AsyncMock(return_value=None)
    mock_file_container.delete_item = AsyncMock(return_value=None)
    mock_log_container.delete_item = AsyncMock(return_value=None)

    # Call the delete_all method
    await cosmos_db_client.delete_all(user_id)

    mock_batch_container.delete_item.assert_called_once()
    mock_file_container.delete_item.assert_called_once()
    mock_log_container.delete_item.assert_called_once()


@pytest.mark.asyncio
async def test_delete_all_exception(cosmos_db_client, mocker):
    user_id = f"user_{uuid4()}"

    # Mock batch_container to raise an exception on delete
    mock_batch_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'batch_container', mock_batch_container)
    mock_batch_container.delete_item = mock.AsyncMock(
        side_effect=Exception("Delete failed")
    )

    # Also mock file_container and log_container to avoid accidental execution
    mock_file_container = mock.MagicMock()
    mock_log_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'file_container', mock_file_container)
    mocker.patch.object(cosmos_db_client, 'log_container', mock_log_container)

    # Mock logger to verify error handling
    mock_logger = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'logger', mock_logger)

    # Call the method and expect it to raise the exception
    with pytest.raises(Exception, match="Delete failed"):
        await cosmos_db_client.delete_all(user_id)

    # Check that logger.error was called with expected error message
    called_args, called_kwargs = mock_logger.error.call_args
    assert called_args[0] == "Failed to delete all user data"
    assert "error" in called_kwargs
    assert "Delete failed" in called_kwargs["error"]


@pytest.mark.asyncio
async def test_delete_logs(cosmos_db_client, mocker):
    file_id = str(uuid4())

    # Mock the log container with AsyncMock
    mock_log_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'log_container', mock_log_container)

    # Simulate the query result for logs
    log_ids = [str(uuid4()), str(uuid4())]

    # Define the async generator function to simulate query result
    async def mock_query_items(query, parameters):
        for log_id in log_ids:
            yield {"id": log_id}

    # Assign the async generator to query_items mock
    mock_log_container.query_items.side_effect = mock_query_items

    # Mock delete_item method for log_container
    mock_log_container.delete_item = AsyncMock(return_value=None)

    # Call the delete_logs method
    await cosmos_db_client.delete_logs(file_id)

    # Assert delete_item is called for each log id
    for log_id in log_ids:
        mock_log_container.delete_item.assert_any_call(log_id, partition_key=log_id)

    mock_log_container.query_items.assert_called_once()


@pytest.mark.asyncio
async def test_delete_logs_exception(cosmos_db_client, mocker):
    file_id = str(uuid4())

    # Mock log_container.query_items to raise an exception
    mock_log_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'log_container', mock_log_container)
    mock_log_container.query_items = mock.MagicMock(
        side_effect=Exception("Query failed")
    )

    # Mock logger to verify error handling
    mock_logger = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'logger', mock_logger)

    # Call the method and expect it to raise the exception
    with pytest.raises(Exception, match="Query failed"):
        await cosmos_db_client.delete_logs(file_id)

    # Check that logger.error was called with expected error message
    called_args, called_kwargs = mock_logger.error.call_args
    assert called_args[0] == "Failed to delete all user data"
    assert "error" in called_kwargs
    assert "Query failed" in called_kwargs["error"]


@pytest.mark.asyncio
async def test_delete_batch(cosmos_db_client, mocker):
    user_id = str(uuid4())
    batch_id = str(uuid4())

    # Mock the batch container with AsyncMock
    mock_batch_container = AsyncMock()
    mocker.patch.object(cosmos_db_client, "batch_container", mock_batch_container)

    # Call the delete_batch method
    await cosmos_db_client.delete_batch(user_id, batch_id)

    mock_batch_container.delete_item.assert_called_once()


@pytest.mark.asyncio
async def test_delete_batch_exception(cosmos_db_client, mocker):
    user_id = f"user_{uuid4()}"
    batch_id = str(uuid4())

    # Mock batch_container.delete_item to raise an exception
    mock_batch_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'batch_container', mock_batch_container)
    mock_batch_container.delete_item = mock.AsyncMock(
        side_effect=Exception("Delete failed")
    )

    # Mock logger to verify error logging
    mock_logger = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'logger', mock_logger)

    # Expect the exception to be raised from the inner try block
    with pytest.raises(Exception, match="Delete failed"):
        await cosmos_db_client.delete_batch(user_id, batch_id)

    # Check that both error logs were triggered
    assert mock_logger.error.call_count == 2

    # First log: failed to delete the specific batch
    first_call_args, first_call_kwargs = mock_logger.error.call_args_list[0]
    assert f"Failed to delete batch with ID: {batch_id}" in first_call_args[0]
    assert "error" in first_call_kwargs
    assert "Delete failed" in first_call_kwargs["error"]

    # Second log: higher-level operation failed
    second_call_args, second_call_kwargs = mock_logger.error.call_args_list[1]
    assert second_call_args[0] == "Failed to perform delete batch operation"
    assert "error" in second_call_kwargs
    assert "Delete failed" in second_call_kwargs["error"]


@pytest.mark.asyncio
async def test_delete_file(cosmos_db_client, mocker):
    user_id = str(uuid4())
    file_id = str(uuid4())

    # Mock containers with AsyncMock
    mock_file_container = AsyncMock()
    mock_log_container = AsyncMock()

    # Patching the containers with mock objects
    mocker.patch.object(cosmos_db_client, 'file_container', mock_file_container)
    mocker.patch.object(cosmos_db_client, 'log_container', mock_log_container)

    # Mock the delete_logs method (since it's called in delete_file)
    mocker.patch.object(cosmos_db_client, 'delete_logs', return_value=None)

    # Call the delete_file method
    await cosmos_db_client.delete_file(user_id, file_id)

    cosmos_db_client.delete_logs.assert_called_once_with(file_id)

    mock_file_container.delete_item.assert_called_once_with(file_id, partition_key=file_id)


@pytest.mark.asyncio
async def test_delete_file_exception(cosmos_db_client, mocker):
    user_id = f"user_{uuid4()}"
    file_id = str(uuid4())

    # Mock delete_logs to raise an exception
    mocker.patch.object(
        cosmos_db_client,
        'delete_logs',
        mock.AsyncMock(side_effect=Exception("Delete file failed"))
    )

    # Mock file_container to ensure delete_item is not accidentally called
    mock_file_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'file_container', mock_file_container)

    # Mock logger to verify error logging
    mock_logger = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'logger', mock_logger)

    # Expect an exception to be raised from delete_logs
    with pytest.raises(Exception, match="Delete file failed"):
        await cosmos_db_client.delete_file(user_id, file_id)

    mock_logger.error.assert_called_once()
    called_args, _ = mock_logger.error.call_args
    assert f"Failed to delete file and logs for file_id {file_id}" in called_args[0]


@pytest.mark.asyncio
async def test_add_file_log(cosmos_db_client, mocker):
    file_id = uuid4()
    description = "File processing started"
    last_candidate = "candidate_123"
    log_type = LogType.INFO
    agent_type = AgentType.MIGRATOR
    author_role = AuthorRole.ASSISTANT

    # Mock log container create_item method
    mock_log_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'log_container', mock_log_container)

    # Mock the create_item method
    mock_log_container.create_item = AsyncMock(return_value=None)

    # Call the method
    await cosmos_db_client.add_file_log(
        file_id, description, last_candidate, log_type, agent_type, author_role
    )

    mock_log_container.create_item.assert_called_once()


@pytest.mark.asyncio
async def test_update_batch_entry(cosmos_db_client, mocker):
    batch_id = "batch_123"
    user_id = "user_123"
    status = ProcessStatus.IN_PROGRESS
    file_count = 5

    # Mock batch container replace_item method
    mock_batch_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'batch_container', mock_batch_container)

    # Mock the get_batch method
    mocker.patch.object(cosmos_db_client, 'get_batch', return_value={
        "batch_id": batch_id,
        "status": ProcessStatus.READY_TO_PROCESS.value,
        "user_id": user_id,
        "file_count": 0,
        "updated_at": "2025-04-07T00:00:00Z"
    })

    # Mock the replace_item method
    mock_batch_container.replace_item = AsyncMock(return_value=None)

    # Call the method
    updated_batch = await cosmos_db_client.update_batch_entry(batch_id, user_id, status, file_count)

    # Assert that replace_item was called with the correct arguments
    mock_batch_container.replace_item.assert_called_once_with(item=batch_id, body={
        "batch_id": batch_id,
        "status": status.value,
        "user_id": user_id,
        "file_count": file_count,
        "updated_at": updated_batch["updated_at"]
    })

    # Assert the returned batch matches expected values
    assert updated_batch["batch_id"] == batch_id
    assert updated_batch["status"] == status.value
    assert updated_batch["file_count"] == file_count


@pytest.mark.asyncio
async def test_close(cosmos_db_client, mocker):
    # Mock the client and logger
    mock_client = mock.MagicMock()
    mock_logger = mock.MagicMock()
    cosmos_db_client.client = mock_client
    cosmos_db_client.logger = mock_logger

    # Call the method
    await cosmos_db_client.close()

    # Assert that the client was closed
    mock_client.close.assert_called_once()

    # Assert that logger's info method was called
    mock_logger.info.assert_called_once_with("Closed Cosmos DB connection")


@pytest.mark.asyncio
async def test_get_batch_history(cosmos_db_client, mocker):
    user_id = "user_123"
    limit = 5
    offset = 0
    sort_order = "DESC"

    # Mock batch container query_items method
    mock_batch_container = mock.MagicMock()
    mocker.patch.object(cosmos_db_client, 'batch_container', mock_batch_container)

    # Simulate the query result for batches
    expected_batches = [
        {"batch_id": "batch_1", "status": ProcessStatus.IN_PROGRESS.value, "user_id": user_id, "file_count": 5},
        {"batch_id": "batch_2", "status": ProcessStatus.COMPLETED.value, "user_id": user_id, "file_count": 3},
    ]

    # Define the async generator function to simulate query result
    async def mock_query_items(query, parameters):
        for batch in expected_batches:
            yield batch

    # Assign the async generator to query_items mock
    mock_batch_container.query_items.side_effect = mock_query_items

    # Call the method
    batches = await cosmos_db_client.get_batch_history(user_id, limit, sort_order, offset)

    # Assert the returned batches are correct
    assert len(batches) == len(expected_batches)
    assert batches[0]["batch_id"] == expected_batches[0]["batch_id"]

    mock_batch_container.query_items.assert_called_once()
