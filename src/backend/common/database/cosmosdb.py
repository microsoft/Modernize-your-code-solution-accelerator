from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from azure.cosmos.aio import CosmosClient
from azure.cosmos.aio._database import DatabaseProxy
from azure.cosmos.exceptions import (
    CosmosResourceExistsError
)

from common.database.database_base import DatabaseBase
from common.logger.app_logger import AppLogger
from common.models.api import (
    AgentType,
    BatchRecord,
    FileLog,
    FileRecord,
    LogType,
    ProcessStatus,
)

from semantic_kernel.contents import AuthorRole


class CosmosDBClient(DatabaseBase):
    def __init__(
        self,
        endpoint: str,
        credential: any,
        database_name: str,
        batch_container: str,
        file_container: str,
        log_container: str,
    ):
        self.endpoint = endpoint
        self.credential = credential
        self.database_name = database_name
        self.batch_container_name = batch_container
        self.file_container_name = file_container
        self.log_container_name = log_container
        self.logger = AppLogger("CosmosDB")
        self.client = None
        self.batch_container = None
        self.file_container = None
        self.log_container = None

    async def initialize_cosmos(self):
        try:
            self.client = CosmosClient(url=self.endpoint, credential=self.credential)
            database = self.client.get_database_client(self.database_name)
            self.batch_container = await self._get_container(
                database, self.batch_container_name
            )
            self.file_container = await self._get_container(
                database, self.file_container_name
            )
            self.log_container = await self._get_container(
                database, self.log_container_name
            )
        except Exception as e:
            self.logger.error("Failed to initialize Cosmos DB", error=str(e))
            raise

    async def _get_container(
        self, database: DatabaseProxy, container_name
    ):
        try:
            return database.get_container_client(container_name)

        except Exception as e:
            self.logger.error("Failed to Get cosmosdb container", error=str(e))
            raise

    async def create_batch(self, user_id: str, batch_id: UUID) -> BatchRecord:
        try:
            batch = BatchRecord(
                batch_id=batch_id,
                user_id=user_id,
                file_count=0,  # start with 0 file
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                status=ProcessStatus.READY_TO_PROCESS,
            )
            try:
                await self.batch_container.create_item(body=batch.dict())
                return batch
            except CosmosResourceExistsError:
                self.logger.info(f"Batch with ID {batch_id} already exists")
                batchexists = await self.get_batch(user_id, str(batch_id))
                return batchexists

        except Exception as e:
            self.logger.error("Failed to create batch", error=str(e))
            raise

    async def add_file(
        self, batch_id: UUID, file_id: UUID, file_name: str, storage_path: str
    ) -> FileRecord:
        try:
            file_record = FileRecord(
                file_id=file_id,
                batch_id=batch_id,
                original_name=file_name,
                blob_path=storage_path,
                translated_path="",
                status=ProcessStatus.READY_TO_PROCESS,
                error_count=0,
                syntax_count=0,  # start with 0 syntaxis
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            await self.file_container.create_item(body=file_record.dict())
            return file_record
        except Exception as e:
            self.logger.error("Failed to add file", error=str(e))
            raise

    async def update_file(self, file_record: FileRecord) -> FileRecord:
        try:
            await self.file_container.replace_item(
                item=str(file_record.file_id), body=file_record.dict()
            )
            return file_record
        except Exception as e:
            self.logger.error("Failed to update file", error=str(e))
            raise

    async def update_batch(self, batch_record: BatchRecord) -> BatchRecord:
        """
        Asynchronously updates a batch record in the database.

        Args:
            batch_record (BatchRecord): The batch record to be updated.

        Returns:
            BatchRecord: The updated batch record.

        Raises:
            Exception: If the update operation fails.
        """
        try:
            await self.batch_container.replace_item(
                item=str(batch_record.batch_id), body=batch_record.dict()
            )
            return batch_record
        except Exception as e:
            self.logger.error("Failed to update batch", error=str(e))
            raise

    async def get_batch(self, user_id: str, batch_id: str) -> Optional[Dict]:
        try:
            query = (
                "SELECT * FROM c WHERE c.batch_id = @batch_id and c.user_id = @user_id"
            )
            params = [
                {"name": "@batch_id", "value": batch_id},
                {"name": "@user_id", "value": user_id},
            ]
            batch = None
            async for item in self.batch_container.query_items(
                query=query, parameters=params
            ):
                batch = item

            return batch
        except Exception as e:
            self.logger.error("Failed to get batch", error=str(e))
            raise

    async def get_file(self, file_id: str) -> Optional[Dict]:
        try:
            query = "SELECT * FROM c WHERE c.file_id = @file_id "
            params = [{"name": "@file_id", "value": file_id}]
            file_entry = None
            async for item in self.file_container.query_items(
                query=query, parameters=params
            ):
                file_entry = item
            return file_entry
        except Exception as e:
            self.logger.error("Failed to get file", error=str(e))
            raise

    async def get_batch_files(self, batch_id: str) -> List[Dict]:
        try:
            query = (
                "SELECT * FROM c WHERE c.batch_id = @batch_id ORDER BY c.created_at ASC"
            )
            params = [
                {"name": "@batch_id", "value": batch_id},
            ]
            files = []  # Store all files
            async for item in self.file_container.query_items(
                query=query, parameters=params
            ):

                files.append(item)  # Append each file to the list

            return files
        except Exception as e:
            self.logger.error("Failed to get files", error=str(e))
            raise

    async def get_batch_from_id(self, batch_id: str) -> Dict:
        """Retrieve a batch from the database using the batch ID."""
        try:
            query = "SELECT * FROM c WHERE c.batch_id = @batch_id"
            params = [{"name": "@batch_id", "value": batch_id}]

            batch = None  # Store the batch
            async for item in self.batch_container.query_items(
                query=query, parameters=params
            ):
                batch = item  # Assign the batch to the variable

            return batch  # Return the batch
        except Exception as e:
            self.logger.error("Failed to get batch from ID", error=str(e))
            raise

    async def get_user_batches(self, user_id: str) -> Dict:
        """Retrieve all batches for a given user."""
        try:
            query = "SELECT * FROM c WHERE c.user_id = @user_id"
            params = [{"name": "@user_id", "value": user_id}]

            batches = []  # Store all batches
            async for item in self.batch_container.query_items(
                query=query, parameters=params
            ):
                batches.append(item)  # Append each batch to the list

            return batches  # Return a dictionary containing the batch list
        except Exception as e:
            self.logger.error("Failed to get user batches", error=str(e))
            raise

    async def get_file_logs(self, file_id: str) -> List[Dict]:
        """Retrieve all logs for a given file."""
        try:
            query = (
                "SELECT * FROM c WHERE c.file_id = @file_id ORDER BY c.timestamp DESC"
            )
            params = [{"name": "@file_id", "value": file_id}]

            logs = []  # Store all logs
            async for item in self.log_container.query_items(
                query=query, parameters=params
            ):
                logs.append(item)  # Append each log entry to the list

            return logs  # Return a dictionary containing the log list
        except Exception as e:
            self.logger.error("Failed to get file logs", error=str(e))
            raise

    async def delete_all(self, user_id: str) -> None:
        try:
            await self.batch_container.delete_item(user_id, partition_key=user_id)
            await self.file_container.delete_item(user_id, partition_key=user_id)
            await self.log_container.delete_item(user_id, partition_key=user_id)
        except Exception as e:
            self.logger.error("Failed to delete all user data", error=str(e))
            raise

    async def delete_logs(self, file_id: str) -> None:
        try:
            query = "SELECT c.id FROM c WHERE c.file_id = @file_id"
            params = [{"name": "@file_id", "value": file_id}]
            async for item in self.log_container.query_items(
                query=query, parameters=params
            ):
                # Use the item's id as well as the file_id as partition key for deletion.
                await self.log_container.delete_item(
                    item["id"], partition_key=item["id"]
                )
        except Exception as e:
            self.logger.error("Failed to delete all user data", error=str(e))
            raise

    async def delete_batch(self, user_id: str, batch_id: str) -> None:
        try:
            # Deleting the batch from the batch container
            try:
                await self.batch_container.delete_item(batch_id, partition_key=batch_id)
            except Exception as e:
                self.logger.error(
                    f"Failed to delete batch with ID: {batch_id}", error=str(e)
                )
                raise

        except Exception as e:
            self.logger.error("Failed to perform delete batch operation", error=str(e))
            raise

    async def delete_file(self, user_id: str, file_id: str) -> None:
        """Delete all log entries and the file associated with the given file_id."""
        try:
            await self.delete_logs(file_id)
            # Now delete the file entry
            await self.file_container.delete_item(file_id, partition_key=file_id)
            # self.logger.info(f"Successfully deleted file with ID {file_id}")

        except Exception as e:
            self.logger.error(
                f"Failed to delete file and logs for file_id {file_id}: {str(e)}"
            )
            raise

    async def add_file_log(
        self,
        file_id: UUID,
        description: str,
        last_candidate: str,
        log_type: LogType,
        agent_type: AgentType,
        author_role: AuthorRole,
    ) -> None:
        """Log a file status update."""
        try:
            log_id = uuid4()
            log_entry = FileLog(
                log_id=log_id,
                file_id=file_id,
                description=description,
                log_type=log_type,
                agent_type=agent_type,
                last_candidate=last_candidate,
                author_role=author_role,
                timestamp=datetime.now(timezone.utc),
            )
            await self.log_container.create_item(body=log_entry.dict())
        except Exception as e:
            self.logger.error("Failed to log file status", error=str(e))
            raise

    async def update_batch_entry(
        self, batch_id: str, user_id: str, status: ProcessStatus, file_count: int
    ):
        """Update batch status."""
        try:
            batch = await self.get_batch(user_id, batch_id)
            if not batch:
                raise ValueError("Batch not found")

            if isinstance(status, ProcessStatus):
                batch["status"] = status.value
            else:
                batch["status"] = status

            batch["updated_at"] = datetime.utcnow().isoformat()
            batch["file_count"] = file_count

            await self.batch_container.replace_item(item=batch_id, body=batch)

            return batch
        except Exception as e:
            self.logger.error("Failed to update batch entry", error=str(e))
            raise

    async def close(self) -> None:
        if self.client:
            self.client.close()
            self.logger.info("Closed Cosmos DB connection")

    async def delete_file_logs(self, file_id: str) -> None:
        pass

    async def get_batch_history(
        self,
        user_id: str,
        limit: Optional[int] = None,
        sort_order: str = "DESC",
        offset: int = 0,
    ) -> List[Dict]:
        try:
            offset = int(offset)  # Ensure offset is an integer
        except ValueError:
            raise ValueError("Offset must be an integer.")

        # Base query to fetch batch history for the user
        query = f"""
            SELECT * FROM c
            WHERE c.user_id = @user_id
            and c.status != 'ready_to_process'
            ORDER BY c.updated_at {sort_order}
        """

        params = [{"name": "@user_id", "value": user_id}]

        if limit is not None:
            try:
                limit = int(limit)  # Ensure limit is an integer
                query += " OFFSET @offset LIMIT @limit"
                params.append({"name": "@offset", "value": offset})
                params.append({"name": "@limit", "value": limit})
            except ValueError:
                raise ValueError("Limit must be an integer.")

        batches = []
        async for batch in self.batch_container.query_items(
            query=query, parameters=params
        ):
            batches.append(batch)

        return batches
