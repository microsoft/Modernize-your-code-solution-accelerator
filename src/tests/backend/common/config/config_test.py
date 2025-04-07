import unittest
from unittest.mock import patch

# from config import Config
from common.config.config import Config


class TestConfigInitialization(unittest.TestCase):
    @patch.dict(
        "os.environ",
        {
            "AZURE_TENANT_ID": "test-tenant-id",
            "AZURE_CLIENT_ID": "test-client-id",
            "AZURE_CLIENT_SECRET": "test-client-secret",
            "COSMOSDB_DATABASE": "test-database",
            "COSMOSDB_BATCH_CONTAINER": "test-batch-container",
            "COSMOSDB_FILE_CONTAINER": "test-file-container",
            "COSMOSDB_LOG_CONTAINER": "test-log-container",
            "AZURE_BLOB_CONTAINER_NAME": "test-blob-container-name",
            "AZURE_BLOB_ACCOUNT_NAME": "test-blob-account-name",
        },
        clear=True,
    )
    def test_config_initialization(self):
        """Test if all attributes are correctly assigned from environment variables."""
        config = Config()

        # Ensure every attribute is accessed
        self.assertEqual(config.azure_tenant_id, "test-tenant-id")
        self.assertEqual(config.azure_client_id, "test-client-id")
        self.assertEqual(config.azure_client_secret, "test-client-secret")

        self.assertEqual(config.cosmosdb_endpoint, "test-cosmosdb-endpoint")
        self.assertEqual(config.cosmosdb_database, "test-database")
        self.assertEqual(config.cosmosdb_batch_container, "test-batch-container")
        self.assertEqual(config.cosmosdb_file_container, "test-file-container")
        self.assertEqual(config.cosmosdb_log_container, "test-log-container")

        self.assertEqual(config.azure_blob_container_name, "test-blob-container-name")
        self.assertEqual(config.azure_blob_account_name, "test-blob-account-name")

    @patch.dict(
        "os.environ",
        {
            "COSMOSDB_ENDPOINT": "test-cosmosdb-endpoint",
            "COSMOSDB_DATABASE": "test-database",
            "COSMOSDB_BATCH_CONTAINER": "test-batch-container",
            "COSMOSDB_FILE_CONTAINER": "test-file-container",
            "COSMOSDB_LOG_CONTAINER": "test-log-container",
        },
    )
    def test_cosmosdb_config_initialization(self):
        config = Config()
        self.assertEqual(config.cosmosdb_endpoint, "test-cosmosdb-endpoint")
        self.assertEqual(config.cosmosdb_database, "test-database")
        self.assertEqual(config.cosmosdb_batch_container, "test-batch-container")
        self.assertEqual(config.cosmosdb_file_container, "test-file-container")
        self.assertEqual(config.cosmosdb_log_container, "test-log-container")


if __name__ == "__main__":
    unittest.main()
