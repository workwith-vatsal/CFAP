'use client';

import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  RefreshCw,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Smile,
  Tag,
  Layers,
  Clock,
  ChevronLeft,
  ChevronRight,
  Info,
  SlidersHorizontal,
  FileText,
  BarChart3,
} from 'lucide-react';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import {
  Analysis,
  AnalysisStage,
  AnalysisSummary,
  FeedbackResultItem,
} from '@/types/analysis';
import { Dataset } from '@/types/dataset';
import { analysisApi } from '@/lib/api/analysis';
import { ExecutiveBIDashboard } from '@/components/analysis/ExecutiveBIDashboard';
import { ExplainabilityModal } from '@/components/analysis/ExplainabilityModal';

interface AnalysisDashboardProps {
  dataset: Dataset;
  onAnalysisUpdated?: () => void;
}

const STAGE_LABELS: Record<AnalysisStage, string> = {
  INITIALIZED: 'Initializing Pipeline',
  LOADING: 'Loading Dataset & Feedback Column',
  PREPROCESSING: 'Cleaning & Preprocessing Text',
  SENTIMENT: 'BERT Sentiment Analysis',
  EMOTION: 'DistilRoBERTa Emotion Classification',
  EMBEDDINGS: 'Generating MiniLM Embeddings',
  TOPIC_MODELING: 'BERTopic Topic Discovery',
  AGGREGATION: 'Computing Metrics & Summaries',
  COMPLETED: 'Analysis Complete',
  FAILED: 'Analysis Failed',
};

const EMOTION_COLORS: Record<string, { bg: string; text: string; bar: string }> = {
  joy: { bg: 'bg-emerald-500/10 dark:bg-emerald-500/20', text: 'text-emerald-700 dark:text-emerald-400', bar: 'bg-emerald-500' },
  neutral: { bg: 'bg-slate-500/10 dark:bg-slate-500/20', text: 'text-slate-700 dark:text-slate-400', bar: 'bg-slate-500' },
  surprise: { bg: 'bg-amber-500/10 dark:bg-amber-500/20', text: 'text-amber-700 dark:text-amber-400', bar: 'bg-amber-500' },
  sadness: { bg: 'bg-blue-500/10 dark:bg-blue-500/20', text: 'text-blue-700 dark:text-blue-400', bar: 'bg-blue-500' },
  fear: { bg: 'bg-purple-500/10 dark:bg-purple-500/20', text: 'text-purple-700 dark:text-purple-400', bar: 'bg-purple-500' },
  anger: { bg: 'bg-rose-500/10 dark:bg-rose-500/20', text: 'text-rose-700 dark:text-rose-400', bar: 'bg-rose-500' },
  disgust: { bg: 'bg-orange-500/10 dark:bg-orange-500/20', text: 'text-orange-700 dark:text-orange-400', bar: 'bg-orange-500' },
};

