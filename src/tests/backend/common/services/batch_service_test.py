from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from common.models.api import AgentType, AuthorRole, BatchRecord, FileResult, LogType, ProcessStatus
from common.services.batch_service import BatchService

from fastapi import HTTPException, UploadFile

import pytest

import pytest_asyncio


@pytest.fixture
def mock_service(mocker):
    service = BatchService()
    service.logger = mocker.Mock()
    service.database = MagicMock()

    return service


@pytest_asyncio.fixture
async def service():
    svc = BatchService()
    svc.logger = MagicMock()
    return svc


def batch_service():
    service = BatchService()  # Correct constructor
    service.database = MagicMock()  # Inject mock database
    return service


@pytest.mark.asyncio
@patch("common.services.batch_service.DatabaseFactory.get_database", new_callable=AsyncMock)
async def test_initialize_database(mock_get_db, service):
    mock_db = AsyncMock()
    mock_get_db.return_value = mock_db
    await service.initialize_database()
    assert service.database == mock_db


@pytest.mark.asyncio
async def test_get_batch_found(service):
    service.database = AsyncMock()
    batch_id = uuid4()
    user_id = "user123"
    service.database.get_batch.return_value = {"id": str(batch_id)}
    service.database.get_batch_files.return_value = [{"file_id": "f1"}]
    result = await service.get_batch(batch_id, user_id)
    assert result["batch"] == {"id": str(batch_id)}
    assert result["files"] == [{"file_id": "f1"}]


@pytest.mark.asyncio
async def test_get_batch_not_found(service):
    service.database = AsyncMock()
    batch_id = uuid4()
    user_id = "user123"
    service.database.get_batch.return_value = None
    result = await service.get_batch(batch_id, user_id)
    assert result is None


@pytest.mark.asyncio
async def test_get_file_found(service):
    service.database = AsyncMock()
    service.database.get_file.return_value = {"file_id": "file123"}
    result = await service.get_file("file123")
    assert result == {"file": {"file_id": "file123"}}


@pytest.mark.asyncio
async def test_get_file_not_found(service):
    service.database = AsyncMock()
    service.database.get_file.return_value = None
    result = await service.get_file("notfound")
    assert result is None


@pytest.mark.asyncio
@patch("common.services.batch_service.BlobStorageFactory.get_storage", new_callable=AsyncMock)
@patch("common.models.api.FileRecord.fromdb")
@patch("common.models.api.BatchRecord.fromdb")
async def test_get_file_report_success(mock_batch_fromdb, mock_file_fromdb, mock_get_storage, service):
    service.database = AsyncMock()
    file_id = "file123"
    mock_file = {"batch_id": uuid4(), "translated_path": "some/path"}
    mock_batch = {"batch_id": "batch123"}
    mock_logs = [{"log": "log1"}]
    mock_translated = "translated content"
    service.database.get_file.return_value = mock_file
    service.database.get_batch_from_id.return_value = mock_batch
    service.database.get_file_logs.return_value = mock_logs
    mock_file_fromdb.return_value = MagicMock(dict=lambda: mock_file, batch_id=mock_file["batch_id"], translated_path="some/path")
    mock_batch_fromdb.return_value = MagicMock(dict=lambda: mock_batch)
    mock_storage = AsyncMock()
    mock_storage.get_file.return_value = mock_translated
    mock_get_storage.return_value = mock_storage
    result = await service.get_file_report(file_id)
    assert result["file"] == mock_file
    assert result["batch"] == mock_batch
    assert result["logs"] == mock_logs
    assert result["translated_content"] == mock_translated


@pytest.mark.asyncio
@patch("common.services.batch_service.BlobStorageFactory.get_storage", new_callable=AsyncMock)
async def test_get_file_translated_success(mock_get_storage, service):
    file = {"translated_path": "some/path"}
    mock_storage = AsyncMock()
    mock_storage.get_file.return_value = "translated"
    mock_get_storage.return_value = mock_storage
    result = await service.get_file_translated(file)
    assert result == "translated"


