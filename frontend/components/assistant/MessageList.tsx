'use client';

import React, { useEffect, useRef } from 'react';
import { Bot, Sparkles, AlertCircle } from 'lucide-react';
import { AssistantMessage } from '@/types/assistant';
import { MessageItem } from './MessageItem';

interface MessageListProps {
  messages: AssistantMessage[];
  isLoading: boolean;
  error?: string | null;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading,
  error,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, error]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-400">
        <div className="w-16 h-16 rounded-2xl bg-indigo-950/40 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4 shadow-inner">
          <Sparkles className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-semibold text-slate-200 mb-2">
          Dataset-Grounded AI Assistant
        </h3>
        <p className="text-sm text-slate-400 max-w-md mb-4 leading-relaxed">
          Ask questions grounded in your selected dataset and completed CFAP analysis.
          Get verified metrics on sentiment distribution, emotion breakdown, topic clusters, and customer feedback.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-2 space-y-2">
      {messages.map((msg) => (
        <MessageItem key={msg.id} message={msg} />
      ))}

      {isLoading && (
        <div className="flex gap-3 my-4">
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700/80 flex items-center justify-center shrink-0 text-indigo-400 mt-1 animate-pulse">
            <Bot className="w-4 h-4" />
          </div>
          <div className="bg-slate-900/90 rounded-2xl rounded-tl-sm px-5 py-3 shadow border border-slate-800 flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-xs text-slate-400 font-medium">
              Retrieving CFAP analytics & reasoning...
            </span>
          </div>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-3 my-2 rounded-xl bg-rose-950/40 border border-rose-800/50 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};
