import asyncio
import enum
import uuid
from datetime import datetime

from azure.cosmos import PartitionKey, exceptions

from common.database.cosmosdb import CosmosDBClient
from common.logger.app_logger import AppLogger
from common.models.api import ProcessStatus

import pytest


# --- Enums for Testing ---
class DummyProcessStatus(enum.Enum):
    READY_TO_PROCESS = "READY"
    PROCESSING = "PROCESSING"


class DummyLogType(enum.Enum):
    INFO = "INFO"
    ERROR = "ERROR"


@pytest.fixture(autouse=True)
def patch_enums(monkeypatch):
    monkeypatch.setattr("common.models.api.ProcessStatus", DummyProcessStatus)
    monkeypatch.setattr("common.models.api.LogType", DummyLogType)


# --- implementations to simulate Cosmos DB behavior ---
async def async_query_generator(items):
    for item in items:
        yield item


async def async_query_error_generator(*args, **kwargs):
    raise Exception("Error in query")
    if False:
        yield


class DummyContainerClient:
    def __init__(self, container_name):
        self.container_name = container_name
        self.created_items = []
        self.deleted_items = []
        self._query_items_func = None

    async def create_item(self, body):
        self.created_items.append(body)

    async def replace_item(self, item, body):
        return body

    async def delete_item(self, item, partition_key=None):
        self.deleted_items.append((item, partition_key))

    async def delete_items(self, key):
        self.deleted_items.append(key)

    async def query_items(self, query, parameters):
        if self._query_items_func:
            async for item in self._query_items_func(query, parameters):
                yield item
        else:
            if False:
                yield

    def set_query_items(self, func):
        self._query_items_func = func


class DummyDatabase:
    def __init__(self, database_name):
        self.database_name = database_name
        self.containers = {}

    async def create_container(self, id, partition_key):
        if id in self.containers:
            raise exceptions.CosmosResourceExistsError(404, "Container exists")
        container = DummyContainerClient(id)
        self.containers[id] = container
        return container

    def get_container_client(self, container_name):
        return self.containers.get(container_name, DummyContainerClient(container_name))


class DummyCosmosClient:
    def __init__(self, url, credential):
        self.url = url
        self.credential = credential
        self._database = DummyDatabase("dummy_db")
        self.closed = False

    def get_database_client(self, database_name):
        return self._database

    def close(self):
        self.closed = True


class FakeCosmosDBClient(CosmosDBClient):
    async def _async_init(
        self,
        endpoint: str,
        credential: any,
        database_name: str,
        batch_container: str,
        file_container: str,
        log_container: str,
    ):
        self.endpoint = endpoint
        self.credential = credential
        self.database_name = database_name
        self.batch_container_name = batch_container
        self.file_container_name = file_container
        self.log_container_name = log_container
        self.logger = AppLogger("CosmosDB")
        self.client = DummyCosmosClient(endpoint, credential)
        db = self.client.get_database_client(database_name)
        self.batch_container = await db.create_container(
            batch_container, PartitionKey(path="/batch_id")
        )
        self.file_container = await db.create_container(
            file_container, PartitionKey(path="/file_id")
        )
        self.log_container = await db.create_container(
            log_container, PartitionKey(path="/log_id")
        )

    @classmethod
    async def create(
        cls,
        endpoint,
        credential,
        database_name,
        batch_container,
        file_container,
        log_container,
    ):
        instance = cls.__new__(cls)
        await instance._async_init(
            endpoint,
            credential,
            database_name,
            batch_container,
            file_container,
            log_container,
        )
        return instance

    # Minimal implementations for abstract methods not under test.
    async def delete_file_logs(self, file_id: str) -> None:
        await self.log_container.delete_items(file_id)

    async def log_batch_status(
        self, batch_id: str, status: ProcessStatus, processed_files: int
    ) -> None:
        return


# --- Fixture ---
@pytest.fixture
def cosmosdb_client(event_loop):
    client = event_loop.run_until_complete(
        FakeCosmosDBClient.create(
            endpoint="dummy_endpoint",
            credential="dummy_credential",
            database_name="dummy_db",
            batch_container="batch",
            file_container="file",
            log_container="log",
        )
    )
    return client


# --- Test Cases ---


@pytest.mark.asyncio
async def test_initialization_success(cosmosdb_client):
    assert cosmosdb_client.client is not None
    assert cosmosdb_client.batch_container is not None
    assert cosmosdb_client.file_container is not None
    assert cosmosdb_client.log_container is not None


