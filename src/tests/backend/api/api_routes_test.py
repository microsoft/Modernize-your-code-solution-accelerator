"""Tests for API routes module."""
# pylint: disable=redefined-outer-name,unused-argument

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from backend.api.api_routes import (
    delete_all_details,
    delete_batch_details,
    delete_file_details,
    download_files,
    get_batch_status,
    get_batch_summary,
    get_file_details,
    list_batch_history,
    record_exception_to_trace,
    router,
    start_processing,
    upload_file,
)

from fastapi import FastAPI, HTTPException

import pytest


@pytest.fixture
def test_app():
    """Create a test FastAPI app with the router."""
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return app


@pytest.fixture
def mock_batch_service():
    """Create a mock BatchService."""
    with patch("backend.api.api_routes.BatchService") as mock:
        service = AsyncMock()
        service.initialize_database = AsyncMock()
        service.is_valid_uuid = MagicMock(return_value=True)
        service.get_batch = AsyncMock()
        service.get_batch_summary = AsyncMock()
        service.get_batch_for_zip = AsyncMock()
        service.upload_file_to_batch = AsyncMock()
        service.get_file_report = AsyncMock()
        service.delete_batch_and_files = AsyncMock()
        service.delete_file = AsyncMock()
        service.delete_all_from_storage_cosmos = AsyncMock()
        service.get_batch_history = AsyncMock()
        mock.return_value = service
        yield service


@pytest.fixture
def mock_auth_user():
    """Create a mock authenticated user."""
    with patch("backend.api.api_routes.get_authenticated_user") as mock:
        user = MagicMock()
        user.user_principal_id = str(uuid.uuid4())
        mock.return_value = user
        yield mock