@pytest.mark.asyncio
@patch("common.services.batch_service.BlobStorageFactory.get_storage", new_callable=AsyncMock)
async def test_get_file_translated_error(mock_get_storage, service):
    file = {"translated_path": "some/path"}
    mock_storage = AsyncMock()
    mock_storage.get_file.side_effect = IOError("Failed to download")
    mock_get_storage.return_value = mock_storage
    result = await service.get_file_translated(file)
    assert result == ""


@pytest.mark.asyncio
async def test_get_batch_for_zip(service):
    service.database = AsyncMock()
    service.get_file_translated = AsyncMock(return_value="file-content")
    service.database.get_batch_files.return_value = [
        {"original_name": "doc1.txt", "translated_path": "path1"},
        {"original_name": "doc2.txt", "translated_path": "path2"},
    ]
    result = await service.get_batch_for_zip("batch1")
    assert len(result) == 2
    assert result[0][0] == "rslt_doc1.txt"
    assert result[0][1] == "file-content"


@pytest.mark.asyncio
@patch("common.models.api.BatchRecord.fromdb")
async def test_get_batch_summary_success(mock_batch_fromdb, service):
    service.database = AsyncMock()
    mock_batch = {"batch_id": "batch1"}
    mock_batch_record = MagicMock(dict=lambda: {"batch_id": "batch1"})
    mock_batch_fromdb.return_value = mock_batch_record
    service.database.get_batch.return_value = mock_batch
    service.database.get_batch_files.return_value = [
        {"file_id": "file1", "translated_path": "path1"},
        {"file_id": "file2", "translated_path": None},
    ]
    service.database.get_file_logs.return_value = ["log1"]
    service.get_file_translated = AsyncMock(return_value="translated")
    result = await service.get_batch_summary("batch1", "user1")
    assert "files" in result
    assert "batch" in result
    assert result["files"][0]["logs"] == ["log1"]
    assert result["files"][0]["translated_content"] == "translated"


@pytest.mark.asyncio
async def test_batch_zip_with_no_files(service):
    service.database = AsyncMock()
    service.database.get_batch_files.return_value = []
    service.get_file_translated = AsyncMock()
    result = await service.get_batch_for_zip("batch_empty")
    assert result == []


def test_is_valid_uuid():
    service = BatchService()
    valid = str(uuid4())
    invalid = "not-a-uuid"
    assert service.is_valid_uuid(valid)
    assert not service.is_valid_uuid(invalid)


def test_generate_file_path():
    service = BatchService()
    path = service.generate_file_path("batch1", "user1", "file1", "test@file.pdf")
    assert path == "user1/batch1/file1/test_file.pdf"


@pytest.mark.asyncio
async def test_delete_batch_existing():
    service = BatchService()
    service.database = AsyncMock()
    batch_id = uuid4()
    service.database.get_batch.return_value = {"id": str(batch_id)}
    service.database.delete_batch.return_value = None
    result = await service.delete_batch(batch_id, "user1")
    assert result["message"] == "Batch deleted successfully"
    assert result["batch_id"] == str(batch_id)


@pytest.mark.asyncio
async def test_delete_file_success():
    service = BatchService()
    service.database = AsyncMock()
    file_id = uuid4()
    batch_id = uuid4()
    mock_file = MagicMock()
    mock_file.batch_id = batch_id
    mock_file.blob_path = "some/path/file.pdf"
    mock_file.translated_path = "some/path/file_translated.pdf"
    with patch("common.storage.blob_factory.BlobStorageFactory.get_storage", new_callable=AsyncMock) as mock_storage:
        mock_storage.return_value.delete_file.return_value = True
        service.database.get_file.return_value = mock_file
        service.database.get_batch.return_value = {"id": str(batch_id)}
        service.database.get_batch_files.return_value = [1, 2]
        with patch("common.models.api.FileRecord.fromdb", return_value=mock_file), \
             patch("common.models.api.BatchRecord.fromdb") as mock_batch_record:
            mock_record = MagicMock()
            mock_record.file_count = 1
            service.database.update_batch.return_value = None
            mock_batch_record.return_value = mock_record
            result = await service.delete_file(file_id, "user1")
            assert result["message"] == "File deleted successfully"
            assert result["file_id"] == str(file_id)


