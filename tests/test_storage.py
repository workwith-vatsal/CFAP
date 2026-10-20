import os
import pytest
from backend.app.services.storage.local import LocalStorageService


def test_local_storage_save_get_delete(tmp_path):
    storage = LocalStorageService(root_dir=str(tmp_path))
    rel_path = "user_1/test_file.csv"
    data = b"col1,col2\nval1,val2\n"

    # Save
    saved_path = storage.save_file(data, rel_path)
    assert saved_path == rel_path
    assert storage.file_exists(rel_path) is True

    # Get
    retrieved = storage.get_file(rel_path)
    assert retrieved == data

    # Delete
    assert storage.delete_file(rel_path) is True
    assert storage.file_exists(rel_path) is False
    assert storage.delete_file(rel_path) is False


def test_local_storage_path_traversal_prevention(tmp_path):
    storage = LocalStorageService(root_dir=str(tmp_path))

    # Path traversal attempts
    with pytest.raises(ValueError, match="Path traversal"):
        storage.save_file(b"bad", "../outside.txt")

    with pytest.raises(ValueError, match="Path traversal"):
        storage.save_file(b"bad", "sub/../../outside.txt")

    with pytest.raises(ValueError, match="Invalid storage path"):
        storage.save_file(b"bad", "")