@pytest.mark.asyncio
async def test_init_error(monkeypatch):
    async def fake_async_init(*args, **kwargs):
        raise Exception("client error")

    monkeypatch.setattr(FakeCosmosDBClient, "_async_init", fake_async_init)
    with pytest.raises(Exception) as exc_info:
        await FakeCosmosDBClient.create("dummy", "dummy", "dummy", "a", "b", "c")
    assert "client error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_or_create_container_existing(monkeypatch, cosmosdb_client):
    db = DummyDatabase("dummy_db")
    existing = DummyContainerClient("existing")
    db.containers["existing"] = existing

    async def fake_create_container(id, partition_key):
        raise exceptions.CosmosResourceExistsError(404, "Container exists")

    monkeypatch.setattr(db, "create_container", fake_create_container)
    monkeypatch.setattr(db, "get_container_client", lambda name: existing)

    # Directly call _get_or_create_container on a new instance.
    instance = FakeCosmosDBClient.__new__(FakeCosmosDBClient)
    instance.logger = AppLogger("CosmosDB")
    result = await instance._get_or_create_container(db, "existing", "/id")
    assert result is existing


@pytest.mark.asyncio
async def test_create_batch_success(monkeypatch, cosmosdb_client):
    called = False

    async def fake_create_item(body):
        nonlocal called
        called = True

    monkeypatch.setattr(
        cosmosdb_client.batch_container, "create_item", fake_create_item
    )
    bid = uuid.uuid4()
    batch = await cosmosdb_client.create_batch("user1", bid)
    assert batch.batch_id == bid
    assert batch.user_id == "user1"
    assert called


@pytest.mark.asyncio
async def test_create_batch_error(monkeypatch, cosmosdb_client):
    async def fake_create_item(body):
        raise Exception("Batch creation error")

    monkeypatch.setattr(
        cosmosdb_client.batch_container, "create_item", fake_create_item
    )
    with pytest.raises(Exception) as exc_info:
        await cosmosdb_client.create_batch("user1", uuid.uuid4())
    assert "Batch creation error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_add_file_success(monkeypatch, cosmosdb_client):
    called = False

    async def fake_create_item(body):
        nonlocal called
        called = True

    monkeypatch.setattr(cosmosdb_client.file_container, "create_item", fake_create_item)
    bid = uuid.uuid4()
    fid = uuid.uuid4()
    fs = await cosmosdb_client.add_file(bid, fid, "test.txt", "path/to/blob")
    assert fs.file_id == fid
    assert fs.original_name == "test.txt"
    assert fs.blob_path == "path/to/blob"
    assert called


@pytest.mark.asyncio
async def test_add_file_error(monkeypatch, cosmosdb_client):
    async def fake_create_item(body):
        raise Exception("Add file error")

    monkeypatch.setattr(
        cosmosdb_client.file_container,
        "create_item",
        lambda *args, **kwargs: fake_create_item(*args, **kwargs),
    )
    with pytest.raises(Exception) as exc_info:
        await cosmosdb_client.add_file(
            uuid.uuid4(), uuid.uuid4(), "test.txt", "path/to/blob"
        )
    assert "Add file error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_batch_success(monkeypatch, cosmosdb_client):
    batch_item = {
        "id": "batch1",
        "user_id": "user1",
        "created_at": datetime.utcnow().isoformat(),
    }
    file_item = {"file_id": "file1", "batch_id": "batch1"}

    async def fake_query_items_batch(*args, **kwargs):
        for item in [batch_item]:
            yield item

    async def fake_query_items_files(*args, **kwargs):
        for item in [file_item]:
            yield item

    cosmosdb_client.batch_container.set_query_items(fake_query_items_batch)
    cosmosdb_client.file_container.set_query_items(fake_query_items_files)
    result = await cosmosdb_client.get_batch("user1", "batch1")
    assert result is not None
    assert result.get("id") == "batch1"


