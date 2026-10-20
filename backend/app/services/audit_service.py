import hashlib
import logging
from typing import Any
from sqlalchemy.orm import Session

from backend.app.models.audit_log import AuditLog

logger = logging.getLogger("audit_service")

# Disallowed keys that must never appear in audit metadata
SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "otp",
    "jwt",
    "api_key",
    "secret",
    "authorization",
    "cookie",
    "feedback_text",
    "customer_feedback",
    "raw_text",
    "file_content",
}


class AuditService:
    @staticmethod
    def hash_ip(ip_address: str | None) -> str | None:
        """
        Generate a privacy-preserving SHA-256 hash of the client IP address.
        """
        if not ip_address or not ip_address.strip():
            return None
        return hashlib.sha256(ip_address.strip().encode("utf-8")).hexdigest()

    @staticmethod
    def sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        """
        Sanitize audit log metadata ensuring zero sensitive credentials,
        tokens, or raw customer feedback text are persisted.
        """
        if not metadata:
            return None

        sanitized: dict[str, Any] = {}
        for key, value in metadata.items():
            key_lower = str(key).lower()
            if key_lower in SENSITIVE_KEYS or any(sens in key_lower for sens in ["password", "token", "secret", "cookie", "raw_text", "feedback_text"]):
                continue

            # Bound string values
            if isinstance(value, str):
                sanitized[key] = value[:200]
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, list):
                sanitized[key] = [str(x)[:100] for x in value[:10]]
            elif isinstance(value, dict):
                # Recursively sanitize shallow sub-dict
                sub = AuditService.sanitize_metadata(value)
                if sub:
                    sanitized[key] = sub
            else:
                sanitized[key] = str(value)[:100]

        return sanitized

    @classmethod
    def log_event(
        cls,
        db: Session,
        action: str,
        resource_type: str,
        resource_id: str | int | None = None,
        user_id: int | None = None,
        status: str = "SUCCESS",
        ip_address: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog | None:
        """
        Record a security-relevant event to the audit log.
        Safely catches exceptions to ensure audit logging never disrupts primary requests.
        """
        try:
            ip_hash = cls.hash_ip(ip_address)
            sanitized_meta = cls.sanitize_metadata(metadata)

            log_entry = AuditLog(
                user_id=user_id,
                action=action.upper()[:50],
                resource_type=resource_type.lower()[:50],
                resource_id=str(resource_id)[:100] if resource_id is not None else None,
                status=status.upper()[:20],
                ip_hash=ip_hash,
                metadata_json=sanitized_meta,
            )

            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            return log_entry
        except Exception as e:
            logger.warning(f"Failed to record audit log event {action}: {e}")
            try:
                db.rollback()
            except Exception:
                pass
            return None
