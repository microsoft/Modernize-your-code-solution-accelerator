# blob_factory_test.py
import asyncio
import json
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Adjust sys.path so that the project root is found.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# Set required environment variables (dummy values)
os.environ["COSMOSDB_ENDPOINT"] = "https://dummy-endpoint"
os.environ["COSMOSDB_KEY"] = "dummy-key"
os.environ["COSMOSDB_DATABASE"] = "dummy-database"
os.environ["COSMOSDB_CONTAINER"] = "dummy-container"
os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "dummy-deployment"
os.environ["AZURE_OPENAI_API_VERSION"] = "2023-01-01"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://dummy-openai-endpoint"

# Patch missing azure module so that event_utils imports without error.
sys.modules["azure.monitor.events.extension"] = MagicMock()

# --- Import the module under test ---
from common.storage.blob_factory import BlobStorageFactory
from common.storage.blob_base import BlobStorageBase
from common.storage.blob_azure import AzureBlobStorage

# --- Dummy configuration for testing ---
class DummyConfig:
    azure_blob_connection_string = "dummy_connection_string"
    azure_blob_container_name = "dummy_container"

# --- Fixture to patch Config in our tests ---
@pytest.fixture(autouse=True)
def patch_config(monkeypatch):
    # Import the real Config from your project.
    from common.config.config import Config
    
    def dummy_init(self):
        self.azure_blob_connection_string = DummyConfig.azure_blob_connection_string
        self.azure_blob_container_name = DummyConfig.azure_blob_container_name
    monkeypatch.setattr(Config, "__init__", dummy_init)
    # Reset the BlobStorageFactory singleton before each test.
    BlobStorageFactory._instance = None


class DummyAzureBlobStorage(BlobStorageBase):
    def __init__(self, connection_string: str, container_name: str):
        self.connection_string = connection_string
        self.container_name = container_name
        self.initialized = False
        self.files = {}  # maps blob_path to tuple(file_content, content_type, metadata)

    async def initialize(self):
        self.initialized = True

    async def upload_file(self, file_content: bytes, blob_path: str, content_type: str, metadata: dict):
        self.files[blob_path] = (file_content, content_type, metadata)
        return {
            "url": f"https://dummy.blob.core.windows.net/{self.container_name}/{blob_path}",
            "size": len(file_content),
            "etag": "dummy_etag"
        }

    async def get_file(self, blob_path: str):
        if blob_path in self.files:
            return self.files[blob_path][0]
        else:
            raise FileNotFoundError(f"File {blob_path} not found")

    async def delete_file(self, blob_path: str):
        if blob_path in self.files:
            del self.files[blob_path]
        # No error if file does not exist.

    async def list_files(self, prefix: str = ""):
        return [path for path in self.files if path.startswith(prefix)]

    async def close(self):
        self.initialized = False

# --- Fixture to patch AzureBlobStorage ---
@pytest.fixture(autouse=True)
def patch_azure_blob_storage(monkeypatch):
    monkeypatch.setattr("common.storage.blob_factory.AzureBlobStorage", DummyAzureBlobStorage)
    BlobStorageFactory._instance = None

# -------------------- Tests for BlobStorageFactory --------------------

@pytest.mark.asyncio
async def test_get_storage_success():
    """Test that get_storage returns an initialized DummyAzureBlobStorage instance and is a singleton."""
    storage = await BlobStorageFactory.get_storage()
    assert isinstance(storage, DummyAzureBlobStorage)
    assert storage.initialized is True

    # Call get_storage again; it should return the same instance.
    storage2 = await BlobStorageFactory.get_storage()
    assert storage is storage2

@pytest.mark.asyncio
async def test_get_storage_missing_config(monkeypatch):
    """
    Test that get_storage raises a ValueError when configuration is missing.
    We simulate missing connection string and container name.
    """
    from common.config.config import Config
    def dummy_init_missing(self):
        self.azure_blob_connection_string = ""
        self.azure_blob_container_name = ""
    monkeypatch.setattr(Config, "__init__", dummy_init_missing)
    with pytest.raises(ValueError, match="Azure Blob Storage configuration is missing"):
        await BlobStorageFactory.get_storage()

@pytest.mark.asyncio
async def test_close_storage_success():
    """Test that close_storage calls close() on the storage instance and resets the singleton."""
    storage = await BlobStorageFactory.get_storage()
    # Patch close() method with an async mock.
    storage.close = AsyncMock()
    await BlobStorageFactory.close_storage()
    storage.close.assert_called_once()
    assert BlobStorageFactory._instance is None

# -------------------- File Upload Tests --------------------

@pytest.mark.asyncio
async def test_upload_file_success():
    """Test that upload_file successfully uploads a file and returns metadata."""
    storage = DummyAzureBlobStorage("dummy", "container")
    await storage.initialize()
    file_content = b"Hello, Blob!"
    blob_path = "folder/blob.txt"
    content_type = "text/plain"
    metadata = {"meta": "data"}
    result = await storage.upload_file(file_content, blob_path, content_type, metadata)
    assert "url" in result
    assert result["size"] == len(file_content)
    assert blob_path in storage.files

