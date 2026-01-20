"""Tests for event_utils module."""

import os
from unittest.mock import patch, MagicMock

import pytest

from backend.api.event_utils import track_event_if_configured


class TestTrackEventIfConfigured:
    """Tests for track_event_if_configured function."""

    def test_track_event_with_instrumentation_key(self):
        """Test tracking event when instrumentation key is set."""
        with patch.dict(os.environ, {"APPLICATIONINSIGHTS_CONNECTION_STRING": "test-key"}):
            with patch("backend.api.event_utils.track_event") as mock_track:
                track_event_if_configured("TestEvent", {"key": "value"})
                
                mock_track.assert_called_once_with("TestEvent", {"key": "value"})

    def test_track_event_without_instrumentation_key(self):
        """Test tracking event when instrumentation key is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove the key if it exists
            os.environ.pop("APPLICATIONINSIGHTS_CONNECTION_STRING", None)
            with patch("backend.api.event_utils.track_event") as mock_track:
                with patch("backend.api.event_utils.logging.warning") as mock_warning:
                    track_event_if_configured("TestEvent", {"key": "value"})
                    
                    mock_track.assert_not_called()
                    mock_warning.assert_called_once()

    def test_track_event_with_empty_data(self):
        """Test tracking event with empty data."""
        with patch.dict(os.environ, {"APPLICATIONINSIGHTS_CONNECTION_STRING": "test-key"}):
            with patch("backend.api.event_utils.track_event") as mock_track:
                track_event_if_configured("TestEvent", {})
                
                mock_track.assert_called_once_with("TestEvent", {})

    def test_track_event_with_complex_data(self):
        """Test tracking event with complex data."""
        with patch.dict(os.environ, {"APPLICATIONINSIGHTS_CONNECTION_STRING": "test-key"}):
            with patch("backend.api.event_utils.track_event") as mock_track:
                complex_data = {
                    "batch_id": "test-batch",
                    "file_count": 10,
                    "status": "completed",
                    "nested": {"key": "value"},
                }
                
                track_event_if_configured("ComplexEvent", complex_data)
                
                mock_track.assert_called_once_with("ComplexEvent", complex_data)
