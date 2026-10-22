export type AnalysisStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export type AnalysisStage =
  | 'INITIALIZED'
  | 'LOADING'
  | 'PREPROCESSING'
  | 'SENTIMENT'
  | 'EMOTION'
  | 'EMBEDDINGS'
  | 'TOPIC_MODELING'
  | 'AGGREGATION'
  | 'COMPLETED'
  | 'FAILED';

export interface SentimentSummary {
  total_analyzed: number;
  positive_count: number;
  positive_percentage: number;
  neutral_count: number;
  neutral_percentage: number;
  negative_count: number;
  negative_percentage: number;
  net_sentiment_score: number;
  average_confidence: number;
  star_distribution: Record<string, number>;
}

export interface EmotionDetail {
  count: number;
  percentage: number;
  average_probability: number;
}

export interface EmotionSummary {
  dominant_emotion: string;
  emotion_breakdown: Record<string, EmotionDetail>;
  average_confidence: number;
}

export interface TopicKeyword {
  word: string;
  score: number;
}

export interface TopicInfoItem {
  topic_id: number;
  name: string;
  count: number;
  percentage: number;
  keywords: TopicKeyword[];
}

export interface TopTopicItem {
  topic_id: number;
  name: string;
  count: number;
  percentage: number;
  top_keywords: string[];
}

export interface TopicSummary {
  total_topics: number;
  outlier_count: number;
  outlier_percentage: number;
  top_topics: TopTopicItem[];
}

export interface Analysis {
  id: number;
  dataset_id: number;
  owner_id: number;
  status: AnalysisStatus;
  progress: number;
  current_stage: AnalysisStage;
  error_message?: string | null;
  total_feedback_rows: number;
  usable_feedback_rows: number;
  sentiment_model?: string | null;
  emotion_model?: string | null;
  embedding_model?: string | null;
  bertopic_version?: string | null;
  sentiment_summary?: SentimentSummary | null;
  emotion_summary?: EmotionSummary | null;
  topic_summary?: TopicSummary | null;
  topic_info?: TopicInfoItem[] | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AnalysisSummary {
  id: number;
  dataset_id: number;
  status: AnalysisStatus;
  progress: number;
  current_stage: AnalysisStage;
  total_feedback_rows: number;
  usable_feedback_rows: number;
  created_at: string;
  completed_at?: string | null;
}

export interface FeedbackResultItem {
  id: number;
  analysis_id: number;
  row_index: number;
  text_length: number;
  sentiment_label?: 'positive' | 'neutral' | 'negative' | null;
  raw_sentiment_label?: string | null;
  sentiment_score?: number | null;
  emotion_label?: string | null;
  emotion_score?: number | null;
  emotion_scores?: Record<string, number> | null;
  topic_id?: number | null;
  topic_label?: string | null;
  is_valid: boolean;
  created_at: string;
}

export interface FeedbackResultListResponse {
  items: FeedbackResultItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
