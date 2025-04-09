import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from fastapi import UploadFile, HTTPException

from common.services.batch_service import BatchService
from common.models.api import (
    FileRecord,
    BatchRecord,
    FileResult,
    LogType,
    AgentType,
    ProcessStatus,
)

# ---------- Helpers ----------
def make_file_record(**overrides):
    return FileRecord(
        file_id=overrides.get("file_id", "file1"),
        batch_id=overrides.get("batch_id", "batch123"),
        original_name=overrides.get("original_name", "file.txt"),
        blob_path=overrides.get("blob_path", "blob/path/file.txt"),
        translated_path=overrides.get("translated_path", "translated/file.txt"),
        status=overrides.get("status", ProcessStatus.READY_TO_PROCESS),
        error_count=overrides.get("error_count", 0),
        syntax_count=overrides.get("syntax_count", 0),
        created_at=overrides.get("created_at", datetime.utcnow()),
        updated_at=overrides.get("updated_at", datetime.utcnow())
    )

def make_batch_record(**overrides):
    return BatchRecord(
        batch_id=overrides.get("batch_id", "batch123"),
        user_id=overrides.get("user_id", "user1"),
        file_count=overrides.get("file_count", 1),
        created_at=overrides.get("created_at", datetime.utcnow().isoformat()),
        updated_at=overrides.get("updated_at", datetime.utcnow().isoformat()),
        status=overrides.get("status", ProcessStatus.READY_TO_PROCESS),
    )

# ---------- Fixtures ----------
@pytest.fixture
def batch_service():
    service = BatchService()
    service.logger = MagicMock()
    service.database = AsyncMock()
    return service

# ---------- Tests ----------
@pytest.mark.asyncio
async def test_get_batch_success(batch_service):
    batch_id = uuid4()
    user_id = "test_user"
    batch_service.database.get_batch.return_value = {"batch_id": str(batch_id)}
    batch_service.database.get_batch_files.return_value = [{"file_id": "f1"}]

    result = await batch_service.get_batch(batch_id, user_id)
    assert result["batch"]["batch_id"] == str(batch_id)
    assert result["files"] == [{"file_id": "f1"}]

@pytest.mark.asyncio
async def test_get_file_not_found(batch_service):
    batch_service.database.get_file.return_value = None
    result = await batch_service.get_file("missing_file_id")
    assert result is None

def test_is_valid_uuid_valid(batch_service):
    assert batch_service.is_valid_uuid(str(uuid4())) is True

def test_generate_file_path(batch_service):
    path = batch_service.generate_file_path("batch1", "user1", "file1", "file@.txt")
    assert path == "user1/batch1/file1/file_.txt"

@pytest.mark.asyncio
@patch("common.storage.blob_factory.BlobStorageFactory.get_storage", new_callable=AsyncMock)
async def test_get_file_report_success(mock_storage, batch_service):
    file_id = "file1"
    file_record = make_file_record(file_id=file_id)
    batch_record = make_batch_record(batch_id=file_record.batch_id)

    batch_service.database.get_file.return_value = file_record.dict()
    batch_service.database.get_batch_from_id.return_value = batch_record.dict()
    batch_service.database.get_file_logs.return_value = [{"log_type": "INFO"}]

    with patch("common.models.api.FileRecord.fromdb", return_value=file_record), \
         patch("common.models.api.BatchRecord.fromdb", return_value=batch_record), \
         patch.object(mock_storage, "get_file", new=AsyncMock(return_value="translated content")):

        result = await batch_service.get_file_report(file_id)
        assert result["translated_content"] == "translated content"

@pytest.mark.asyncio
@patch("common.storage.blob_factory.BlobStorageFactory.get_storage", new_callable=AsyncMock)
async def test_upload_file_to_batch_creates_batch(mock_storage, batch_service):
    batch_id = str(uuid4())
    user_id = "test_user"
    filename = "doc.txt"
    file_mock = MagicMock(spec=UploadFile)
    file_mock.filename = filename
    file_mock.content_type = "text/plain"
    file_mock.read = AsyncMock(return_value=b"content")

    # Simulate batch creation
    batch_service.database.get_batch.return_value = None
    batch_service.database.create_batch.return_value = {"batch_id": batch_id}
    batch_service.database.get_batch_files.return_value = [{"file_id": "f1"}]
    batch_service.database.get_file.return_value = {"file_id": "new_id"}

    mock_storage.upload_file.return_value = None

    file_record = make_file_record(file_id="new_id", batch_id=batch_id)

    with patch("common.models.api.FileRecord.fromdb", return_value=file_record), \
         patch("uuid.uuid4", return_value=uuid4()):

        result = await batch_service.upload_file_to_batch(batch_id, user_id, file_mock)
        assert "file" in result
        assert "batch" in result

@pytest.mark.asyncio
@patch("common.storage.blob_factory.BlobStorageFactory.get_storage", new_callable=AsyncMock)
async def test_delete_batch_and_files_batch_not_found(mock_storage, batch_service):
    batch_service.database.get_batch.return_value = None
    result = await batch_service.delete_batch_and_files("batch123", "user1")
    assert result["message"] == "Batch not found"

@pytest.mark.asyncio
async def test_update_file_not_found(batch_service):
    batch_service.database.get_file.return_value = None
    with pytest.raises(HTTPException) as exc_info:
        await batch_service.update_file("file123", ProcessStatus.COMPLETED, FileResult.SUCCESS, 1, 2)
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_batch_files_final_update_with_error_log(batch_service):
    file_id = str(uuid4())
    file_record = make_file_record(file_id=file_id, translated_path=None, status=ProcessStatus.IN_PROGRESS)

    batch_service.database.get_batch_files.return_value = [file_record.dict()]
    batch_service.get_file_counts = AsyncMock(return_value=(1, 0))
    batch_service.update_file_record = AsyncMock()
    batch_service.create_file_log = AsyncMock()

    with patch("common.models.api.FileRecord.fromdb", return_value=file_record):
        await batch_service.batch_files_final_update("batch1")
        batch_service.update_file_record.assert_awaited()
