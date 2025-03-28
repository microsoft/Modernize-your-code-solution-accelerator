# blob_azure_test.py

import asyncio
from datetime import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Import the class under test
from common.storage.blob_azure import AzureBlobStorage
from azure.core.exceptions import ResourceExistsError


class DummyBlob:
    """A dummy blob item returned by list_blobs."""
    def __init__(self, name, size, creation_time, content_type, metadata):
        self.name = name
        self.size = size
        self.creation_time = creation_time
        self.content_settings = MagicMock(content_type=content_type)
        self.metadata = metadata

class DummyAsyncIterator:
    """A dummy async iterator that yields the given items."""
    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item

class DummyDownloadStream:
    """A dummy download stream whose content_as_bytes method returns a fixed byte string."""
    async def content_as_bytes(self):
        return b"file content"

# --- Fixtures ---

@pytest.fixture
def dummy_storage():
    # Create an instance with dummy connection string and container name.
    return AzureBlobStorage("dummy_connection_string", "dummy_container")

@pytest.fixture
def dummy_container_client():
    container = MagicMock()
    container.create_container = AsyncMock()
    container.list_blobs = MagicMock()  # Will be overridden per test.
    container.get_blob_client = MagicMock()
    return container

@pytest.fixture
def dummy_service_client(dummy_container_client):
    service = MagicMock()
    service.get_container_client.return_value = dummy_container_client
    return service

@pytest.fixture
def dummy_blob_client():
    blob_client = MagicMock()
    blob_client.upload_blob = AsyncMock()
    blob_client.get_blob_properties = AsyncMock()
    blob_client.download_blob = AsyncMock()
    blob_client.delete_blob = AsyncMock()
    blob_client.url = "https://dummy.blob.core.windows.net/dummy_container/dummy_blob"
    return blob_client

# --- Tests for AzureBlobStorage methods ---

@pytest.mark.asyncio
async def test_initialize_creates_container(dummy_storage, dummy_service_client, dummy_container_client):
    with patch("common.storage.blob_azure.BlobServiceClient.from_connection_string", return_value=dummy_service_client) as mock_from_conn:
        # Simulate normal container creation.
        dummy_container_client.create_container = AsyncMock()
        await dummy_storage.initialize()
        mock_from_conn.assert_called_once_with("dummy_connection_string")
        dummy_service_client.get_container_client.assert_called_once_with("dummy_container")
        dummy_container_client.create_container.assert_awaited_once()

@pytest.mark.asyncio
async def test_initialize_container_already_exists(dummy_storage, dummy_service_client, dummy_container_client):
    with patch("common.storage.blob_azure.BlobServiceClient.from_connection_string", return_value=dummy_service_client):
        # Simulate container already existing.
        dummy_container_client.create_container = AsyncMock(side_effect=ResourceExistsError("Container exists"))
        with patch.object(dummy_storage.logger, "debug") as mock_debug:
            await dummy_storage.initialize()
            dummy_container_client.create_container.assert_awaited_once()
            mock_debug.assert_called_with("Container dummy_container already exists")

@pytest.mark.asyncio
async def test_initialize_failure(dummy_storage):
    # Simulate failure during initialization.
    with patch("common.storage.blob_azure.BlobServiceClient.from_connection_string", side_effect=Exception("Init error")):
        with patch.object(dummy_storage.logger, "error") as mock_error:
            with pytest.raises(Exception, match="Init error"):
                await dummy_storage.initialize()
            mock_error.assert_called()

@pytest.mark.asyncio
async def test_upload_file_success(dummy_storage, dummy_blob_client):
    # Patch get_blob_client to return our dummy blob client.
    dummy_storage.container_client = MagicMock()
    dummy_storage.container_client.get_blob_client.return_value = dummy_blob_client

    # Create a dummy properties object.
    dummy_properties = MagicMock()
    dummy_properties.size = 1024
    dummy_properties.content_settings = MagicMock(content_type="text/plain")
    dummy_properties.creation_time = datetime(2023, 1, 1)
    dummy_properties.etag = "dummy_etag"
    dummy_blob_client.get_blob_properties = AsyncMock(return_value=dummy_properties)

    file_content = b"Hello, world!"
    result = await dummy_storage.upload_file(file_content, "dummy_blob.txt", "text/plain", {"key": "value"})
    dummy_storage.container_client.get_blob_client.assert_called_once_with("dummy_blob.txt")
    dummy_blob_client.upload_blob.assert_awaited_with(file_content, content_type="text/plain", metadata={"key": "value"}, overwrite=True)
    dummy_blob_client.get_blob_properties.assert_awaited()
    assert result["path"] == "dummy_blob.txt"
    assert result["size"] == 1024
    assert result["content_type"] == "text/plain"
    assert result["url"] == dummy_blob_client.url
    assert result["etag"] == "dummy_etag"

