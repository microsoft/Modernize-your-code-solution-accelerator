"""Tests for sql_agents/convert_script.py module."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.sql_agents.convert_script import (
    convert_script,
    validate_migration,
)
from backend.common.models.api import FileRecord, ProcessStatus


class MockChatMessageContent:
    """Mock for ChatMessageContent."""
    
    def __init__(self, name="test", content="{}", role="assistant"):
        self.name = name
        self.content = content
        self.role = role


class TestValidateMigration:
    """Tests for validate_migration function."""

    @pytest.mark.asyncio
    async def test_validate_migration_success(self):
        """Test successful migration validation."""
        file_record = MagicMock()
        file_record.file_id = str(uuid.uuid4())
        file_record.batch_id = str(uuid.uuid4())
        
        mock_batch_service = MagicMock()
        mock_batch_service.create_file_log = AsyncMock()
        
        carry_response = MockChatMessageContent()
        
        with patch("backend.sql_agents.convert_script.send_status_update"):
            result = await validate_migration(
                "SELECT * FROM test",
                carry_response,
                file_record,
                mock_batch_service
            )
            
            assert result is True
            mock_batch_service.create_file_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_migration_empty_query(self):
        """Test validation with empty query."""
        file_record = MagicMock()
        file_record.file_id = str(uuid.uuid4())
        file_record.batch_id = str(uuid.uuid4())
        
        mock_batch_service = MagicMock()
        mock_batch_service.create_file_log = AsyncMock()
        
        carry_response = MockChatMessageContent()
        
        with patch("backend.sql_agents.convert_script.send_status_update"):
            result = await validate_migration(
                "",
                carry_response,
                file_record,
                mock_batch_service
            )
            
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_migration_none_query(self):
        """Test validation with None query."""
        file_record = MagicMock()
        file_record.file_id = str(uuid.uuid4())
        file_record.batch_id = str(uuid.uuid4())
        
        mock_batch_service = MagicMock()
        mock_batch_service.create_file_log = AsyncMock()
        
        carry_response = None
        
        with patch("backend.sql_agents.convert_script.send_status_update"):
            result = await validate_migration(
                None,
                carry_response,
                file_record,
                mock_batch_service
            )
            
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_migration_none_response(self):
        """Test validation when carry_response is None."""
        file_record = MagicMock()
        file_record.file_id = str(uuid.uuid4())
        file_record.batch_id = str(uuid.uuid4())
        
        mock_batch_service = MagicMock()
        mock_batch_service.create_file_log = AsyncMock()
        
        with patch("backend.sql_agents.convert_script.send_status_update"):
            result = await validate_migration(
                "",
                None,
                file_record,
                mock_batch_service
            )
            
            assert result is False


class TestConvertScript:
    """Tests for convert_script function."""

    @pytest.mark.asyncio
    async def test_convert_script_success(self):
        """Test successful script conversion."""
        source_script = "SELECT * FROM informix_table"
        file_record = MagicMock()
        file_record.file_id = str(uuid.uuid4())
        file_record.batch_id = str(uuid.uuid4())
        
        mock_batch_service = MagicMock()
        mock_batch_service.create_file_log = AsyncMock()
        
        mock_sql_agents = MagicMock()
        mock_sql_agents.idx_agents = {
            "migrator": MagicMock(),
            "picker": MagicMock(),
        }
        
        mock_comms_manager = MagicMock()
        mock_comms_manager.group_chat = MagicMock()
        mock_comms_manager.group_chat.add_chat_message = AsyncMock()
        mock_comms_manager.group_chat.is_complete = True
        mock_comms_manager.cleanup = AsyncMock()
        
        # Create async generator mock for async_invoke
        async def mock_async_invoke():
            yield MockChatMessageContent(
                name="semantic_verifier",
                content='{"judgement": "pass", "differences": [], "summary": "OK"}',
                role="assistant"
            )
        
        mock_comms_manager.async_invoke = mock_async_invoke
        
        with patch("backend.sql_agents.convert_script.CommsManager", return_value=mock_comms_manager):
            with patch("backend.sql_agents.convert_script.send_status_update"):
                with patch("backend.sql_agents.convert_script.validate_migration", new_callable=AsyncMock, return_value=True):
                    result = await convert_script(
                        source_script,
                        file_record,
                        mock_batch_service,
                        mock_sql_agents
                    )

    @pytest.mark.asyncio
    async def test_convert_script_cleanup_always_runs(self):
        """Test that cleanup runs even on exception."""
        source_script = "SELECT * FROM test"
        file_record = MagicMock()
        file_record.file_id = str(uuid.uuid4())
        file_record.batch_id = str(uuid.uuid4())
        
        mock_batch_service = MagicMock()
        mock_batch_service.create_file_log = AsyncMock()
        
        mock_sql_agents = MagicMock()
        mock_sql_agents.idx_agents = {}
        
        mock_comms_manager = MagicMock()
        mock_comms_manager.group_chat = MagicMock()
        mock_comms_manager.group_chat.add_chat_message = AsyncMock(side_effect=Exception("Error"))
        mock_comms_manager.cleanup = AsyncMock()
        
        with patch("backend.sql_agents.convert_script.CommsManager", return_value=mock_comms_manager):
            with patch("backend.sql_agents.convert_script.send_status_update"):
                try:
                    await convert_script(
                        source_script,
                        file_record,
                        mock_batch_service,
                        mock_sql_agents
                    )
                except:
                    pass
                
                # Cleanup should be called even on exception
                mock_comms_manager.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_script_handles_async_invoke_exception(self):
        """Test handling of exception during async_invoke."""
        source_script = "SELECT * FROM test"
        file_record = MagicMock()
        file_record.file_id = str(uuid.uuid4())
        file_record.batch_id = str(uuid.uuid4())
        
        mock_batch_service = MagicMock()
        mock_batch_service.create_file_log = AsyncMock()
        
        mock_sql_agents = MagicMock()
        mock_sql_agents.idx_agents = {}
        
        mock_comms_manager = MagicMock()
        mock_comms_manager.group_chat = MagicMock()
        mock_comms_manager.group_chat.add_chat_message = AsyncMock()
        mock_comms_manager.group_chat.is_complete = True
        mock_comms_manager.cleanup = AsyncMock()
        
        # Create async generator that raises exception
        async def mock_async_invoke_error():
            raise Exception("Invoke error")
            yield  # Make it a generator
        
        mock_comms_manager.async_invoke = mock_async_invoke_error
        
        with patch("backend.sql_agents.convert_script.CommsManager", return_value=mock_comms_manager):
            with patch("backend.sql_agents.convert_script.send_status_update"):
                result = await convert_script(
                    source_script,
                    file_record,
                    mock_batch_service,
                    mock_sql_agents
                )
                
                # Should return "No migration" on error (this is the initial value)
                assert result == "No migration"
