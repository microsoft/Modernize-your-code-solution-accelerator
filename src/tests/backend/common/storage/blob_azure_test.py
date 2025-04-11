import json
import os
import sys
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from io import BytesIO

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..', 'backend')))

from common.storage.blob_azure import AzureBlobStorage


@pytest.fixture
def mock_blob_service():
    """Fixture to mock Azure Blob Storage service client"""
    with patch("common.storage.blob_azure.BlobServiceClient") as mock_service:
        mock_service_instance = MagicMock()
        mock_container_client = MagicMock()
        mock_blob_client = MagicMock()

        # Set up mock methods
        mock_service.return_value = mock_service_instance
        mock_service_instance.get_container_client.return_value = mock_container_client
        mock_container_client.get_blob_client.return_value = mock_blob_client

        yield mock_service_instance, mock_container_client, mock_blob_client


@pytest.fixture
def blob_storage(mock_blob_service):
    """Fixture to initialize AzureBlobStorage with mocked dependencies"""
    service_client, container_client, blob_client = mock_blob_service
    return AzureBlobStorage(account_name="test_account", container_name="test_container")


@pytest.mark.asyncio
async def test_upload_file(blob_storage, mock_blob_service):
    """Test uploading a file"""
    _, _, mock_blob_client = mock_blob_service
    mock_blob_client.upload_blob.return_value = MagicMock()
    mock_blob_client.get_blob_properties.return_value = MagicMock(
        size=1024,
        content_settings=MagicMock(content_type="text/plain"),
        creation_time="2024-03-15T12:00:00Z",
        etag="dummy_etag",
    )

    file_content = BytesIO(b"dummy data")

    result = await blob_storage.upload_file(file_content, "test_blob.txt", "text/plain")

    assert result["path"] == "test_blob.txt"
    assert result["size"] == 1024
    assert result["content_type"] == "text/plain"
    assert result["created_at"] == "2024-03-15T12:00:00Z"
    assert result["etag"] == "dummy_etag"
    assert "url" in result


@pytest.mark.asyncio
async def test_upload_file_exception(blob_storage, mock_blob_service):
    """Test upload_file when an exception occurs"""
    _, _, mock_blob_client = mock_blob_service
    mock_blob_client.upload_blob.side_effect = Exception("Upload failed")

    with pytest.raises(Exception, match="Upload failed"):
        await blob_storage.upload_file(BytesIO(b"dummy data"), "test_blob.txt")


@pytest.mark.asyncio
async def test_get_file(blob_storage, mock_blob_service):
    """Test downloading a file"""
    _, _, mock_blob_client = mock_blob_service
    mock_blob_client.download_blob.return_value.readall.return_value = b"dummy data"

    result = await blob_storage.get_file("test_blob.txt")

    assert result == "dummy data"


@pytest.mark.asyncio
async def test_get_file_exception(blob_storage, mock_blob_service):
    """Test get_file when an exception occurs"""
    _, _, mock_blob_client = mock_blob_service
    mock_blob_client.download_blob.side_effect = Exception("Download failed")

    with pytest.raises(Exception, match="Download failed"):
        await blob_storage.get_file("test_blob.txt")


@pytest.mark.asyncio
async def test_delete_file(blob_storage, mock_blob_service):
    """Test deleting a file"""
    _, _, mock_blob_client = mock_blob_service
    mock_blob_client.delete_blob.return_value = None

    result = await blob_storage.delete_file("test_blob.txt")

    assert result is True


@pytest.mark.asyncio
async def test_delete_file_exception(blob_storage, mock_blob_service):
    """Test delete_file when an exception occurs"""
    _, _, mock_blob_client = mock_blob_service
    mock_blob_client.delete_blob.side_effect = Exception("Delete failed")

    result = await blob_storage.delete_file("test_blob.txt")

    assert result is False


@pytest.mark.asyncio
async def test_list_files(blob_storage, mock_blob_service):
    """Test listing files in a container"""
    _, mock_container_client, _ = mock_blob_service

    class AsyncIterator:
        """Helper class to create an async iterator"""
        def __init__(self, items):
            self._items = items

        def __aiter__(self):
            self._iter = iter(self._items)
            return self

        async def __anext__(self):
            try:
                return next(self._iter)
            except StopIteration:
                raise StopAsyncIteration

    mock_blobs = [
        MagicMock(name="file1.txt"),
        MagicMock(name="file2.txt"),
    ]

    # Explicitly set attributes to avoid MagicMock issues
    mock_blobs[0].name = "file1.txt"
    mock_blobs[0].size = 123
    mock_blobs[0].creation_time = "2024-03-15T12:00:00Z"
    mock_blobs[0].content_settings = MagicMock(content_type="text/plain")
    mock_blobs[0].metadata = {}

    mock_blobs[1].name = "file2.txt"
    mock_blobs[1].size = 456
    mock_blobs[1].creation_time = "2024-03-16T12:00:00Z"
    mock_blobs[1].content_settings = MagicMock(content_type="application/json")
    mock_blobs[1].metadata = {}

    mock_container_client.list_blobs = MagicMock(return_value=AsyncIterator(mock_blobs))

    result = await blob_storage.list_files()

    assert len(result) == 2
    assert result[0]["name"] == "file1.txt"
    assert result[0]["size"] == 123
    assert result[0]["created_at"] == "2024-03-15T12:00:00Z"
    assert result[0]["content_type"] == "text/plain"
    assert result[0]["metadata"] == {}

    assert result[1]["name"] == "file2.txt"
    assert result[1]["size"] == 456
    assert result[1]["created_at"] == "2024-03-16T12:00:00Z"
    assert result[1]["content_type"] == "application/json"
    assert result[1]["metadata"] == {}


@pytest.mark.asyncio
async def test_list_files_exception(blob_storage, mock_blob_service):
    """Test list_files when an exception occurs"""
    _, mock_container_client, _ = mock_blob_service
    mock_container_client.list_blobs.side_effect = Exception("List failed")

    with pytest.raises(Exception, match="List failed"):
        await blob_storage.list_files()


@pytest.mark.asyncio
async def test_close(blob_storage, mock_blob_service):
    """Test closing the storage client"""
    service_client, _, _ = mock_blob_service

    await blob_storage.close()

    service_client.close.assert_called_once()

@pytest.mark.asyncio
async def test_blob_storage_init_exception():
    """Test that an exception during initialization logs the error message"""
    with patch("common.storage.blob_azure.BlobServiceClient") as mock_service, \
         patch("logging.getLogger") as mock_logger:  # Patch logging globally

        # Mock logger instance
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        # Simulate an exception when creating BlobServiceClient
        mock_service.side_effect = Exception("Connection failed")

        # Try to initialize AzureBlobStorage
        try:
            AzureBlobStorage(account_name="test_account", container_name="test_container")
        except Exception:
            pass  # Prevent test failure due to the exception

        # Construct the expected JSON log format
        expected_error_log = json.dumps({
            "message": "Failed to initialize Azure Blob Storage",
            "context": {
                "error": "Connection failed",
                "account_name": "test_account"
            }
        })

        expected_debug_log = json.dumps({
            "message": "Container test_container already exists"
        })

        # Assert that error logging happened with the expected JSON string
        mock_logger_instance.error.assert_called_once_with(expected_error_log)

        # Assert that debug log is written for container existence
        mock_logger_instance.debug.assert_called_once_with(expected_debug_log)