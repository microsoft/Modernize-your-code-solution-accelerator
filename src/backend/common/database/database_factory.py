import asyncio
from typing import Optional

from common.config.config import Config
from common.database.cosmosdb import CosmosDBClient
from common.database.database_base import DatabaseBase
from common.logger.app_logger import AppLogger


class DatabaseFactory:
    _instance: Optional[DatabaseBase] = None
    _lock: Optional[asyncio.Lock] = None
    _logger = AppLogger("DatabaseFactory")

    @staticmethod
    def _get_lock() -> asyncio.Lock:
        if DatabaseFactory._lock is None:
            DatabaseFactory._lock = asyncio.Lock()
        return DatabaseFactory._lock

    @staticmethod
    async def get_database():
        if DatabaseFactory._instance is not None:
            return DatabaseFactory._instance

        async with DatabaseFactory._get_lock():
            # Double-check after acquiring the lock
            if DatabaseFactory._instance is not None:
                return DatabaseFactory._instance

            config = Config()  # Create an instance of Config

            cosmos_db_client = CosmosDBClient(
                endpoint=config.cosmosdb_endpoint,
                credential=config.get_azure_credentials(),
                database_name=config.cosmosdb_database,
                batch_container=config.cosmosdb_batch_container,
                file_container=config.cosmosdb_file_container,
                log_container=config.cosmosdb_log_container,
            )

            await cosmos_db_client.initialize_cosmos()

            DatabaseFactory._instance = cosmos_db_client
            return cosmos_db_client


# Local testing of config and code
# Note that you have to assign yourself data plane access to Cosmos in script for this to work locally.  See
# https://learn.microsoft.com/en-us/azure/cosmos-db/table/security/how-to-grant-data-plane-role-based-access?tabs=built-in-definition%2Ccsharp&pivots=azure-interface-cli
# Note that your principal id is your entra object id for your user account.
async def main():
    database = await DatabaseFactory.get_database()
    await database.initialize_cosmos()
    await database.create_batch("mark1", "123e4567-e89b-12d3-a456-426614174000")
    await database.add_file(
        "123e4567-e89b-12d3-a456-426614174000",
        "123e4567-e89b-12d3-a456-426614174001",
        "q1_informix.sql",
        "https://cmsamarktaylstor.blob.core.windows.net/cmsablob",
    )
    tstbatch = await database.get_batch("mark1", "123e4567-e89b-12d3-a456-426614174000")
    print(tstbatch)
    await database.close()


if __name__ == "__main__":
    asyncio.run(main())
