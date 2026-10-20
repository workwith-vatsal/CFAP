from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class TokenContributionSchema(BaseModel):
    token: str
    shap_value: float
    position: int
    importance: float
    direction: str  # "positive" | "negative" | "neutral"


class SentimentMappingSchema(BaseModel):
    raw_star_output: str
    cfap_mapped_sentiment: str
    mapping_rule: str
    explanation_basis: str


class ExplainabilityResponse(BaseModel):
    id: Optional[int] = None
    analysis_id: int
    feedback_result_id: int
    predicted_label: str
    raw_predicted_label: Optional[str] = None
    confidence: float
    base_value: float
    token_contributions: List[TokenContributionSchema]
    positive_tokens: List[TokenContributionSchema] = []
    negative_tokens: List[TokenContributionSchema] = []
    model_name: str
    explainer_name: str
    is_cached: bool = False
    sentiment_mapping: SentimentMappingSchema


class SentimentCountSchema(BaseModel):
    count: int
    percentage: float


class SentimentDistributionSchema(BaseModel):
    positive: SentimentCountSchema
    neutral: SentimentCountSchema
    negative: SentimentCountSchema


class TopEmotionSchema(BaseModel):
    emotion: str
    count: int
    percentage: float


class TopTopicSchema(BaseModel):
    topic_id: int
    label: str
    count: int
    percentage: float
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    net_sentiment_score: float = 0.0


class ExecutiveOverviewResponse(BaseModel):
    analysis_id: int
    total_feedback: int
    usable_feedback: int
    sentiment_distribution: SentimentDistributionSchema
    net_sentiment_score: float
    positive_ratio: float
    average_confidence: float
    top_emotions: List[TopEmotionSchema]
    top_topics: List[TopTopicSchema]


class InsightSchema(BaseModel):
    id: str
    type: str  # "positive_driver" | "friction_driver" | "emotion_tone" | "risk_alert"
    title: str
    description: str
    metric_value: Optional[str] = None
    severity: str  # "positive" | "warning" | "critical" | "info"


class RecommendationSchema(BaseModel):
    id: str
    title: str
    description: str
    priority: str  # "High" | "Medium" | "Low"


class InsightsResponse(BaseModel):
    health_score: float
    health_status: str
    summary: str
    insights: List[InsightSchema]
    recommendations: List[RecommendationSchema]


class SentimentEmotionMatrixRow(BaseModel):
    sentiment: str
    emotions: Dict[str, Dict[str, Any]]
    total: int


class SentimentEmotionMatrixResponse(BaseModel):
    columns: List[str]
    rows: List[SentimentEmotionMatrixRow]


class SentimentTopicItem(BaseModel):
    topic_id: int
    topic_label: str
    total_count: int
    positive_count: int
    positive_percentage: float
    neutral_count: int
    neutral_percentage: float
    negative_count: int
    negative_percentage: float
    net_sentiment_score: float


class SentimentTopicMatrixResponse(BaseModel):
    topics: List[SentimentTopicItem]


class EmotionTopicItem(BaseModel):
    topic_id: int
    topic_label: str
    total_count: int
    emotions: Dict[str, Dict[str, Any]]


class EmotionTopicMatrixResponse(BaseModel):
    emotions: List[str]
    topics: List[EmotionTopicItem]


class CrossMatricesResponse(BaseModel):
    sentiment_emotion: SentimentEmotionMatrixResponse
    sentiment_topic: SentimentTopicMatrixResponse
    emotion_topic: EmotionTopicMatrixResponse


class TimelinePoint(BaseModel):
    period: str
    total_count: int
    positive_count: int
    neutral_count: int
    negative_count: int
    net_sentiment_score: float
    dominant_emotion: str


class TemporalTrendsResponse(BaseModel):
    available: bool
    reason: Optional[str] = None
    date_column: Optional[str] = None
    interval: Optional[str] = None
    timeline: List[TimelinePoint] = []


class CategoryBreakdownItem(BaseModel):
    category_value: str
    total_count: int
    positive_count: int
    positive_percentage: float
    neutral_count: int
    neutral_percentage: float
    negative_count: int
    negative_percentage: float
    net_sentiment_score: float
    dominant_emotion: str


class CategoricalBreakdownResponse(BaseModel):
    available: bool
    reason: Optional[str] = None
    categorical_columns: List[str] = []
    active_column: Optional[str] = None
    breakdown: List[CategoryBreakdownItem] = []
