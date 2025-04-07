from common.config.config import Config
from common.database.database_factory import DatabaseFactory

import pytest


class DummyConfig:
    cosmosdb_endpoint = "dummy_endpoint"
    cosmosdb_database = "dummy_database"
    cosmosdb_batch_container = "dummy_batch"
    cosmosdb_file_container = "dummy_file"
    cosmosdb_log_container = "dummy_log"


class DummyCosmosDBClient:
    def __init__(self, endpoint, credential, database_name, batch_container, file_container, log_container):
        self.endpoint = endpoint
        self.credential = credential
        self.database_name = database_name
        self.batch_container = batch_container
        self.file_container = file_container
        self.log_container = log_container


def dummy_config_init(self):
    self.cosmosdb_endpoint = DummyConfig.cosmosdb_endpoint
    self.cosmosdb_database = DummyConfig.cosmosdb_database
    self.cosmosdb_batch_container = DummyConfig.cosmosdb_batch_container
    self.cosmosdb_file_container = DummyConfig.cosmosdb_file_container
    self.cosmosdb_log_container = DummyConfig.cosmosdb_log_container
    # Provide a dummy method for credentials.
    self.get_azure_credentials = lambda: "dummy_credential"


@pytest.fixture(autouse=True)
def patch_config(monkeypatch):
    # Patch the __init__ of Config so that an instance will have the required attributes.
    monkeypatch.setattr(Config, "__init__", dummy_config_init)


@pytest.fixture(autouse=True)
def patch_cosmosdb_client(monkeypatch):
    # Patch CosmosDBClient in the module under test to use our dummy client.
    monkeypatch.setattr("common.database.database_factory.CosmosDBClient", DummyCosmosDBClient)


def test_get_database():
    """
    Test that DatabaseFactory.get_database() correctly returns an instance of the.

    dummy CosmosDB client with the expected configuration values.
    """
    # When get_database() is called, it creates a new Config() instance.
    db_instance = DatabaseFactory.get_database()

    # Verify that the returned instance is our dummy client with the expected attributes.
    assert isinstance(db_instance, DummyCosmosDBClient)
    assert db_instance.endpoint == DummyConfig.cosmosdb_endpoint
    assert db_instance.credential == "dummy_credential"
    assert db_instance.database_name == DummyConfig.cosmosdb_database
    assert db_instance.batch_container == DummyConfig.cosmosdb_batch_container
    assert db_instance.file_container == DummyConfig.cosmosdb_file_container
    assert db_instance.log_container == DummyConfig.cosmosdb_log_container
