"""Tests for event_utils module."""

import os
from unittest.mock import MagicMock, patch

from backend.api.event_utils import track_event_if_configured


class TestTrackEventIfConfigured:
    """Tests for track_event_if_configured function."""

    def test_track_event_with_instrumentation_key(self):
        """Test tracking event when instrumentation key is set."""
        connection_string = "InstrumentationKey=test-key;IngestionEndpoint=https://test.com"
        with patch.dict(os.environ, {"APPLICATIONINSIGHTS_CONNECTION_STRING": connection_string}):
            with patch("backend.api.event_utils._get_telemetry_client") as mock_get_client:
                mock_client = MagicMock()
                mock_get_client.return_value = mock_client

                track_event_if_configured("TestEvent", {"key": "value"})

                mock_client.track_event.assert_called_once_with("TestEvent", properties={"key": "value"})
                mock_client.flush.assert_called_once()

    def test_track_event_without_instrumentation_key(self):
        """Test tracking event when instrumentation key is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove the key if it exists
            os.environ.pop("APPLICATIONINSIGHTS_CONNECTION_STRING", None)
            with patch("backend.api.event_utils._get_telemetry_client") as mock_get_client:
                with patch("backend.api.event_utils.logging.warning") as mock_warning:
                    track_event_if_configured("TestEvent", {"key": "value"})

                    mock_get_client.assert_not_called()
                    mock_warning.assert_called_once()

    def test_track_event_with_empty_data(self):
        """Test tracking event with empty data."""
        connection_string = "InstrumentationKey=test-key;IngestionEndpoint=https://test.com"
        with patch.dict(os.environ, {"APPLICATIONINSIGHTS_CONNECTION_STRING": connection_string}):
            with patch("backend.api.event_utils._get_telemetry_client") as mock_get_client:
                mock_client = MagicMock()
                mock_get_client.return_value = mock_client

                track_event_if_configured("TestEvent", {})

                mock_client.track_event.assert_called_once_with("TestEvent", properties={})
                mock_client.flush.assert_called_once()

    def test_track_event_with_complex_data(self):
        """Test tracking event with complex data."""
        connection_string = "InstrumentationKey=test-key;IngestionEndpoint=https://test.com"
        with patch.dict(os.environ, {"APPLICATIONINSIGHTS_CONNECTION_STRING": connection_string}):
            with patch("backend.api.event_utils._get_telemetry_client") as mock_get_client:
                mock_client = MagicMock()
                mock_get_client.return_value = mock_client

                complex_data = {
                    "batch_id": "test-batch",
                    "file_count": 10,
                    "status": "completed",
                    "nested": {"key": "value"},
                }

                track_event_if_configured("ComplexEvent", complex_data)

                # Values are converted to strings in the actual implementation
                expected_properties = {
                    "batch_id": "test-batch",
                    "file_count": "10",
                    "status": "completed",
                    "nested": "{'key': 'value'}",
                }

                mock_client.track_event.assert_called_once_with("ComplexEvent", properties=expected_properties)
                mock_client.flush.assert_called_once()

    def test_track_event_client_returns_none(self):
        """Test tracking event when client initialization fails."""
        connection_string = "InstrumentationKey=test-key;IngestionEndpoint=https://test.com"
        with patch.dict(os.environ, {"APPLICATIONINSIGHTS_CONNECTION_STRING": connection_string}):
            with patch("backend.api.event_utils._get_telemetry_client") as mock_get_client:
                mock_get_client.return_value = None
                with patch("backend.api.event_utils.logging.warning") as mock_warning:
                    track_event_if_configured("TestEvent", {"key": "value"})

                    mock_warning.assert_called_once()

    def test_track_event_with_exception(self):
        """Test tracking event when an exception occurs."""
        connection_string = "InstrumentationKey=test-key;IngestionEndpoint=https://test.com"
        with patch.dict(os.environ, {"APPLICATIONINSIGHTS_CONNECTION_STRING": connection_string}):
            with patch("backend.api.event_utils._get_telemetry_client") as mock_get_client:
                mock_client = MagicMock()
                mock_client.track_event.side_effect = Exception("Test error")
                mock_get_client.return_value = mock_client

                with patch("backend.api.event_utils.logging.error") as mock_error:
                    track_event_if_configured("TestEvent", {"key": "value"})

                    mock_error.assert_called_once()
