from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageService(ABC):
    """Abstract interface for dataset file storage."""

    @abstractmethod
    def save_file(
        self,
        content: bytes | BinaryIO,
        relative_path: str,
    ) -> str:
        """Save file content to the relative storage path. Returns the relative storage path."""
        pass

    @abstractmethod
    def get_file(self, relative_path: str) -> bytes:
        """Retrieve full file contents as bytes."""
        pass

    def read(self, relative_path: str) -> bytes:
        """Convenience alias for get_file."""
        return self.get_file(relative_path)

    @abstractmethod
    def get_file_path(self, relative_path: str) -> str:
        """Get filesystem path for local access (if supported)."""
        pass

    @abstractmethod
    def delete_file(self, relative_path: str) -> bool:
        """Delete file at relative path. Returns True if deleted, False if not found."""
        pass

    @abstractmethod
    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists at relative path."""
        pass
