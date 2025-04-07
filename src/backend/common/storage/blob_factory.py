from typing import Optional

from common.config.config import Config  # Load config
from common.logger.app_logger import AppLogger
from common.storage.blob_azure import AzureBlobStorage
from common.storage.blob_base import BlobStorageBase


class BlobStorageFactory:
    _instance: Optional[BlobStorageBase] = None
    _logger = AppLogger("BlobStorageFactory")

    @staticmethod
    async def get_storage() -> BlobStorageBase:
        if BlobStorageFactory._instance is None:
            config = Config()

            BlobStorageFactory._instance = AzureBlobStorage(
                account_name=config.azure_blob_account_name,
                container_name=config.azure_blob_container_name,
            )
            BlobStorageFactory._logger.info(
                f"Initialized Azure Blob Storage: {config.azure_blob_container_name}"
            )
        return BlobStorageFactory._instance

    @staticmethod
    async def close_storage() -> None:
        if BlobStorageFactory._instance:
            BlobStorageFactory._instance = None


# Local testing of config and code
if __name__ == "__main__":
    # Example usage
    import asyncio

    async def main():
        storage = await BlobStorageFactory.get_storage()
        # Use the storage instance...
        blob = await storage.get_file("q1_informix.sql")
        print(blob)
        await BlobStorageFactory.close_storage()

    asyncio.run(main())
