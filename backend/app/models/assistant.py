from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class AssistantConversation(Base):
    __tablename__ = "assistant_conversations"

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

    title: Mapped[str] = mapped_column(
        String(255),
        default="New Conversation",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user = relationship("User")
    dataset = relationship("Dataset")
    analysis = relationship("Analysis")
    messages = relationship(
        "AssistantMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AssistantMessage.created_at.asc()",
    )


class AssistantMessage(Base):
    __tablename__ = "assistant_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("assistant_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # 'user', 'assistant', 'system'

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    question_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    sources_json: Mapped[list | dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    is_grounded: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    # Relationships
    conversation = relationship(
        "AssistantConversation",
        back_populates="messages",
    )