@pytest.mark.asyncio
async def test_upload_file_to_batch_dict_batch():
    service = BatchService()
    service.database = AsyncMock()
    file = UploadFile(filename="hello@file.txt", file=BytesIO(b"test content"))
    batch_id = str(uuid4())
    file_id = str(uuid4())
    with patch("common.storage.blob_factory.BlobStorageFactory.get_storage", new_callable=AsyncMock) as mock_storage, \
         patch("uuid.uuid4", return_value=file_id), \
         patch("common.models.api.FileRecord.fromdb", return_value={"blob_path": "path"}):

        mock_storage.return_value.upload_file.return_value = None
        service.database.get_batch.side_effect = [None, {"file_count": 0}]
        service.database.create_batch.return_value = {}
        service.database.get_batch_files.return_value = ["file1", "file2"]
        service.database.get_file.return_value = {"filename": file.filename}
        service.database.update_batch_entry.return_value = {"batch_id": batch_id, "file_count": 2}
        result = await service.upload_file_to_batch(batch_id, "user1", file)
        assert "batch" in result
        assert "file" in result


@pytest.mark.asyncio
async def test_upload_file_to_batch_invalid_storage():
    service = BatchService()
    service.database = AsyncMock()
    file = UploadFile(filename="file.txt", file=BytesIO(b"data"))
    with patch("common.storage.blob_factory.BlobStorageFactory.get_storage", return_value=None):
        with pytest.raises(RuntimeError) as exc_info:
            await service.upload_file_to_batch(str(uuid4()), "user1", file)
        # Check outer exception message
        assert str(exc_info.value) == "File upload failed"

        # Check original cause of the exception
        assert isinstance(exc_info.value.__cause__, RuntimeError)
        assert str(exc_info.value.__cause__) == "Storage service not initialized"


@pytest.mark.asyncio
async def test_delete_batch_success(mock_service):
    batch_id = uuid4()
    user_id = "test_user"
    mock_service.database.get_batch = AsyncMock(return_value={"id": str(batch_id)})
    mock_service.database.delete_batch = AsyncMock()
    result = await mock_service.delete_batch(batch_id, user_id)
    assert result["message"] == "Batch deleted successfully"
    assert result["batch_id"] == str(batch_id)


def test_is_valid_uuid_valid(mock_service):
    assert mock_service.is_valid_uuid(str(uuid4())) is True


def test_is_valid_uuid_invalid(mock_service):
    assert mock_service.is_valid_uuid("not-a-uuid") is False


def test_generate_file_path_only_filename():
    service = BatchService()
    path = service.generate_file_path(None, None, None, "weird@name!.txt")
    assert path.endswith("weird_name_.txt")


def test_is_valid_uuid_empty_string():
    service = BatchService()
    assert not service.is_valid_uuid("")


def test_is_valid_uuid_partial_uuid():
    service = BatchService()
    assert not service.is_valid_uuid("1234abcd")


@pytest.mark.asyncio
async def test_delete_file_file_not_found():
    service = BatchService()
    service.database = AsyncMock()
    file_id = str(uuid4())

    service.database.get_file.return_value = None
    result = await service.delete_file(file_id, "user1")
    assert result is None


