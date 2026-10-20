'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, CornerDownLeft } from 'lucide-react';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export const MessageInput: React.FC<MessageInputProps> = ({
  onSendMessage,
  isLoading,
  disabled = false,
}) => {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const maxLength = 1000;

  useEffect(() => {
    if (!isLoading && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || isLoading || disabled) return;
    onSendMessage(text.trim());
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    // Auto-grow textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-3 border-t border-slate-800 bg-slate-950/80 backdrop-blur"
    >
      <div className="relative rounded-2xl bg-slate-900 border border-slate-800 focus-within:border-indigo-500/60 focus-within:ring-1 focus-within:ring-indigo-500/40 transition-all p-2 shadow-inner">
        <textarea
          ref={textareaRef}
          rows={1}
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          maxLength={maxLength}
          disabled={isLoading || disabled}
          placeholder={
            disabled
              ? 'Select a dataset and completed analysis to start...'
              : 'Ask a grounded question about this feedback analysis...'
          }
          className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none px-2 py-1 max-h-32"
        />

        <div className="flex items-center justify-between pt-1 px-2 border-t border-slate-800/40 text-[11px] text-slate-400">
          <div className="flex items-center gap-1">
            <CornerDownLeft className="w-3 h-3 text-slate-400" />
            <span>Press Enter to send, Shift+Enter for new line</span>
          </div>

          <div className="flex items-center gap-3">
            <span
              className={`text-[10px] ${
                text.length > maxLength * 0.9 ? 'text-amber-400' : 'text-slate-400'
              }`}
            >
              {text.length}/{maxLength}
            </span>

            <button
              type="submit"
              disabled={!text.trim() || isLoading || disabled}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Send</span>
            </button>
          </div>
        </div>
      </div>
    </form>
  );
};
