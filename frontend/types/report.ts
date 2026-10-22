export type ReportStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export type ReportType = 'FULL' | 'EXECUTIVE' | 'ANALYSIS' | 'full' | 'executive' | 'analysis';

export interface ReportItem {
  id: number;
  user_id: number;
  dataset_id: number;
  analysis_id: number;
  report_type: string;
  status: ReportStatus;
  file_size_bytes?: number | null;
  error_message?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface ReportListResponse {
  items: ReportItem[];
  total: number;
}

export interface ReportCreateRequest {
  dataset_id: number;
  analysis_id: number;
  report_type: string;
}
