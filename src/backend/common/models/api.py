from __future__ import annotations

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List
from uuid import UUID

from semantic_kernel.contents import AuthorRole

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class LogType(Enum):
    SUCCESS = "success"  # green
    INFO = "info"  # blue
    WARNING = "warning"  # yellow/orange
    ERROR = "error"  # red

    def __new__(cls, value):
        # If value is a string, normalize it to lowercase
        if isinstance(value, str):
            value = value.lower()
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    @classmethod
    def _missing_(cls, value):
        return cls.INFO


class TranslateType(Enum):
    TSQL = "T-SQL"
    INFORMIX = "Informix"


class ProcessStatus(Enum):
    READY_TO_PROCESS = "ready_to_process"
    IN_PROGRESS = "in_process"
    COMPLETED = "completed"
    FAILED = "failed"

    def __new__(cls, value):
        # If value is a string, normalize it to lowercase
        if isinstance(value, str):
            value = value.lower()
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    @classmethod
    def _missing_(cls, value):
        return cls.READY_TO_PROCESS


class FileResult(Enum):
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = None  # Assigning None

    def __new__(cls, value):
        # If value is a string, normalize it to lowercase
        if isinstance(value, str):
            value = value.lower()
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN


class AgentType(Enum):
    """Agent types."""

    MIGRATOR = "migrator"
    FIXER = "fixer"
    PICKER = "picker"
    SEMANTIC_VERIFIER = "semantic_verifier"
    SYNTAX_CHECKER = "syntax_checker"
    SELECTION = "selection"
    TERMINATION = "termination"
    HUMAN = "human"
    ALL = "agents"  # For all agents

    def __new__(cls, value):
        # If value is a string, normalize it to lowercase
        if isinstance(value, str):
            value = value.lower()
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    @classmethod
    def _missing_(cls, value):
        return cls.ALL


class FileLog:
    def __init__(
        self,
        log_id: UUID,
        file_id: UUID,
        description: str,
        last_candidate: str,
        log_type: LogType,
        agent_type: AgentType,
        author_role: AuthorRole,
        timestamp: datetime,
    ):
        self.log_id = log_id
        self.file_id = file_id
        self.description = description
        self.last_candidate = last_candidate
        self.log_type = log_type
        self.agent_type = agent_type
        self.author_role = author_role
        self.timestamp = timestamp

    @staticmethod
    def fromdb(data: Dict) -> FileLog:
        """Convert str to UUID after fetching from the database."""
        return FileLog(
            log_id=UUID(data["log_id"]),  # Convert str → UUID
            file_id=UUID(data["file_id"]),  # Convert str → UUID
            description=data["description"],
            last_candidate=data["last_candidate"],
            log_type=LogType(data["log_type"]),
            agent_type=AgentType(data["agent_type"]),
            author_role=(
                AuthorRole(data["author_role"])
                if data.get("author_role")
                else AuthorRole("assistant")
            ),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )

    def dict(self) -> Dict:
        """Convert UUID to str before inserting into the database."""
        return {
            "id": str(self.log_id),  # Convert UUID → str
            "log_id": str(self.log_id),  # Convert UUID → str
            "file_id": str(self.file_id),  # Convert UUID → str
            "description": self.description,
            "last_candidate": self.last_candidate,
            "log_type": self.log_type.value,
            "agent_type": self.agent_type.value,
            "author_role": self.author_role.value,
            "timestamp": self.timestamp.isoformat(),
        }


