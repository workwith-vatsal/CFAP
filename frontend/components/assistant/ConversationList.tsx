'use client';

import React from 'react';
import { Plus, MessageSquare, Trash2, Clock } from 'lucide-react';
import { AssistantConversationSummary } from '@/types/assistant';

interface ConversationListProps {
  conversations: AssistantConversationSummary[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  onNewChat: () => void;
  onDelete: (id: number) => void;
  isLoading?: boolean;
}

export const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  selectedId,
  onSelect,
  onNewChat,
  onDelete,
  isLoading = false,
}) => {
  return (
    <div className="w-64 border-r border-slate-800 bg-slate-950/60 flex flex-col h-full shrink-0">
      {/* Sidebar Header */}
      <div className="p-3 border-b border-slate-800 flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Conversations
        </span>
        <button
          type="button"
          onClick={onNewChat}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-600/90 hover:bg-indigo-600 text-white text-xs font-medium transition-colors shadow-sm"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Conversations Scrollable List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {isLoading ? (
          <div className="p-4 text-center text-xs text-slate-400 animate-pulse">
            Loading conversations...
          </div>
        ) : conversations.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-400">
            <MessageSquare className="w-6 h-6 mx-auto mb-2 text-slate-600" />
            No conversations yet. Start a new chat!
          </div>
        ) : (
          conversations.map((c) => {
            const isSelected = c.id === selectedId;
            return (
              <div
                key={c.id}
                onClick={() => onSelect(c.id)}
                className={`group flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-all border text-left ${
                  isSelected
                    ? 'bg-indigo-950/40 border-indigo-500/40 text-indigo-200'
                    : 'bg-slate-900/40 border-slate-800/60 text-slate-300 hover:bg-slate-850 hover:border-slate-700/80'
                }`}
              >
                <div className="flex items-start gap-2.5 min-w-0 flex-1 mr-1">
                  <MessageSquare
                    className={`w-4 h-4 mt-0.5 shrink-0 ${
                      isSelected ? 'text-indigo-400' : 'text-slate-500'
                    }`}
                  />
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-medium truncate leading-tight">
                      {c.title}
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-[10px] text-slate-400">
                      <span className="flex items-center gap-0.5">
                        <Clock className="w-2.5 h-2.5" />
                        {new Date(c.updated_at).toLocaleDateString([], {
                          month: 'short',
                          day: 'numeric',
                        })}
                      </span>
                      <span>• {c.message_count} msgs</span>
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  title="Delete conversation"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm('Delete this conversation?')) {
                      onDelete(c.id);
                    }
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-rose-950/60 text-slate-500 hover:text-rose-400 transition-all shrink-0"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
