from unittest.mock import MagicMock, patch


from common.storage.blob_factory import BlobStorageFactory


import pytest


@pytest.mark.asyncio
async def test_get_storage_logs_on_init():
    """Test that logger logs on initialization"""
    # Force reset the singleton before test
    BlobStorageFactory._instance = None

    mock_storage_instance = MagicMock()

    with patch("common.storage.blob_factory.AzureBlobStorage", return_value=mock_storage_instance), \
         patch("common.storage.blob_factory.Config") as mock_config, \
         patch.object(BlobStorageFactory, "_logger") as mock_logger:

        mock_config_instance = MagicMock()
        mock_config_instance.azure_blob_account_name = "account"
        mock_config_instance.azure_blob_container_name = "container"
        mock_config.return_value = mock_config_instance

        await BlobStorageFactory.get_storage()

        mock_logger.info.assert_called_once_with("Initialized Azure Blob Storage: container")


@pytest.mark.asyncio
async def test_close_storage_resets_instance():
    """Test that close_storage resets the singleton instance"""
    # Setup instance first
    mock_storage_instance = MagicMock()

    with patch("common.storage.blob_factory.AzureBlobStorage", return_value=mock_storage_instance), \
         patch("common.storage.blob_factory.Config") as mock_config:

        mock_config_instance = MagicMock()
        mock_config_instance.azure_blob_account_name = "account"
        mock_config_instance.azure_blob_container_name = "container"
        mock_config.return_value = mock_config_instance

        instance = await BlobStorageFactory.get_storage()
        assert instance is not None

        await BlobStorageFactory.close_storage()

        assert BlobStorageFactory._instance is None


@pytest.mark.asyncio
async def test_get_storage_after_close_reinitializes():
    """Test that get_storage reinitializes after close_storage is called"""
    # Force reset before test
    BlobStorageFactory._instance = None

    with patch("common.storage.blob_factory.AzureBlobStorage") as mock_storage, \
         patch("common.storage.blob_factory.Config") as mock_config:

        mock_storage.side_effect = [MagicMock(name="instance1"), MagicMock(name="instance2")]

        mock_config_instance = MagicMock()
        mock_config_instance.azure_blob_account_name = "account"
        mock_config_instance.azure_blob_container_name = "container"
        mock_config.return_value = mock_config_instance

        # First init
        instance1 = await BlobStorageFactory.get_storage()
        await BlobStorageFactory.close_storage()

        # Re-init
        instance2 = await BlobStorageFactory.get_storage()

        assert instance1 is not instance2
        assert mock_storage.call_count == 2
