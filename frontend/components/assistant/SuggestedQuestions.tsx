import React from 'react';
import { Sparkles, MessageSquare } from 'lucide-react';
import { SuggestedQuestion } from '@/types/assistant';

interface SuggestedQuestionsProps {
  questions: SuggestedQuestion[];
  onSelectQuestion: (question: string) => void;
  disabled?: boolean;
}

export const SuggestedQuestions: React.FC<SuggestedQuestionsProps> = ({
  questions,
  onSelectQuestion,
  disabled = false,
}) => {
  if (!questions || questions.length === 0) return null;

  return (
    <div className="space-y-2 my-3">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-400">
        <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
        <span>Suggested Questions</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {questions.map((q, idx) => (
          <button
            key={idx}
            type="button"
            disabled={disabled}
            onClick={() => onSelectQuestion(q.question)}
            className="text-left text-xs bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-indigo-500/50 text-slate-300 hover:text-indigo-200 px-3 py-2 rounded-xl transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed group flex items-start gap-2"
          >
            <MessageSquare className="w-3.5 h-3.5 text-indigo-400/70 group-hover:text-indigo-300 mt-0.5 shrink-0" />
            <span className="leading-snug">{q.question}</span>
          </button>
        ))}
      </div>
    </div>
  );
};
