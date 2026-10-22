import { apiClient } from './apiClient';
import { BenchmarkSummaryResponse } from '@/types';

export const benchmarksApi = {
  getSummary: async (analysisId: number): Promise<BenchmarkSummaryResponse> => {
    return apiClient.get<BenchmarkSummaryResponse>(`/api/v1/benchmarks/summary?analysis_id=${analysisId}`);
  },
};
