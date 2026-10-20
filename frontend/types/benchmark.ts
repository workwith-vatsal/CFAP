export interface MetricComparison {
  metric_name: string;
  user_value: number;
  platform_median: number;
  platform_mean: number;
  platform_p25: number;
  platform_p75: number;
  difference: number;
  observation: string;
}

export interface EmotionComparison {
  emotion: string;
  user_percentage: number;
  platform_average_percentage: number;
}

export interface SentimentComparison {
  positive_user_pct: number;
  positive_platform_pct: number;
  neutral_user_pct: number;
  neutral_platform_pct: number;
  negative_user_pct: number;
  negative_platform_pct: number;
}

export interface BenchmarkMethodology {
  eligible_sample_size: number;
  min_required_sample_size: number;
  inclusion_criteria: string;
  anonymization_method: string;
  non_causal_statement: string;
}

export interface BenchmarkSummaryResponse {
  is_eligible: boolean;
  eligible_sample_size: number;
  min_required_sample_size: number;
  message: string | null;
  analysis_id: number;
  dataset_name: string;
  net_sentiment_score: MetricComparison | null;
  data_quality_score: MetricComparison | null;
  sentiment_distribution: SentimentComparison | null;
  emotion_distribution: EmotionComparison[] | null;
  volume_comparison: MetricComparison | null;
  methodology: BenchmarkMethodology;
  privacy_notice: string;
}
