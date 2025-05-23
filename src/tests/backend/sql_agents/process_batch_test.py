import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from azure.core.exceptions import ServiceResponseError as ServiceResponseException

from common.models.api import FileRecord, FileResult, LogType, ProcessStatus

import pytest

from semantic_kernel.contents import AuthorRole

from sql_agents.helpers.models import AgentType
from sql_agents.process_batch import add_rai_disclaimer, process_batch_async, process_error


@pytest.mark.asyncio
@patch("sql_agents.process_batch.add_rai_disclaimer", return_value="SELECT * FROM converted;")
@patch("sql_agents.process_batch.process_error", new_callable=AsyncMock)
@patch("sql_agents.process_batch.is_text")
@patch("sql_agents.process_batch.send_status_update")
@patch("sql_agents.process_batch.convert_script", new_callable=AsyncMock)
@patch("sql_agents.process_batch.SqlAgents.create", new_callable=AsyncMock)
@patch("sql_agents.process_batch.AzureAIAgent.create_client")
@patch("sql_agents.process_batch.DefaultAzureCredential")
@patch("sql_agents.process_batch.BatchService")
@patch("sql_agents.process_batch.BlobStorageFactory.get_storage", new_callable=AsyncMock)
async def test_process_batch_async_success(
    mock_get_storage,
    mock_batch_service_cls,
    mock_creds_cls,
    mock_create_client,
    mock_sql_agents_create,
    mock_convert_script,
    mock_send_status_update,
    mock_is_text,
    mock_process_error,
    mock_add_disclaimer,
):
    # UUID and timestamps for mocks
    file_id = str(UUID(int=0))
    now = datetime.datetime.utcnow()

    # Mock file dict (simulates DB record)
    file_dict = {
        "file_id": file_id,
        "blob_path": "blob/path",
        "batch_id": "1",
        "original_name": "file.sql",
        "translated_path": "translated.sql",
        "status": ProcessStatus.READY_TO_PROCESS.value,
        "error_count": 0,
        "syntax_count": 0,
        "created_at": now,
        "updated_at": now,
    }

    # Setup BlobStorage mock
    mock_storage = AsyncMock()
    mock_storage.get_file.return_value = "SELECT * FROM dummy;"
    mock_get_storage.return_value = mock_storage

    # Setup BatchService mock
    mock_batch_service = AsyncMock()
    mock_batch_service.database.get_batch_files.return_value = [file_dict]
    mock_batch_service.initialize_database.return_value = None
    mock_batch_service.update_batch.return_value = None
    mock_batch_service.update_file_record.return_value = None
    mock_batch_service.create_candidate.return_value = None
    mock_batch_service.update_file_counts.return_value = None
    mock_batch_service.batch_files_final_update.return_value = None
    mock_batch_service.create_file_log.return_value = None
    mock_batch_service_cls.return_value = mock_batch_service

    # Mock DefaultAzureCredential async context manager
    mock_creds = MagicMock()
    mock_creds.__aenter__.return_value = mock_creds
    mock_creds.__aexit__.return_value = None
    mock_creds_cls.return_value = mock_creds

    # Mock AzureAIAgent.create_client async context manager
    mock_client = MagicMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_create_client.return_value = mock_client

    # Mock SqlAgents.create and its delete_agents
    mock_agents = AsyncMock()
    mock_agents.delete_agents.return_value = None
    mock_sql_agents_create.return_value = mock_agents

    # Successful text file path
    mock_is_text.return_value = True
    mock_convert_script.return_value = "SELECT * FROM converted;"

    # Mock the FileRecord.fromdb method to return a mock file_record
    mock_file_record = MagicMock()
    mock_file_record.status = ProcessStatus.READY_TO_PROCESS
    mock_file_record.file_id = file_id
    mock_file_record.blob_path = file_dict["blob_path"]
    mock_file_record.batch_id = file_dict["batch_id"]
    mock_file_record.file_result = FileResult.SUCCESS
    mock_file_record.error_count = 0

    # Patch FileRecord to return the mock
    with patch("sql_agents.process_batch.FileRecord.fromdb", return_value=mock_file_record):
        # Execute function
        await process_batch_async("1", "informix", "tsql")

    # Assertions
    mock_batch_service.update_file_record.assert_called_with(mock_file_record)
    # mock_send_status_update.assert_called_once()
    mock_process_error.assert_not_called()


