from typing import Any, BinaryIO, Dict, Optional

from helper.azure_credential_utils import get_azure_credential
from azure.storage.blob import BlobServiceClient

from common.logger.app_logger import AppLogger
from common.storage.blob_base import BlobStorageBase


class AzureBlobStorage(BlobStorageBase):
    def __init__(self, account_name: str, container_name: Optional[str] = None):
        self.logger = AppLogger("AzureBlobStorage")
        try:
            self.account_name = account_name
            self.container_name = container_name
            self.service_client = None
            self.container_client = None
            credential = get_azure_credential()  # Using Managed Identity Authentication
            self.service_client = BlobServiceClient(
                account_url=f"https://{self.account_name}.blob.core.windows.net/",
                credential=credential,
            )

            self.container_client = self.service_client.get_container_client(
                self.container_name
            )

            # self.logger.info(f"Created container: {self.container_name}")
        except Exception as e:
            self.logger.error(
                "Failed to initialize Azure Blob Storage",
                error=str(e),
                account_name=account_name,
            )
            self.logger.debug(f"Container {self.container_name} already exists")

    async def upload_file(
        self,
        file_content: BinaryIO,
        blob_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Upload a file to Azure Blob Storage."""
        try:
            blob_client = self.container_client.get_blob_client(blob_path)

        except Exception as e:
            self.logger.error(".get_blob_client", error=str(e), blob_path=blob_path)
            raise
        try:
            # Upload the file
            upload_results = blob_client.upload_blob(  # noqa: F841
                file_content,
                content_type=content_type,
                metadata=metadata,
                overwrite=True,
            )
        except Exception as e:
            self.logger.error("upload_blob", error=str(e), blob_path=blob_path)
            raise
        try:

            # Get blob properties
            properties = blob_client.get_blob_properties()

            return {
                "path": blob_path,
                "size": properties.size,
                "content_type": properties.content_settings.content_type,
                "created_at": properties.creation_time,
                "url": blob_client.url,
                "etag": properties.etag,
            }
        except Exception as e:
            self.logger.error("get_blob_properties", error=str(e), blob_path=blob_path)
            raise

    async def get_file(self, blob_path: str) -> BinaryIO:
        """Download a file from Azure Blob Storage."""
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            download_stream = blob_client.download_blob()
            file_bytes = download_stream.readall()
            # using utf-8-sig to remove BOM - Byte Order Mark
            # this also screens out non text utf-8 files

            return file_bytes.decode("utf-8-sig")

        except Exception as e:
            self.logger.error(
                "Failed to download file", error=str(e), blob_path=blob_path
            )
            raise

    async def delete_file(self, blob_path: str) -> bool:
        """Delete a file from Azure Blob Storage."""
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            blob_client.delete_blob()
            return True

        except Exception as e:
            self.logger.error(
                "Failed to delete file", error=str(e), blob_path=blob_path
            )
            return False

    async def list_files(self, prefix: Optional[str] = None) -> list[Dict[str, Any]]:
        """List files in Azure Blob Storage."""
        try:
            blobs = []
            async for blob in self.container_client.list_blobs(name_starts_with=prefix):
                blobs.append(
                    {
                        "name": blob.name,
                        "size": blob.size,
                        "created_at": blob.creation_time,
                        "content_type": blob.content_settings.content_type,
                        "metadata": blob.metadata,
                    }
                )
            return blobs

        except Exception as e:
            self.logger.error("Failed to list files", error=str(e), prefix=prefix)
            raise

    async def close(self) -> None:
        """Close blob storage connections."""
        if self.service_client:
            self.service_client.close()
            self.logger.info("Closed blob storage connection")
