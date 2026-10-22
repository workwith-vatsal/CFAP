export interface AssistantSource {
  type: string;
  label: string;
}

export interface AssistantMessage {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  question_type?: string | null;
  sources_json?: AssistantSource[] | null;
  is_grounded: boolean;
  created_at: string;
}

export interface AssistantConversationSummary {
  id: number;
  dataset_id: number;
  analysis_id: number;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface AssistantConversationDetail {
  id: number;
  dataset_id: number;
  analysis_id: number;
  title: string;
  created_at: string;
  updated_at: string;
  messages: AssistantMessage[];
}

export interface SuggestedQuestion {
  category: string;
  question: string;
}

export interface AssistantMessageResponse {
  id: number;
  conversation_id: number;
  role: string;
  content: string;
  question_type?: string | null;
  sources?: AssistantSource[] | null;
  is_grounded: boolean;
  created_at: string;
}
