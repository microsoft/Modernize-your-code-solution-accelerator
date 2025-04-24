# test_app_logger.py

import logging
import json
import pytest
from unittest.mock import patch, MagicMock

from src.backend.common.logger.app_logger import AppLogger, LogLevel  # replace 'your_module_name' with the correct one


@pytest.fixture
def logger_name():
    return "test_logger"


@pytest.fixture
def app_logger(logger_name):
    return AppLogger(logger_name)


def test_log_level_constants():
    assert LogLevel.NONE == logging.NOTSET
    assert LogLevel.DEBUG == logging.DEBUG
    assert LogLevel.INFO == logging.INFO
    assert LogLevel.WARNING == logging.WARNING
    assert LogLevel.ERROR == logging.ERROR
    assert LogLevel.CRITICAL == logging.CRITICAL


@patch("src.backend.common.logger.app_logger.logging.getLogger")
def test_app_logger_init(mock_get_logger, logger_name):
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    logger = AppLogger(logger_name)

    assert logger.logger == mock_logger
    mock_logger.setLevel.assert_called_once_with(logging.DEBUG)
    
    # New Correct Check: Check that addHandler was called with StreamHandler
    assert mock_logger.addHandler.called
    handler_arg = mock_logger.addHandler.call_args[0][0]
    assert isinstance(handler_arg, logging.StreamHandler)



def test_format_message_without_kwargs(app_logger):
    message = "test message"
    formatted = app_logger._format_message(message)
    expected = json.dumps({"message": message})
    assert formatted == expected


def test_format_message_with_kwargs(app_logger):
    message = "test message"
    context = {"user": "john", "action": "login"}
    formatted = app_logger._format_message(message, **context)
    expected = json.dumps({"message": message, "context": context})
    assert formatted == expected


@patch.object(logging.Logger, "debug")
def test_debug(mock_debug, app_logger):
    app_logger.debug("Debug Message", user="test")
    assert mock_debug.called
    args, kwargs = mock_debug.call_args
    log_entry = json.loads(args[0])
    assert log_entry["message"] == "Debug Message"
    assert "context" in log_entry
    assert log_entry["context"]["user"] == "test"


@patch.object(logging.Logger, "info")
def test_info(mock_info, app_logger):
    app_logger.info("Info Message", user="test")
    assert mock_info.called
    args, kwargs = mock_info.call_args
    log_entry = json.loads(args[0])
    assert log_entry["message"] == "Info Message"


@patch.object(logging.Logger, "warning")
def test_warning(mock_warning, app_logger):
    app_logger.warning("Warning Message", user="test")
    assert mock_warning.called
    args, kwargs = mock_warning.call_args
    log_entry = json.loads(args[0])
    assert log_entry["message"] == "Warning Message"


@patch.object(logging.Logger, "error")
def test_error(mock_error, app_logger):
    app_logger.error("Error Message", user="test")
    assert mock_error.called
    args, kwargs = mock_error.call_args
    log_entry = json.loads(args[0])
    assert log_entry["message"] == "Error Message"


@patch.object(logging.Logger, "critical")
def test_critical(mock_critical, app_logger):
    app_logger.critical("Critical Message", user="test")
    assert mock_critical.called
    args, kwargs = mock_critical.call_args
    log_entry = json.loads(args[0])
    assert log_entry["message"] == "Critical Message"


@patch("src.backend.common.logger.app_logger.logging.getLogger")
def test_set_min_log_level(mock_get_logger):
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    AppLogger.set_min_log_level(LogLevel.ERROR)

    mock_logger.setLevel.assert_called_with(LogLevel.ERROR)
