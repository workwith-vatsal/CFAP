import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_active_verified_user
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.schemas.assistant import (
    AssistantConversationDetailSchema,
    AssistantConversationSummarySchema,
    ConversationCreateRequest,
    MessageResponse,
    MessageSendRequest,
    SuggestedQuestionSchema,
)
from backend.app.services.assistant.service import AssistantService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["Dataset-Grounded AI Assistant"])


@router.post(
    "/conversations",
    response_model=AssistantConversationDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    payload: ConversationCreateRequest,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Creates a new conversational thread attached to a specific completed dataset analysis.
    Enforces strict multi-tenant ownership: User -> Dataset -> Analysis.
    """
    conversation = AssistantService.create_conversation(
        user_id=current_user.id,
        dataset_id=payload.dataset_id,
        analysis_id=payload.analysis_id,
        title=payload.title,
        db=db,
    )
    return conversation


@router.get(
    "/conversations",
    response_model=List[AssistantConversationSummarySchema],
)
def list_conversations(
    dataset_id: Optional[int] = Query(None, description="Filter by dataset ID"),
    analysis_id: Optional[int] = Query(None, description="Filter by analysis ID"),
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Lists all assistant conversations belonging to the authenticated user.
    """
    conversations = AssistantService.list_conversations(
        user_id=current_user.id,
        dataset_id=dataset_id,
        analysis_id=analysis_id,
        db=db,
    )
    summaries = []
    for c in conversations:
        summaries.append({
            "id": c.id,
            "dataset_id": c.dataset_id,
            "analysis_id": c.analysis_id,
            "title": c.title,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
            "message_count": len(c.messages) if c.messages else 0,
        })
    return summaries


@router.get(
    "/conversations/{conversation_id}",
    response_model=AssistantConversationDetailSchema,
)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves full conversation history and grounded assistant responses.
    """
    return AssistantService.get_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
        db=db,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def send_message(
    conversation_id: int,
    payload: MessageSendRequest,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Sends a user question to the dataset-grounded assistant.
    Flow: Router -> Context Builder -> CFAP Analytics -> LLM Reasoning -> Grounding Validator.
    """
    return AssistantService.send_message(
        conversation_id=conversation_id,
        content=payload.content,
        current_user=current_user,
        db=db,
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_200_OK,
)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Deletes an assistant conversation and all its associated messages.
    """
    AssistantService.delete_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
        db=db,
    )
    return {"success": True, "message": "Conversation deleted successfully."}


@router.get(
    "/analyses/{analysis_id}/suggested-questions",
    response_model=List[SuggestedQuestionSchema],
)
def get_suggested_questions(
    analysis_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Returns dynamically generated, grounded suggested questions for a completed analysis.
    """
    return AssistantService.get_suggested_questions(
        analysis_id=analysis_id,
        current_user=current_user,
        db=db,
    )
