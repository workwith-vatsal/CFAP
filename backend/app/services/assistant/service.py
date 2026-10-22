from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.assistant import AssistantConversation, AssistantMessage
from backend.app.models.dataset import Dataset
from backend.app.models.user import User
from backend.app.services.assistant.context_builder import ContextBuilder
from backend.app.services.assistant.grounding import GroundingValidator
from backend.app.services.assistant.prompts import ASSISTANT_SYSTEM_PROMPT
from backend.app.services.assistant.provider import (
    BaseLLMProvider,
    ProviderUnavailableError,
    get_llm_provider,
)
from backend.app.services.assistant.question_router import QuestionRouter

logger = logging.getLogger(__name__)


class AssistantService:
    """
    Core Assistant Service for CFAP Phase 6.
    Orchestrates conversation lifecycle, multi-tenant isolation,
    analytics-first evidence retrieval, LLM generation, and grounding validation.
    """

    @classmethod
    def create_conversation(
        cls,
        user_id: int,
        dataset_id: int,
        analysis_id: int,
        title: Optional[str],
        db: Session,
    ) -> AssistantConversation:
        """
        Creates a new assistant conversation after validating dataset/analysis ownership and status.
        """
        # 1. Verify Dataset ownership
        dataset = (
            db.query(Dataset)
            .filter(Dataset.id == dataset_id, Dataset.owner_id == user_id)
            .first()
        )
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found or access denied.",
            )

        # 2. Verify Analysis ownership and COMPLETED status
        analysis = (
            db.query(Analysis)
            .filter(
                Analysis.id == analysis_id,
                Analysis.dataset_id == dataset_id,
                Analysis.owner_id == user_id,
            )
            .first()
        )
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found or does not belong to this dataset/user.",
            )

        if analysis.status != AnalysisStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Assistant conversations require a COMPLETED analysis (current status: {analysis.status}).",
            )

        conv_title = title.strip() if title and title.strip() else f"Chat: {dataset.name[:30]}"

        conversation = AssistantConversation(
            user_id=user_id,
            dataset_id=dataset_id,
            analysis_id=analysis_id,
            title=conv_title,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    @classmethod
    def list_conversations(
        cls,
        user_id: int,
        dataset_id: Optional[int],
        analysis_id: Optional[int],
        db: Session,
    ) -> List[AssistantConversation]:
        """
        Lists conversations belonging to the authenticated user.
        """
        query = db.query(AssistantConversation).filter(
            AssistantConversation.user_id == user_id
        )
        if dataset_id is not None:
            query = query.filter(AssistantConversation.dataset_id == dataset_id)
        if analysis_id is not None:
            query = query.filter(AssistantConversation.analysis_id == analysis_id)

        return query.order_by(AssistantConversation.updated_at.desc()).all()

    @classmethod
    def get_conversation(
        cls,
        conversation_id: int,
        user_id: int,
        db: Session,
    ) -> AssistantConversation:
        """
        Retrieves a single conversation with tenant verification.
        """
        conversation = (
            db.query(AssistantConversation)
            .filter(
                AssistantConversation.id == conversation_id,
                AssistantConversation.user_id == user_id,
            )
            .first()
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or access denied.",
            )
        return conversation

    @classmethod
    def delete_conversation(
        cls,
        conversation_id: int,
        user_id: int,
        db: Session,
    ) -> None:
        """
        Deletes a conversation and cascades to its messages.
        """
        conversation = cls.get_conversation(conversation_id, user_id, db)
        db.delete(conversation)
        db.commit()

    @classmethod
    def send_message(
        cls,
        conversation_id: int,
        content: str,
        current_user: User,
        db: Session,
        provider_override: Optional[BaseLLMProvider] = None,
    ) -> Dict[str, Any]:
        """
        Processes a user question, retrieves authoritative CFAP evidence, generates a response,
        validates grounding, and persists both messages.
        """
        text = content.strip()
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content cannot be empty.",
            )
        if len(text) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message exceeds maximum allowed length of 1000 characters.",
            )

        conversation = cls.get_conversation(conversation_id, current_user.id, db)

        # 1. Verify Analysis is still COMPLETED
        analysis = (
            db.query(Analysis)
            .filter(
                Analysis.id == conversation.analysis_id,
                Analysis.owner_id == current_user.id,
            )
            .first()
        )
        if not analysis or analysis.status != AnalysisStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The associated analysis is unavailable or not in COMPLETED status.",
            )

        # 2. Persist User Message
        user_msg = AssistantMessage(
            conversation_id=conversation.id,
            role="user",
            content=text,
            created_at=datetime.utcnow(),
        )
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        # 3. Deterministic Question Routing
        q_type = QuestionRouter.route_question(text)

        # 4. Context Construction from CFAP Analytics Engine
        context = ContextBuilder.build_context(
            analysis=analysis,
            current_user=current_user,
            db=db,
            question=text,
            question_type=q_type,
        )

        # 5. LLM Provider Generation
        provider = provider_override or get_llm_provider()

        try:
            raw_response = provider.generate_response(
                prompt=text,
                system_prompt=ASSISTANT_SYSTEM_PROMPT,
                context=context,
                max_tokens=settings.ai_assistant_max_tokens or 1024,
                temperature=settings.ai_assistant_temperature or 0.2,
            )
        except ProviderUnavailableError as pue:
            logger.warning(f"AI Assistant provider unavailable: {pue}")
            raw_response = (
                f"The AI Assistant provider is currently unavailable ({str(pue)}). "
                f"Please check system configuration or try again later."
            )
            context["sources"] = [{"type": "error", "label": "Provider Unavailable"}]
        except Exception as gen_err:
            logger.error(f"Unexpected error during assistant generation: {gen_err}")
            raw_response = (
                "An unexpected error occurred while communicating with the AI assistant. "
                "Please try again."
            )
            context["sources"] = [{"type": "error", "label": "Generation Error"}]

        # 6. Grounding Validation & Sanitization
        validation = GroundingValidator.validate_and_sanitize(
            generated_text=raw_response,
            context=context,
        )

        # 7. Persist Assistant Message
        assistant_msg = AssistantMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=validation.sanitized_text,
            question_type=q_type,
            sources_json=context.get("sources", []),
            is_grounded=validation.is_grounded,
            created_at=datetime.utcnow(),
        )
        db.add(assistant_msg)

        # Update conversation title if it was initial
        if conversation.title == "New Conversation" or conversation.title.startswith("Chat:"):
            snippet = text[:40] + ("..." if len(text) > 40 else "")
            conversation.title = snippet

        conversation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(assistant_msg)

        return {
            "id": assistant_msg.id,
            "conversation_id": conversation.id,
            "role": "assistant",
            "content": assistant_msg.content,
            "question_type": q_type,
            "sources": assistant_msg.sources_json,
            "is_grounded": assistant_msg.is_grounded,
            "created_at": assistant_msg.created_at.isoformat(),
        }

    @classmethod
    def get_suggested_questions(
        cls,
        analysis_id: int,
        current_user: User,
        db: Session,
    ) -> List[Dict[str, str]]:
        """
        Returns grounded suggested questions tailored to the completed analysis results.
        """
        # Verify ownership & completion
        analysis = (
            db.query(Analysis)
            .filter(Analysis.id == analysis_id, Analysis.owner_id == current_user.id)
            .first()
        )
        if not analysis or analysis.status != AnalysisStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Completed analysis not found.",
            )

        return [
            {
                "category": "OVERVIEW",
                "question": "What is the overall sentiment distribution and health score?",
            },
            {
                "category": "SENTIMENT",
                "question": "What percentage of customer feedback is negative?",
            },
            {
                "category": "EMOTION",
                "question": "What emotions dominate negative feedback?",
            },
            {
                "category": "TOPIC",
                "question": "Which topics have the lowest Net Sentiment Score?",
            },
            {
                "category": "TREND",
                "question": "How has customer sentiment evolved over time?",
            },
            {
                "category": "FEEDBACK_SEARCH",
                "question": "Show representative examples of negative customer complaints.",
            },
        ]
