"""DatabaseBase class for managing database operations"""

import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from semantic_kernel.contents import AuthorRole

from common.models.api import BatchRecord, FileRecord, LogType
from sql_agents.helpers.models import AgentType


class DatabaseBase(ABC):
    """Abstract base class for database operations"""

    @abstractmethod
    async def initialize_cosmos(self) -> None:
        """Initialize the cosmosdb client and create container if needed"""

    @abstractmethod
    async def create_batch(self, user_id: str, batch_id: uuid.UUID) -> BatchRecord:
        """Create a new conversion batch"""

    @abstractmethod
    async def get_file_logs(self, file_id: str) -> Dict:
        """Retrieve all logs for a file"""

    @abstractmethod
    async def get_batch_from_id(self, batch_id: str) -> Dict:
        """Retrieve all logs for a file"""

    @abstractmethod
    async def get_batch_files(self, batch_id: str) -> List[Dict]:
        """Retrieve all files for a batch"""

    @abstractmethod
    async def delete_file_logs(self, file_id: str) -> None:
        """Delete all logs for a file"""

    @abstractmethod
    async def get_user_batches(self, user_id: str) -> Dict:
        """Retrieve all batches for a user"""

    @abstractmethod
    async def add_file(
        self, batch_id: uuid.UUID, file_id: uuid.UUID, file_name: str, storage_path: str
    ) -> FileRecord:
        """Add a file entry to the database"""

    @abstractmethod
    async def get_batch(self, user_id: str, batch_id: str) -> Optional[Dict]:
        """Retrieve a batch and its associated files"""

    @abstractmethod
    async def get_file(self, file_id: str) -> Optional[Dict]:
        """Retrieve a file entry along with its logs"""

    @abstractmethod
    async def add_file_log(
        self,
        file_id: str,
        description: str,
        last_candidate: str,
        log_type: LogType,
        agent_type: AgentType,
        author_role: AuthorRole,
    ) -> None:
        """Log a file status update"""

    @abstractmethod
    async def update_file(self, file_record: FileRecord) -> None:
        """update file record"""

    @abstractmethod
    async def update_batch(self, batch_record: BatchRecord) -> BatchRecord:
        """Update a batch record"""

    @abstractmethod
    async def delete_all(self, user_id: str) -> None:
        """Delete all batches, files, and logs for a user"""

    @abstractmethod
    async def delete_batch(self, user_id: str, batch_id: str) -> None:
        """Delete a batch along with its files and logs"""

    @abstractmethod
    async def delete_file(self, user_id: str, batch_id: str, file_id: str) -> None:
        """Delete a file and its logs, and update batch file count"""

    @abstractmethod
    async def get_batch_history(self, user_id: str, batch_id: str) -> List[Dict]:
        """Retrieve all logs for a batch"""

    @abstractmethod
    async def close(self) -> None:
        """Close database connection"""
