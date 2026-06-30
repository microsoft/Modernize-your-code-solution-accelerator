import pytest


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    # Clear environment variables that might affect tests.
    keys = [
        "AZURE_TENANT_ID",
        "AZURE_CLIENT_ID",
        "AZURE_CLIENT_SECRET",
        "COSMOSDB_ENDPOINT",
        "COSMOSDB_DATABASE",
        "COSMOSDB_BATCH_CONTAINER",
        "COSMOSDB_FILE_CONTAINER",
        "COSMOSDB_LOG_CONTAINER",
        "AZURE_BLOB_CONTAINER_NAME",
        "AZURE_BLOB_ACCOUNT_NAME",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def test_config_initialization(monkeypatch):
    # Set the full configuration environment variables.
    monkeypatch.setenv("AZURE_TENANT_ID", "test-tenant-id")
    monkeypatch.setenv("AZURE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("COSMOSDB_ENDPOINT", "test-cosmosdb-endpoint")
    monkeypatch.setenv("COSMOSDB_DATABASE", "test-database")
    monkeypatch.setenv("COSMOSDB_BATCH_CONTAINER", "test-batch-container")
    monkeypatch.setenv("COSMOSDB_FILE_CONTAINER", "test-file-container")
    monkeypatch.setenv("COSMOSDB_LOG_CONTAINER", "test-log-container")
    monkeypatch.setenv("AZURE_BLOB_CONTAINER_NAME", "test-blob-container-name")
    monkeypatch.setenv("AZURE_BLOB_ACCOUNT_NAME", "test-blob-account-name")

    # Local import to avoid triggering circular imports during module collection.
    from common.config.config import Config
    config = Config()

    assert config.azure_tenant_id == "test-tenant-id"
    assert config.azure_client_id == "test-client-id"
    assert config.azure_client_secret == "test-client-secret"
    assert config.cosmosdb_endpoint == "test-cosmosdb-endpoint"
    assert config.cosmosdb_database == "test-database"
    assert config.cosmosdb_batch_container == "test-batch-container"
    assert config.cosmosdb_file_container == "test-file-container"
    assert config.cosmosdb_log_container == "test-log-container"
    assert config.azure_blob_container_name == "test-blob-container-name"
    assert config.azure_blob_account_name == "test-blob-account-name"


def test_cosmosdb_config_initialization(monkeypatch):
    # Set only cosmosdb-related environment variables.
    monkeypatch.setenv("COSMOSDB_ENDPOINT", "test-cosmosdb-endpoint")
    monkeypatch.setenv("COSMOSDB_DATABASE", "test-database")
    monkeypatch.setenv("COSMOSDB_BATCH_CONTAINER", "test-batch-container")
    monkeypatch.setenv("COSMOSDB_FILE_CONTAINER", "test-file-container")
    monkeypatch.setenv("COSMOSDB_LOG_CONTAINER", "test-log-container")

    from common.config.config import Config
    config = Config()

    assert config.cosmosdb_endpoint == "test-cosmosdb-endpoint"
    assert config.cosmosdb_database == "test-database"
    assert config.cosmosdb_batch_container == "test-batch-container"
    assert config.cosmosdb_file_container == "test-file-container"
    assert config.cosmosdb_log_container == "test-log-container"
