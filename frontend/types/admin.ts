export interface AdminSystemOverviewResponse {
  total_users: number;
  active_users: number;
  verified_users: number;
  admin_users: number;
  total_datasets: number;
  total_dataset_rows: number;
  total_analyses: number;
  completed_analyses: number;
  failed_analyses: number;
  processing_analyses: number;
  total_reports: number;
  system_status: string;
  database_connected: boolean;
  recent_activities: Array<{
    id: number;
    action: string;
    resource_type: string;
    resource_id: string | null;
    status: string;
    user_email: string;
    created_at: string;
  }>;
}

export interface AdminUserListItem {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  auth_provider: string;
  dataset_count: number;
  analysis_count: number;
  created_at: string;
  updated_at: string;
}

export interface AdminUserListResponse {
  items: AdminUserListItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface AdminUserStatusUpdate {
  is_active: boolean;
}

export interface AdminAuditLogListItem {
  id: number;
  user_id: number | null;
  user_email: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  status: string;
  ip_hash: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
}

export interface AdminAuditLogListResponse {
  items: AdminAuditLogListItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}
