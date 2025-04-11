import pytest
import asyncio
import os
import sys
from unittest import mock

from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone
from azure.cosmos.exceptions import CosmosResourceExistsError

# Add backend directory to sys.path
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..", "backend")),
)

from common.models.api import (
    AgentType,
    BatchRecord,
    FileLog,
    LogType,
    ProcessStatus,
    FileRecord,
    AuthorRole,
)
from common.logger.app_logger import AppLogger
from common.database.cosmosdb import (
    CosmosDBClient,
)
from azure.cosmos.aio import CosmosClient

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

    # Use AsyncMock to mock asynchronous container creation
    mock_database.create_container = AsyncMock(side_effect=[
        mock_batch_container,
        mock_file_container,
        mock_log_container
    ])

    # Call the initialize_cosmos method
    await cosmos_db_client.initialize_cosmos()

    # Assert that the containers were created or fetched successfully
    mock_database.create_container.assert_any_call(id=batch_container, partition_key=mock.ANY)
    mock_database.create_container.assert_any_call(id=file_container, partition_key=mock.ANY)
    mock_database.create_container.assert_any_call(id=log_container, partition_key=mock.ANY)

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

    # Simulate a general exception during container creation
    mock_database.create_container = AsyncMock(side_effect=Exception("Failed to create container"))

    # Call the initialize_cosmos method and expect it to raise an error
    with pytest.raises(Exception) as exc_info:
        await cosmos_db_client.initialize_cosmos()

    # Assert that the exception message matches the expected message
    assert str(exc_info.value) == "Failed to create container"


@pytest.mark.asyncio
async def test_initialize_cosmos_container_exists_error(cosmos_db_client, mocker):
    # Mocking CosmosClient and its methods
    mock_client = mocker.patch.object(CosmosClient, 'get_database_client', return_value=mock.MagicMock())
    mock_database = mock_client.return_value

    # Simulating CosmosResourceExistsError for container creation
    mock_database.create_container = AsyncMock(side_effect=CosmosResourceExistsError)

    # Use AsyncMock for asynchronous methods
    mock_batch_container = mock.MagicMock()
    mock_file_container = mock.MagicMock()
    mock_log_container = mock.MagicMock()

    # Use AsyncMock to mock asynchronous container creation
    mock_database.create_container = AsyncMock(side_effect=[
        mock_batch_container,
        mock_file_container,
        mock_log_container
    ])

    # Call the initialize_cosmos method
    await cosmos_db_client.initialize_cosmos()

    # Assert that the container creation method was called with the correct arguments
    mock_database.create_container.assert_any_call(id='batch_container', partition_key=mock.ANY)
    mock_database.create_container.assert_any_call(id='file_container', partition_key=mock.ANY)
    mock_database.create_container.assert_any_call(id='log_container', partition_key=mock.ANY)

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