@pytest.mark.asyncio
async def test_get_batch_not_found(monkeypatch, cosmosdb_client):
    async def fake_query_items(*args, **kwargs):
        if False:
            yield

    cosmosdb_client.batch_container.set_query_items(fake_query_items)
    result = await cosmosdb_client.get_batch("user1", "nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_get_batch_error(monkeypatch, cosmosdb_client):
    async def fake_query_items(*args, **kwargs):
        raise Exception("Query batch error")
        if False:
            yield

    monkeypatch.setattr(
        cosmosdb_client.batch_container,
        "query_items",
        lambda *args, **kwargs: fake_query_items(*args, **kwargs),
    )
    with pytest.raises(Exception) as exc_info:
        await cosmosdb_client.get_batch("user1", "batch1")
    assert "Query batch error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_file_success(monkeypatch, cosmosdb_client):
    file_item = {"file_id": "file1", "original_name": "test.txt"}

    async def fake_query_items(*args, **kwargs):
        for item in [file_item]:
            yield item

    cosmosdb_client.file_container.set_query_items(fake_query_items)
    result = await cosmosdb_client.get_file("file1")
    assert result == file_item


@pytest.mark.asyncio
async def test_get_file_error(monkeypatch, cosmosdb_client):
    async def fake_query_items(*args, **kwargs):
        raise Exception("Query file error")
        if False:
            yield

    monkeypatch.setattr(
        cosmosdb_client.file_container,
        "query_items",
        lambda *args, **kwargs: fake_query_items(*args, **kwargs),
    )
    with pytest.raises(Exception) as exc_info:
        await cosmosdb_client.get_file("file1")
    assert "Query file error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_batch_files_success(monkeypatch, cosmosdb_client):
    file_item = {"file_id": "file1", "batch_id": "batch1"}

    async def fake_query_items(*args, **kwargs):
        for item in [file_item]:
            yield item

    cosmosdb_client.file_container.set_query_items(fake_query_items)
    files = await cosmosdb_client.get_batch_files("user1", "batch1")
    assert files == [file_item]


@pytest.mark.asyncio
async def test_get_user_batches_success(monkeypatch, cosmosdb_client):
    batch_item1 = {"id": "batch1", "user_id": "user1"}
    batch_item2 = {"id": "batch2", "user_id": "user1"}

    async def fake_query_items(*args, **kwargs):
        for item in [batch_item1, batch_item2]:
            yield item

    cosmosdb_client.batch_container.set_query_items(fake_query_items)
    result = await cosmosdb_client.get_user_batches("user1")
    assert result == [batch_item1, batch_item2]


@pytest.mark.asyncio
async def test_get_user_batches_error(monkeypatch, cosmosdb_client):
    async def fake_query_items(*args, **kwargs):
        raise Exception("User batches error")
        if False:
            yield

    monkeypatch.setattr(
        cosmosdb_client.batch_container,
        "query_items",
        lambda *args, **kwargs: fake_query_items(*args, **kwargs),
    )
    with pytest.raises(Exception) as exc_info:
        await cosmosdb_client.get_user_batches("user1")
    assert "User batches error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_file_logs_success(monkeypatch, cosmosdb_client):
    log_item = {
        "file_id": "file1",
        "description": "log",
        "timestamp": datetime.utcnow().isoformat(),
    }

    async def fake_query_items(*args, **kwargs):
        for item in [log_item]:
            yield item

    cosmosdb_client.log_container.set_query_items(fake_query_items)
    result = await cosmosdb_client.get_file_logs("file1")
    assert result == [log_item]


@pytest.mark.asyncio
async def test_get_file_logs_error(monkeypatch, cosmosdb_client):
    async def fake_query_items(*args, **kwargs):
        raise Exception("Log query error")
        if False:
            yield

    monkeypatch.setattr(
        cosmosdb_client.log_container,
        "query_items",
        lambda *args, **kwargs: fake_query_items(*args, **kwargs),
    )
    with pytest.raises(Exception) as exc_info:
        await cosmosdb_client.get_file_logs("file1")
    assert "Log query error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_all_success(monkeypatch, cosmosdb_client):
    async def fake_delete_items(key):
        return

    monkeypatch.setattr(
        cosmosdb_client.batch_container, "delete_items", fake_delete_items
    )
    monkeypatch.setattr(
        cosmosdb_client.file_container, "delete_items", fake_delete_items
    )
    monkeypatch.setattr(
        cosmosdb_client.log_container, "delete_items", fake_delete_items
    )
    await cosmosdb_client.delete_all("user1")


@pytest.mark.asyncio
async def test_delete_all_error(monkeypatch, cosmosdb_client):
    async def fake_delete_items(key):
        raise Exception("Delete all error")

    monkeypatch.setattr(
        cosmosdb_client.batch_container, "delete_items", fake_delete_items
    )
    with pytest.raises(Exception) as exc_info:
        await cosmosdb_client.delete_all("user1")
    assert "Delete all error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_logs_success(monkeypatch, cosmosdb_client):
    async def fake_delete_items(key):
        return

    monkeypatch.setattr(
        cosmosdb_client.log_container, "delete_items", fake_delete_items
    )
    await cosmosdb_client.delete_logs("file1")


@pytest.mark.asyncio
async def test_delete_batch_success(monkeypatch, cosmosdb_client):
    delete_calls = []

    async def fake_delete_items(key):
        delete_calls.append(key)

    async def fake_delete_item(item, partition_key):
        delete_calls.append((item, partition_key))

    monkeypatch.setattr(
        cosmosdb_client.file_container, "delete_items", fake_delete_items
    )
    monkeypatch.setattr(
        cosmosdb_client.log_container, "delete_items", fake_delete_items
    )
    monkeypatch.setattr(
        cosmosdb_client.batch_container, "delete_item", fake_delete_item
    )
    await cosmosdb_client.delete_batch("user1", "batch1")
    assert len(delete_calls) == 3


@pytest.mark.asyncio
async def test_delete_file_success(monkeypatch, cosmosdb_client):
    calls = []

    async def fake_delete_items(key):
        calls.append(("log_delete", key))

    async def fake_delete_item(file_id):
        calls.append(("file_delete", file_id))

    monkeypatch.setattr(
        cosmosdb_client.log_container, "delete_items", fake_delete_items
    )
    monkeypatch.setattr(cosmosdb_client.file_container, "delete_item", fake_delete_item)
    await cosmosdb_client.delete_file("user1", "batch1", "file1")
    assert ("log_delete", "file1") in calls
    assert ("file_delete", "file1") in calls


@pytest.mark.asyncio
async def test_log_file_status_success(monkeypatch, cosmosdb_client):
    called = False

    async def fake_create_item(body):
        nonlocal called
        called = True

    monkeypatch.setattr(cosmosdb_client.log_container, "create_item", fake_create_item)
    await cosmosdb_client.log_file_status(
        "file1", DummyProcessStatus.READY_TO_PROCESS, "desc", DummyLogType.INFO
    )
    assert called


@pytest.mark.asyncio
async def test_log_file_status_error(monkeypatch, cosmosdb_client):
    async def fake_create_item(body):
        raise Exception("Log error")

    monkeypatch.setattr(
        cosmosdb_client.log_container,
        "create_item",
        lambda *args, **kwargs: fake_create_item(*args, **kwargs),
    )
    with pytest.raises(Exception) as exc_info:
        await cosmosdb_client.log_file_status(
            "file1", DummyProcessStatus.READY_TO_PROCESS, "desc", DummyLogType.INFO
        )
    assert "Log error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_batch_entry_success(monkeypatch, cosmosdb_client):
    dummy_batch = {
        "id": "batch1",
        "user_id": "user1",
        "status": DummyProcessStatus.READY_TO_PROCESS,
        "updated_at": datetime.utcnow().isoformat(),
        "file_count": 0,
    }

    async def fake_get_batch(user_id, batch_id):
        return dummy_batch.copy()

    monkeypatch.setattr(cosmosdb_client, "get_batch", fake_get_batch)
    updated_body = None

    async def fake_replace_item(item, body):
        nonlocal updated_body
        updated_body = body
        return body

    monkeypatch.setattr(
        cosmosdb_client.batch_container, "replace_item", fake_replace_item
    )
    new_status = DummyProcessStatus.PROCESSING
    file_count = 5
    result = await cosmosdb_client.update_batch_entry(
        "batch1", "user1", new_status, file_count
    )
    assert result["file_count"] == file_count
    assert result["status"] == new_status.value
    assert updated_body is not None


@pytest.mark.asyncio
async def test_update_batch_entry_not_found(monkeypatch, cosmosdb_client):
    monkeypatch.setattr(
        cosmosdb_client, "get_batch", lambda u, b: asyncio.sleep(0, result=None)
    )
    with pytest.raises(ValueError, match="Batch not found"):
        await cosmosdb_client.update_batch_entry(
            "nonexistent", "user1", DummyProcessStatus.READY_TO_PROCESS, 0
        )


@pytest.mark.asyncio
async def test_close(monkeypatch, cosmosdb_client):
    closed = False

    def fake_close():
        nonlocal closed
        closed = True

    monkeypatch.setattr(cosmosdb_client.client, "close", fake_close)
    await cosmosdb_client.close()
    assert closed