export const AnalysisDashboard: React.FC<AnalysisDashboardProps> = ({
  dataset,
  onAnalysisUpdated,
}) => {
  const { t } = useLanguage();
  const { showToast } = useToast();

  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [history, setHistory] = useState<AnalysisSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isTriggering, setIsTriggering] = useState<boolean>(false);

  // Filter & pagination state for feedback explorer
  const [results, setResults] = useState<FeedbackResultItem[]>([]);
  const [totalResults, setTotalResults] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [selectedSentiment, setSelectedSentiment] = useState<string>('');
  const [selectedEmotion, setSelectedEmotion] = useState<string>('');
  const [selectedTopic, setSelectedTopic] = useState<string>('');
  const [isLoadingResults, setIsLoadingResults] = useState<boolean>(false);

  // Phase 5 State: View switcher & SHAP Explainability modal
  const [viewMode, setViewMode] = useState<'executive' | 'pipeline'>('executive');
  const [selectedRowForExplain, setSelectedRowForExplain] = useState<FeedbackResultItem | null>(null);

  // Fetch Latest Analysis and History
  const fetchAnalysisData = async () => {
    try {
      const [latestRes, historyRes] = await Promise.allSettled([
        analysisApi.getLatestAnalysis(dataset.id),
        analysisApi.getAnalysisHistory(dataset.id),
      ]);

      if (latestRes.status === 'fulfilled') {
        setAnalysis(latestRes.value);
      } else {
        setAnalysis(null);
      }

      if (historyRes.status === 'fulfilled') {
        setHistory(historyRes.value);
      }
    } catch {
      // Handled gracefully
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;

    async function initialLoad() {
      try {
        const [latestRes, historyRes] = await Promise.allSettled([
          analysisApi.getLatestAnalysis(dataset.id),
          analysisApi.getAnalysisHistory(dataset.id),
        ]);

        if (isMounted) {
          if (latestRes.status === 'fulfilled') {
            setAnalysis(latestRes.value);
          } else {
            setAnalysis(null);
          }

          if (historyRes.status === 'fulfilled') {
            setHistory(historyRes.value);
          }
        }
      } catch {
        // Handled gracefully
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    initialLoad();

    return () => {
      isMounted = false;
    };
  }, [dataset.id]);

  // Polling while analysis is active
  useEffect(() => {
    if (!analysis || (analysis.status !== 'QUEUED' && analysis.status !== 'PROCESSING')) {
      return;
    }

    const currentAnalysisId = analysis.id;

    const interval = setInterval(async () => {
      try {
        const updated = await analysisApi.getAnalysisById(currentAnalysisId);
        setAnalysis(updated);
        if (updated.status === 'COMPLETED' || updated.status === 'FAILED') {
          clearInterval(interval);
          if (onAnalysisUpdated) onAnalysisUpdated();
          showToast(
            updated.status === 'COMPLETED'
              ? 'AI Analysis completed successfully!'
              : `Analysis failed: ${updated.error_message || 'Unknown error'}`,
            updated.status === 'COMPLETED' ? 'success' : 'error'
          );
        }
      } catch {
        // Continue polling
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [analysis, onAnalysisUpdated, showToast]);

  // Fetch Results when Analysis is completed or filters change
  useEffect(() => {
    if (!analysis || analysis.status !== 'COMPLETED') return;

    let isMounted = true;

    async function loadResults() {
      if (!analysis) return;
      if (isMounted) setIsLoadingResults(true);
      try {
        const res = await analysisApi.getAnalysisResults(analysis.id, {
          page: currentPage,
          pageSize: 20,
          sentiment: selectedSentiment || undefined,
          emotion: selectedEmotion || undefined,
          topicId: selectedTopic ? Number(selectedTopic) : undefined,
        });
        if (isMounted) {
          setResults(res.items);
          setTotalResults(res.total);
          setTotalPages(res.total_pages);
        }
      } catch {
        if (isMounted) {
          showToast('Failed to load feedback analysis results.', 'error');
        }
      } finally {
        if (isMounted) {
          setIsLoadingResults(false);
        }
      }
    }

    loadResults();

    return () => {
      isMounted = false;
    };
  }, [analysis, currentPage, selectedSentiment, selectedEmotion, selectedTopic, showToast]);

  const handleTriggerAnalysis = async () => {
    setIsTriggering(true);
    try {
      const triggered = await analysisApi.triggerAnalysis(dataset.id);
      setAnalysis(triggered);
      showToast('AI Analysis pipeline started!', 'info');
      if (onAnalysisUpdated) onAnalysisUpdated();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to launch analysis.';
      showToast(msg, 'error');
    } finally {
      setIsTriggering(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <LoadingSpinner size="lg" />
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Loading AI Analysis data...
        </p>
      </div>
    );
  }

  // State: No analysis has been executed yet
  if (!analysis) {
    return (
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-10 text-center shadow-sm">
        <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mx-auto mb-5">
          <Sparkles className="w-8 h-8" />
        </div>
        <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
          {t.analysis.noAnalysisYet}
        </h3>
        <p className="text-slate-600 dark:text-slate-400 max-w-lg mx-auto mb-6 text-sm leading-relaxed">
          {t.analysis.noAnalysisDesc}
        </p>
        <Button
          onClick={handleTriggerAnalysis}
          isLoading={isTriggering}
          variant="primary"
          className="gap-2 shadow-lg shadow-indigo-500/20"
        >
          <Sparkles className="w-4 h-4" />
          {t.analysis.runAnalysis}
        </Button>
      </div>
    );
  }

  const isProcessing = analysis.status === 'QUEUED' || analysis.status === 'PROCESSING';

  return (
    <div className="space-y-8">
      {/* Top Header & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              {t.analysis.tabTitle}
            </h2>
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider ${
                analysis.status === 'COMPLETED'
                  ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                  : analysis.status === 'FAILED'
                  ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20'
                  : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 animate-pulse'
              }`}
            >
              {analysis.status}
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Run ID #{analysis.id} &bull; Started {new Date(analysis.created_at).toLocaleString()}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={fetchAnalysisData}
            variant="outline"
            size="sm"
            className="gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>

          {!isProcessing && (
            <Button
              onClick={handleTriggerAnalysis}
              isLoading={isTriggering}
              variant="primary"
              size="sm"
              className="gap-2 shadow-md shadow-indigo-500/20"
            >
              <Sparkles className="w-4 h-4" />
              {t.analysis.reRun}
            </Button>
          )}
        </div>
      </div>

      {/* Live Pipeline Progress (Active Analysis) */}
      {isProcessing && (
        <div className="bg-gradient-to-br from-indigo-900/10 via-slate-900/5 to-purple-900/10 dark:from-indigo-950/40 dark:to-purple-950/40 border border-indigo-200 dark:border-indigo-800/60 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <LoadingSpinner size="sm" />
              <div>
                <p className="font-semibold text-slate-900 dark:text-white text-sm">
                  {STAGE_LABELS[analysis.current_stage] || analysis.current_stage}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  AI Models are processing feedback rows...
                </p>
              </div>
            </div>
            <span className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
              {analysis.progress}%
            </span>
          </div>

          <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-3 overflow-hidden">
            <div
              className="bg-gradient-to-r from-indigo-500 to-purple-500 h-3 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${analysis.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Model Architecture & English Limitation Banner */}
      {analysis.status === 'COMPLETED' && (
        <div className="bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 text-xs text-slate-600 dark:text-slate-400 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3 font-mono">
            <span className="flex items-center gap-1.5 font-sans font-semibold text-slate-900 dark:text-slate-200">
              <Layers className="w-4 h-4 text-indigo-500" />
              {t.analysis.modelMetadataTitle}:
            </span>
            <span>
              <strong>Sentiment:</strong> {analysis.sentiment_model || 'nlptown/bert-base-multilingual-uncased-sentiment'} (5★ &rarr; 3-Class)
            </span>
            <span>
              <strong>Emotion:</strong> {analysis.emotion_model || 'j-hartmann/emotion-english-distilroberta-base'} (7-Class)
            </span>
            <span>
              <strong>Embeddings:</strong> {analysis.embedding_model || 'sentence-transformers/all-MiniLM-L6-v2'} (384-dim)
            </span>
            <span>
              <strong>BERTopic:</strong> v{analysis.bertopic_version || '0.16.0'}
            </span>
          </div>

          <div className="flex items-start gap-2 pt-2 border-t border-slate-200 dark:border-slate-800/80 text-amber-700 dark:text-amber-400/90">
            <Info className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{t.analysis.englishEmotionNotice}</span>
          </div>
        </div>
      )}

      {/* Analysis Error View */}
      {analysis.status === 'FAILED' && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-2xl p-6 text-rose-700 dark:text-rose-400">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-base">Analysis Run Failed</h4>
              <p className="text-sm mt-1">{analysis.error_message || 'An unexpected error occurred during processing.'}</p>
            </div>
          </div>
        </div>
      )}

      {/* Completed Analytical Insights */}
      {analysis.status === 'COMPLETED' && analysis.sentiment_summary && (
        <>
          {/* Phase 5 View Switcher: Executive BI vs AI Pipeline Engine */}
          <div className="flex items-center gap-2 p-1.5 bg-slate-100 dark:bg-slate-800/80 rounded-2xl w-fit border border-slate-200 dark:border-slate-700/60 shadow-sm">
            <button
              type="button"
              onClick={() => setViewMode('executive')}
              className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl transition-all ${
                viewMode === 'executive'
                  ? 'bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              {t.analysis.executiveTab}
            </button>
            <button
              type="button"
              onClick={() => setViewMode('pipeline')}
              className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl transition-all ${
                viewMode === 'pipeline'
                  ? 'bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <Sparkles className="w-4 h-4" />
              {t.analysis.pipelineTab}
            </button>
          </div>

          {viewMode === 'executive' ? (
            <ExecutiveBIDashboard analysis={analysis} dataset={dataset} />
          ) : (
            <>
              {/* Summary Metric Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
                {/* Total Analyzed */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
                  <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
                    <span className="text-xs font-medium uppercase tracking-wider">{t.analysis.usableRows}</span>
                    <FileText className="w-4 h-4 text-indigo-500" />
                  </div>
                  <p className="text-3xl font-extrabold text-slate-900 dark:text-white">
                    {analysis.usable_feedback_rows.toLocaleString()}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Out of {analysis.total_feedback_rows} total rows
                  </p>
                </div>

                {/* Net Sentiment Score */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
                  <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
                    <span className="text-xs font-medium uppercase tracking-wider">{t.analysis.netSentiment}</span>
                    {analysis.sentiment_summary.net_sentiment_score >= 0 ? (
                      <TrendingUp className="w-4 h-4 text-emerald-500" />
                    ) : (
                      <TrendingDown className="w-4 h-4 text-rose-500" />
                    )}
                  </div>
                  <div className="flex items-baseline gap-2">
                    <p
                      className={`text-3xl font-extrabold ${
                        analysis.sentiment_summary.net_sentiment_score > 0
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : analysis.sentiment_summary.net_sentiment_score < 0
                          ? 'text-rose-600 dark:text-rose-400'
                          : 'text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      {analysis.sentiment_summary.net_sentiment_score > 0 ? '+' : ''}
                      {analysis.sentiment_summary.net_sentiment_score}
                    </p>
                    <span className="text-xs text-slate-500">/ 100</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Avg Confidence: {(analysis.sentiment_summary.average_confidence * 100).toFixed(1)}%
                  </p>
                </div>

                {/* Dominant Emotion */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
                  <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
                    <span className="text-xs font-medium uppercase tracking-wider">{t.analysis.dominantEmotion}</span>
                    <Smile className="w-4 h-4 text-amber-500" />
                  </div>
                  <p className="text-2xl font-extrabold capitalize text-slate-900 dark:text-white">
                    {analysis.emotion_summary?.dominant_emotion || 'Neutral'}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Confidence: {((analysis.emotion_summary?.average_confidence || 0) * 100).toFixed(1)}%
                  </p>
                </div>

                {/* Discovered Topics */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
                  <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
                    <span className="text-xs font-medium uppercase tracking-wider">{t.analysis.discoveredTopics}</span>
                    <Tag className="w-4 h-4 text-purple-500" />
                  </div>
                  <p className="text-3xl font-extrabold text-slate-900 dark:text-white">
                    {analysis.topic_summary?.total_topics || 0}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Outlier Ratio: {analysis.topic_summary?.outlier_percentage || 0}%
                  </p>
                </div>
              </div>

              {/* Detailed Sentiment & Emotion Breakdown */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Sentiment Visualizer */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
                  <div className="flex items-center justify-between mb-5">
                    <h3 className="font-bold text-base text-slate-900 dark:text-white flex items-center gap-2">
                      <Smile className="w-5 h-5 text-emerald-500" />
                      {t.analysis.sentimentBreakdown}
                    </h3>
                  </div>

                  {/* Stacked Sentiment Ratio Bar */}
                  <div className="w-full h-4 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden flex mb-6">
                    <div
                      className="bg-emerald-500 h-full transition-all duration-500"
                      style={{ width: `${analysis.sentiment_summary.positive_percentage}%` }}
                      title={`Positive: ${analysis.sentiment_summary.positive_percentage}%`}
                    />
                    <div
                      className="bg-slate-400 h-full transition-all duration-500"
                      style={{ width: `${analysis.sentiment_summary.neutral_percentage}%` }}
                      title={`Neutral: ${analysis.sentiment_summary.neutral_percentage}%`}
                    />
                    <div
                      className="bg-rose-500 h-full transition-all duration-500"
                      style={{ width: `${analysis.sentiment_summary.negative_percentage}%` }}
                      title={`Negative: ${analysis.sentiment_summary.negative_percentage}%`}
                    />
                  </div>

                  {/* 3 Classes */}
                  <div className="grid grid-cols-3 gap-3 mb-6">
                    <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
                      <div className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 uppercase">Positive</div>
                      <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                        {analysis.sentiment_summary.positive_percentage}%
                      </div>
                      <div className="text-xs text-slate-500">
                        {analysis.sentiment_summary.positive_count} rows
                      </div>
                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-500/10 border border-slate-500/20 text-center">
                      <div className="text-xs font-semibold text-slate-700 dark:text-slate-400 uppercase">Neutral</div>
                      <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                        {analysis.sentiment_summary.neutral_percentage}%
                      </div>
                      <div className="text-xs text-slate-500">
                        {analysis.sentiment_summary.neutral_count} rows
                      </div>
                    </div>

                    <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-center">
                      <div className="text-xs font-semibold text-rose-700 dark:text-rose-400 uppercase">Negative</div>
                      <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                        {analysis.sentiment_summary.negative_percentage}%
                      </div>
                      <div className="text-xs text-slate-500">
                        {analysis.sentiment_summary.negative_count} rows
                      </div>
                    </div>
                  </div>

                  {/* Star Distribution Breakdown */}
                  {analysis.sentiment_summary.star_distribution && (
                    <div className="space-y-2 pt-4 border-t border-slate-100 dark:border-slate-800">
                      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                        Original Model Rating (1★ – 5★)
                      </p>
                      {['5 stars', '4 stars', '3 stars', '2 stars', '1 star'].map((starKey) => {
                        const count = analysis.sentiment_summary?.star_distribution?.[starKey] || 0;
                        const pct = analysis.usable_feedback_rows > 0
                          ? ((count / analysis.usable_feedback_rows) * 100).toFixed(1)
                          : '0.0';
                        return (
                          <div key={starKey} className="flex items-center gap-3 text-xs">
                            <span className="w-14 font-mono font-medium text-slate-700 dark:text-slate-300">
                              {starKey}
                            </span>
                            <div className="flex-1 bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                              <div
                                className={`h-2 rounded-full ${
                                  starKey.startsWith('4') || starKey.startsWith('5')
                                    ? 'bg-emerald-500'
                                    : starKey.startsWith('3')
                                    ? 'bg-slate-400'
                                    : 'bg-rose-500'
                                }`}
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <span className="w-16 text-right font-mono text-slate-500">
                              {count} ({pct}%)
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Emotion Visualizer */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
                  <div className="flex items-center justify-between mb-5">
                    <h3 className="font-bold text-base text-slate-900 dark:text-white flex items-center gap-2">
                      <Smile className="w-5 h-5 text-purple-500" />
                      {t.analysis.emotionBreakdown}
                    </h3>
                  </div>

                  <div className="space-y-3.5">
                    {Object.entries(analysis.emotion_summary?.emotion_breakdown || {}).map(
                      ([emotionName, details]) => {
                        const colors = EMOTION_COLORS[emotionName.toLowerCase()] || EMOTION_COLORS.neutral;
                        return (
                          <div key={emotionName} className="space-y-1">
                            <div className="flex items-center justify-between text-xs">
                              <span className={`font-semibold capitalize px-2 py-0.5 rounded-md ${colors.bg} ${colors.text}`}>
                                {emotionName}
                              </span>
                              <span className="text-slate-500 font-mono">
                                {details.count} rows ({details.percentage}%) &bull; avg {(details.average_probability * 100).toFixed(1)}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
                              <div
                                className={`${colors.bar} h-2.5 rounded-full transition-all duration-500`}
                                style={{ width: `${details.percentage}%` }}
                              />
                            </div>
                          </div>
                        );
                      }
                    )}
                  </div>
                </div>
              </div>

              {/* Discovered Topic Clusters */}
              {analysis.topic_info && analysis.topic_info.length > 0 && (
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
                  <div className="flex items-center justify-between mb-5">
                    <h3 className="font-bold text-base text-slate-900 dark:text-white flex items-center gap-2">
                      <Tag className="w-5 h-5 text-indigo-500" />
                      {t.analysis.topicClusters}
                    </h3>
                    <span className="text-xs text-slate-500 font-mono">
                      {analysis.topic_summary?.total_topics} topics discovered
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {analysis.topic_info.map((topic) => (
                      <div
                        key={topic.topic_id}
                        className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-3"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 font-mono">
                            {topic.topic_id === -1 ? 'Outliers' : `Theme #${topic.topic_id}`}
                          </span>
                          <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                            {topic.count} items ({topic.percentage}%)
                          </span>
                        </div>

                        <h4 className="text-sm font-semibold text-slate-900 dark:text-white truncate" title={topic.name}>
                          {topic.name}
                        </h4>

                        {topic.keywords && topic.keywords.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {topic.keywords.map((kw, kwIdx) => (
                              <span
                                key={kwIdx}
                                className="px-2 py-0.5 rounded text-[11px] bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border border-indigo-500/20"
                              >
                                {kw.word}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Feedback Row-level Explorer (Privacy-Preserving & SHAP Explainability) */}
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-5">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <h3 className="font-bold text-base text-slate-900 dark:text-white flex items-center gap-2">
                      <SlidersHorizontal className="w-5 h-5 text-indigo-500" />
                      {t.analysis.resultsTable}
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                      Showing {results.length} of {totalResults} analytical predictions &bull; Click Explain (SHAP) for token-level feature attribution
                    </p>
                  </div>

                  {/* Filters */}
                  <div className="flex flex-wrap items-center gap-2">
                    <select
                      value={selectedSentiment}
                      onChange={(e) => {
                        setSelectedSentiment(e.target.value);
                        setCurrentPage(1);
                      }}
                      aria-label="Filter by sentiment"
                      className="px-3 py-1.5 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="">{t.analysis.filterSentiment}</option>
                      <option value="positive">Positive</option>
                      <option value="neutral">Neutral</option>
                      <option value="negative">Negative</option>
                    </select>

                    <select
                      value={selectedEmotion}
                      onChange={(e) => {
                        setSelectedEmotion(e.target.value);
                        setCurrentPage(1);
                      }}
                      aria-label="Filter by dominant emotion"
                      className="px-3 py-1.5 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="">{t.analysis.filterEmotion}</option>
                      {['joy', 'neutral', 'surprise', 'sadness', 'fear', 'anger', 'disgust'].map((emo) => (
                        <option key={emo} value={emo}>
                          {emo.charAt(0).toUpperCase() + emo.slice(1)}
                        </option>
                      ))}
                    </select>

                    {analysis.topic_info && (
                      <select
                        value={selectedTopic}
                        onChange={(e) => {
                          setSelectedTopic(e.target.value);
                          setCurrentPage(1);
                        }}
                        aria-label="Filter by topic theme"
                        className="px-3 py-1.5 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="">{t.analysis.filterTopic}</option>
                        {analysis.topic_info.map((top) => (
                          <option key={topicKey(top.topic_id)} value={top.topic_id.toString()}>
                            {top.name}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>

                {/* Results Table */}
                <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-600 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-slate-800">
                      <tr>
                        <th className="py-3 px-4">{t.analysis.colIndex}</th>
                        <th className="py-3 px-4">{t.analysis.colLength}</th>
                        <th className="py-3 px-4">{t.analysis.colSentiment}</th>
                        <th className="py-3 px-4">{t.analysis.colEmotion}</th>
                        <th className="py-3 px-4">{t.analysis.colTopic}</th>
                        <th className="py-3 px-4 text-right">{t.analysis.colExplain}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {isLoadingResults ? (
                        <tr>
                          <td colSpan={6} className="py-8 text-center text-slate-500">
                            <LoadingSpinner size="sm" />
                          </td>
                        </tr>
                      ) : results.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="py-8 text-center text-slate-500">
                            No feedback rows match the selected filters.
                          </td>
                        </tr>
                      ) : (
                        results.map((row) => {
                          const emoColor = row.emotion_label
                            ? EMOTION_COLORS[row.emotion_label.toLowerCase()] || EMOTION_COLORS.neutral
                            : EMOTION_COLORS.neutral;

                          return (
                            <tr key={row.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                              <td className="py-3 px-4 font-mono text-slate-500">#{row.row_index + 1}</td>
                              <td className="py-3 px-4 font-mono text-slate-500">{row.text_length} chars</td>
                              <td className="py-3 px-4">
                                {row.sentiment_label ? (
                                  <div className="flex items-center gap-2">
                                    <span
                                      className={`px-2 py-0.5 rounded-md font-semibold capitalize ${
                                        row.sentiment_label === 'positive'
                                          ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                                          : row.sentiment_label === 'negative'
                                          ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                                          : 'bg-slate-500/10 text-slate-600 dark:text-slate-400'
                                      }`}
                                    >
                                      {row.sentiment_label}
                                    </span>
                                    <span className="text-[11px] font-mono text-slate-400">
                                      {row.raw_sentiment_label} ({Math.round((row.sentiment_score || 0) * 100)}%)
                                    </span>
                                  </div>
                                ) : (
                                  <span className="text-slate-400">N/A</span>
                                )}
                              </td>
                              <td className="py-3 px-4">
                                {row.emotion_label ? (
                                  <div className="flex items-center gap-2">
                                    <span className={`px-2 py-0.5 rounded-md font-semibold capitalize ${emoColor.bg} ${emoColor.text}`}>
                                      {row.emotion_label}
                                    </span>
                                    <span className="text-[11px] font-mono text-slate-400">
                                      {Math.round((row.emotion_score || 0) * 100)}%
                                    </span>
                                  </div>
                                ) : (
                                  <span className="text-slate-400">N/A</span>
                                )}
                              </td>
                              <td className="py-3 px-4">
                                <span className="text-slate-700 dark:text-slate-300 truncate max-w-xs block" title={row.topic_label || 'Unassigned'}>
                                  {row.topic_label || 'Unassigned'}
                                </span>
                              </td>
                              <td className="py-3 px-4 text-right">
                                <button
                                  type="button"
                                  onClick={() => setSelectedRowForExplain(row)}
                                  className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-lg bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-500/20 border border-indigo-500/20 transition-colors shadow-sm"
                                  title="Explain prediction using SHAP token attribution"
                                >
                                  <Sparkles className="w-3 h-3 text-indigo-500" />
                                  {t.analysis.explainButton}
                                </button>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Pagination Controls */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between pt-3 text-xs text-slate-500">
                    <span>
                      Page {currentPage} of {totalPages}
                    </span>
                    <div className="flex items-center gap-2">
                      <Button
                        onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                        disabled={currentPage <= 1 || isLoadingResults}
                        variant="outline"
                        size="sm"
                      >
                        <ChevronLeft className="w-3.5 h-3.5 mr-1" />
                        Previous
                      </Button>
                      <Button
                        onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                        disabled={currentPage >= totalPages || isLoadingResults}
                        variant="outline"
                        size="sm"
                      >
                        Next
                        <ChevronRight className="w-3.5 h-3.5 ml-1" />
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          {/* Analysis History Section */}
          {history.length > 1 && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <h3 className="font-bold text-base text-slate-900 dark:text-white flex items-center gap-2 mb-4">
                <Clock className="w-5 h-5 text-slate-500" />
                {t.analysis.historyTitle} ({history.length} runs)
              </h3>
              <div className="space-y-2">
                {history.map((hRun) => (
                  <div
                    key={hRun.id}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 text-xs"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono font-bold text-slate-700 dark:text-slate-300">
                        Run #{hRun.id}
                      </span>
                      <span className="text-slate-500">
                        {new Date(hRun.created_at).toLocaleString()}
                      </span>
                      <span className="text-slate-500">
                        {hRun.usable_feedback_rows} rows analyzed
                      </span>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded font-semibold uppercase ${
                        hRun.status === 'COMPLETED'
                          ? 'bg-emerald-500/10 text-emerald-600'
                          : hRun.status === 'FAILED'
                          ? 'bg-rose-500/10 text-rose-600'
                          : 'bg-amber-500/10 text-amber-600'
                      }`}
                    >
                      {hRun.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Phase 5 SHAP Explainability Modal */}
      {selectedRowForExplain && (
        <ExplainabilityModal
          isOpen={!!selectedRowForExplain}
          onClose={() => setSelectedRowForExplain(null)}
          analysisId={analysis.id}
          feedbackResult={selectedRowForExplain}
        />
      )}
    </div>
  );
};

function topicKey(id: number): string {
  return `top_${id}`;
}