@pytest.mark.asyncio
async def test_upload_file_to_batch_storage_upload_fails():
    service = BatchService()
    service.database = AsyncMock()
    file = UploadFile(filename="test.txt", file=BytesIO(b"abc"))
    file_id = str(uuid4())

    with patch("common.storage.blob_factory.BlobStorageFactory.get_storage") as mock_get_storage, \
         patch("uuid.uuid4", return_value=file_id):
        mock_storage = AsyncMock()
        mock_storage.upload_file.side_effect = RuntimeError("upload failed")
        mock_get_storage.return_value = mock_storage

        service.database.get_batch.side_effect = [None, {"file_count": 0}]
        service.database.create_batch.return_value = {}
        service.database.get_batch_files.return_value = []
        service.database.update_batch_entry.return_value = {}

        with pytest.raises(RuntimeError, match="File upload failed"):
            await service.upload_file_to_batch("batch123", "user1", file)

            @pytest.mark.asyncio
            async def test_update_file_counts_success(service):
                service.database = AsyncMock()
                file_id = str(uuid4())
                mock_file = {"file_id": file_id}
                mock_logs = [
                    {"log_type": LogType.ERROR.value},
                    {"log_type": LogType.WARNING.value},
                    {"log_type": LogType.WARNING.value},
                ]
                service.database.get_file.return_value = mock_file
                service.database.get_file_logs.return_value = mock_logs
                with patch("common.models.api.FileRecord.fromdb", return_value=MagicMock()) as mock_file_record:
                    await service.update_file_counts(file_id)
                    mock_file_record.assert_called_once()
                    service.database.update_file.assert_called_once()

            @pytest.mark.asyncio
            async def test_update_file_counts_no_logs(service):
                service.database = AsyncMock()
                file_id = str(uuid4())
                mock_file = {"file_id": file_id}
                service.database.get_file.return_value = mock_file
                service.database.get_file_logs.return_value = []
                with patch("common.models.api.FileRecord.fromdb", return_value=MagicMock()) as mock_file_record:
                    await service.update_file_counts(file_id)
                    mock_file_record.assert_called_once()
                    service.database.update_file.assert_called_once()

            @pytest.mark.asyncio
            async def test_get_file_counts_success(service):
                service.database = AsyncMock()
                file_id = str(uuid4())
                mock_logs = [
                    {"log_type": LogType.ERROR.value},
                    {"log_type": LogType.WARNING.value},
                    {"log_type": LogType.WARNING.value},
                ]
                service.database.get_file_logs.return_value = mock_logs
                error_count, syntax_count = await service.get_file_counts(file_id)
                assert error_count == 1
                assert syntax_count == 2

            @pytest.mark.asyncio
            async def test_get_file_counts_no_logs(service):
                service.database = AsyncMock()
                file_id = str(uuid4())
                service.database.get_file_logs.return_value = []
                error_count, syntax_count = await service.get_file_counts(file_id)
                assert error_count == 0
                assert syntax_count == 0

            @pytest.mark.asyncio
            async def test_get_batch_history_success(service):
                service.database = AsyncMock()
                user_id = "user123"
                mock_history = [{"batch_id": "batch1"}, {"batch_id": "batch2"}]
                service.database.get_batch_history.return_value = mock_history
                result = await service.get_batch_history(user_id, limit=10, offset=0)
                assert result == mock_history

            @pytest.mark.asyncio
            async def test_get_batch_history_no_history(service):
                service.database = AsyncMock()
                user_id = "user123"
                service.database.get_batch_history.return_value = []
                result = await service.get_batch_history(user_id, limit=10, offset=0)
                assert result == []

                @pytest.mark.asyncio
                @patch("common.services.batch_service.DatabaseFactory.get_database", new_callable=AsyncMock)
                async def test_initialize_database_success(mock_get_database, service):
                    # Arrange
                    mock_database = AsyncMock()
                    mock_get_database.return_value = mock_database

                    # Act
                    await service.initialize_database()

                    # Assert
                    assert service.database == mock_database
                    mock_get_database.assert_called_once()

                @pytest.mark.asyncio
                @patch("common.services.batch_service.DatabaseFactory.get_database", new_callable=AsyncMock)
                async def test_initialize_database_failure(mock_get_database, service):
                    # Arrange
                    mock_get_database.side_effect = RuntimeError("Database initialization failed")

                    # Act & Assert
                    with pytest.raises(RuntimeError, match="Database initialization failed"):
                        await service.initialize_database()
                    mock_get_database.assert_called_once()

                    @pytest.mark.asyncio
                    @patch("common.services.batch_service.DatabaseFactory.get_database", new_callable=AsyncMock)
                    async def test_initialize_database_success(mock_get_database, service):
                        # Arrange
                        mock_database = AsyncMock()
                        mock_get_database.return_value = mock_database

                        # Act
                        await service.initialize_database()

                        # Assert
                        assert service.database == mock_database
                        mock_get_database.assert_called_once()

                    @pytest.mark.asyncio
                    @patch("common.services.batch_service.DatabaseFactory.get_database", new_callable=AsyncMock)
                    async def test_initialize_database_failure(mock_get_database, service):
                        # Arrange
                        mock_get_database.side_effect = RuntimeError("Database initialization failed")

                        # Act & Assert
                        with pytest.raises(RuntimeError, match="Database initialization failed"):
                            await service.initialize_database()
                        mock_get_database.assert_called_once()


