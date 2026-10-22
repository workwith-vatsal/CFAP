export type DatasetStatus =
  | 'UPLOADING'
  | 'PROCESSING'
  | 'READY'
  | 'FAILED'
  | 'ARCHIVED';

export type ColumnDetectedType =
  | 'feedback'
  | 'rating'
  | 'date'
  | 'category'
  | 'product'
  | 'customer_id'
  | 'numeric'
  | 'boolean'
  | 'sensitive'
  | 'unknown';

export interface ColumnQualityInfo {
  name: string;
  detected_type: ColumnDetectedType;
  raw_dtype: string;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  is_sensitive: boolean;
}

export interface ScoreBreakdown {
  usable_feedback_score: number;
  completeness_score: number;
  uniqueness_score: number;
  structure_score: number;
}

export interface DataQualityReport {
  rows: number;
  total_columns: number;
  usable_rows: number;
  invalid_rows: number;
  duplicate_rows: number;
  missing_values: number;
  feedback_column: string | null;
  feedback_confidence: number | null;
  missing_feedback: number;
  blank_feedback: number;
  quality_score: number;
  score_breakdown: ScoreBreakdown;
  columns: ColumnQualityInfo[];
  columns_detail?: ColumnQualityInfo[];
}

export interface Dataset {
  id: number;
  owner_id: number;
  name: string;
  original_filename: string;
  file_type: 'csv' | 'xlsx';
  file_size_bytes: number;
  row_count: number;
  column_count: number;
  status: DatasetStatus;
  feedback_column?: string | null;
  feedback_confidence?: number | null;
  quality_score?: number | null;
  created_at: string;
  updated_at: string;
  error_message?: string | null;
  quality_checked_at?: string | null;
  quality_report?: DataQualityReport | null;
}

export interface DatasetListResponse {
  datasets: Dataset[];
  total: number;
}

export interface DataPreviewResponse {
  columns: string[];
  total_preview_rows: number;
  rows: Array<Record<string, string | number | boolean | null>>;
}
