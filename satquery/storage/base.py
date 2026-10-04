"""
satquery.storage.base
=====================
Storage backend abstraction interface (Section 29).
Supports LocalStorage, S3Storage, and MinIOStorage with a unified file management API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, List, Optional


class BaseStorage(ABC):
    """Abstract storage backend."""

    @abstractmethod
    def save_bytes(self, category: str, filename: str, data: bytes) -> str:
        """Saves raw bytes into the specified category folder and returns relative path/URI."""
        pass

    @abstractmethod
    def read_bytes(self, category: str, filename: str) -> bytes:
        """Reads raw bytes from storage."""
        pass

    @abstractmethod
    def get_path(self, category: str, filename: str) -> Path:
        """Returns local absolute path for direct filesystem access if available."""
        pass

    @abstractmethod
    def exists(self, category: str, filename: str) -> bool:
        """Checks if a file exists in the specified category."""
        pass

    @abstractmethod
    def list_files(self, category: str) -> List[str]:
        """Lists all files stored in the specified category."""
        pass

    @abstractmethod
    def delete(self, category: str, filename: str) -> bool:
        """Deletes a file from storage."""
        pass