@pytest.mark.asyncio
async def test_update_file_success():
    service = BatchService()
    service.database = AsyncMock()
    file_id = str(uuid4())
    mock_file = {"file_id": file_id}
    mock_record = MagicMock()
    mock_record.error_count = 0
    mock_record.syntax_count = 0

    service.database.get_file.return_value = mock_file
    with patch("common.models.api.FileRecord.fromdb", return_value=mock_record):
        await service.update_file(file_id, ProcessStatus.COMPLETED, FileResult.SUCCESS, 1, 2)
        assert mock_record.error_count == 1
        assert mock_record.syntax_count == 2
        service.database.update_file.assert_called_once()


@pytest.mark.asyncio
async def test_update_file_record():
    service = BatchService()
    service.database = AsyncMock()
    mock_file_record = MagicMock()
    await service.update_file_record(mock_file_record)
    service.database.update_file.assert_called_once_with(mock_file_record)


@pytest.mark.asyncio
async def test_create_file_log():
    service = BatchService()
    service.database = AsyncMock()
    file_id = str(uuid4())
    await service.create_file_log(
        file_id=file_id,
        description="test log",
        last_candidate="candidate",
        log_type=LogType.SUCCESS,
        agent_type=AgentType.HUMAN,
        author_role=AuthorRole.USER
    )
    service.database.add_file_log.assert_called_once()


@pytest.mark.asyncio
async def test_update_batch_success():
    service = BatchService()
    service.database = AsyncMock()
    batch_id = str(uuid4())
    mock_batch = {"batch_id": batch_id}
    mock_batch_record = MagicMock()
    service.database.get_batch_from_id.return_value = mock_batch
    with patch("common.models.api.BatchRecord.fromdb", return_value=mock_batch_record):
        await service.update_batch(batch_id, ProcessStatus.COMPLETED)
        service.database.update_batch.assert_called_once_with(mock_batch_record)


@pytest.mark.asyncio
async def test_delete_batch_and_files_success():
    service = BatchService()
    service.database = AsyncMock()
    batch_id = str(uuid4())
    user_id = "user"
    mock_file = MagicMock()
    mock_file.file_id = uuid4()
    mock_file.blob_path = "blob/file"
    mock_file.translated_path = "blob/translated"
    service.database.get_batch.return_value = {"batch_id": batch_id}
    service.database.get_batch_files.return_value = [mock_file]

    with patch("common.models.api.FileRecord.fromdb", return_value=mock_file), \
         patch("common.storage.blob_factory.BlobStorageFactory.get_storage", new_callable=AsyncMock) as mock_storage:
        mock_storage.return_value.delete_file.return_value = True
        result = await service.delete_batch_and_files(batch_id, user_id)
        assert result["message"] == "Files deleted successfully"


