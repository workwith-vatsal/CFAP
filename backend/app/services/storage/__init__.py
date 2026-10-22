from backend.app.services.storage.base import StorageService
from backend.app.services.storage.local import LocalStorageService

_storage_instance: StorageService | None = None


def get_storage_service() -> StorageService:
    """Return the configured storage service singleton."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = LocalStorageService()
    return _storage_instance


__all__ = [
    "StorageService",
    "LocalStorageService",
    "get_storage_service",
]
