import json
import logging
from typing import Any


class LogLevel:
    NONE = logging.NOTSET
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class AppLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        self.logger.addHandler(console)

    def _format_message(self, message: Any, **kwargs) -> str:
        log_entry = {"message": str(message)}
        if kwargs:
            log_entry["context"] = kwargs
        return json.dumps(log_entry)

    def debug(self, message: Any, **kwargs) -> None:
        self.logger.debug(self._format_message(message, **kwargs))

    def info(self, message: Any, **kwargs) -> None:
        self.logger.info(self._format_message(message, **kwargs))

    def warning(self, message: Any, **kwargs) -> None:
        self.logger.warning(self._format_message(message, **kwargs))

    def error(self, message: Any, **kwargs) -> None:
        self.logger.error(self._format_message(message, **kwargs))

    def critical(self, message: Any, **kwargs) -> None:
        self.logger.critical(self._format_message(message, **kwargs))

    @classmethod
    def set_min_log_level(cls, level: int) -> None:
        logging.getLogger().setLevel(level)
