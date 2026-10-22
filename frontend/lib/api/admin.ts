import { apiClient } from './apiClient';
import {
  AdminAuditLogListResponse,
  AdminSystemOverviewResponse,
  AdminUserListItem,
  AdminUserListResponse,
} from '@/types';

export interface ListUsersParams {
  page?: number;
  limit?: number;
  search?: string;
  role?: string;
  is_active?: boolean;
}

export interface ListAuditLogsParams {
  page?: number;
  limit?: number;
  action?: string;
  resource_type?: string;
  status?: string;
  user_id?: number;
  start_date?: string;
  end_date?: string;
}

export const adminApi = {
  getOverview: async (): Promise<AdminSystemOverviewResponse> => {
    return apiClient.get<AdminSystemOverviewResponse>('/api/v1/admin/overview');
  },

  listUsers: async (params?: ListUsersParams): Promise<AdminUserListResponse> => {
    const query = new URLSearchParams();
    if (params?.page) query.append('page', params.page.toString());
    if (params?.limit) query.append('limit', params.limit.toString());
    if (params?.search) query.append('search', params.search);
    if (params?.role) query.append('role', params.role);
    if (params?.is_active !== undefined) query.append('is_active', String(params.is_active));

    const qs = query.toString();
    return apiClient.get<AdminUserListResponse>(`/api/v1/admin/users${qs ? `?${qs}` : ''}`);
  },

  updateUserStatus: async (userId: number, isActive: boolean): Promise<AdminUserListItem> => {
    return apiClient.patch<AdminUserListItem>(`/api/v1/admin/users/${userId}/status`, {
      is_active: isActive,
    });
  },

  listAuditLogs: async (params?: ListAuditLogsParams): Promise<AdminAuditLogListResponse> => {
    const query = new URLSearchParams();
    if (params?.page) query.append('page', params.page.toString());
    if (params?.limit) query.append('limit', params.limit.toString());
    if (params?.action) query.append('action', params.action);
    if (params?.resource_type) query.append('resource_type', params.resource_type);
    if (params?.status) query.append('status', params.status);
    if (params?.user_id) query.append('user_id', params.user_id.toString());
    if (params?.start_date) query.append('start_date', params.start_date);
    if (params?.end_date) query.append('end_date', params.end_date);

    const qs = query.toString();
    return apiClient.get<AdminAuditLogListResponse>(`/api/v1/admin/audit-logs${qs ? `?${qs}` : ''}`);
  },
};
