import os
import shutil
from typing import BinaryIO
from pathlib import Path

from backend.app.core.config import settings
from backend.app.services.storage.base import StorageService


class LocalStorageService(StorageService):
    """
    Local filesystem storage implementation with strict multi-tenant directory
    isolation and path traversal attack prevention.
    """

    def __init__(self, root_dir: str | None = None):
        if root_dir:
            self.root_dir = os.path.abspath(root_dir)
        else:
            base_dir = os.path.abspath(settings.upload_dir)
            self.root_dir = base_dir

        os.makedirs(self.root_dir, exist_ok=True)

    def _resolve_safe_path(self, relative_path: str) -> str:
        """
        Validate and resolve a relative path against root_dir.
        Raises ValueError if path traversal or escaping root_dir is detected.
        """
        # Normalize and strip leading separators
        clean_rel = os.path.normpath(relative_path).lstrip("/\\")

        # Guard against empty or dangerous relative path
        if not clean_rel or clean_rel == ".":
            raise ValueError("Invalid storage path: path cannot be empty.")

        # Resolve absolute target path
        target_path = os.path.abspath(os.path.join(self.root_dir, clean_rel))

        # Strict containment check
        common_prefix = os.path.commonpath([self.root_dir, target_path])
        if common_prefix != self.root_dir:
            raise ValueError(f"Path traversal attempt detected: {relative_path}")

        return target_path

    def save_file(
        self,
        content: bytes | BinaryIO,
        relative_path: str,
    ) -> str:
        target_path = self._resolve_safe_path(relative_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        if isinstance(content, bytes):
            with open(target_path, "wb") as f:
                f.write(content)
        else:
            with open(target_path, "wb") as f:
                shutil.copyfileobj(content, f)

        return relative_path

    def get_file(self, relative_path: str) -> bytes:
        target_path = self._resolve_safe_path(relative_path)
        if not os.path.isfile(target_path):
            raise FileNotFoundError(f"Storage file not found: {relative_path}")

        with open(target_path, "rb") as f:
            return f.read()

    read = get_file

    def get_file_path(self, relative_path: str) -> str:
        target_path = self._resolve_safe_path(relative_path)
        if not os.path.isfile(target_path):
            raise FileNotFoundError(f"Storage file not found: {relative_path}")
        return target_path

    def delete_file(self, relative_path: str) -> bool:
        try:
            target_path = self._resolve_safe_path(relative_path)
            if os.path.isfile(target_path):
                os.remove(target_path)
                # Attempt to clean up empty parent directories up to root_dir
                parent = os.path.dirname(target_path)
                while parent != self.root_dir and os.path.exists(parent):
                    try:
                        if not os.listdir(parent):
                            os.rmdir(parent)
                            parent = os.path.dirname(parent)
                        else:
                            break
                    except OSError:
                        break
                return True
            return False
        except (ValueError, FileNotFoundError):
            return False

    def file_exists(self, relative_path: str) -> bool:
        try:
            target_path = self._resolve_safe_path(relative_path)
            return os.path.isfile(target_path)
        except ValueError:
            return False