@pytest.mark.asyncio
async def test_batch_files_final_update():
    service = BatchService()
    service.database = AsyncMock()
    file_id = str(uuid4())
    file = {
        "file_id": file_id,
        "translated_path": "",
        "status": "IN_PROGRESS"
    }
    service.database.get_batch_files.return_value = [file]
    with patch("common.models.api.FileRecord.fromdb", return_value=MagicMock(file_id=file_id, translated_path="", status=None)), \
         patch.object(service, "get_file_counts", return_value=(1, 1)), \
         patch.object(service, "create_file_log", new_callable=AsyncMock), \
         patch.object(service, "update_file_record", new_callable=AsyncMock):
        await service.batch_files_final_update("batch1")


@pytest.mark.asyncio
async def test_delete_all_from_storage_cosmos_success():
    service = BatchService()
    service.database = AsyncMock()
    user_id = "user123"
    file_id = str(uuid4())
    batch_id = str(uuid4())
    mock_file = {
        "translated_path": "translated/path"
    }

    service.get_all_batches = AsyncMock(return_value=[{"batch_id": batch_id}])
    service.database.get_file.return_value = mock_file
    service.database.list_files = AsyncMock(return_value=[{"name": f"user/{batch_id}/{file_id}/file.txt"}])

    with patch("common.storage.blob_factory.BlobStorageFactory.get_storage", new_callable=AsyncMock) as mock_storage:
        mock_storage.return_value.list_files.return_value = [{"name": f"user/{batch_id}/{file_id}/file.txt"}]
        mock_storage.return_value.delete_file.return_value = True
        result = await service.delete_all_from_storage_cosmos(user_id)
        assert result["message"] == "All user data deleted successfully"


@pytest.mark.asyncio
async def test_create_candidate_success():
    service = BatchService()
    service.database = AsyncMock()
    file_id = str(uuid4())
    batch_id = str(uuid4())
    user_id = "user123"
    mock_file = {"batch_id": batch_id, "original_name": "doc.txt"}
    mock_batch = {"user_id": user_id}

    with patch("common.models.api.FileRecord.fromdb", return_value=MagicMock(original_name="doc.txt", batch_id=batch_id)), \
         patch("common.models.api.BatchRecord.fromdb", return_value=MagicMock(user_id=user_id)), \
         patch.object(service, "get_file_counts", return_value=(0, 1)), \
         patch.object(service, "update_file_record", new_callable=AsyncMock), \
         patch("common.storage.blob_factory.BlobStorageFactory.get_storage", new_callable=AsyncMock) as mock_storage:

        mock_storage.return_value.upload_file.return_value = None
        service.database.get_file.return_value = mock_file
        service.database.get_batch_from_id.return_value = mock_batch
        await service.create_candidate(file_id, "Some content")


@pytest.mark.asyncio
async def test_batch_files_final_update_success_path():
    service = BatchService()
    service.database = AsyncMock()
    file_id = str(uuid4())
    file = {
        "file_id": file_id,
        "translated_path": "some/path",
        "status": "IN_PROGRESS"
    }

    mock_file_record = MagicMock(translated_path="some/path", file_id=file_id)
    service.database.get_batch_files.return_value = [file]

    with patch("common.models.api.FileRecord.fromdb", return_value=mock_file_record), \
         patch.object(service, "update_file_record", new_callable=AsyncMock):
        await service.batch_files_final_update("batch123")


@pytest.mark.asyncio
async def test_get_file_counts_logs_none():
    service = BatchService()
    service.database = AsyncMock()
    service.database.get_file_logs.return_value = None
    error_count, syntax_count = await service.get_file_counts("file_id")
    assert error_count == 0
    assert syntax_count == 0


