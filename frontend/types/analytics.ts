export interface TokenContribution {
  token: string;
  shap_value: number;
  position: number;
  importance: number;
  direction: 'positive' | 'negative' | 'neutral';
}

export interface SentimentMappingMetadata {
  raw_star_output: string;
  cfap_mapped_sentiment: string;
  mapping_rule: string;
  explanation_basis: string;
}

export interface ExplainabilityData {
  id?: number | null;
  analysis_id: number;
  feedback_result_id: number;
  predicted_label: string;
  raw_predicted_label?: string | null;
  confidence: number;
  base_value: number;
  token_contributions: TokenContribution[];
  positive_tokens: TokenContribution[];
  negative_tokens: TokenContribution[];
  model_name: string;
  explainer_name: string;
  is_cached: boolean;
  sentiment_mapping: SentimentMappingMetadata;
}

export interface SentimentCount {
  count: number;
  percentage: number;
}

export interface SentimentDistribution {
  positive: SentimentCount;
  neutral: SentimentCount;
  negative: SentimentCount;
}

export interface TopEmotion {
  emotion: string;
  count: number;
  percentage: number;
}

export interface TopTopic {
  topic_id: number;
  label: string;
  count: number;
  percentage: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  net_sentiment_score: number;
}

export interface ExecutiveOverview {
  analysis_id: number;
  total_feedback: number;
  usable_feedback: number;
  sentiment_distribution: SentimentDistribution;
  net_sentiment_score: number;
  positive_ratio: number;
  average_confidence: number;
  top_emotions: TopEmotion[];
  top_topics: TopTopic[];
}

export interface InsightItem {
  id: string;
  type: 'positive_driver' | 'friction_driver' | 'emotion_tone' | 'risk_alert';
  title: string;
  description: string;
  metric_value?: string | null;
  severity: 'positive' | 'warning' | 'critical' | 'info';
}

export interface RecommendationItem {
  id: string;
  title: string;
  description: string;
  priority: 'High' | 'Medium' | 'Low';
}

export interface DeterministicInsights {
  health_score: number;
  health_status: string;
  summary: string;
  insights: InsightItem[];
  recommendations: RecommendationItem[];
}

export interface SentimentEmotionMatrixRow {
  sentiment: string;
  emotions: Record<string, { count: number; percentage: number }>;
  total: number;
}

export interface SentimentEmotionMatrix {
  columns: string[];
  rows: SentimentEmotionMatrixRow[];
}

export interface SentimentTopicItem {
  topic_id: number;
  topic_label: string;
  total_count: number;
  positive_count: number;
  positive_percentage: number;
  neutral_count: number;
  neutral_percentage: number;
  negative_count: number;
  negative_percentage: number;
  net_sentiment_score: number;
}

export interface SentimentTopicMatrix {
  topics: SentimentTopicItem[];
}

export interface EmotionTopicItem {
  topic_id: number;
  topic_label: string;
  total_count: number;
  emotions: Record<string, { count: number; percentage: number }>;
}

export interface EmotionTopicMatrix {
  emotions: string[];
  topics: EmotionTopicItem[];
}

export interface CrossMatricesData {
  sentiment_emotion: SentimentEmotionMatrix;
  sentiment_topic: SentimentTopicMatrix;
  emotion_topic: EmotionTopicMatrix;
}

export interface TimelinePoint {
  period: string;
  total_count: number;
  positive_count: number;
  neutral_count: number;
  negative_count: number;
  net_sentiment_score: number;
  dominant_emotion: string;
}

export interface TemporalTrendsData {
  available: boolean;
  reason?: string | null;
  date_column?: string | null;
  interval?: string | null;
  timeline: TimelinePoint[];
}

export interface CategoryBreakdownItem {
  category_value: string;
  total_count: number;
  positive_count: number;
  positive_percentage: number;
  neutral_count: number;
  neutral_percentage: number;
  negative_count: number;
  negative_percentage: number;
  net_sentiment_score: number;
  dominant_emotion: string;
}

export interface CategoricalBreakdownData {
  available: boolean;
  reason?: string | null;
  categorical_columns: string[];
  active_column?: string | null;
  breakdown: CategoryBreakdownItem[];
}
