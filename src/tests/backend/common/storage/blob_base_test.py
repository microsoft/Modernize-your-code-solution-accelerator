from io import BytesIO
from typing import Any, BinaryIO, Dict, Optional


from common.storage.blob_base import BlobStorageBase  # Adjust import path as needed


import pytest


class MockBlobStorage(BlobStorageBase):
    """Mock implementation of BlobStorageBase for testing"""

    async def upload_file(
        self,
        file_content: BinaryIO,
        blob_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        return {
            "path": blob_path,
            "size": len(file_content.read()),
            "content_type": content_type or "application/octet-stream",
            "metadata": metadata or {},
            "url": f"https://mockstorage.com/{blob_path}",
        }

    async def get_file(self, blob_path: str) -> BinaryIO:
        return BytesIO(b"mock data")

    async def delete_file(self, blob_path: str) -> bool:
        return True

    async def list_files(self, prefix: Optional[str] = None) -> list[Dict[str, Any]]:
        return [
            {"name": "file1.txt", "size": 100, "content_type": "text/plain"},
            {"name": "file2.jpg", "size": 200, "content_type": "image/jpeg"},
        ]


@pytest.fixture
def mock_blob_storage():
    """Fixture to provide a MockBlobStorage instance"""
    return MockBlobStorage()


@pytest.mark.asyncio
async def test_upload_file(mock_blob_storage):
    """Test upload_file method"""
    file_content = BytesIO(b"dummy data")
    result = await mock_blob_storage.upload_file(file_content, "test_blob.txt", "text/plain")

    assert result["path"] == "test_blob.txt"
    assert result["size"] == len(b"dummy data")
    assert result["content_type"] == "text/plain"
    assert "url" in result


@pytest.mark.asyncio
async def test_get_file(mock_blob_storage):
    """Test get_file method"""
    result = await mock_blob_storage.get_file("test_blob.txt")

    assert isinstance(result, BytesIO)
    assert result.read() == b"mock data"


@pytest.mark.asyncio
async def test_delete_file(mock_blob_storage):
    """Test delete_file method"""
    result = await mock_blob_storage.delete_file("test_blob.txt")

    assert result is True


@pytest.mark.asyncio
async def test_list_files(mock_blob_storage):
    """Test list_files method"""
    result = await mock_blob_storage.list_files()

    assert len(result) == 2
    assert result[0]["name"] == "file1.txt"
    assert result[1]["name"] == "file2.jpg"
    assert result[0]["size"] == 100
    assert result[1]["size"] == 200
