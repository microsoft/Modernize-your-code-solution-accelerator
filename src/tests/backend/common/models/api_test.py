import pytest
from uuid import uuid4
from datetime import datetime
from backend.common.models.api import (
    FileLog, FileRecord, FileProcessUpdate, FileProcessUpdateJSONEncoder,
    QueueBatch, BatchRecord,
    LogType, AgentType, AuthorRole, ProcessStatus, FileResult, TranslateType
)

@pytest.fixture
def common_datetime():
    return datetime.now()

@pytest.fixture
def uuid_pair():
    return str(uuid4()), str(uuid4())

def test_filelog_fromdb_and_dict(uuid_pair, common_datetime):
    log_id, file_id = uuid_pair
    data = {
        "log_id": log_id,
        "file_id": file_id,
        "description": "test log",
        "last_candidate": "some_candidate",
        "log_type": "SUCCESS",
        "agent_type": "migrator",
        "author_role": "user",
        "timestamp": common_datetime.isoformat(),
    }
    log = FileLog.fromdb(data)
    assert log.log_id.hex == log_id.replace("-", "")
    assert log.dict()["log_type"] == "info"

    assert log.dict()["author_role"] == "user"

def test_filerecord_fromdb_and_dict(uuid_pair, common_datetime):
    file_id, batch_id = uuid_pair
    data = {
        "file_id": file_id,
        "batch_id": batch_id,
        "original_name": "file.sql",
        "blob_path": "/blob/file.sql",
        "translated_path": "/translated/file.sql",
        "status": "in_progress",
        "file_result": "warning",
        "error_count": 2,
        "syntax_count": 5,
        "created_at": common_datetime.isoformat(),
        "updated_at": common_datetime.isoformat(),
    }
    record = FileRecord.fromdb(data)
    assert record.file_id.hex == file_id.replace("-", "")
    assert record.dict()["status"] == "ready_to_process"
    assert record.dict()["file_result"] == "warning"

def test_fileprocessupdate_dict(uuid_pair):
    file_id, batch_id = uuid_pair
    update = FileProcessUpdate(
        file_id=file_id,
        batch_id=batch_id,
        process_status=ProcessStatus.COMPLETED,
        file_result=FileResult.SUCCESS,
        agent_type=AgentType.FIXER,
        agent_message="Translation done",
    )
    result = update.dict()
    assert result["process_status"] == "completed"
    assert result["file_result"] == "success"
    assert result["agent_type"] == "fixer"
    assert result["agent_message"] == "Translation done"

def test_fileprocessupdate_json_encoder(uuid_pair):
    file_id, batch_id = uuid_pair
    update = FileProcessUpdate(
        file_id=file_id,
        batch_id=batch_id,
        process_status=ProcessStatus.FAILED,
        file_result=FileResult.ERROR,
        agent_type=AgentType.HUMAN,
        agent_message="Something failed",
    )
    json_string = FileProcessUpdateJSONEncoder().encode(update)
    assert "failed" in json_string
    assert "human" in json_string

def test_queuebatch_dict(uuid_pair, common_datetime):
    batch_id, _ = uuid_pair
    batch = QueueBatch(
        batch_id=batch_id,
        user_id="user123",
        translate_from="en",
        translate_to="tsql",
        created_at=common_datetime,
        updated_at=common_datetime,
        status=ProcessStatus.IN_PROGRESS,
    )
    result = batch.dict()
    assert result["status"] == "in_process"
    assert result["user_id"] == "user123"

def test_batchrecord_fromdb_and_dict(uuid_pair, common_datetime):
    batch_id, _ = uuid_pair
    data = {
        "batch_id": batch_id,
        "user_id": "user123",
        "file_count": 3,
        "created_at": common_datetime.isoformat(),
        "updated_at": common_datetime.isoformat(),
        "status": "completed",
        "from_language": "Informix",
        "to_language": "T-SQL"
    }
    record = BatchRecord.fromdb(data)
    assert record.status == ProcessStatus.COMPLETED
    assert record.from_language == TranslateType.INFORMIX
    assert record.to_language == TranslateType.TSQL
    assert record.dict()["status"] == "completed"
