import { apiClient } from '@/lib/api/apiClient';
import {
  AssistantConversationDetail,
  AssistantConversationSummary,
  AssistantMessageResponse,
  SuggestedQuestion,
} from '@/types/assistant';

export const assistantApi = {
  createConversation: async (
    datasetId: number,
    analysisId: number,
    title?: string
  ): Promise<AssistantConversationDetail> => {
    return apiClient.post<AssistantConversationDetail>(
      '/api/v1/assistant/conversations',
      {
        dataset_id: datasetId,
        analysis_id: analysisId,
        title,
      }
    );
  },

  listConversations: async (
    datasetId?: number,
    analysisId?: number
  ): Promise<AssistantConversationSummary[]> => {
    const params = new URLSearchParams();
    if (datasetId) params.append('dataset_id', datasetId.toString());
    if (analysisId) params.append('analysis_id', analysisId.toString());
    const qs = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get<AssistantConversationSummary[]>(
      `/api/v1/assistant/conversations${qs}`
    );
  },

  getConversation: async (
    conversationId: number
  ): Promise<AssistantConversationDetail> => {
    return apiClient.get<AssistantConversationDetail>(
      `/api/v1/assistant/conversations/${conversationId}`
    );
  },

  sendMessage: async (
    conversationId: number,
    content: string
  ): Promise<AssistantMessageResponse> => {
    return apiClient.post<AssistantMessageResponse>(
      `/api/v1/assistant/conversations/${conversationId}/messages`,
      { content }
    );
  },

  deleteConversation: async (
    conversationId: number
  ): Promise<{ success: boolean; message: string }> => {
    return apiClient.delete<{ success: boolean; message: string }>(
      `/api/v1/assistant/conversations/${conversationId}`
    );
  },

  getSuggestedQuestions: async (
    analysisId: number
  ): Promise<SuggestedQuestion[]> => {
    return apiClient.get<SuggestedQuestion[]>(
      `/api/v1/assistant/analyses/${analysisId}/suggested-questions`
    );
  },
};
