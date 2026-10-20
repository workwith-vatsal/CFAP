import { apiClient } from '@/lib/api/apiClient';
import {
  CategoricalBreakdownData,
  CrossMatricesData,
  DeterministicInsights,
  ExecutiveOverview,
  ExplainabilityData,
  TemporalTrendsData,
} from '@/types/analytics';

export const analyticsApi = {
  getExecutiveOverview: async (analysisId: number): Promise<ExecutiveOverview> => {
    return apiClient.get<ExecutiveOverview>(
      `/api/v1/analyses/${analysisId}/analytics/overview`
    );
  },

  getDeterministicInsights: async (
    analysisId: number
  ): Promise<DeterministicInsights> => {
    return apiClient.get<DeterministicInsights>(
      `/api/v1/analyses/${analysisId}/analytics/insights`
    );
  },

  getCrossMatrices: async (analysisId: number): Promise<CrossMatricesData> => {
    return apiClient.get<CrossMatricesData>(
      `/api/v1/analyses/${analysisId}/analytics/cross-matrices`
    );
  },

  getTemporalTrends: async (
    analysisId: number,
    interval: string = 'auto'
  ): Promise<TemporalTrendsData> => {
    return apiClient.get<TemporalTrendsData>(
      `/api/v1/analyses/${analysisId}/analytics/temporal-trends?interval=${encodeURIComponent(interval)}`
    );
  },

  getCategoricalBreakdown: async (
    analysisId: number,
    column?: string
  ): Promise<CategoricalBreakdownData> => {
    const qs = column ? `?column=${encodeURIComponent(column)}` : '';
    return apiClient.get<CategoricalBreakdownData>(
      `/api/v1/analyses/${analysisId}/analytics/categorical${qs}`
    );
  },

  getExplainability: async (
    analysisId: number,
    feedbackResultId: number
  ): Promise<ExplainabilityData> => {
    return apiClient.get<ExplainabilityData>(
      `/api/v1/analyses/${analysisId}/results/${feedbackResultId}/explain`
    );
  },
};
