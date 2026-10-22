from datetime import datetime
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class ExplainabilityResult(Base):
    """
    On-demand SHAP token attribution result for a feedback prediction.

    Privacy note: This model stores token-level attribution weights,
    model baseline values, and class prediction metadata. Preprocessed
    or raw customer feedback text is NOT duplicated.

    Cache Identity: (analysis_id, feedback_result_id, model_name, explainer_name)
    Allows re-explaining under different models or explainer configurations
    without enforcing a global unique constraint on feedback_result_id.
    """
    __tablename__ = "explainability_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    analysis_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    feedback_result_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("feedback_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Derived 3-class sentiment label (Positive / Neutral / Negative)
    predicted_label: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Raw model output (e.g. "5 stars", "1 star")
    raw_predicted_label: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    base_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # Structured token attribution list:
    # [{"token": "excellent", "shap_value": 0.42, "position": 0}, ...]
    token_contributions: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    explainer_name: Mapped[str] = mapped_column(
        String(100),
        default="PartitionExplainer",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    analysis = relationship("Analysis")
    feedback_result = relationship("FeedbackResult")

    __table_args__ = (
        Index(
            "ix_explainability_cache",
            "analysis_id",
            "feedback_result_id",
            "model_name",
            "explainer_name",
        ),
    )