@pytest.mark.asyncio
@patch("sql_agents.process_batch.add_rai_disclaimer", return_value="SELECT * FROM converted;")
@patch("sql_agents.process_batch.process_error", new_callable=AsyncMock)
@patch("sql_agents.process_batch.is_text")
@patch("sql_agents.process_batch.send_status_update")
@patch("sql_agents.process_batch.convert_script", new_callable=AsyncMock)
@patch("sql_agents.process_batch.SqlAgents.create", new_callable=AsyncMock)
@patch("sql_agents.process_batch.AzureAIAgent.create_client")
@patch("sql_agents.process_batch.DefaultAzureCredential")
@patch("sql_agents.process_batch.BatchService")
@patch("sql_agents.process_batch.BlobStorageFactory.get_storage", new_callable=AsyncMock)
async def test_process_batch_async_invalid_text_file(
    mock_get_storage,
    mock_batch_service_cls,
    mock_creds_cls,
    mock_create_client,
    mock_sql_agents_create,
    mock_convert_script,
    mock_send_status_update,
    mock_is_text,
    mock_process_error,
    mock_add_disclaimer,
):
    # UUID and timestamps for mocks
    file_id = str(UUID(int=1))
    now = datetime.datetime.utcnow()

    file_dict = {
        "file_id": file_id,
        "blob_path": "invalid/blob/path.sql",
        "batch_id": "1",
        "original_name": "bad.sql",
        "translated_path": "translated.sql",
        "status": ProcessStatus.READY_TO_PROCESS.value,
        "error_count": 0,
        "syntax_count": 0,
        "created_at": now,
        "updated_at": now,
    }

    # Mock the BlobStorage get_file to return dummy content
    mock_storage = AsyncMock()
    mock_storage.get_file.return_value = "binary content"
    mock_get_storage.return_value = mock_storage

    # Setup BatchService mock
    mock_batch_service = AsyncMock()
    mock_batch_service.database.get_batch_files.return_value = [file_dict]
    mock_batch_service.initialize_database.return_value = None
    mock_batch_service.update_batch.return_value = None
    mock_batch_service.update_file_record.return_value = None
    mock_batch_service.create_file_log.return_value = None
    mock_batch_service_cls.return_value = mock_batch_service

    # Setup Azure credential and client mocks
    mock_creds = MagicMock()
    mock_creds.__aenter__.return_value = mock_creds
    mock_creds.__aexit__.return_value = None
    mock_creds_cls.return_value = mock_creds

    mock_client = MagicMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_create_client.return_value = mock_client

    mock_sql_agents = AsyncMock()
    mock_sql_agents.delete_agents.return_value = None
    mock_sql_agents_create.return_value = mock_sql_agents

    # Simulate non-text file
    mock_is_text.return_value = False

    # Patch FileRecord.fromdb to return a mock
    mock_file_record = MagicMock()
    mock_file_record.file_id = file_id
    mock_file_record.batch_id = file_dict["batch_id"]
    mock_file_record.blob_path = file_dict["blob_path"]
    mock_file_record.status = ProcessStatus.READY_TO_PROCESS
    mock_file_record.file_result = FileResult.SUCCESS
    mock_file_record.error_count = 0

    with patch("sql_agents.process_batch.FileRecord.fromdb", return_value=mock_file_record):
        await process_batch_async("1", "informix", "tsql")

    # Assertions: ensure correct flow for invalid text file
    mock_is_text.assert_called_once()
    mock_batch_service.create_file_log.assert_called_once_with(
        str(file_id),
        "File is not a valid text file. Skipping.",
        "",
        LogType.ERROR,
        AgentType.ALL,
        AuthorRole.ASSISTANT,
    )
    mock_send_status_update.assert_called_once()
    mock_batch_service.update_file_record.assert_called_with(mock_file_record)
    assert mock_file_record.status == ProcessStatus.COMPLETED
    assert mock_file_record.file_result == FileResult.ERROR
    assert mock_file_record.error_count == 1


