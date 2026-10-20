from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class SentimentSummarySchema(BaseModel):
    total_analyzed: int
    positive_count: int
    positive_percentage: float
    neutral_count: int
    neutral_percentage: float
    negative_count: int
    negative_percentage: float
    net_sentiment_score: float
    average_confidence: float
    star_distribution: Dict[str, int] = {}


class EmotionDetailSchema(BaseModel):
    count: int
    percentage: float
    average_probability: float


class EmotionSummarySchema(BaseModel):
    dominant_emotion: str
    emotion_breakdown: Dict[str, EmotionDetailSchema] = {}
    average_confidence: float


class TopicKeywordSchema(BaseModel):
    word: str
    score: float


class TopicInfoItemSchema(BaseModel):
    topic_id: int
    name: str
    count: int
    percentage: float
    keywords: List[TopicKeywordSchema] = []


class TopTopicItemSchema(BaseModel):
    topic_id: int
    name: str
    count: int
    percentage: float
    top_keywords: List[str] = []


class TopicSummarySchema(BaseModel):
    total_topics: int
    outlier_count: int
    outlier_percentage: float
    top_topics: List[TopTopicItemSchema] = []


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: int
    owner_id: int
    status: str
    progress: int
    current_stage: str
    error_message: Optional[str] = None
    total_feedback_rows: int
    usable_feedback_rows: int
    sentiment_model: Optional[str] = None
    emotion_model: Optional[str] = None
    embedding_model: Optional[str] = None
    bertopic_version: Optional[str] = None
    sentiment_summary: Optional[Dict[str, Any]] = None
    emotion_summary: Optional[Dict[str, Any]] = None
    topic_summary: Optional[Dict[str, Any]] = None
    topic_info: Optional[List[Dict[str, Any]]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AnalysisSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: int
    status: str
    progress: int
    current_stage: str
    total_feedback_rows: int
    usable_feedback_rows: int
    created_at: datetime
    completed_at: Optional[datetime] = None


class FeedbackResultItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    analysis_id: int
    row_index: int
    text_length: int
    sentiment_label: Optional[str] = None
    raw_sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    emotion_label: Optional[str] = None
    emotion_score: Optional[float] = None
    emotion_scores: Optional[Dict[str, float]] = None
    topic_id: Optional[int] = None
    topic_label: Optional[str] = None
    is_valid: bool
    created_at: datetime


class FeedbackResultListResponse(BaseModel):
    items: List[FeedbackResultItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
