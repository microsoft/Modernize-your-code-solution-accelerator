from unittest.mock import AsyncMock, patch


import pytest


@pytest.fixture(autouse=True)
def patch_config(monkeypatch):
    """Patch Config class to use dummy values."""
    from common.config.config import Config

    def dummy_init(self):
        """Mocked __init__ method for Config to set dummy values."""
        self.cosmosdb_endpoint = "dummy_endpoint"
        self.cosmosdb_database = "dummy_database"
        self.cosmosdb_batch_container = "dummy_batch"
        self.cosmosdb_file_container = "dummy_file"
        self.cosmosdb_log_container = "dummy_log"
        self.get_azure_credentials = lambda: "dummy_credential"

    monkeypatch.setattr(Config, "__init__", dummy_init)  # Replace the init method


@pytest.fixture(autouse=True)
def patch_cosmosdb_client(monkeypatch):
    """Patch CosmosDBClient to use a dummy implementation."""

    class DummyCosmosDBClient:
        def __init__(self, endpoint, credential, database_name, batch_container, file_container, log_container):
            self.endpoint = endpoint
            self.credential = credential
            self.database_name = database_name
            self.batch_container = batch_container
            self.file_container = file_container
            self.log_container = log_container

        async def initialize_cosmos(self):
            pass

        async def create_batch(self, *args, **kwargs):
            pass

        async def add_file(self, *args, **kwargs):
            pass

        async def get_batch(self, *args, **kwargs):
            return "mock_batch"

        async def close(self):
            pass

    monkeypatch.setattr("common.database.database_factory.CosmosDBClient", DummyCosmosDBClient)


@pytest.mark.asyncio
async def test_get_database():
    """Test database retrieval using the factory."""
    from common.database.database_factory import DatabaseFactory

    db_instance = await DatabaseFactory.get_database()

    assert db_instance.endpoint == "dummy_endpoint"
    assert db_instance.credential == "dummy_credential"
    assert db_instance.database_name == "dummy_database"
    assert db_instance.batch_container == "dummy_batch"
    assert db_instance.file_container == "dummy_file"
    assert db_instance.log_container == "dummy_log"


@pytest.mark.asyncio
async def test_main_function():
    """Test the main function in database factory."""
    with patch("common.database.database_factory.DatabaseFactory.get_database", new_callable=AsyncMock, return_value=AsyncMock()) as mock_get_database, patch("builtins.print") as mock_print:
      
        from common.database.database_factory import main
        await main()

        mock_get_database.assert_called_once()
        mock_print.assert_called()  # Ensures print is executed
