import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from common.database.database_factory import DatabaseFactory
from common.logger.app_logger import AppLogger
from common.models.api import (
    AgentType,
    BatchRecord,
    FileRecord,
    FileResult,
    LogType,
    ProcessStatus,
)
from common.storage.blob_factory import BlobStorageFactory
from fastapi import HTTPException, UploadFile
from semantic_kernel.contents import AuthorRole


class BatchService:
    def __init__(self):
        self.logger = AppLogger("BatchService")
        self.database = None

    async def initialize_database(self):
        """Ensure the database is initialized before using it."""
        # Initialize database connection
        self.database = await DatabaseFactory.get_database()

    async def get_batch(self, batch_id: UUID, user_id: str) -> Optional[Dict]:
        """Retrieve batch details including files"""
        batch = await self.database.get_batch(user_id, batch_id)
        if not batch:
            return None
        files = await self.database.get_batch_files(batch_id)

        return {"batch": batch, "files": files}

    async def get_file(self, file_id: str) -> Optional[Dict]:
        """Retrieve file details"""
        file = await self.database.get_file(file_id)
        if not file:
            return None

        return {"file": file}

    async def get_file_report(self, file_id: str) -> Optional[Dict]:
        """Retrieve file logs"""
        file = await self.database.get_file(file_id)
        file_record = FileRecord.fromdb(file)
        batch = await self.database.get_batch_from_id(str(file_record.batch_id))
        batch_record = BatchRecord.fromdb(batch)

        logs = await self.database.get_file_logs(file_id)
        file_content = ""
        translated_content = ""
        try:
            storage = await BlobStorageFactory.get_storage()
            if file_record.translated_path not in ["", None]:
                translated_content = await storage.get_file(file_record.translated_path)
        except (FileNotFoundError, IOError) as e:
            self.logger.error(f"Error downloading file content: {str(e)}")

        return {
            "file": file_record.dict(),
            "batch": batch_record.dict(),
            "logs": logs,
            "file_content": file_content,
            "translated_content": translated_content,
        }

    async def get_file_translated(self, file: dict):
        """Retrieve file logs"""

        translated_content = ""
        try:
            storage = await BlobStorageFactory.get_storage()
            if file["translated_path"] not in ["", None]:
                translated_content = await storage.get_file(file["translated_path"])
        except (FileNotFoundError, IOError) as e:
            self.logger.error(f"Error downloading file content: {str(e)}")

        return translated_content

    async def get_batch_for_zip(self, batch_id: str) -> List[Tuple[str, str]]:
        """Retrieve batch details including files in a single zip archive"""
        files = []
        try:
            files_meta = await self.database.get_batch_files(batch_id)

            # Process each file to retrieve its logs
            for file_meta in files_meta:
                try:
                    file_content = await self.get_file_translated(file_meta)

                    files.append(
                        ("rslt_" + file_meta.get("original_name"), file_content)
                    )

                except Exception as e:
                    self.logger.error(
                        f"Error processing file {file_meta.get('original_name')}: {str(e)}"
                    )
            return files
        except Exception as e:
            self.logger.error(f"Error retrieving batch information for zip: {str(e)}")
            raise  # Re-raise for caller handling

    async def get_batch_summary(self, batch_id: str, user_id: str) -> Optional[Dict]:
        """Retrieve file logs"""
        try:
            try:
                batch = await self.database.get_batch(user_id, batch_id)
            except Exception as e:
                self.logger.error(f"Error retrieving batch information: {str(e)}")
            try:
                batch_record = BatchRecord.fromdb(batch)
            except Exception as e:
                self.logger.error(f"Error converting batch record: {str(e)}")
            files = await self.database.get_batch_files(batch_id)

            # Process each file to retrieve its logs
            for file in files:
                try:
                    logs = await self.database.get_file_logs(file["file_id"])
                    file["logs"] = logs
                    if file["translated_path"]:
                        try:
                            translated_content = await self.get_file_translated(file)
                            file["translated_content"] = translated_content
                        except Exception as e:
                            self.logger.error(
                                f"Error retrieving translated content for file {file['file_id']}: {str(e)}"
                            )
                except Exception as e:
                    self.logger.error(
                        f"Error retrieving logs for file {file['file_id']}: {str(e)}"
                    )
                    file["logs"] = []  # Set empty logs on error

            return {
                "files": files,
                "batch": batch_record.dict(),
            }
        except Exception as e:
            self.logger.error(f"Error retrieving batch information: {str(e)}")
            raise  # Re-raise for caller handling

    async def delete_batch(self, batch_id: UUID, user_id: str):
        """Delete a batch along with its files and logs"""
        batch = await self.database.get_batch(user_id, batch_id)
        if batch:
            await self.database.delete_batch(user_id, batch_id)

            self.logger.info(f"Successfully deleted batch with ID: {batch_id}")
            return {"message": "Batch deleted successfully", "batch_id": str(batch_id)}

    async def delete_file(self, file_id: UUID, user_id: str):
        """Delete a file and its logs, and update batch file count"""
        try:
            # Ensure storage is available
            storage = await BlobStorageFactory.get_storage()
            if not storage:
                raise RuntimeError("Storage service not initialized")

            file = await self.database.get_file(file_id)

            if not file:
                return None
            file_record = FileRecord.fromdb(file)
            batch_id = str(file_record.batch_id)
            # Delete file from storage
            blob_path = file_record.blob_path
            deleted = await storage.delete_file(blob_path)

            if not deleted:
                raise RuntimeError("Failed to delete file from storage")

            if file_record.translated_path:
                await storage.delete_file(file_record.translated_path)

            # Delete file entry from database
            await self.database.delete_file(user_id, file_id)

            # Fetch batch entry and reduce file count
            batch = await self.database.get_batch(user_id, batch_id)
            if batch is not None:
                try:
                    batch_record = BatchRecord.fromdb(batch)
                except Exception as e:
                    self.logger.error(f"Error converting batch record: {str(e)}")
                try:
                    files = await self.database.get_batch_files(batch_id)
                    if not files:
                        self.logger.error(f"Error fetching files for batch {batch_id}")
                    batch_record.file_count = len(files)
                    batch_record.updated_at = datetime.utcnow().isoformat()
                    await self.database.update_batch(batch_record)
                except Exception as e:
                    self.logger.error(f"Error updating batch file count: {str(e)}")
            self.logger.info(
                f"Successfully deleted file {file_id} from batch {batch_id}"
            )
            return {"message": "File deleted successfully", "file_id": str(file_id)}
        except (RuntimeError, ValueError, IOError) as e:
            self.logger.error(f"Error deleting file: {str(e)}")
            raise RuntimeError("File deletion failed") from e

    async def delete_all(self, user_id: str):
        """Delete all batches, files, and logs for a user"""
        return await self.database.delete_all(user_id)

    async def get_all_batches(self, user_id: str):
        """Retrieve all batches for a user"""
        return await self.database.get_user_batches(user_id)

    def is_valid_uuid(self, value: str) -> bool:
        """Validate if a given string is a valid UUID."""
        try:
            UUID(value, version=4)
            return True
        except ValueError:
            return False

    def generate_file_path(
        self, batch_id: str, user_id: str, file_id: str, filename: str
    ) -> str:
        """Generate a clean file path: user_id/batch_id/file_id/clean_filename."""
        # Remove invalid characters and replace with "_"
        clean_filename = re.sub(r"[^\w.-]", "_", filename)
        # Construct the path
        file_path = f"{user_id}/{batch_id}/{file_id}/{clean_filename}"
        # self.logger.info(f"Generated file path: {file_path}")
        return file_path

    async def upload_file_to_batch(self, batch_id: str, user_id: str, file: UploadFile):
        """Upload a file, create entries in the database, and log the process"""
        try:
            # Ensure storage is available
            storage = await BlobStorageFactory.get_storage()
            if not storage:
                raise RuntimeError("Storage service not initialized")

            # Try to fetch the batch; if it doesn't exist, create a new one
            batch = await self.database.get_batch(user_id, batch_id)
            if not batch:
                batch = await self.database.create_batch(user_id, UUID(batch_id))

            # Generate a unique file ID
            file_id = str(uuid4())
            # Generate a clean file path
            blob_path = self.generate_file_path(
                batch_id, user_id, file_id, file.filename
            )

            # Upload file to blob storage
            file_content = await file.read()

            await storage.upload_file(
                file_content=file_content,
                blob_path=blob_path,
                content_type=file.content_type,
                metadata={"batch_id": batch_id, "user_id": user_id, "file_id": file_id},
            )

            # Create file entry
            await self.database.add_file(batch_id, file_id, file.filename, blob_path)
            file_record = await self.database.get_file(file_id)

            await self.database.add_file_log(
                UUID(file_id),
                "File uploaded successfully",
                "",
                LogType.SUCCESS,
                AgentType.HUMAN,
                AuthorRole.USER,
            )
            if isinstance(batch, dict):
                # Update batch file count
                files = await self.database.get_batch_files(batch_id)
                batch["file_count"] = len(files)
                batch = await self.database.update_batch_entry(
                    batch_id,
                    user_id,
                    ProcessStatus.READY_TO_PROCESS,
                    batch["file_count"],
                )
                # Return response
                return {"batch": batch, "file": file_record}

            elif isinstance(batch, BatchRecord):
                # Update batch file count
                files = await self.database.get_batch_files(batch_id)
                batch.file_count = len(files)
                batch.updated_at = datetime.utcnow().isoformat()
                await self.database.update_batch_entry(
                    batch_id, user_id, ProcessStatus.READY_TO_PROCESS, batch.file_count
                )
                # Return response
                return {"batch": batch, "file": file_record}

            else:
                raise RuntimeError(
                    "Error: batch is neither a dictionary nor a BatchRecord!"
                )

        except (RuntimeError, ValueError, IOError) as e:
            self.logger.error("Error uploading file", error=str(e))
            raise RuntimeError("File upload failed") from e

    async def delete_batch_and_files(self, batch_id: str, user_id: str):
        """Delete a file from storage, remove its database entry, logs, and update the batch count."""
        try:
            # Ensure storage is available
            storage = await BlobStorageFactory.get_storage()
            if not storage:
                raise RuntimeError("Storage service not initialized")

            batch = await self.database.get_batch(user_id, batch_id)
            self.logger.info(f"Batch for delete: {batch}")
            if not batch:
                return {"message": "Batch not found"}

            files = await self.database.get_batch_files(batch_id)
            if not files:
                raise ValueError("No files found in the batch")
            for file in files:
                file_record = FileRecord.fromdb(file)
                blob_path = file_record.blob_path

                deleted = await storage.delete_file(blob_path)

                if not deleted:
                    self.logger.error(
                        f"Failed to delete file from storage: {blob_path}"
                    )

                if file_record.translated_path:
                    delete_translate = await storage.delete_file(
                        file_record.translated_path
                    )
                    if not delete_translate:
                        self.logger.error(
                            f"Failed to delete translated file from storage: {file_record.translated_path}"
                        )

                # Delete file and log entry from database
                await self.database.delete_file(user_id, str(file_record.file_id))
            await self.database.delete_batch(user_id, batch_id)
            return {"message": "Files deleted successfully"}

        except (RuntimeError, ValueError, IOError) as e:
            self.logger.error("Error deleting file", error=str(e))
            raise RuntimeError("File deletion failed") from e

    async def update_file(
        self,
        file_id: str,
        status: ProcessStatus,
        file_result: FileResult,
        error_count: int,
        syntax_count: int,
    ):
        """Update file entry in the database"""
        file = await self.database.get_file(file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        file_record = FileRecord.fromdb(file)
        file_record.status = status
        file_record.file_result = file_result
        file_record.error_count += error_count
        file_record.syntax_count += syntax_count
        file_record.updated_at = datetime.utcnow()
        await self.database.update_file(file_record)
        return file_record

    async def update_file_record(self, file_record: FileRecord):
        """Update file entry in the database"""
        await self.database.update_file(file_record)

    async def create_file_log(
        self,
        file_id: str,
        description: str,
        last_candidate: str,
        log_type: LogType,
        agent_type: AgentType,
        author_role: AuthorRole,
    ):
        """Create a new file log entry in the database"""
        await self.database.add_file_log(
            UUID(file_id),
            description,
            last_candidate,
            log_type,
            agent_type,
            author_role,
        )

    async def update_batch(self, batch_id: str, status: ProcessStatus):
        """Update batch status to completed"""
        batch = await self.database.get_batch_from_id(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        batch_record = BatchRecord.fromdb(batch)
        batch_record.status = status
        batch_record.updated_at = datetime.utcnow()
        await self.database.update_batch(batch_record)

    async def create_candidate(self, file_id: str, candidate: str):
        """Create a new candidate entry in the database and upload the candita file to storage"""
        # Ensure storage is available
        storage = await BlobStorageFactory.get_storage()
        if not storage:
            raise RuntimeError("Storage service not initialized")

        file = await self.database.get_file(file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        file_record = FileRecord.fromdb(file)
        batch_id = str(file_record.batch_id)
        batch = await self.database.get_batch_from_id(batch_id)
        batch_record = BatchRecord.fromdb(batch)
        user_id = batch_record.user_id
        # Generate a clean file path
        blob_path = self.generate_file_path(
            str(batch_id), user_id, file_id, f"candidate_{file_record.original_name}"
        )

        # Upload file to blob storage
        file_content = candidate
        try:
            await storage.upload_file(
                file_content=file_content,
                blob_path=blob_path,
                content_type="text/plain",
                metadata={"batch_id": batch_id, "user_id": user_id, "file_id": file_id},
            )
        except Exception as e:
            self.logger.error(f"Error uploading file content: {str(e)}")
        file_record.translated_path = blob_path
        file_record.status = ProcessStatus.COMPLETED
        file_record.updated_at = datetime.utcnow()

        error_count, syntax_count = await self.get_file_counts(file_id)

        file_record.file_result = (
            FileResult.ERROR if error_count > 0 else FileResult.SUCCESS
        )
        file_record.error_count = error_count
        file_record.syntax_count = syntax_count
        await self.update_file_record(file_record)

    async def batch_files_final_update(self, batch_id: str):
        files = await self.database.get_batch_files(batch_id)
        for file in files:
            file_record = FileRecord.fromdb(file)
            if file_record.status == ProcessStatus.COMPLETED:
                # nothing to do if the file is already completed
                continue
            # file didn't completed successfully
            file_record.status = ProcessStatus.COMPLETED
            file_record.file_result = FileResult.ERROR
            error_count, syntax_count = await self.get_file_counts(
                str(file_record.file_id)
            )
            file_record.error_count = error_count + 1
            file_record.syntax_count = syntax_count
            try:
                await self.create_file_log(
                    str(file_record.file_id),
                    "File didn't finish successfully.",
                    "",
                    LogType.ERROR,
                    AgentType.SEMANTIC_VERIFIER,
                    AuthorRole.ASSISTANT,
                )
            except (RuntimeError, ValueError, IOError) as e:
                self.logger.error(f"Error creating file log: {str(e)}")
            try:
                await self.update_file_record(file_record)
            except Exception as e:
                self.logger.error(f"Error updating file record: {str(e)}")

    async def update_file_counts(self, file_id: str):
        file = await self.database.get_file(file_id)
        if not file:
            return None
        file_record = FileRecord.fromdb(file)
        error_count, syntax_count = await self.get_file_counts(file_id)
        file_record.status = ProcessStatus.COMPLETED
        file_record.file_result = (
            FileResult.ERROR if error_count > 0 else FileResult.SUCCESS
        )
        file_record.error_count = error_count
        file_record.syntax_count = syntax_count
        await self.update_file_record(file_record)

    async def get_file_counts(self, file_id: str):
        file_logs = await self.database.get_file_logs(file_id)
        if not file_logs:
            return 0, 0
        error_count = (
            sum(1 for log in file_logs if log["log_type"] == LogType.ERROR.value)
            if file_logs
            else 0
        )
        syntax_count = (  # Count syntax errors
            sum(1 for log in file_logs if log["log_type"] == LogType.WARNING.value)
            if file_logs
            else 0
        )
        return error_count, syntax_count

    async def get_batch_from_id(self, batch_id: str):
        """Retrieve a batch record from the database"""
        return await self.database.get_batch_from_id(batch_id)

    async def delete_all_from_storage_cosmos(self, user_id: str):
        """Delete a all files from storage, remove its database entry, logs"""
        try:
            # Ensure storage is available
            storage = await BlobStorageFactory.get_storage()
            if not storage:
                raise RuntimeError("Storage service not initialized")

            # List all the storage files
            liststoragefiles = await storage.list_files()
            for storage_file in liststoragefiles:
                blob_path = storage_file["name"]

                deleted = await storage.delete_file(blob_path)

                if not deleted:
                    raise RuntimeError("Failed to delete file from storage")

                # Get the file id
                file_id = blob_path.split("/")[2]
                # Fetch file entry
                file_entry = await self.database.get_file(file_id)
                if not file_entry:
                    self.logger.info(f"File not found: {file_id}")
                else:
                    if file_entry["translated_path"]:
                        await storage.delete_file(file_entry["translated_path"])

                    # Delete file and log entry from database
                    await self.database.delete_file(user_id, file_id)

            # Get all batches
            alluserbatches = await self.get_all_batches(user_id)
            try:
                for userbatch in alluserbatches:
                    batch_id = userbatch["batch_id"]
                    await self.database.delete_batch(user_id, batch_id)

                return {"message": "All user data deleted successfully"}

            except Exception as e:
                self.logger.error(
                    f"Error occurred while deleting the batch with ID: {batch_id}",
                    error=str(e),
                )
                raise RuntimeError("Delete batch operation failed") from e

        except (RuntimeError, ValueError, IOError) as e:
            self.logger.error(
                "Error occured while deleting all the Batches/Files/Logs", error=str(e)
            )
            raise RuntimeError("Delete all operation failed") from e

    async def get_batch_history(
        self, user_id: str, limit: Optional[int] = None, offset: int = 0
    ) -> List[Dict]:
        """Retrieve batch processing history for the user with pagination support."""
        try:
            # Ensure the database connection is initialized
            if not self.database:
                await self.initialize_database()

            # Fetch batch history from CosmosDBClient
            batch_history = await self.database.get_batch_history(
                user_id, limit=limit, offset=offset
            )

            if not batch_history:
                self.logger.info(f"No batch history found for user {user_id}")
                return []

            return batch_history
        except (RuntimeError, ValueError, IOError) as e:
            self.logger.error(f"Failed to retrieve batch history: {str(e)}")
            raise RuntimeError("Error retrieving batch history") from e