class FileRecord:
    def __init__(
        self,
        file_id: UUID,
        batch_id: UUID,
        original_name: str,
        blob_path: str,
        translated_path: str,
        status: ProcessStatus,
        error_count: int,
        syntax_count: int,
        created_at: datetime,
        updated_at: datetime,
        file_result: FileResult = None,
    ):
        self.file_id = file_id
        self.batch_id = batch_id
        self.original_name = original_name
        self.blob_path = blob_path
        self.translated_path = translated_path
        self.status = status
        self.file_result = file_result
        self.error_count = error_count
        self.syntax_count = syntax_count
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def fromdb(data: Dict) -> FileRecord:
        """Convert str to UUID after fetching from the database."""
        return FileRecord(
            file_id=UUID(data["file_id"]),  # Convert str → UUID
            batch_id=UUID(data["batch_id"]),  # Convert str → UUID
            original_name=data["original_name"],
            blob_path=data["blob_path"],
            translated_path=data["translated_path"],
            status=ProcessStatus(data["status"]),
            file_result=(
                FileResult(data["file_result"]) if data["file_result"] else None
            ),
            error_count=data["error_count"],
            syntax_count=data["syntax_count"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    def dict(self) -> Dict:
        """Convert UUID to str before inserting into the database."""
        return {
            "id": str(self.file_id),
            "file_id": str(self.file_id),  # Convert UUID → str
            "batch_id": str(self.batch_id),  # Convert UUID → str
            "original_name": self.original_name,
            "blob_path": self.blob_path,
            "translated_path": self.translated_path,
            "status": self.status.value,
            "file_result": self.file_result.value if self.file_result else None,
            "error_count": self.error_count,
            "syntax_count": self.syntax_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class FileProcessUpdate:
    """websocket payload for file process updates."""

    def __init__(
        self,
        batch_id: UUID = None,
        file_id: UUID = None,
        process_status: ProcessStatus = None,
        agent_type: AgentType = None,
        agent_message: str = None,
        file_result: FileResult = None,
    ):
        self.batch_id = batch_id
        self.file_id = file_id
        self.process_status = process_status
        self.file_result = file_result
        self.agent_type = agent_type
        self.agent_message = agent_message

    def dict(self) -> Dict:
        return {
            "batch_id": str(self.batch_id) if self.batch_id is not None else None,
            "file_id": str(self.file_id) if self.file_id is not None else None,
            "process_status": (
                self.process_status.value if self.process_status is not None else None
            ),
            "file_result": (
                self.file_result.value if self.file_result is not None else None
            ),
            "agent_type": (
                self.agent_type.value if self.agent_type is not None else None
            ),
            "agent_message": (
                self.agent_message if self.agent_message is not None else None
            ),
        }


class FileProcessUpdateJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for serializing FileProcessUpdate, ProcessStatus, and FileResult objects."""

    def default(self, obj):
        # Check if the object is an instance of FileProcessUpdate, ProcessStatus, or FileResult
        if isinstance(obj, (FileProcessUpdate, ProcessStatus, FileResult, AgentType)):
            return obj.dict()
        # Check if the object is an instance of UUID and convert it to a string
        if isinstance(obj, UUID):
            return str(obj)
        # For other types, use the default serialization method
        return super().default(obj)


class QueueBatch:
    def __init__(
        self,
        batch_id: UUID,
        user_id: str,
        translate_from: str,
        translate_to: str,
        created_at: datetime,
        updated_at: datetime,
        status: ProcessStatus,
    ):
        self.batch_id = batch_id
        self.user_id = user_id
        self.translate_from = translate_from
        self.translate_to = translate_to
        self.created_at = created_at
        self.updated_at = updated_at
        self.status = status

    def dict(self) -> Dict:
        """Convert UUID to str before inserting into the database."""
        return {
            "batch_id": str(self.batch_id),  # Convert UUID → str for DB
            "user_id": self.user_id,
            "translate_from": self.translate_from,
            "translate_to": self.translate_to,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.value,
        }


class BatchRecord:
    def __init__(
        self,
        batch_id: UUID,
        user_id: str,
        file_count: int,
        created_at: datetime,
        updated_at: datetime,
        status: ProcessStatus,
        from_language: TranslateType = TranslateType.INFORMIX,
        to_language: TranslateType = TranslateType.TSQL,
    ):
        self.batch_id = batch_id
        self.user_id = user_id
        self.file_count = file_count
        self.created_at = created_at
        self.updated_at = updated_at
        self.status = status
        self.from_language = from_language
        self.to_language = to_language

    @staticmethod
    def fromdb(data: Dict) -> BatchRecord:
        logging.info(f"BatchRecord.fromdb: {data}")
        """Convert str to UUID after fetching from the database"""
        # Handle from_language with default
        if "from_language" in data and data["from_language"]:
            from_lang = TranslateType(data["from_language"])
        else:
            from_lang = TranslateType.INFORMIX

        # Handle to_language with default
        if "to_language" in data and data["to_language"]:
            to_lang = TranslateType(data["to_language"])
        else:
            to_lang = TranslateType.TSQL

        return BatchRecord(
            batch_id=UUID(data["batch_id"]),  # Convert str → UUID
            user_id=data["user_id"],
            file_count=data["file_count"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            status=ProcessStatus(data["status"]),
            from_language=from_lang,
            to_language=to_lang,
        )

    def dict(self) -> Dict:
        """Convert UUID to str before inserting into the database."""
        return {
            "id": str(self.batch_id),
            "batch_id": str(self.batch_id),  # Convert UUID → str for DB
            "user_id": self.user_id,
            "file_count": self.file_count,
            "created_at": (
                self.created_at.isoformat()
                if hasattr(self.created_at, "isoformat")
                else self.created_at
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if hasattr(self.updated_at, "isoformat")
                else self.updated_at
            ),
            "status": self.status.value,
            "from_language": self.from_language.value,
            "to_language": self.to_language.value,
        }


class FileReport:
    def __init__(
        self,
        file: FileRecord,
        logs: List[FileLog],
        batch: BatchRecord,
        file_content: str,
        translated_content: str,
        log_reports: List[Dict],
    ):
        self.file = file
        self.logs = logs
        self.batch = batch
        self.file_content = file_content
        self.translated_content = translated_content
        self.log_reports = log_reports
