'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Bot,
  Database,
  ChevronDown,
  AlertCircle,
} from 'lucide-react';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { Dataset } from '@/types/dataset';
import { Analysis } from '@/types/analysis';
import {
  AssistantConversationSummary,
  AssistantMessage,
  SuggestedQuestion,
} from '@/types/assistant';
import { getDatasets } from '@/lib/api/datasets';
import { analysisApi } from '@/lib/api/analysis';
import { assistantApi } from '@/lib/api/assistant';
import { ConversationList } from './ConversationList';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { SuggestedQuestions } from './SuggestedQuestions';

interface AssistantViewProps {
  initialDatasetId?: number;
  initialAnalysisId?: number;
}

export const AssistantView: React.FC<AssistantViewProps> = ({
  initialDatasetId,
  initialAnalysisId,
}) => {
  const { t } = useLanguage();

  // Dataset & Analysis State
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(
    initialDatasetId || null
  );
  const [selectedAnalysis, setSelectedAnalysis] = useState<Analysis | null>(null);
  const [isLoadingMetadata, setIsLoadingMetadata] = useState(true);

  // Conversations State
  const [conversations, setConversations] = useState<
    AssistantConversationSummary[]
  >([]);
  const [activeConversationId, setActiveConversationId] = useState<
    number | null
  >(null);
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [suggestedQuestions, setSuggestedQuestions] = useState<
    SuggestedQuestion[]
  >([]);

  // Action State
  const [isSending, setIsSending] = useState(false);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // 1. Initial Load of Datasets
  useEffect(() => {
    let isMounted = true;
    async function loadDatasets() {
      setIsLoadingMetadata(true);
      try {
        const res = await getDatasets(false);
        const ready = (res.datasets || []).filter((d) => d.status === 'READY');
        if (isMounted) {
          setDatasets(ready);
          if (!selectedDatasetId && ready.length > 0) {
            setSelectedDatasetId(ready[0].id);
          }
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : 'Failed to load datasets.';
          setErrorMessage(msg);
        }
      } finally {
        if (isMounted) {
          setIsLoadingMetadata(false);
        }
      }
    }
    loadDatasets();
    return () => {
      isMounted = false;
    };
  }, [selectedDatasetId]);

  // 2. Fetch Latest or Target Completed Analysis for Selected Dataset
  useEffect(() => {
    let isMounted = true;
    async function loadAnalysis() {
      if (!selectedDatasetId) {
        if (isMounted) setSelectedAnalysis(null);
        return;
      }

      try {
        if (initialAnalysisId) {
          const specific = await analysisApi.getAnalysisById(initialAnalysisId);
          if (isMounted && specific && specific.status === 'COMPLETED') {
            setSelectedAnalysis(specific);
            return;
          }
        }

        const latest = await analysisApi.getLatestAnalysis(selectedDatasetId);
        if (isMounted) {
          if (latest && latest.status === 'COMPLETED') {
            setSelectedAnalysis(latest);
          } else {
            setSelectedAnalysis(null);
          }
        }
      } catch {
        if (isMounted) setSelectedAnalysis(null);
      }
    }
    loadAnalysis();
    return () => {
      isMounted = false;
    };
  }, [selectedDatasetId, initialAnalysisId]);

  // 3. Load Suggested Questions for Analysis
  useEffect(() => {
    let isMounted = true;
    async function loadSuggested() {
      if (!selectedAnalysis) {
        if (isMounted) setSuggestedQuestions([]);
        return;
      }
      try {
        const questions = await assistantApi.getSuggestedQuestions(
          selectedAnalysis.id
        );
        if (isMounted) setSuggestedQuestions(questions);
      } catch {
        if (isMounted) setSuggestedQuestions([]);
      }
    }
    loadSuggested();
    return () => {
      isMounted = false;
    };
  }, [selectedAnalysis]);

  // 4. Load Conversations List for Dataset / Analysis
  const refreshConversations = useCallback(async () => {
    if (!selectedDatasetId || !selectedAnalysis) {
      setConversations([]);
      return;
    }
    setIsLoadingConversations(true);
    try {
      const list = await assistantApi.listConversations(
        selectedDatasetId,
        selectedAnalysis.id
      );
      setConversations(list);

      // Auto-select first conversation if none selected
      if (list.length > 0 && !activeConversationId) {
        setActiveConversationId(list[0].id);
      } else if (list.length === 0) {
        setActiveConversationId(null);
        setMessages([]);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load conversations.';
      setErrorMessage(msg);
    } finally {
      setIsLoadingConversations(false);
    }
  }, [selectedDatasetId, selectedAnalysis, activeConversationId]);

  useEffect(() => {
    let isMounted = true;
    async function fetchList() {
      if (!selectedDatasetId || !selectedAnalysis) {
        if (isMounted) setConversations([]);
        return;
      }
      setIsLoadingConversations(true);
      try {
        const list = await assistantApi.listConversations(
          selectedDatasetId,
          selectedAnalysis.id
        );
        if (isMounted) {
          setConversations(list);
          if (list.length > 0) {
            setActiveConversationId((prev) => prev ?? list[0].id);
          } else {
            setActiveConversationId(null);
            setMessages([]);
          }
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : 'Failed to load conversations.';
          setErrorMessage(msg);
        }
      } finally {
        if (isMounted) {
          setIsLoadingConversations(false);
        }
      }
    }
    fetchList();
    return () => {
      isMounted = false;
    };
  }, [selectedDatasetId, selectedAnalysis]);

  // 5. Load Active Conversation History
  useEffect(() => {
    let isMounted = true;
    async function loadConversationDetail() {
      if (!activeConversationId) {
        if (isMounted) setMessages([]);
        return;
      }
      try {
        const detail = await assistantApi.getConversation(activeConversationId);
        if (isMounted) {
          setMessages(detail.messages || []);
          setErrorMessage(null);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : 'Failed to load conversation history.';
          setErrorMessage(msg);
        }
      }
    }
    loadConversationDetail();
    return () => {
      isMounted = false;
    };
  }, [activeConversationId]);

  // Handlers
  const handleNewChat = async () => {
    if (!selectedDatasetId || !selectedAnalysis) return;
    try {
      const newConv = await assistantApi.createConversation(
        selectedDatasetId,
        selectedAnalysis.id,
        'New Conversation'
      );
      await refreshConversations();
      setActiveConversationId(newConv.id);
      setMessages([]);
      setErrorMessage(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create new conversation.';
      setErrorMessage(msg);
    }
  };

  const handleDeleteConversation = async (id: number) => {
    try {
      await assistantApi.deleteConversation(id);
      if (activeConversationId === id) {
        setActiveConversationId(null);
        setMessages([]);
      }
      await refreshConversations();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete conversation.';
      setErrorMessage(msg);
    }
  };

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isSending) return;

    let targetConvId = activeConversationId;

    // Create a new conversation on the fly if none exists
    if (!targetConvId) {
      if (!selectedDatasetId || !selectedAnalysis) return;
      try {
        const created = await assistantApi.createConversation(
          selectedDatasetId,
          selectedAnalysis.id,
          text.slice(0, 30) + '...'
        );
        targetConvId = created.id;
        setActiveConversationId(created.id);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to initialize conversation.';
        setErrorMessage(msg);
        return;
      }
    }

    // Optimistically append user message to UI
    const tempUserMsg: AssistantMessage = {
      id: Date.now(),
      conversation_id: targetConvId,
      role: 'user',
      content: text,
      is_grounded: true,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setIsSending(true);
    setErrorMessage(null);

    try {
      const res = await assistantApi.sendMessage(targetConvId, text);
      const assistantMsg: AssistantMessage = {
        id: res.id,
        conversation_id: res.conversation_id,
        role: 'assistant',
        content: res.content,
        question_type: res.question_type,
        sources_json: res.sources,
        is_grounded: res.is_grounded,
        created_at: res.created_at,
      };
      setMessages((prev) => [...prev, assistantMsg]);
      refreshConversations();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to get grounded response.';
      setErrorMessage(msg);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] bg-slate-950 text-slate-100 rounded-2xl border border-slate-800 shadow-2xl overflow-hidden">
      {/* Top Header: Dataset & Analysis Selection */}
      <div className="px-5 py-3.5 bg-slate-900/90 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shadow-inner">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <span>{t.assistant?.title || 'Dataset-Grounded AI Assistant'}</span>
              <span className="px-2 py-0.5 rounded-full bg-indigo-950 border border-indigo-500/30 text-indigo-400 text-[10px] uppercase font-mono font-semibold tracking-wider">
                Phase 6 Verified
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              {t.assistant?.subtitle || 'Reasoning strictly grounded in authoritative CFAP analytics'}
            </p>
          </div>
        </div>

        {/* Dataset Selector Dropdown */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <select
              value={selectedDatasetId || ''}
              onChange={(e) => setSelectedDatasetId(Number(e.target.value))}
              disabled={isLoadingMetadata || datasets.length === 0}
              className="appearance-none bg-slate-900 border border-slate-700 hover:border-slate-600 rounded-xl px-4 py-2 pr-9 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer shadow-sm disabled:opacity-50"
            >
              {datasets.length === 0 ? (
                <option value="">No datasets available</option>
              ) : (
                datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.row_count} rows)
                  </option>
                ))
              )}
            </select>
            <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {selectedAnalysis ? (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 text-xs font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Analysis #{selectedAnalysis.id} (Ready)</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-950/60 border border-amber-500/30 text-amber-300 text-xs font-medium">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>No completed analysis</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Content: Sidebar + Chat Timeline */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar: Conversations */}
        <ConversationList
          conversations={conversations}
          selectedId={activeConversationId}
          onSelect={(id) => setActiveConversationId(id)}
          onNewChat={handleNewChat}
          onDelete={handleDeleteConversation}
          isLoading={isLoadingConversations}
        />

        {/* Right Area: Messages + Input */}
        <div className="flex-1 flex flex-col h-full bg-slate-950 relative overflow-hidden">
          {!selectedAnalysis ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-400">
              <Database className="w-12 h-12 text-slate-600 mb-3" />
              <h3 className="text-base font-semibold text-slate-200">
                {t.assistant?.noAnalysisFound || 'No Completed Analysis Found'}
              </h3>
              <p className="text-xs text-slate-400 max-w-sm mt-1">
                {t.assistant?.noAnalysisDesc ||
                  'Please select a dataset that has a completed Phase 4/5 analysis to chat with the AI assistant.'}
              </p>
            </div>
          ) : (
            <>
              {/* Message List */}
              <MessageList
                messages={messages}
                isLoading={isSending}
                error={errorMessage}
              />

              {/* Suggested Questions Section */}
              {messages.length === 0 && suggestedQuestions.length > 0 && (
                <div className="px-5 pb-2">
                  <SuggestedQuestions
                    questions={suggestedQuestions}
                    onSelectQuestion={handleSendMessage}
                    disabled={isSending}
                  />
                </div>
              )}

              {/* Message Input Box */}
              <MessageInput
                onSendMessage={handleSendMessage}
                isLoading={isSending}
                disabled={!selectedAnalysis}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
};
