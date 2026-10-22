from datetime import datetime
import enum
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class ReportStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ReportType(str, enum.Enum):
    FULL = "full"
    EXECUTIVE = "executive"
    ANALYSIS = "analysis"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dataset_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    analysis_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    report_type: Mapped[str] = mapped_column(
        String(50),
        default=ReportType.FULL.value,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default=ReportStatus.QUEUED.value,
        nullable=False,
        index=True,
    )

    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    file_size_bytes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    user = relationship("User")
    dataset = relationship("Dataset")
    analysis = relationship("Analysis")
