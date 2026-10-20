import React from 'react';
import { Database, BarChart3, Tag, Layers, Sparkles, CheckCircle2 } from 'lucide-react';
import { AssistantSource } from '@/types/assistant';

interface SourceIndicatorsProps {
  sources?: AssistantSource[] | null;
  isGrounded?: boolean;
}

export const SourceIndicators: React.FC<SourceIndicatorsProps> = ({
  sources,
  isGrounded = true,
}) => {
  if (!sources || sources.length === 0) return null;

  const getIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'analytics':
        return <BarChart3 className="w-3 h-3 text-indigo-400" />;
      case 'feedback_samples':
        return <Database className="w-3 h-3 text-cyan-400" />;
      case 'explainability':
        return <Sparkles className="w-3 h-3 text-amber-400" />;
      case 'dataset_metadata':
        return <Layers className="w-3 h-3 text-emerald-400" />;
      default:
        return <Tag className="w-3 h-3 text-slate-400" />;
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-800/60 mt-3 text-xs">
      <span className="text-slate-400 font-medium flex items-center gap-1 mr-1 text-[11px]">
        {isGrounded && (
          <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
        )}
        Grounded in:
      </span>
      {sources.map((src, idx) => (
        <span
          key={idx}
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-800/80 border border-slate-700/60 text-slate-300 text-[11px]"
        >
          {getIcon(src.type)}
          <span>{src.label}</span>
        </span>
      ))}
    </div>
  );
};
