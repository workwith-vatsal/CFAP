import os
from backend.app.core.config import settings

SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}
SUPPORTED_MIME_TYPES = {
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "application/csv",
    "application/x-csv",
    "text/x-csv",
    "text/comma-separated-values",
}


class FileValidationError(Exception):
    """Raised when uploaded file fails validation checks."""
    pass


def validate_upload_file(
    filename: str | None,
    file_size_bytes: int,
    content_type: str | None = None,
) -> str:
    """
    Validate uploaded file before saving and ingestion.
    Returns normalized file_type ('csv' or 'xlsx').
    Raises FileValidationError on any invalid condition.
    """
    if not filename or not filename.strip():
        raise FileValidationError("Filename cannot be empty.")

    # Prevent basic path traversal in filename check
    sanitized_filename = os.path.basename(filename.strip())
    if not sanitized_filename or sanitized_filename.startswith("."):
        raise FileValidationError("Invalid filename.")

    _, ext = os.path.splitext(sanitized_filename)
    ext_lower = ext.lower()

    if ext_lower not in SUPPORTED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file format '{ext}'. Only .csv and .xlsx files are supported."
        )

    if file_size_bytes <= 0:
        raise FileValidationError("Uploaded file is empty (0 bytes).")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if file_size_bytes > max_bytes:
        raise FileValidationError(
            f"File size exceeds the maximum allowed limit of {settings.max_upload_size_mb}MB."
        )

    return ext_lower.lstrip(".")
