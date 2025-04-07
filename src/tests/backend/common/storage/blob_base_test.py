from datetime import datetime
from typing import Any, BinaryIO, Dict

# Import the abstract base class from the production code.
from common.storage.blob_base import BlobStorageBase

import pytest
# Create a dummy concrete subclass of BlobStorageBase that calls the parent's abstract methods.


class DummyBlobStorage(BlobStorageBase):
    async def initialize(self) -> None:
        # Call the parent (which is just a pass)
        await super().initialize()
        # Return a dummy value so we can verify our override is called.
        return "initialized"

    async def upload_file(
        self,
        file_content: BinaryIO,
        blob_path: str,
        content_type: str = None,
        metadata: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        await super().upload_file(file_content, blob_path, content_type, metadata)
        # Return a dummy dictionary that simulates upload details.
        return {
            "url": "https://dummy.blob.core.windows.net/dummy_container/" + blob_path,
            "size": len(file_content),
            "etag": "dummy_etag",
        }

    async def get_file(self, blob_path: str) -> BinaryIO:
        await super().get_file(blob_path)
        # Return dummy binary content.
        return b"dummy content"

    async def delete_file(self, blob_path: str) -> bool:
        await super().delete_file(blob_path)
        # Simulate a successful deletion.
        return True

    async def list_files(self, prefix: str = None) -> list[Dict[str, Any]]:
        await super().list_files(prefix)
        return [
            {
                "name": "dummy.txt",
                "size": 123,
                "created_at": datetime.now(),
                "content_type": "text/plain",
                "metadata": {"dummy": "value"},
            }
        ]


# tests cases with each method.


@pytest.mark.asyncio
async def test_initialize():
    storage = DummyBlobStorage()
    result = await storage.initialize()
    # Since the dummy override returns "initialized" after calling super(),
    # we assert that the result equals that string.
    assert result == "initialized"


@pytest.mark.asyncio
async def test_upload_file():
    storage = DummyBlobStorage()
    content = b"hello world"
    blob_path = "folder/hello.txt"
    content_type = "text/plain"
    metadata = {"key": "value"}
    result = await storage.upload_file(content, blob_path, content_type, metadata)
    # Verify that our dummy return value is as expected.
    assert (
        result["url"]
        == "https://dummy.blob.core.windows.net/dummy_container/" + blob_path
    )
    assert result["size"] == len(content)
    assert result["etag"] == "dummy_etag"


@pytest.mark.asyncio
async def test_get_file():
    storage = DummyBlobStorage()
    result = await storage.get_file("folder/hello.txt")
    # Verify that we get the dummy binary content.
    assert result == b"dummy content"


@pytest.mark.asyncio
async def test_delete_file():
    storage = DummyBlobStorage()
    result = await storage.delete_file("folder/hello.txt")
    # Verify that deletion returns True.
    assert result is True


@pytest.mark.asyncio
async def test_list_files():
    storage = DummyBlobStorage()
    result = await storage.list_files("dummy")
    # Verify that we receive a list with one item having a 'name' key.
    assert isinstance(result, list)
    assert len(result) == 1
    assert "dummy.txt" in result[0]["name"]
    assert result[0]["size"] == 123
    assert result[0]["content_type"] == "text/plain"
    assert result[0]["metadata"] == {"dummy": "value"}


@pytest.mark.asyncio
async def test_smoke_all_methods():
    storage = DummyBlobStorage()
    init_val = await storage.initialize()
    assert init_val == "initialized"
    upload_val = await storage.upload_file(
        b"data", "file.txt", "text/plain", {"a": "b"}
    )
    assert upload_val["size"] == 4
    file_val = await storage.get_file("file.txt")
    assert file_val == b"dummy content"
    delete_val = await storage.delete_file("file.txt")
    assert delete_val is True
    list_val = await storage.list_files("file")
    assert isinstance(list_val, list)