@pytest.mark.asyncio
async def test_create_candidate_upload_error():
    service = BatchService()
    service.database = AsyncMock()
    file_id = str(uuid4())
    mock_file = {"batch_id": str(uuid4()), "original_name": "doc.txt"}
    mock_batch = {"user_id": "user1"}

    with patch("common.models.api.FileRecord.fromdb", return_value=MagicMock(original_name="doc.txt", batch_id=mock_file["batch_id"])), \
         patch("common.models.api.BatchRecord.fromdb", return_value=MagicMock(user_id="user1")), \
         patch("common.storage.blob_factory.BlobStorageFactory.get_storage", new_callable=AsyncMock) as mock_storage, \
         patch.object(service, "get_file_counts", return_value=(1, 1)), \
         patch.object(service, "update_file_record", new_callable=AsyncMock):

        mock_storage.return_value.upload_file.side_effect = Exception("Upload fail")
        service.database.get_file.return_value = mock_file
        service.database.get_batch_from_id.return_value = mock_batch

        await service.create_candidate(file_id, "candidate content")


@pytest.mark.asyncio
async def test_get_batch_history_failure():
    service = BatchService()
    service.logger = MagicMock()
    service.database = AsyncMock()

    service.database.get_batch_history.side_effect = RuntimeError("DB failure")

    with pytest.raises(RuntimeError, match="Error retrieving batch history"):
        await service.get_batch_history("user1", limit=5, offset=0)


@pytest.mark.asyncio
async def test_delete_file_logs_exception():
    service = BatchService()
    service.database = AsyncMock()
    file_id = str(uuid4())
    batch_id = str(uuid4())
    mock_file = MagicMock()
    mock_file.batch_id = batch_id
    mock_file.blob_path = "blob"
    mock_file.translated_path = "translated"
    with patch("common.storage.blob_factory.BlobStorageFactory.get_storage", new_callable=AsyncMock) as mock_storage:
        mock_storage.return_value.delete_file.return_value = True
        service.database.get_file.return_value = mock_file
        service.database.get_batch.return_value = {"id": str(batch_id)}
        service.database.get_batch_files.return_value = [1, 2]

        with patch("common.models.api.FileRecord.fromdb", return_value=mock_file), \
             patch("common.models.api.BatchRecord.fromdb") as mock_batch_record:
            mock_record = MagicMock()
            mock_record.file_count = 2
            mock_batch_record.return_value = mock_record
            service.database.update_batch.side_effect = Exception("Update failed")

            result = await service.delete_file(file_id, "user1")
            assert result["message"] == "File deleted successfully"


@pytest.mark.asyncio
async def test_upload_file_to_batch_batchrecord():
    service = BatchService()
    service.database = AsyncMock()
    file = UploadFile(filename="test.txt", file=BytesIO(b"test content"))
    batch_id = str(uuid4())
    file_id = str(uuid4())

    # Create a mock BatchRecord instance
    mock_batch_record = MagicMock(spec=BatchRecord)
    mock_batch_record.file_count = 0
    mock_batch_record.updated_at = None

    with patch("uuid.uuid4", return_value=file_id), \
         patch("common.storage.blob_factory.BlobStorageFactory.get_storage", new_callable=AsyncMock) as mock_storage, \
         patch("common.models.api.FileRecord.fromdb", return_value={"blob_path": "blob/path"}), \
         patch("common.models.api.BatchRecord.fromdb", return_value=mock_batch_record):

        mock_storage.return_value.upload_file.return_value = None
        # This will trigger the BatchRecord path
        service.database.get_batch.side_effect = [mock_batch_record]
        service.database.get_batch_files.return_value = ["file1", "file2"]
        service.database.get_file.return_value = {"file_id": file_id}
        service.database.update_batch_entry.return_value = mock_batch_record

        result = await service.upload_file_to_batch(batch_id, "user1", file)
        assert "batch" in result
        assert "file" in result