@pytest.mark.asyncio
@patch("sql_agents.process_batch.add_rai_disclaimer", return_value="SELECT * FROM converted;")
@patch("sql_agents.process_batch.process_error", new_callable=AsyncMock)
@patch("sql_agents.process_batch.is_text")
@patch("sql_agents.process_batch.send_status_update")
@patch("sql_agents.process_batch.convert_script", new_callable=AsyncMock)
@patch("sql_agents.process_batch.SqlAgents.create", new_callable=AsyncMock)
@patch("sql_agents.process_batch.AzureAIAgent.create_client")
@patch("sql_agents.process_batch.DefaultAzureCredential")
@patch("sql_agents.process_batch.BatchService")
@patch("sql_agents.process_batch.BlobStorageFactory.get_storage", new_callable=AsyncMock)
async def test_process_batch_unicode_decode_error(
    mock_get_storage,
    mock_batch_service_cls,
    mock_creds_cls,
    mock_create_client,
    mock_sql_agents_create,
    mock_convert_script,
    mock_send_status_update,
    mock_is_text,
    mock_process_error,
    mock_add_disclaimer,
):
    file_id = str(UUID(int=2))
    now = datetime.datetime.utcnow()
    file_dict = {
        "file_id": file_id,
        "blob_path": "bad/path.sql",
        "batch_id": "2",
        "original_name": "bad.sql",
        "translated_path": "converted.sql",
        "status": ProcessStatus.READY_TO_PROCESS.value,
        "error_count": 0,
        "syntax_count": 0,
        "created_at": now,
        "updated_at": now,
    }

    # Trigger UnicodeDecodeError on get_file
    mock_storage = AsyncMock()
    mock_storage.get_file.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "error")
    mock_get_storage.return_value = mock_storage

    mock_batch_service = AsyncMock()
    mock_batch_service.database.get_batch_files.return_value = [file_dict]
    mock_batch_service_cls.return_value = mock_batch_service

    mock_creds_cls.return_value.__aenter__.return_value = MagicMock()
    mock_create_client.return_value.__aenter__.return_value = MagicMock()
    mock_sql_agents_create.return_value = AsyncMock()

    mock_file_record = MagicMock()
    mock_file_record.file_id = file_id
    mock_file_record.batch_id = "2"
    mock_file_record.blob_path = "bad/path.sql"
    with patch("sql_agents.process_batch.FileRecord.fromdb", return_value=mock_file_record):
        await process_batch_async("2", "informix", "tsql")

    mock_process_error.assert_called_once()


@pytest.mark.asyncio
@patch("sql_agents.process_batch.process_error", new_callable=AsyncMock)
@patch("sql_agents.process_batch.is_text")
@patch("sql_agents.process_batch.SqlAgents.create", new_callable=AsyncMock)
@patch("sql_agents.process_batch.AzureAIAgent.create_client")
@patch("sql_agents.process_batch.DefaultAzureCredential")
@patch("sql_agents.process_batch.BatchService")
@patch("sql_agents.process_batch.BlobStorageFactory.get_storage", new_callable=AsyncMock)
async def test_process_batch_service_response_exception(
    mock_get_storage,
    mock_batch_service_cls,
    mock_creds_cls,
    mock_create_client,
    mock_sql_agents_create,
    mock_is_text,
    mock_process_error,
):
    file_id = str(UUID(int=3))
    now = datetime.datetime.utcnow()
    file_dict = {
        "file_id": file_id,
        "blob_path": "some/blob.sql",
        "batch_id": "3",
        "original_name": "serviceerror.sql",
        "translated_path": "translated.sql",
        "status": ProcessStatus.READY_TO_PROCESS.value,
        "error_count": 0,
        "syntax_count": 0,
        "created_at": now,
        "updated_at": now,
    }

    # Trigger ServiceResponseException
    mock_storage = AsyncMock()
    mock_storage.get_file.side_effect = ServiceResponseException("Service error")
    mock_get_storage.return_value = mock_storage

    mock_batch_service = AsyncMock()
    mock_batch_service.database.get_batch_files.return_value = [file_dict]
    mock_batch_service_cls.return_value = mock_batch_service

    mock_creds_cls.return_value.__aenter__.return_value = MagicMock()
    mock_create_client.return_value.__aenter__.return_value = MagicMock()
    mock_sql_agents_create.return_value = AsyncMock()

    mock_file_record = MagicMock()
    mock_file_record.file_id = file_id
    mock_file_record.batch_id = "3"
    mock_file_record.blob_path = "some/blob.sql"

    with patch("sql_agents.process_batch.FileRecord.fromdb", return_value=mock_file_record):
        await process_batch_async("3", "informix", "tsql")

    mock_process_error.assert_called_once()


