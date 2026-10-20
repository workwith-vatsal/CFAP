import { apiClient } from '@/lib/api/apiClient';
import { ReportCreateRequest, ReportItem, ReportListResponse } from '@/types/report';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const reportsApi = {
  createReport: async (data: ReportCreateRequest): Promise<ReportItem> => {
    return apiClient.post<ReportItem>('/api/v1/reports', data);
  },

  listReports: async (
    datasetId?: number,
    analysisId?: number
  ): Promise<ReportListResponse> => {
    const params = new URLSearchParams();
    if (datasetId) params.append('dataset_id', String(datasetId));
    if (analysisId) params.append('analysis_id', String(analysisId));
    const qs = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get<ReportListResponse>(`/api/v1/reports${qs}`);
  },

  getReport: async (reportId: number): Promise<ReportItem> => {
    return apiClient.get<ReportItem>(`/api/v1/reports/${reportId}`);
  },

  deleteReport: async (
    reportId: number
  ): Promise<{ message: string; id: number }> => {
    return apiClient.delete<{ message: string; id: number }>(
      `/api/v1/reports/${reportId}`
    );
  },

  downloadReportPdf: async (reportId: number, filename?: string): Promise<void> => {
    const url = `${API_BASE_URL}/api/v1/reports/${reportId}/download`;
    const response = await fetch(url, {
      method: 'GET',
      credentials: 'include',
    });

    if (!response.ok) {
      let errorMsg = 'Failed to download report.';
      try {
        const json = await response.json();
        if (json.detail) errorMsg = json.detail;
      } catch {
        // Fallback
      }
      throw new Error(errorMsg);
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename || `CFAP_Report_${reportId}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(downloadUrl);
    document.body.removeChild(a);
  },
};
