from typing import Any
from pydantic import BaseModel, Field


class MetricComparison(BaseModel):
    metric_name: str
    user_value: float
    platform_median: float
    platform_mean: float
    platform_p25: float
    platform_p75: float
    difference: float
    observation: str


class EmotionComparison(BaseModel):
    emotion: str
    user_percentage: float
    platform_average_percentage: float


class SentimentComparison(BaseModel):
    positive_user_pct: float
    positive_platform_pct: float
    neutral_user_pct: float
    neutral_platform_pct: float
    negative_user_pct: float
    negative_platform_pct: float


class BenchmarkMethodology(BaseModel):
    eligible_sample_size: int
    min_required_sample_size: int
    inclusion_criteria: str = (
        "Aggregates derived exclusively from completed analyses with verified data quality. Failed or processing analyses are strictly excluded."
    )
    anonymization_method: str = (
        "Mathematical distributions and percentiles computed cross-tenant with k-anonymity safeguards. Zero individual tenant identifiers or customer texts are exposed."
    )
    non_causal_statement: str = (
        "Benchmark aggregates reflect observational comparisons across analyzed datasets and do not establish causal relationships."
    )


class BenchmarkSummaryResponse(BaseModel):
    is_eligible: bool
    eligible_sample_size: int
    min_required_sample_size: int
    message: str | None = None
    analysis_id: int
    dataset_name: str
    net_sentiment_score: MetricComparison | None = None
    data_quality_score: MetricComparison | None = None
    sentiment_distribution: SentimentComparison | None = None
    emotion_distribution: list[EmotionComparison] | None = None
    volume_comparison: MetricComparison | None = None
    methodology: BenchmarkMethodology
    privacy_notice: str = (
        "Benchmark metrics represent anonymized platform aggregates. Individual user identities, dataset names, and customer feedback are never exposed."
    )
