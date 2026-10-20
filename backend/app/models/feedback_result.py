from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    LargeBinary,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class FeedbackResult(Base):
    """
    Per-row analysis result for each feedback item in a dataset.

    Privacy note: This model intentionally does NOT store the original
    or preprocessed customer feedback text. The original uploaded file
    remains the sole source of feedback text. Only analytical outputs
    (sentiment, emotion, topic, embedding) and metadata are persisted.
    """
    __tablename__ = "feedback_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    analysis_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
    )

    row_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    text_length: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Sentiment — from nlptown/bert-base-multilingual-uncased-sentiment
    # raw_sentiment_label: original model output (e.g. "4 stars")
    # sentiment_label: mapped 3-class (Positive/Neutral/Negative)
    # sentiment_score: model confidence for the predicted class
    sentiment_label: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    raw_sentiment_label: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    sentiment_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Emotion — from j-hartmann/emotion-english-distilroberta-base
    emotion_label: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    emotion_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    emotion_scores: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Topic — from BERTopic
    topic_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    topic_label: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Embedding — 384-dim float32 from MiniLM, stored as BYTEA
    # Serialization/deserialization is handled by embedding_storage utility
    embedding: Mapped[bytes | None] = mapped_column(
        LargeBinary,
        nullable=True,
    )

    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    analysis = relationship("Analysis", back_populates="feedback_results")

    __table_args__ = (
        Index("ix_feedback_results_analysis_row", "analysis_id", "row_index"),
    )
