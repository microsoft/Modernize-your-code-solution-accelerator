import json
import logging
from unittest.mock import MagicMock, patch

from common.logger.app_logger import AppLogger, LogLevel  # Adjust the import based on your actual path

import pytest


@pytest.fixture
def logger_name():
    return "test_logger"


@pytest.fixture
def logger_instance(logger_name):
    """Fixture to return AppLogger with mocked handler"""
    with patch("common.logger.app_logger.logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield AppLogger(logger_name)


def test_log_levels():
    """Ensure log levels are set correctly"""
    assert LogLevel.NONE == logging.NOTSET
    assert LogLevel.DEBUG == logging.DEBUG
    assert LogLevel.INFO == logging.INFO
    assert LogLevel.WARNING == logging.WARNING
    assert LogLevel.ERROR == logging.ERROR
    assert LogLevel.CRITICAL == logging.CRITICAL


def test_format_message_basic(logger_instance):
    result = logger_instance._format_message("Test message")
    parsed = json.loads(result)
    assert parsed["message"] == "Test message"
    assert "context" not in parsed


def test_format_message_with_context(logger_instance):
    result = logger_instance._format_message("Contextual message", key1="value1", key2="value2")
    parsed = json.loads(result)
    assert parsed["message"] == "Contextual message"
    assert parsed["context"] == {"key1": "value1", "key2": "value2"}


def test_debug_log(logger_instance):
    with patch.object(logger_instance.logger, "debug") as mock_debug:
        logger_instance.debug("Debug log", user="tester")
        mock_debug.assert_called_once()
        log_json = json.loads(mock_debug.call_args[0][0])
        assert log_json["message"] == "Debug log"
        assert log_json["context"]["user"] == "tester"


def test_info_log(logger_instance):
    with patch.object(logger_instance.logger, "info") as mock_info:
        logger_instance.info("Info log", module="log_module")
        mock_info.assert_called_once()
        log_json = json.loads(mock_info.call_args[0][0])
        assert log_json["message"] == "Info log"
        assert log_json["context"]["module"] == "log_module"


def test_warning_log(logger_instance):
    with patch.object(logger_instance.logger, "warning") as mock_warning:
        logger_instance.warning("Warning log")
        mock_warning.assert_called_once()


def test_error_log(logger_instance):
    with patch.object(logger_instance.logger, "error") as mock_error:
        logger_instance.error("Error log", error_code=500)
        mock_error.assert_called_once()
        log_json = json.loads(mock_error.call_args[0][0])
        assert log_json["message"] == "Error log"
        assert log_json["context"]["error_code"] == 500
        # Called outside an exception context, so exc_info should be False
        assert mock_error.call_args[1]["exc_info"] is False


def test_error_log_with_active_exception(logger_instance):
    with patch.object(logger_instance.logger, "error") as mock_error:
        try:
            raise ValueError("test error")
        except ValueError:
            logger_instance.error("Error log inside exception")
        mock_error.assert_called_once()
        # Called inside an exception context, so exc_info should be True
        assert mock_error.call_args[1]["exc_info"] is True


def test_error_log_without_active_exception(logger_instance):
    with patch.object(logger_instance.logger, "error") as mock_error:
        logger_instance.error("Error log outside exception")
        mock_error.assert_called_once()
        # Called outside an exception context, so exc_info should be False
        assert mock_error.call_args[1]["exc_info"] is False


def test_error_log_explicit_exc_info_override(logger_instance):
    with patch.object(logger_instance.logger, "error") as mock_error:
        try:
            raise ValueError("test error")
        except ValueError:
            logger_instance.error("Suppressed traceback", exc_info=False)
        mock_error.assert_called_once()
        # Explicit exc_info=False should override auto-detection even inside an exception context
        assert mock_error.call_args[1]["exc_info"] is False


def test_critical_log(logger_instance):
    with patch.object(logger_instance.logger, "critical") as mock_critical:
        logger_instance.critical("Critical log")
        mock_critical.assert_called_once()


def test_set_min_log_level():
    with patch("common.logger.app_logger.logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        AppLogger.set_min_log_level(LogLevel.ERROR)

        mock_logger.setLevel.assert_called_once_with(LogLevel.ERROR)
