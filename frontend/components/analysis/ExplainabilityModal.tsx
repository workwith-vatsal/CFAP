'use client';

import React, { useEffect, useState } from 'react';
import {
  X,
  Sparkles,
  Zap,
  Info,
  TrendingUp,
  TrendingDown,
  Star,
  Cpu,
  ShieldCheck,
  Layers,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { FeedbackResultItem } from '@/types/analysis';
import { ExplainabilityData, TokenContribution } from '@/types/analytics';
import { analyticsApi } from '@/lib/api/analytics';

interface ExplainabilityModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysisId: number;
  feedbackResult: FeedbackResultItem | null;
}

export const ExplainabilityModal: React.FC<ExplainabilityModalProps> = ({
  isOpen,
  onClose,
  analysisId,
  feedbackResult,
}) => {
  const [data, setData] = useState<ExplainabilityData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredToken, setHoveredToken] = useState<TokenContribution | null>(null);

  useEffect(() => {
    if (!isOpen || !feedbackResult) return;

    let isMounted = true;
    const fetchExplanation = async () => {
      setIsLoading(true);
      setError(null);
      setData(null);
      try {
        const res = await analyticsApi.getExplainability(
          analysisId,
          feedbackResult.id
        );
        if (isMounted) {
          setData(res);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg =
            err instanceof Error
              ? err.message
              : 'Failed to compute SHAP explanation.';
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchExplanation();

    return () => {
      isMounted = false;
    };
  }, [isOpen, feedbackResult, analysisId]);

  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !feedbackResult) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto overflow-x-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                SHAP Feature Attribution
                {data?.is_cached && (
                  <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                    <Zap className="w-3 h-3" /> Cached
                  </span>
                )}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                Feedback Row #{feedbackResult.row_index + 1} &bull; ID: {feedbackResult.id}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 flex-1">
          {isLoading ? (
            <div className="py-16 flex flex-col items-center justify-center gap-4 text-center">
              <LoadingSpinner size="lg" className="text-indigo-600" />
              <div className="space-y-1">
                <p className="font-semibold text-sm text-slate-900 dark:text-white">
                  Computing SHAP Token Attributions...
                </p>
                <p className="text-xs text-slate-500 max-w-sm">
                  Evaluating feature contributions through the BERT sequence classification pipeline.
                </p>
              </div>
            </div>
          ) : error ? (
            <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-sm space-y-2">
              <div className="font-bold flex items-center gap-2">
                <Info className="w-4 h-4" />
                Explanation Error
              </div>
              <p className="text-xs">{error}</p>
              <Button onClick={() => onClose()} variant="outline" size="sm" className="mt-2">
                Close
              </Button>
            </div>
          ) : data ? (
            <>
              {/* Architecture & Prediction Banner */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 text-xs">
                <div>
                  <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Raw Model Output</span>
                  <div className="flex items-center gap-1 font-bold text-slate-900 dark:text-white mt-0.5">
                    <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                    {data.raw_predicted_label || 'N/A'}
                  </div>
                </div>

                <div>
                  <span className="text-slate-500 dark:text-slate-400 block text-[11px]">CFAP Sentiment</span>
                  <div className="flex items-center gap-1.5 font-bold mt-0.5">
                    <span
                      className={`inline-block w-2 h-2 rounded-full ${
                        data.predicted_label === 'Positive'
                          ? 'bg-emerald-500'
                          : data.predicted_label === 'Negative'
                          ? 'bg-rose-500'
                          : 'bg-slate-500'
                      }`}
                    />
                    <span
                      className={
                        data.predicted_label === 'Positive'
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : data.predicted_label === 'Negative'
                          ? 'text-rose-600 dark:text-rose-400'
                          : 'text-slate-700 dark:text-slate-300'
                      }
                    >
                      {data.predicted_label}
                    </span>
                  </div>
                </div>

                <div>
                  <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Confidence</span>
                  <div className="font-mono font-bold text-slate-900 dark:text-white mt-0.5">
                    {Math.round(data.confidence * 100)}%
                  </div>
                </div>

                <div>
                  <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Base Expected Value</span>
                  <div className="font-mono font-bold text-slate-900 dark:text-white mt-0.5">
                    {data.base_value.toFixed(4)}
                  </div>
                </div>
              </div>

              {/* Model Transparency Box */}
              <div className="p-3.5 rounded-xl bg-indigo-50/50 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/50 text-[11px] text-indigo-900 dark:text-indigo-300 flex items-start gap-2.5">
                <ShieldCheck className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <span className="font-semibold">Deterministic 5-Star to 3-Class Mapping</span>
                  <p className="text-indigo-700 dark:text-indigo-400">
                    {data.sentiment_mapping.explanation_basis} (Rule: {data.sentiment_mapping.mapping_rule})
                  </p>
                </div>
              </div>

              {/* Token Attribution Interactive Flow */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                    <Layers className="w-4 h-4 text-indigo-500" />
                    Token Feature Attribution Stream
                  </span>
                  <div className="flex items-center gap-3 text-[11px]">
                    <span className="flex items-center gap-1">
                      <span className="w-2.5 h-2.5 rounded bg-emerald-500/30 border border-emerald-500/50" />
                      Positive Influence
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2.5 h-2.5 rounded bg-rose-500/30 border border-rose-500/50" />
                      Negative / Counter
                    </span>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 font-sans text-sm leading-relaxed flex flex-wrap gap-1 items-center min-h-[100px]">
                  {data.token_contributions.map((tc, idx) => {
                    const isPos = tc.shap_value > 0;
                    const isNeg = tc.shap_value < 0;

                    let bgStyle = 'bg-transparent text-slate-700 dark:text-slate-300';
                    if (isPos) {
                      bgStyle = `bg-emerald-500/20 text-emerald-900 dark:text-emerald-200 border-b-2 border-emerald-500 font-medium`;
                    } else if (isNeg) {
                      bgStyle = `bg-rose-500/20 text-rose-900 dark:text-rose-200 border-b-2 border-rose-500 font-medium`;
                    }

                    return (
                      <span
                        key={`${tc.position}-${idx}`}
                        onMouseEnter={() => setHoveredToken(tc)}
                        onMouseLeave={() => setHoveredToken(null)}
                        className={`px-1.5 py-0.5 rounded transition-all cursor-pointer hover:scale-105 hover:shadow-sm ${bgStyle}`}
                        title={`Token: "${tc.token}" | SHAP: ${tc.shap_value > 0 ? '+' : ''}${tc.shap_value.toFixed(4)}`}
                      >
                        {tc.token}
                      </span>
                    );
                  })}
                </div>

                {/* Hovered Token Inspector Bar */}
                {hoveredToken && (
                  <div className="p-2.5 rounded-xl bg-slate-900 text-white text-xs flex items-center justify-between animate-in fade-in duration-150">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-indigo-400">
                        &ldquo;{hoveredToken.token}&rdquo;
                      </span>
                      <span className="text-slate-400">Position #{hoveredToken.position}</span>
                    </div>
                    <div className="flex items-center gap-3 font-mono">
                      <span
                        className={
                          hoveredToken.shap_value > 0
                            ? 'text-emerald-400'
                            : hoveredToken.shap_value < 0
                            ? 'text-rose-400'
                            : 'text-slate-400'
                        }
                      >
                        SHAP: {hoveredToken.shap_value > 0 ? '+' : ''}
                        {hoveredToken.shap_value.toFixed(4)}
                      </span>
                      <span className="text-slate-400">
                        Impact: {hoveredToken.importance.toFixed(4)}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Top Positive vs Top Negative Drivers */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                {/* Positive Contributors */}
                <div className="p-4 rounded-2xl bg-emerald-50/40 dark:bg-emerald-950/20 border border-emerald-200/50 dark:border-emerald-900/50 space-y-3">
                  <h4 className="text-xs font-bold text-emerald-800 dark:text-emerald-300 flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                    Top Positive Tokens
                  </h4>
                  {data.positive_tokens.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No positive token weights</p>
                  ) : (
                    <div className="space-y-2">
                      {data.positive_tokens.map((pt, i) => (
                        <div key={i} className="flex items-center justify-between text-xs">
                          <span className="font-mono text-emerald-900 dark:text-emerald-200 truncate max-w-[120px]">
                            &ldquo;{pt.token.trim()}&rdquo;
                          </span>
                          <div className="flex items-center gap-2">
                            <div className="w-20 bg-emerald-200/60 dark:bg-emerald-900/60 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-emerald-500 h-full rounded-full"
                                style={{ width: `${Math.min(100, pt.shap_value * 200)}%` }}
                              />
                            </div>
                            <span className="font-mono text-[11px] text-emerald-700 dark:text-emerald-400 w-12 text-right">
                              +{pt.shap_value.toFixed(3)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Negative Contributors */}
                <div className="p-4 rounded-2xl bg-rose-50/40 dark:bg-rose-950/20 border border-rose-200/50 dark:border-rose-900/50 space-y-3">
                  <h4 className="text-xs font-bold text-rose-800 dark:text-rose-300 flex items-center gap-1.5">
                    <TrendingDown className="w-3.5 h-3.5 text-rose-600" />
                    Top Counter-Evidence Tokens
                  </h4>
                  {data.negative_tokens.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No counter token weights</p>
                  ) : (
                    <div className="space-y-2">
                      {data.negative_tokens.map((nt, i) => (
                        <div key={i} className="flex items-center justify-between text-xs">
                          <span className="font-mono text-rose-900 dark:text-rose-200 truncate max-w-[120px]">
                            &ldquo;{nt.token.trim()}&rdquo;
                          </span>
                          <div className="flex items-center gap-2">
                            <div className="w-20 bg-rose-200/60 dark:bg-rose-900/60 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-rose-500 h-full rounded-full"
                                style={{ width: `${Math.min(100, Math.abs(nt.shap_value) * 200)}%` }}
                              />
                            </div>
                            <span className="font-mono text-[11px] text-rose-700 dark:text-rose-400 w-12 text-right">
                              {nt.shap_value.toFixed(3)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Explainer Meta Footer */}
              <div className="flex items-center justify-between pt-2 text-[11px] text-slate-400 dark:text-slate-500 border-t border-slate-100 dark:border-slate-800">
                <span className="flex items-center gap-1">
                  <Cpu className="w-3.5 h-3.5" />
                  Model: {data.model_name}
                </span>
                <span>Explainer: {data.explainer_name}</span>
              </div>
            </>
          ) : null}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 flex justify-end">
          <Button onClick={onClose} variant="primary" size="sm">
            Done
          </Button>
        </div>
      </div>
    </div>
  );
};
