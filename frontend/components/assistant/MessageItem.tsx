'use client';

import React, { useState } from 'react';
import { Bot, User as UserIcon, Copy, Check, ShieldCheck, AlertCircle } from 'lucide-react';
import { AssistantMessage } from '@/types/assistant';
import { SafeMarkdown } from './SafeMarkdown';
import { SourceIndicators } from './SourceIndicators';

interface MessageItemProps {
  message: AssistantMessage;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Ignore clipboard error
    }
  };

  const formattedTime = new Date(message.created_at).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  if (isUser) {
    return (
      <div className="flex justify-end gap-3 my-4 group">
        <div className="max-w-2xl bg-indigo-600/90 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-md border border-indigo-500/30">
          <div className="text-sm font-normal leading-relaxed whitespace-pre-wrap">
            {message.content}
          </div>
          <div className="text-[10px] text-indigo-200/80 text-right mt-1">
            {formattedTime}
          </div>
        </div>
        <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center shrink-0 text-indigo-300">
          <UserIcon className="w-4 h-4" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3 my-4 group">
      <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700/80 flex items-center justify-center shrink-0 text-indigo-400 mt-1 shadow-sm">
        <Bot className="w-4 h-4" />
      </div>

      <div className="flex-1 max-w-3xl bg-slate-900/90 rounded-2xl rounded-tl-sm px-5 py-4 shadow-lg border border-slate-800 hover:border-slate-700/80 transition-colors">
        {/* Header bar */}
        <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-200">CFAP Assistant</span>
            {message.question_type && (
              <span className="px-1.5 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/40 text-[10px] uppercase tracking-wider font-mono">
                {message.question_type}
              </span>
            )}
            {message.is_grounded ? (
              <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Grounded</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[11px] text-amber-400">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>Sanitized</span>
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] text-slate-400">{formattedTime}</span>
            <button
              type="button"
              onClick={handleCopy}
              title="Copy answer"
              className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            >
              {copied ? (
                <Check className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        </div>

        {/* Message Content */}
        <SafeMarkdown content={message.content} />

        {/* Grounding Source Badges */}
        <SourceIndicators
          sources={message.sources_json}
          isGrounded={message.is_grounded}
        />
      </div>
    </div>
  );
};
