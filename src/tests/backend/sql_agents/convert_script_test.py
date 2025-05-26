import datetime
import json
from unittest.mock import AsyncMock, MagicMock, patch

from common.models.api import FileRecord, ProcessStatus

import pytest

from semantic_kernel.agents import Agent
from semantic_kernel.contents import AuthorRole
from semantic_kernel.contents import ChatMessageContent

from sql_agents.convert_script import validate_migration


class DummyAgent(Agent):
    async def invoke(self, *args, **kwargs):
        return "dummy response"

    async def invoke_stream(self, *args, **kwargs):
        yield "dummy stream"

    async def get_response(self, *args, **kwargs):
        return "dummy response"


@pytest.fixture
def file_record():
    return FileRecord(
        batch_id="batch-123",
        file_id="file-456",
        original_name="test.sql",
        blob_path="path/to/blob.sql",
        translated_path="path/to/translated.sql",
        status=ProcessStatus.READY_TO_PROCESS,
        file_result=None,
        syntax_count=0,
        error_count=0,
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
    )


@pytest.fixture
def mock_batch_service():
    service = MagicMock()
    service.create_file_log = AsyncMock()
    return service


@pytest.fixture
def mock_sql_agents():
    return MagicMock(idx_agents=["picker", "migrator", "syntax", "fixer", "verifier"])


@pytest.fixture
def dummy_response_factory():
    def create_response(name, role, content):
        return ChatMessageContent(
            name=name,
            role=role,
            content=content
        )
    return create_response


@pytest.mark.asyncio
@patch("sql_agents.convert_script.send_status_update")
async def test_validate_migration_success(mock_status, file_record, mock_batch_service):
    chat_response = ChatMessageContent(name="picker", role="assistant", content="summary")
    result = await validate_migration("SELECT * FROM valid;", chat_response, file_record, mock_batch_service)
    assert result is True
    assert mock_batch_service.create_file_log.await_count == 1


@pytest.mark.asyncio
@patch("sql_agents.convert_script.send_status_update")
async def test_validate_migration_failure(mock_status, file_record, mock_batch_service):
    result = await validate_migration("", None, file_record, mock_batch_service)
    assert result is False
    assert mock_batch_service.create_file_log.await_count == 1


# Helper for async for loop
async def async_generator(responses):
    for r in responses:
        yield r


def dummy_response(name, content, role=AuthorRole.ASSISTANT.value):
    response = MagicMock()
    response.name = name
    response.role = role
    response.content = json.dumps(content)
    return response


# Async generator utility
async def async_gen(responses):
    for res in responses:
        yield res