@pytest.mark.asyncio
async def test_upload_file_to_batch_unknown_type():
    service = BatchService()
    service.database = AsyncMock()
    file = UploadFile(filename="file.txt", file=BytesIO(b"data"))
    file_id = str(uuid4())

    with patch("uuid.uuid4", return_value=file_id), \
         patch("common.storage.blob_factory.BlobStorageFactory.get_storage", new_callable=AsyncMock) as mock_storage, \
         patch("common.models.api.FileRecord.fromdb", return_value={"blob_path": "path"}):

        mock_storage.return_value.upload_file.return_value = None
        service.database.get_batch.side_effect = [object()]  # Unknown type
        service.database.get_batch_files.return_value = []
        service.database.get_file.return_value = {"file_id": file_id}

        with pytest.raises(RuntimeError, match="File upload failed"):
            await service.upload_file_to_batch("batch123", "user1", file)


@pytest.mark.asyncio
@patch("common.services.batch_service.BlobStorageFactory.get_storage", new_callable=AsyncMock)
@patch("common.models.api.FileRecord.fromdb")
@patch("common.models.api.BatchRecord.fromdb")
async def test_get_file_report_ioerror(mock_batch_fromdb, mock_file_fromdb, mock_get_storage):
    service = BatchService()
    service.database = AsyncMock()
    file_id = "file123"
    mock_file = {"batch_id": uuid4(), "translated_path": "some/path"}
    mock_batch = {"batch_id": "batch123"}
    mock_logs = [{"log": "log1"}]

    mock_file_fromdb.return_value = MagicMock(dict=lambda: mock_file, batch_id=mock_file["batch_id"], translated_path="some/path")
    mock_batch_fromdb.return_value = MagicMock(dict=lambda: mock_batch)
    service.database.get_file.return_value = mock_file
    service.database.get_batch_from_id.return_value = mock_batch
    service.database.get_file_logs.return_value = mock_logs

    mock_storage = AsyncMock()
    mock_storage.get_file.side_effect = IOError("Boom")
    mock_get_storage.return_value = mock_storage

    result = await service.get_file_report(file_id)
    assert result["translated_content"] == ""


@pytest.mark.asyncio
@patch("common.models.api.BatchRecord.fromdb")
async def test_get_batch_summary_log_exception(mock_batch_fromdb):
    service = BatchService()
    service.database = AsyncMock()
    mock_batch = {"batch_id": "batch1"}
    mock_batch_record = MagicMock(dict=lambda: {"batch_id": "batch1"})
    mock_batch_fromdb.return_value = mock_batch_record

    service.database.get_batch.return_value = mock_batch
    service.database.get_batch_files.return_value = [{"file_id": "file1", "translated_path": None}]
    service.database.get_file_logs.side_effect = Exception("DB log fail")

    result = await service.get_batch_summary("batch1", "user1")
    assert result["files"][0]["logs"] == []


@pytest.mark.asyncio
async def test_update_file_not_found():
    service = BatchService()
    service.database = AsyncMock()
    service.database.get_file.return_value = None
    with pytest.raises(HTTPException) as exc:
        await service.update_file("invalid_id", ProcessStatus.COMPLETED, FileResult.SUCCESS, 0, 0)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_candidate_success_flow():
    service = BatchService()
    service.database = AsyncMock()
    file_id = str(uuid4())
    batch_id = str(uuid4())
    user_id = "user1"

    mock_file = {"batch_id": batch_id, "original_name": "test.txt"}
    mock_batch = {"user_id": user_id}

    with patch("common.models.api.FileRecord.fromdb", return_value=MagicMock(original_name="test.txt", batch_id=batch_id)), \
         patch("common.models.api.BatchRecord.fromdb", return_value=MagicMock(user_id=user_id)), \
         patch("common.storage.blob_factory.BlobStorageFactory.get_storage", new_callable=AsyncMock) as mock_storage, \
         patch.object(service, "get_file_counts", return_value=(0, 0)), \
         patch.object(service, "update_file_record", new_callable=AsyncMock):

        service.database.get_file.return_value = mock_file
        service.database.get_batch_from_id.return_value = mock_batch
        mock_storage.return_value.upload_file.return_value = None

        await service.create_candidate(file_id, "candidate content")
