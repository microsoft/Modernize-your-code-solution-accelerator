"""Tests for sql_agents/process_batch.py module."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.sql_agents.process_batch import (
    process_batch_async,
    process_error,
    add_rai_disclaimer,
)
from backend.common.models.api import FileRecord, ProcessStatus, FileResult


def create_mock_file_data(file_id, batch_id, status="pending"):
    """Helper to create complete mock file data with all required fields."""
    return {
        "file_id": file_id,
        "batch_id": batch_id,
        "original_name": "test.sql",
        "blob_path": "/path/to/file",
        "translated_path": "/path/to/translated",
        "status": status,
        "file_result": None,
        "error_count": 0,
        "syntax_count": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


class TestAddRaiDisclaimer:
    """Tests for add_rai_disclaimer function."""

    def test_add_rai_disclaimer(self):
        """Test adding RAI disclaimer to query."""
        query = "SELECT * FROM users"
        
        result = add_rai_disclaimer(query)
        
        assert "AI-generated content may be incorrect" in result
        assert query in result
        assert result.startswith("/*")

    def test_add_rai_disclaimer_empty_query(self):
        """Test adding disclaimer to empty query."""
        result = add_rai_disclaimer("")
        
        assert "AI-generated content may be incorrect" in result

    def test_add_rai_disclaimer_complex_query(self):
        """Test adding disclaimer to complex query."""
        query = """
        SELECT u.id, u.name
        FROM users u
        WHERE u.active = 1
        """
        
        result = add_rai_disclaimer(query)
        
        assert "AI-generated content may be incorrect" in result
        assert query in result


class TestProcessError:
    """Tests for process_error function."""

    @pytest.mark.asyncio
    async def test_process_error(self):
        """Test processing error for a file."""
        file_record = MagicMock()
        file_record.file_id = str(uuid.uuid4())
        file_record.batch_id = str(uuid.uuid4())
        
        mock_batch_service = MagicMock()
        mock_batch_service.create_file_log = AsyncMock()
        
        with patch("backend.sql_agents.process_batch.send_status_update") as mock_send:
            await process_error(
                Exception("Test error"),
                file_record,
                mock_batch_service
            )
            
            mock_batch_service.create_file_log.assert_called_once()
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_error_with_different_exception_types(self):
        """Test processing different exception types."""
        file_record = MagicMock()
        file_record.file_id = str(uuid.uuid4())
        file_record.batch_id = str(uuid.uuid4())
        
        mock_batch_service = MagicMock()
        mock_batch_service.create_file_log = AsyncMock()
        
        with patch("backend.sql_agents.process_batch.send_status_update"):
            # Test with ValueError
            await process_error(ValueError("Value error"), file_record, mock_batch_service)
            
            # Test with RuntimeError
            await process_error(RuntimeError("Runtime error"), file_record, mock_batch_service)
            
            assert mock_batch_service.create_file_log.call_count == 2


class TestProcessBatchAsync:
    """Tests for process_batch_async function."""

    @pytest.mark.asyncio
    async def test_process_batch_no_files(self):
        """Test processing batch with no files - exception is caught and logged."""
        batch_id = str(uuid.uuid4())
        
        mock_storage = AsyncMock()
        mock_batch_service = MagicMock()
        mock_batch_service.initialize_database = AsyncMock()
        mock_batch_service.database = MagicMock()
        mock_batch_service.database.get_batch_files = AsyncMock(return_value=None)
        mock_batch_service.update_batch = AsyncMock()
        
        with patch("backend.sql_agents.process_batch.BlobStorageFactory.get_storage", new_callable=AsyncMock, return_value=mock_storage):
            with patch("backend.sql_agents.process_batch.BatchService", return_value=mock_batch_service):
                with patch("backend.sql_agents.process_batch.get_sql_agents", return_value=None):
                    # The function catches the exception internally, so it won't raise
                    await process_batch_async(batch_id)
                    
                    # Batch should be marked as failed because agents are None
                    mock_batch_service.update_batch.assert_called()

    @pytest.mark.asyncio
    async def test_process_batch_no_agents(self):
        """Test processing batch when agents not initialized."""
        batch_id = str(uuid.uuid4())
        
        mock_storage = AsyncMock()
        mock_batch_service = MagicMock()
        mock_batch_service.initialize_database = AsyncMock()
        mock_batch_service.database = MagicMock()
        mock_batch_service.database.get_batch_files = AsyncMock(return_value=[{"file_id": "test"}])
        mock_batch_service.update_batch = AsyncMock()
        
        with patch("backend.sql_agents.process_batch.BlobStorageFactory.get_storage", new_callable=AsyncMock, return_value=mock_storage):
            with patch("backend.sql_agents.process_batch.BatchService", return_value=mock_batch_service):
                with patch("backend.sql_agents.process_batch.get_sql_agents", return_value=None):
                    await process_batch_async(batch_id)
                    
                    # Should update batch to failed status
                    mock_batch_service.update_batch.assert_called()

    @pytest.mark.asyncio
    async def test_process_batch_with_files(self):
        """Test processing batch with files."""
        batch_id = str(uuid.uuid4())
        file_id = str(uuid.uuid4())
        
        mock_storage = AsyncMock()
        mock_storage.get_file = AsyncMock(return_value="SELECT * FROM test")
        
        mock_batch_service = MagicMock()
        mock_batch_service.initialize_database = AsyncMock()
        mock_batch_service.database = MagicMock()
        mock_batch_service.database.get_batch_files = AsyncMock(return_value=[
            create_mock_file_data(file_id, batch_id)
        ])
        mock_batch_service.update_batch = AsyncMock()
        mock_batch_service.update_file_record = AsyncMock()
        mock_batch_service.create_file_log = AsyncMock()
        mock_batch_service.create_candidate = AsyncMock()
        mock_batch_service.batch_files_final_update = AsyncMock()
        mock_batch_service.update_file_counts = AsyncMock()
        
        mock_sql_agents = MagicMock()
        mock_sql_agents.agent_config = MagicMock()
        mock_sql_agents.idx_agents = {}
        
        with patch("backend.sql_agents.process_batch.BlobStorageFactory.get_storage", new_callable=AsyncMock, return_value=mock_storage):
            with patch("backend.sql_agents.process_batch.BatchService", return_value=mock_batch_service):
                with patch("backend.sql_agents.process_batch.get_sql_agents", return_value=mock_sql_agents):
                    with patch("backend.sql_agents.process_batch.update_agent_config", new_callable=AsyncMock):
                        with patch("backend.sql_agents.process_batch.convert_script", new_callable=AsyncMock, return_value="SELECT * FROM test_migrated"):
                            with patch("backend.sql_agents.process_batch.send_status_update"):
                                await process_batch_async(batch_id)

    @pytest.mark.asyncio
    async def test_process_batch_invalid_file(self):
        """Test processing batch with invalid file (not text)."""
        batch_id = str(uuid.uuid4())
        file_id = str(uuid.uuid4())
        
        mock_storage = AsyncMock()
        mock_storage.get_file = AsyncMock(return_value="")  # Empty content
        
        mock_batch_service = MagicMock()
        mock_batch_service.initialize_database = AsyncMock()
        mock_batch_service.database = MagicMock()
        mock_batch_service.database.get_batch_files = AsyncMock(return_value=[
            create_mock_file_data(file_id, batch_id)
        ])
        mock_batch_service.update_batch = AsyncMock()
        mock_batch_service.update_file_record = AsyncMock()
        mock_batch_service.create_file_log = AsyncMock()
        mock_batch_service.batch_files_final_update = AsyncMock()
        
        mock_sql_agents = MagicMock()
        mock_sql_agents.agent_config = MagicMock()
        
        with patch("backend.sql_agents.process_batch.BlobStorageFactory.get_storage", new_callable=AsyncMock, return_value=mock_storage):
            with patch("backend.sql_agents.process_batch.BatchService", return_value=mock_batch_service):
                with patch("backend.sql_agents.process_batch.get_sql_agents", return_value=mock_sql_agents):
                    with patch("backend.sql_agents.process_batch.update_agent_config", new_callable=AsyncMock):
                        with patch("backend.sql_agents.process_batch.is_text", return_value=False):
                            with patch("backend.sql_agents.process_batch.send_status_update"):
                                await process_batch_async(batch_id)
                                
                                # Should create file log for invalid file
                                mock_batch_service.create_file_log.assert_called()

    @pytest.mark.asyncio
    async def test_process_batch_unicode_decode_error(self):
        """Test processing batch with UnicodeDecodeError."""
        batch_id = str(uuid.uuid4())
        file_id = str(uuid.uuid4())
        
        mock_storage = AsyncMock()
        mock_storage.get_file = AsyncMock(side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "test"))
        
        mock_batch_service = MagicMock()
        mock_batch_service.initialize_database = AsyncMock()
        mock_batch_service.database = MagicMock()
        mock_batch_service.database.get_batch_files = AsyncMock(return_value=[
            create_mock_file_data(file_id, batch_id)
        ])
        mock_batch_service.update_batch = AsyncMock()
        mock_batch_service.update_file_record = AsyncMock()
        mock_batch_service.create_file_log = AsyncMock()
        mock_batch_service.batch_files_final_update = AsyncMock()
        
        mock_sql_agents = MagicMock()
        mock_sql_agents.agent_config = MagicMock()
        
        with patch("backend.sql_agents.process_batch.BlobStorageFactory.get_storage", new_callable=AsyncMock, return_value=mock_storage):
            with patch("backend.sql_agents.process_batch.BatchService", return_value=mock_batch_service):
                with patch("backend.sql_agents.process_batch.get_sql_agents", return_value=mock_sql_agents):
                    with patch("backend.sql_agents.process_batch.update_agent_config", new_callable=AsyncMock):
                        with patch("backend.sql_agents.process_batch.send_status_update"):
                            await process_batch_async(batch_id)

    @pytest.mark.asyncio
    async def test_process_batch_conversion_returns_none(self):
        """Test processing batch when conversion returns None."""
        batch_id = str(uuid.uuid4())
        file_id = str(uuid.uuid4())
        
        mock_storage = AsyncMock()
        mock_storage.get_file = AsyncMock(return_value="SELECT * FROM test")
        
        mock_batch_service = MagicMock()
        mock_batch_service.initialize_database = AsyncMock()
        mock_batch_service.database = MagicMock()
        mock_batch_service.database.get_batch_files = AsyncMock(return_value=[
            create_mock_file_data(file_id, batch_id)
        ])
        mock_batch_service.update_batch = AsyncMock()
        mock_batch_service.update_file_record = AsyncMock()
        mock_batch_service.create_file_log = AsyncMock()
        mock_batch_service.batch_files_final_update = AsyncMock()
        mock_batch_service.update_file_counts = AsyncMock()
        
        mock_sql_agents = MagicMock()
        mock_sql_agents.agent_config = MagicMock()
        mock_sql_agents.idx_agents = {}
        
        with patch("backend.sql_agents.process_batch.BlobStorageFactory.get_storage", new_callable=AsyncMock, return_value=mock_storage):
            with patch("backend.sql_agents.process_batch.BatchService", return_value=mock_batch_service):
                with patch("backend.sql_agents.process_batch.get_sql_agents", return_value=mock_sql_agents):
                    with patch("backend.sql_agents.process_batch.update_agent_config", new_callable=AsyncMock):
                        with patch("backend.sql_agents.process_batch.convert_script", new_callable=AsyncMock, return_value=None):
                            with patch("backend.sql_agents.process_batch.send_status_update"):
                                await process_batch_async(batch_id)
                                
                                # Should call update_file_counts for failed conversion
                                mock_batch_service.update_file_counts.assert_called()
