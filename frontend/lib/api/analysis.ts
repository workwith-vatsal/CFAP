import { apiClient } from '@/lib/api/apiClient';
import {
  Analysis,
  AnalysisSummary,
  FeedbackResultListResponse,
} from '@/types/analysis';

export interface GetAnalysisResultsParams {
  page?: number;
  pageSize?: number;
  sentiment?: string;
  emotion?: string;
  topicId?: number;
  isValid?: boolean;
}

export const analysisApi = {
  triggerAnalysis: async (datasetId: number): Promise<Analysis> => {
    return apiClient.post<Analysis>(`/api/v1/datasets/${datasetId}/analyze`);
  },

  getLatestAnalysis: async (datasetId: number): Promise<Analysis> => {
    return apiClient.get<Analysis>(`/api/v1/datasets/${datasetId}/analysis`);
  },

  getAnalysisHistory: async (datasetId: number): Promise<AnalysisSummary[]> => {
    return apiClient.get<AnalysisSummary[]>(
      `/api/v1/datasets/${datasetId}/analyses`
    );
  },

  getAnalysisById: async (analysisId: number): Promise<Analysis> => {
    return apiClient.get<Analysis>(`/api/v1/analyses/${analysisId}`);
  },

  getAnalysisResults: async (
    analysisId: number,
    params: GetAnalysisResultsParams = {}
  ): Promise<FeedbackResultListResponse> => {
    const query = new URLSearchParams();
    if (params.page) query.set('page', params.page.toString());
    if (params.pageSize) query.set('page_size', params.pageSize.toString());
    if (params.sentiment) query.set('sentiment', params.sentiment);
    if (params.emotion) query.set('emotion', params.emotion);
    if (params.topicId !== undefined)
      query.set('topic_id', params.topicId.toString());
    if (params.isValid !== undefined)
      query.set('is_valid', params.isValid.toString());

    const qs = query.toString();
    const endpoint = `/api/v1/analyses/${analysisId}/results${qs ? `?${qs}` : ''}`;
    return apiClient.get<FeedbackResultListResponse>(endpoint);
  },

  deleteAnalysis: async (analysisId: number): Promise<{ message: string }> => {
    return apiClient.delete<{ message: string }>(
      `/api/v1/analyses/${analysisId}`
    );
  },
};