@pytest.mark.asyncio
async def test_upload_file_error(monkeypatch):
    """Test that an exception during file upload is propagated."""
    storage = DummyAzureBlobStorage("dummy", "container")
    await storage.initialize()
    monkeypatch.setattr(storage, "upload_file", AsyncMock(side_effect=Exception("Upload failed")))
    with pytest.raises(Exception, match="Upload failed"):
        await storage.upload_file(b"data", "file.txt", "text/plain", {})

# -------------------- File Retrieval Tests --------------------

@pytest.mark.asyncio
async def test_get_file_success():
    """Test that get_file retrieves the correct file content."""
    storage = DummyAzureBlobStorage("dummy", "container")
    await storage.initialize()
    blob_path = "folder/data.bin"
    file_content = b"BinaryData"
    storage.files[blob_path] = (file_content, "application/octet-stream", {})
    result = await storage.get_file(blob_path)
    assert result == file_content

@pytest.mark.asyncio
async def test_get_file_not_found():
    """Test that get_file raises FileNotFoundError when file does not exist."""
    storage = DummyAzureBlobStorage("dummy", "container")
    await storage.initialize()
    with pytest.raises(FileNotFoundError):
        await storage.get_file("nonexistent.file")

# -------------------- File Deletion Tests --------------------

@pytest.mark.asyncio
async def test_delete_file_success():
    """Test that delete_file removes an existing file."""
    storage = DummyAzureBlobStorage("dummy", "container")
    await storage.initialize()
    blob_path = "folder/remove.txt"
    storage.files[blob_path] = (b"To remove", "text/plain", {})
    await storage.delete_file(blob_path)
    assert blob_path not in storage.files

@pytest.mark.asyncio
async def test_delete_file_nonexistent():
    """Test that deleting a non-existent file does not raise an error."""
    storage = DummyAzureBlobStorage("dummy", "container")
    await storage.initialize()
    # Should not raise any exception.
    await storage.delete_file("nonexistent.file")
    assert True

# -------------------- File Listing Tests --------------------

@pytest.mark.asyncio
async def test_list_files_with_prefix():
    """Test that list_files returns files that match the given prefix."""
    storage = DummyAzureBlobStorage("dummy", "container")
    await storage.initialize()
    storage.files = {
        "folder/a.txt": (b"A", "text/plain", {}),
        "folder/b.txt": (b"B", "text/plain", {}),
        "other/c.txt": (b"C", "text/plain", {}),
    }
    result = await storage.list_files("folder/")
    assert set(result) == {"folder/a.txt", "folder/b.txt"}

@pytest.mark.asyncio
async def test_list_files_no_files():
    """Test that list_files returns an empty list when no files match the prefix."""
    storage = DummyAzureBlobStorage("dummy", "container")
    await storage.initialize()
    storage.files = {}
    result = await storage.list_files("prefix/")
    assert result == []

# -------------------- Additional Basic Tests --------------------

@pytest.mark.asyncio
async def test_dummy_azure_blob_storage_initialize():
    """Test that initializing DummyAzureBlobStorage sets the initialized flag."""
    storage = DummyAzureBlobStorage("dummy_conn", "dummy_container")
    assert storage.initialized is False
    await storage.initialize()
    assert storage.initialized is True

@pytest.mark.asyncio
async def test_dummy_azure_blob_storage_upload_and_retrieve():
    """Test that a file uploaded to DummyAzureBlobStorage can be retrieved."""
    storage = DummyAzureBlobStorage("dummy_conn", "dummy_container")
    await storage.initialize()
    content = b"Sample file content"
    blob_path = "folder/sample.txt"
    metadata = {"author": "tester"}
    result = await storage.upload_file(content, blob_path, "text/plain", metadata)
    assert "url" in result
    assert result["size"] == len(content)
    retrieved = await storage.get_file(blob_path)
    assert retrieved == content

@pytest.mark.asyncio
async def test_dummy_azure_blob_storage_close():
    """Test that close() sets initialized to False."""
    storage = DummyAzureBlobStorage("dummy_conn", "dummy_container")
    await storage.initialize()
    await storage.close()
    assert storage.initialized is False

# -------------------- Test for BlobStorageFactory Singleton Usage --------------------

def test_common_usage_of_blob_factory():
    """Test that manually setting the singleton in BlobStorageFactory works as expected."""
    # Create a dummy storage instance.
    dummy_storage = DummyAzureBlobStorage("dummy", "container")
    dummy_storage.initialized = True
    BlobStorageFactory._instance = dummy_storage
    storage = asyncio.run(BlobStorageFactory.get_storage())
    assert storage is dummy_storage

if __name__ == "__main__":
    # Run tests when this file is executed directly.
    asyncio.run(pytest.main())