@pytest.fixture
def mock_process_batch():
    """Mock process_batch_async."""
    with patch("backend.api.api_routes.process_batch_async", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_close_connection():
    """Mock close_connection."""
    with patch("backend.api.api_routes.close_connection", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_track_event():
    """Mock track_event_if_configured."""
    with patch("backend.api.api_routes.track_event_if_configured") as mock:
        yield mock


class TestRecordExceptionToTrace:
    """Tests for record_exception_to_trace function."""

    def test_record_exception_with_span(self):
        """Test recording exception when span exists."""
        mock_span = MagicMock()
        with patch("backend.api.api_routes.trace.get_current_span", return_value=mock_span):
            record_exception_to_trace(ValueError("test error"))
            mock_span.record_exception.assert_called_once()
            mock_span.set_status.assert_called_once()

    def test_record_exception_no_span(self):
        """Test recording exception when no span exists."""
        with patch("backend.api.api_routes.trace.get_current_span", return_value=None):
            # Should not raise any exception
            record_exception_to_trace(ValueError("test error"))


class TestStartProcessing:
    """Tests for start_processing endpoint."""

    @pytest.mark.asyncio
    async def test_start_processing_success(self, mock_process_batch, mock_close_connection, mock_track_event):
        """Test successful processing start."""
        batch_id = str(uuid.uuid4())
        mock_request = AsyncMock()
        mock_request.json = AsyncMock(return_value={
            "batch_id": batch_id,
            "translate_from": "informix",
            "translate_to": "tsql"
        })

        result = await start_processing(mock_request)

        assert result["batch_id"] == batch_id
        assert result["status"] == "Processing completed"
        mock_process_batch.assert_called_once()
        mock_close_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_processing_exception(self, mock_process_batch, mock_track_event):
        """Test processing start with exception."""
        mock_request = AsyncMock()
        mock_request.json = AsyncMock(return_value={
            "batch_id": "test-batch",
            "translate_from": "informix",
            "translate_to": "tsql"
        })
        mock_process_batch.side_effect = Exception("Processing failed")

        with patch("backend.api.api_routes.record_exception_to_trace"):
            with pytest.raises(HTTPException) as exc_info:
                await start_processing(mock_request)
            assert exc_info.value.status_code == 500


class TestDownloadFiles:
    """Tests for download_files endpoint."""

    @pytest.mark.asyncio
    async def test_download_files_success(self, mock_batch_service, mock_track_event):
        """Test successful file download."""
        batch_id = str(uuid.uuid4())
        mock_batch_service.get_batch_for_zip.return_value = [
            ("file1.sql", "SELECT * FROM test"),
            ("file2", "INSERT INTO test VALUES (1)")
        ]

        response = await download_files(batch_id)

        assert response.media_type == "application/zip"
        assert "Content-Disposition" in response.headers

    @pytest.mark.asyncio
    async def test_download_files_not_found(self, mock_batch_service, mock_track_event):
        """Test download when batch not found."""
        batch_id = str(uuid.uuid4())
        mock_batch_service.get_batch_for_zip.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await download_files(batch_id)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_download_files_empty_content(self, mock_batch_service, mock_track_event):
        """Test download with empty file content."""
        batch_id = str(uuid.uuid4())
        mock_batch_service.get_batch_for_zip.return_value = [
            ("file1.sql", None),
            ("file2.sql", "SELECT * FROM test")
        ]

        response = await download_files(batch_id)
        assert response.media_type == "application/zip"


class TestGetBatchStatus:
    """Tests for get_batch_status endpoint."""

    @pytest.mark.asyncio
    async def test_get_batch_status_success(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test successful batch status retrieval."""
        batch_id = str(uuid.uuid4())
        mock_request = MagicMock()
        mock_batch_service.get_batch.return_value = {"batch_id": batch_id, "status": "completed"}

        result = await get_batch_status(mock_request, batch_id)

        assert result["batch_id"] == batch_id

    @pytest.mark.asyncio
    async def test_get_batch_status_invalid_uuid(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test batch status with invalid UUID."""
        mock_request = MagicMock()
        mock_batch_service.is_valid_uuid.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await get_batch_status(mock_request, "invalid-uuid")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_batch_status_not_found(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test batch status when not found."""
        batch_id = str(uuid.uuid4())
        mock_request = MagicMock()
        mock_batch_service.get_batch.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_batch_status(mock_request, batch_id)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_batch_status_user_not_authenticated(self, mock_batch_service, mock_track_event):
        """Test batch status when user not authenticated."""
        mock_request = MagicMock()
        with patch("backend.api.api_routes.get_authenticated_user") as mock_auth:
            user = MagicMock()
            user.user_principal_id = None
            mock_auth.return_value = user

            with pytest.raises(HTTPException) as exc_info:
                await get_batch_status(mock_request, str(uuid.uuid4()))
            assert exc_info.value.status_code == 401


class TestGetBatchSummary:
    """Tests for get_batch_summary endpoint."""

    @pytest.mark.asyncio
    async def test_get_batch_summary_success(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test successful batch summary retrieval."""
        batch_id = str(uuid.uuid4())
        mock_request = MagicMock()
        mock_batch_service.get_batch_summary.return_value = {"total_files": 5}

        result = await get_batch_summary(mock_request, batch_id)

        assert result["total_files"] == 5

    @pytest.mark.asyncio
    async def test_get_batch_summary_not_found(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test batch summary when not found."""
        mock_request = MagicMock()
        mock_batch_service.get_batch_summary.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_batch_summary(mock_request, str(uuid.uuid4()))
        assert exc_info.value.status_code == 404


class TestUploadFile:
    """Tests for upload_file endpoint."""

    @pytest.mark.asyncio
    async def test_upload_file_success(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test successful file upload."""
        batch_id = str(uuid.uuid4())
        mock_request = MagicMock()
        mock_file = MagicMock()
        mock_batch_service.upload_file_to_batch.return_value = {"file_id": "test-file-id"}

        result = await upload_file(mock_request, mock_file, batch_id)

        assert result["file_id"] == "test-file-id"

    @pytest.mark.asyncio
    async def test_upload_file_invalid_batch_id(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test file upload with invalid batch ID."""
        mock_request = MagicMock()
        mock_file = MagicMock()
        mock_batch_service.is_valid_uuid.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await upload_file(mock_request, mock_file, "invalid-batch-id")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_file_user_not_authenticated(self, mock_batch_service, mock_track_event):
        """Test file upload when user not authenticated."""
        mock_request = MagicMock()
        mock_file = MagicMock()
        with patch("backend.api.api_routes.get_authenticated_user") as mock_auth:
            user = MagicMock()
            user.user_principal_id = None
            mock_auth.return_value = user

            with pytest.raises(HTTPException) as exc_info:
                await upload_file(mock_request, mock_file, str(uuid.uuid4()))
            assert exc_info.value.status_code == 401


class TestGetFileDetails:
    """Tests for get_file_details endpoint."""

    @pytest.mark.asyncio
    async def test_get_file_details_success(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test successful file details retrieval."""
        file_id = str(uuid.uuid4())
        mock_request = MagicMock()
        mock_batch_service.get_file_report.return_value = {"file_id": file_id}

        result = await get_file_details(mock_request, file_id)

        assert result["file_id"] == file_id

    @pytest.mark.asyncio
    async def test_get_file_details_not_found(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test file details when not found."""
        mock_request = MagicMock()
        mock_batch_service.get_file_report.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_file_details(mock_request, str(uuid.uuid4()))
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_file_details_invalid_id(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test file details with invalid ID."""
        mock_request = MagicMock()
        mock_batch_service.is_valid_uuid.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await get_file_details(mock_request, "invalid-id")
        assert exc_info.value.status_code == 400


class TestDeleteBatchDetails:
    """Tests for delete_batch_details endpoint."""

    @pytest.mark.asyncio
    async def test_delete_batch_success(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test successful batch deletion."""
        batch_id = str(uuid.uuid4())
        mock_request = MagicMock()
        mock_batch_service.delete_batch_and_files.return_value = True

        result = await delete_batch_details(mock_request, batch_id)

        assert result["message"] == "Batch deleted successfully"

    @pytest.mark.asyncio
    async def test_delete_batch_invalid_id(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test batch deletion with invalid ID."""
        mock_request = MagicMock()
        mock_batch_service.is_valid_uuid.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await delete_batch_details(mock_request, "invalid-id")
        assert exc_info.value.status_code == 400


class TestDeleteFileDetails:
    """Tests for delete_file_details endpoint."""

    @pytest.mark.asyncio
    async def test_delete_file_success(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test successful file deletion."""
        file_id = str(uuid.uuid4())
        mock_request = MagicMock()
        mock_batch_service.delete_file.return_value = True

        result = await delete_file_details(mock_request, file_id)

        assert result["message"] == "File deleted successfully"

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test file deletion when not found."""
        mock_request = MagicMock()
        mock_batch_service.delete_file.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await delete_file_details(mock_request, str(uuid.uuid4()))
        assert exc_info.value.status_code == 404


class TestDeleteAllDetails:
    """Tests for delete_all_details endpoint."""

    @pytest.mark.asyncio
    async def test_delete_all_success(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test successful deletion of all data."""
        mock_request = MagicMock()
        mock_batch_service.delete_all_from_storage_cosmos.return_value = True

        result = await delete_all_details(mock_request)

        assert result["message"] == "All user data deleted successfully"

    @pytest.mark.asyncio
    async def test_delete_all_not_found(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test delete all when nothing found."""
        mock_request = MagicMock()
        mock_batch_service.delete_all_from_storage_cosmos.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await delete_all_details(mock_request)
        assert exc_info.value.status_code == 404


class TestListBatchHistory:
    """Tests for list_batch_history endpoint."""

    @pytest.mark.asyncio
    async def test_list_batch_history_success(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test successful batch history retrieval."""
        mock_request = MagicMock()
        mock_batch_service.get_batch_history.return_value = [{"batch_id": "test"}]

        result = await list_batch_history(mock_request)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_batch_history_with_pagination(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test batch history with pagination."""
        mock_request = MagicMock()
        mock_batch_service.get_batch_history.return_value = [{"batch_id": "test"}]

        await list_batch_history(mock_request, offset=10, limit=5)

        mock_batch_service.get_batch_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_batch_history_empty(self, mock_batch_service, mock_auth_user, mock_track_event):
        """Test batch history when empty."""
        mock_request = MagicMock()
        mock_batch_service.get_batch_history.return_value = None

        result = await list_batch_history(mock_request)

        assert result.status_code == 404
