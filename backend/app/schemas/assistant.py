from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ConversationCreateRequest(BaseModel):
    dataset_id: int = Field(..., description="ID of the dataset")
    analysis_id: int = Field(..., description="ID of the completed analysis")
    title: Optional[str] = Field(None, max_length=255, description="Optional title for the conversation")


class MessageSendRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000, description="Natural language question content")


class AssistantSourceSchema(BaseModel):
    type: str
    label: str


class AssistantMessageSchema(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    question_type: Optional[str] = None
    sources_json: Optional[List[Dict[str, Any]]] = None
    is_grounded: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssistantConversationSummarySchema(BaseModel):
    id: int
    dataset_id: int
    analysis_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class AssistantConversationDetailSchema(BaseModel):
    id: int
    dataset_id: int
    analysis_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[AssistantMessageSchema] = []

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    question_type: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    is_grounded: bool = True
    created_at: str


class SuggestedQuestionSchema(BaseModel):
    category: str
    question: str