@pytest.mark.asyncio
@patch("sql_agents.process_batch.process_error", new_callable=AsyncMock)
@patch("sql_agents.process_batch.is_text")
@patch("sql_agents.process_batch.SqlAgents.create", new_callable=AsyncMock)
@patch("sql_agents.process_batch.AzureAIAgent.create_client")
@patch("sql_agents.process_batch.DefaultAzureCredential")
@patch("sql_agents.process_batch.BatchService")
@patch("sql_agents.process_batch.BlobStorageFactory.get_storage", new_callable=AsyncMock)
async def test_process_batch_generic_exception(
    mock_get_storage,
    mock_batch_service_cls,
    mock_creds_cls,
    mock_create_client,
    mock_sql_agents_create,
    mock_is_text,
    mock_process_error,
):
    file_id = str(UUID(int=4))
    now = datetime.datetime.utcnow()
    file_dict = {
        "file_id": file_id,
        "blob_path": "generic/blob.sql",
        "batch_id": "4",
        "original_name": "fail.sql",
        "translated_path": "translated.sql",
        "status": ProcessStatus.READY_TO_PROCESS.value,
        "error_count": 0,
        "syntax_count": 0,
        "created_at": now,
        "updated_at": now,
    }

    # Trigger generic exception
    mock_storage = AsyncMock()
    mock_storage.get_file.side_effect = Exception("Unexpected failure")
    mock_get_storage.return_value = mock_storage

    mock_batch_service = AsyncMock()
    mock_batch_service.database.get_batch_files.return_value = [file_dict]
    mock_batch_service_cls.return_value = mock_batch_service

    mock_creds_cls.return_value.__aenter__.return_value = MagicMock()
    mock_create_client.return_value.__aenter__.return_value = MagicMock()
    mock_sql_agents_create.return_value = AsyncMock()

    mock_file_record = MagicMock()
    mock_file_record.file_id = file_id
    mock_file_record.batch_id = "4"
    mock_file_record.blob_path = "generic/blob.sql"

    with patch("sql_agents.process_batch.FileRecord.fromdb", return_value=mock_file_record):
        await process_batch_async("4", "informix", "tsql")

    mock_process_error.assert_called_once()


@pytest.mark.asyncio
@patch("sql_agents.process_batch.send_status_update")
async def test_process_error(mock_send_status_update):
    # Setup complete FileRecord with required fields
    file_record = FileRecord(
        file_id="1",
        batch_id="b1",
        blob_path="blobpath",
        original_name="file.sql",
        translated_path="translated.sql",
        status=ProcessStatus.READY_TO_PROCESS,
        error_count=0,
        syntax_count=0,
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
    )

    batch_service = AsyncMock()

    await process_error(ValueError("Test error"), file_record, batch_service)

    batch_service.create_file_log.assert_awaited_once()
    mock_send_status_update.assert_called_once()
    assert mock_send_status_update.call_args[1]["status"].file_result == FileResult.ERROR


def test_add_rai_disclaimer():
    original = "SELECT * FROM test;"
    result = add_rai_disclaimer(original)
    assert result.startswith("/*")
    assert original in result
