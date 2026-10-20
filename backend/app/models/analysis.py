from datetime import datetime
import enum
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class AnalysisStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AnalysisStage(str, enum.Enum):
    INITIALIZED = "INITIALIZED"
    LOADING = "LOADING"
    PREPARING = "PREPARING"
    PREPROCESSING = "PREPROCESSING"
    SENTIMENT = "SENTIMENT"
    EMOTION = "EMOTION"
    EMBEDDINGS = "EMBEDDINGS"
    TOPIC_MODELING = "TOPIC_MODELING"
    TOPICS = "TOPICS"
    AGGREGATION = "AGGREGATION"
    FINALIZING = "FINALIZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    dataset_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default=AnalysisStatus.QUEUED.value,
        index=True,
        nullable=False,
    )

    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    current_stage: Mapped[str] = mapped_column(
        String(50),
        default=AnalysisStage.PREPARING.value,
        nullable=False,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    total_feedback_rows: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    usable_feedback_rows: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Model versioning — actual identifiers persisted at runtime
    sentiment_model: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    emotion_model: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    embedding_model: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    bertopic_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Aggregated results — deterministic summaries from actual inference
    sentiment_summary: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    emotion_summary: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    topic_summary: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    topic_info: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    dataset = relationship("Dataset", back_populates="analyses")
    owner = relationship("User", back_populates="analyses")
    feedback_results = relationship(
        "FeedbackResult",
        back_populates="analysis",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
