from abc import ABC, abstractmethod
from typing import Any, BinaryIO, Dict, Optional


class BlobStorageBase(ABC):
    """Abstract base class for blob storage operations."""

    @abstractmethod
    async def upload_file(
        self,
        file_content: BinaryIO,
        blob_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to blob storage.

        Args:
            file_content: The file content to upload
            blob_path: The path where to store the blob
            content_type: Optional content type of the file
            metadata: Optional metadata to store with the blob

        Returns:
            Dict containing upload details (url, size, etc.)
        """
        pass

    @abstractmethod
    async def get_file(self, blob_path: str) -> BinaryIO:
        """
        Retrieve a file from blob storage.

        Args:
            blob_path: Path to the blob

        Returns:
            File content as a binary stream
        """
        pass

    @abstractmethod
    async def delete_file(self, blob_path: str) -> bool:
        """
        Delete a file from blob storage.

        Args:
            blob_path: Path to the blob to delete

        Returns:
            True if deletion was successful
        """
        pass

    @abstractmethod
    async def list_files(self, prefix: Optional[str] = None) -> list[Dict[str, Any]]:
        """
        List files in blob storage.

        Args:
            prefix: Optional prefix to filter blobs

        Returns:
            List of blob details
        """
        pass