@pytest.mark.asyncio
async def test_upload_file_error(dummy_storage, dummy_blob_client):
    dummy_storage.container_client = MagicMock()
    dummy_storage.container_client.get_blob_client.return_value = dummy_blob_client
    dummy_blob_client.upload_blob = AsyncMock(side_effect=Exception("Upload failed"))
    with pytest.raises(Exception, match="Upload failed"):
        await dummy_storage.upload_file(b"data", "blob.txt", "text/plain", {})

@pytest.mark.asyncio
async def test_get_file_success(dummy_storage, dummy_blob_client):
    dummy_storage.container_client = MagicMock()
    dummy_storage.container_client.get_blob_client.return_value = dummy_blob_client
    # Make download_blob return a DummyDownloadStream (not wrapped in extra coroutine)
    dummy_blob_client.download_blob = AsyncMock(return_value=DummyDownloadStream())
    result = await dummy_storage.get_file("blob.txt")
    dummy_storage.container_client.get_blob_client.assert_called_once_with("blob.txt")
    dummy_blob_client.download_blob.assert_awaited()
    assert result == b"file content"

@pytest.mark.asyncio
async def test_get_file_error(dummy_storage, dummy_blob_client):
    dummy_storage.container_client = MagicMock()
    dummy_storage.container_client.get_blob_client.return_value = dummy_blob_client
    dummy_blob_client.download_blob = AsyncMock(side_effect=Exception("Download error"))
    with pytest.raises(Exception, match="Download error"):
        await dummy_storage.get_file("nonexistent.txt")

@pytest.mark.asyncio
async def test_delete_file_success(dummy_storage, dummy_blob_client):
    dummy_storage.container_client = MagicMock()
    dummy_storage.container_client.get_blob_client.return_value = dummy_blob_client
    dummy_blob_client.delete_blob = AsyncMock()
    result = await dummy_storage.delete_file("blob.txt")
    dummy_storage.container_client.get_blob_client.assert_called_once_with("blob.txt")
    dummy_blob_client.delete_blob.assert_awaited()
    assert result is True

@pytest.mark.asyncio
async def test_delete_file_error(dummy_storage, dummy_blob_client):
    dummy_storage.container_client = MagicMock()
    dummy_storage.container_client.get_blob_client.return_value = dummy_blob_client
    dummy_blob_client.delete_blob = AsyncMock(side_effect=Exception("Delete error"))
    result = await dummy_storage.delete_file("blob.txt")
    assert result is False

@pytest.mark.asyncio
async def test_list_files_success(dummy_storage):
    dummy_storage.container_client = MagicMock()
    # Create two dummy blobs.
    blob1 = DummyBlob("file1.txt", 100, datetime(2023, 1, 1), "text/plain", {"a": "1"})
    blob2 = DummyBlob("file2.txt", 200, datetime(2023, 1, 2), "text/plain", {"b": "2"})
    async_iterator = DummyAsyncIterator([blob1, blob2])
    dummy_storage.container_client.list_blobs.return_value = async_iterator
    result = await dummy_storage.list_files("file")
    assert len(result) == 2
    names = {item["name"] for item in result}
    assert names == {"file1.txt", "file2.txt"}

@pytest.mark.asyncio
async def test_list_files_failure(dummy_storage):
    dummy_storage.container_client = MagicMock()
    # Define list_blobs to return an invalid object (simulate error)
    async def invalid_list_blobs(*args, **kwargs):
        # Return a plain string (which does not implement __aiter__)
        return "invalid"
    dummy_storage.container_client.list_blobs = invalid_list_blobs
    with pytest.raises(Exception):
        await dummy_storage.list_files("")

@pytest.mark.asyncio
async def test_close(dummy_storage):
    dummy_storage.service_client = MagicMock()
    dummy_storage.service_client.close = AsyncMock()
    await dummy_storage.close()
    dummy_storage.service_client.close.assert_awaited()
