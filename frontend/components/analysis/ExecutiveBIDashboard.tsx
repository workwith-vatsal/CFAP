'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  HeartPulse,
  Smile,
  Lightbulb,
  Layers,
  Calendar,
  BarChart3,
  Grid,
  CheckCircle2,
  Sparkles,
  Info,
  Bot,
} from 'lucide-react';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Analysis } from '@/types/analysis';
import { Dataset } from '@/types/dataset';
import {
  CategoricalBreakdownData,
  CrossMatricesData,
  DeterministicInsights,
  ExecutiveOverview,
  TemporalTrendsData,
} from '@/types/analytics';
import { analyticsApi } from '@/lib/api/analytics';

interface ExecutiveBIDashboardProps {
  analysis: Analysis;
  dataset: Dataset;
}

type BITab = 'overview' | 'cross_matrices' | 'temporal' | 'categorical';

export const ExecutiveBIDashboard: React.FC<ExecutiveBIDashboardProps> = ({
  analysis,
  dataset,
}) => {
  const [activeTab, setActiveTab] = useState<BITab>('overview');
  const [overview, setOverview] = useState<ExecutiveOverview | null>(null);
  const [insights, setInsights] = useState<DeterministicInsights | null>(null);
  const [crossMatrices, setCrossMatrices] = useState<CrossMatricesData | null>(null);
  const [temporal, setTemporal] = useState<TemporalTrendsData | null>(null);
  const [categorical, setCategorical] = useState<CategoricalBreakdownData | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [temporalInterval, setTemporalInterval] = useState<string>('auto');
  const [selectedCategoryCol, setSelectedCategoryCol] = useState<string>('');

  // Fetch initial BI dataset
  useEffect(() => {
    let isMounted = true;

    const fetchAllBIData = async () => {
      setIsLoading(true);
      try {
        const [ovRes, insRes, cmRes, tempRes, catRes] = await Promise.allSettled([
          analyticsApi.getExecutiveOverview(analysis.id),
          analyticsApi.getDeterministicInsights(analysis.id),
          analyticsApi.getCrossMatrices(analysis.id),
          analyticsApi.getTemporalTrends(analysis.id, temporalInterval),
          analyticsApi.getCategoricalBreakdown(analysis.id),
        ]);

        if (isMounted) {
          if (ovRes.status === 'fulfilled') setOverview(ovRes.value);
          if (insRes.status === 'fulfilled') setInsights(insRes.value);
          if (cmRes.status === 'fulfilled') setCrossMatrices(cmRes.value);
          if (tempRes.status === 'fulfilled') setTemporal(tempRes.value);
          if (catRes.status === 'fulfilled') {
            setCategorical(catRes.value);
            if (catRes.value.active_column) {
              setSelectedCategoryCol(catRes.value.active_column);
            }
          }
        }
      } catch (err) {
        console.error('Failed to load executive BI data', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchAllBIData();

    return () => {
      isMounted = false;
    };
  }, [analysis.id, temporalInterval]);

  // Handle temporal interval change
  const handleTemporalIntervalChange = async (interval: string) => {
    setTemporalInterval(interval);
    try {
      const res = await analyticsApi.getTemporalTrends(analysis.id, interval);
      setTemporal(res);
    } catch (err) {
      console.error('Failed to update temporal interval', err);
    }
  };

  // Handle category column change
  const handleCategoryColChange = async (col: string) => {
    setSelectedCategoryCol(col);
    try {
      const res = await analyticsApi.getCategoricalBreakdown(analysis.id, col);
      setCategorical(res);
    } catch (err) {
      console.error('Failed to update categorical dimension', err);
    }
  };

  if (isLoading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center gap-3">
        <LoadingSpinner size="lg" className="text-indigo-600" />
        <p className="text-sm text-slate-500 font-medium">
          Aggregating Executive Business Intelligence...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Sub-navigation Tabs & Dataset Context */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2 p-1.5 bg-slate-100 dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-800 w-fit">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'overview'
                ? 'bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Activity className="w-4 h-4" />
            Executive Overview & Insights
          </button>

          <button
            onClick={() => setActiveTab('cross_matrices')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'cross_matrices'
                ? 'bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Grid className="w-4 h-4" />
            Cross-Dimensional Matrices
          </button>

          <button
            onClick={() => setActiveTab('temporal')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'temporal'
                ? 'bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Calendar className="w-4 h-4" />
            Temporal Trends
          </button>

          <button
            onClick={() => setActiveTab('categorical')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'categorical'
                ? 'bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            Categorical Dimensions
          </button>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <div className="text-xs text-slate-500 dark:text-slate-400 font-mono px-3 py-1.5 bg-slate-100 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-800">
            Source: <span className="font-semibold text-slate-700 dark:text-slate-200">{dataset.name}</span> &bull; {analysis.usable_feedback_rows} records
          </div>
          <Link
            href={`/dashboard/assistant?datasetId=${dataset.id}&analysisId=${analysis.id}`}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow transition-colors"
          >
            <Bot className="w-3.5 h-3.5" />
            <span>Ask AI Assistant</span>
          </Link>
        </div>
      </div>

      {/* TAB 1: EXECUTIVE OVERVIEW & STRATEGIC INSIGHTS */}
      {activeTab === 'overview' && (
        <div className="space-y-8">
          {/* Top KPI Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* Net Sentiment Score (NSS) */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Net Sentiment Score
                </span>
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center ${
                    (overview?.net_sentiment_score || 0) >= 0
                      ? 'bg-emerald-500/10 text-emerald-600'
                      : 'bg-rose-500/10 text-rose-600'
                  }`}
                >
                  {(overview?.net_sentiment_score || 0) >= 0 ? (
                    <TrendingUp className="w-4 h-4" />
                  ) : (
                    <TrendingDown className="w-4 h-4" />
                  )}
                </div>
              </div>

              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-3xl font-black text-slate-900 dark:text-white font-mono">
                  {(overview?.net_sentiment_score || 0) > 0 ? '+' : ''}
                  {overview?.net_sentiment_score || 0}
                </span>
                <span className="text-xs text-slate-500">NSS (-100 to +100)</span>
              </div>

              <div className="mt-4 flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400">
                <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                  {overview?.sentiment_distribution.positive.percentage}% Pos
                </span>
                &bull;
                <span className="font-semibold text-slate-500">
                  {overview?.sentiment_distribution.neutral.percentage}% Neu
                </span>
                &bull;
                <span className="font-semibold text-rose-600 dark:text-rose-400">
                  {overview?.sentiment_distribution.negative.percentage}% Neg
                </span>
              </div>
            </div>

            {/* Customer Health Score */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Sentiment Health Index
                </span>
                <div className="w-8 h-8 rounded-xl bg-indigo-500/10 text-indigo-600 flex items-center justify-center">
                  <HeartPulse className="w-4 h-4" />
                </div>
              </div>

              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-3xl font-black text-slate-900 dark:text-white font-mono">
                  {insights?.health_score || 50}
                </span>
                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
                  {insights?.health_status || 'Moderate'}
                </span>
              </div>

              <div className="mt-4 w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-indigo-600 h-full rounded-full transition-all duration-500"
                  style={{ width: `${insights?.health_score || 50}%` }}
                />
              </div>
            </div>

            {/* Dominant Emotional State */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Leading Emotion
                </span>
                <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-600 flex items-center justify-center">
                  <Smile className="w-4 h-4" />
                </div>
              </div>

              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-900 dark:text-white capitalize">
                  {overview?.top_emotions[0]?.emotion || 'Neutral'}
                </span>
                <span className="text-xs text-slate-500 font-mono">
                  {overview?.top_emotions[0]?.percentage || 0}%
                </span>
              </div>

              <p className="mt-4 text-xs text-slate-500 truncate">
                {overview?.top_emotions.length || 0} emotional dimensions mapped
              </p>
            </div>

            {/* Total Analyzed & Usability */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Usable Feedback Analyzed
                </span>
                <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
              </div>

              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-3xl font-black text-slate-900 dark:text-white font-mono">
                  {overview?.usable_feedback || 0}
                </span>
                <span className="text-xs text-slate-500 font-mono">
                  / {overview?.total_feedback || 0} total
                </span>
              </div>

              <p className="mt-4 text-xs text-slate-500 font-mono">
                Avg Confidence: {Math.round((overview?.average_confidence || 0) * 100)}%
              </p>
            </div>
          </div>

          {/* Executive Summary Banner */}
          {insights?.summary && (
            <div className="p-6 rounded-3xl bg-gradient-to-r from-indigo-500/10 via-purple-500/5 to-transparent border border-indigo-200/50 dark:border-indigo-900/40">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-2xl bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-md">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div className="space-y-1">
                  <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                    Executive Intelligence Summary
                  </h3>
                  <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed max-w-4xl">
                    {insights.summary}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Deterministic Mathematical Insights & Strategic Recommendations */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Deterministic Insights Cards */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm space-y-4">
              <h3 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
                <Lightbulb className="w-4 h-4 text-amber-500" />
                Grounded Strategic Findings (Zero Hallucinations)
              </h3>

              <div className="space-y-3">
                {insights?.insights.map((ins) => {
                  let borderColor = 'border-slate-200 dark:border-slate-800';
                  let badgeBg = 'bg-slate-500/10 text-slate-600';
                  if (ins.severity === 'positive') {
                    borderColor = 'border-emerald-200 dark:border-emerald-900/50';
                    badgeBg = 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400';
                  } else if (ins.severity === 'critical') {
                    borderColor = 'border-rose-200 dark:border-rose-900/50';
                    badgeBg = 'bg-rose-500/10 text-rose-600 dark:text-rose-400';
                  } else if (ins.severity === 'warning') {
                    borderColor = 'border-amber-200 dark:border-amber-900/50';
                    badgeBg = 'bg-amber-500/10 text-amber-600 dark:text-amber-400';
                  }

                  return (
                    <div
                      key={ins.id}
                      className={`p-4 rounded-2xl bg-slate-50/50 dark:bg-slate-800/30 border ${borderColor} space-y-2`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-slate-900 dark:text-white">
                          {ins.title}
                        </span>
                        {ins.metric_value && (
                          <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded-md ${badgeBg}`}>
                            {ins.metric_value}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                        {ins.description}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Actionable Recommendations */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm space-y-4">
              <h3 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                Actionable Strategic Recommendations
              </h3>

              <div className="space-y-3">
                {insights?.recommendations.map((rec) => (
                  <div
                    key={rec.id}
                    className="p-4 rounded-2xl bg-slate-50/50 dark:bg-slate-800/30 border border-slate-200 dark:border-slate-800 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-slate-900 dark:text-white">
                        {rec.title}
                      </span>
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                          rec.priority === 'High'
                            ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                            : 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400'
                        }`}
                      >
                        {rec.priority} Priority
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                      {rec.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: CROSS-DIMENSIONAL MATRICES */}
      {activeTab === 'cross_matrices' && crossMatrices && (
        <div className="space-y-8">
          {/* Sentiment × Emotion Heatmap Matrix */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm space-y-4">
            <div>
              <h3 className="font-bold text-base text-slate-900 dark:text-white flex items-center gap-2">
                <Grid className="w-5 h-5 text-indigo-600" />
                Sentiment × Emotion Cross-Matrix
              </h3>
              <p className="text-xs text-slate-500">
                Intersection distribution of customer emotional tone across Positive, Neutral, and Negative sentiments.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500">
                    <th className="py-3 px-4 uppercase font-bold">Sentiment</th>
                    {crossMatrices.sentiment_emotion.columns.map((col) => (
                      <th key={col} className="py-3 px-3 uppercase font-bold text-center capitalize">
                        {col}
                      </th>
                    ))}
                    <th className="py-3 px-4 uppercase font-bold text-right">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono">
                  {crossMatrices.sentiment_emotion.rows.map((row) => (
                    <tr key={row.sentiment} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-sans font-bold capitalize text-slate-900 dark:text-white">
                        <span
                          className={`inline-block w-2.5 h-2.5 rounded-full mr-2 ${
                            row.sentiment === 'positive'
                              ? 'bg-emerald-500'
                              : row.sentiment === 'negative'
                              ? 'bg-rose-500'
                              : 'bg-slate-500'
                          }`}
                        />
                        {row.sentiment}
                      </td>
                      {crossMatrices.sentiment_emotion.columns.map((col) => {
                        const cell = row.emotions[col] || { count: 0, percentage: 0 };
                        const intensity = cell.percentage > 0 ? Math.min(1, cell.percentage / 30) : 0;
                        return (
                          <td key={col} className="py-3 px-3 text-center">
                            <div
                              className="py-1 px-2 rounded-lg text-center"
                              style={{
                                backgroundColor:
                                  cell.count > 0
                                    ? row.sentiment === 'positive'
                                      ? `rgba(16, 185, 129, ${0.1 + intensity * 0.4})`
                                      : row.sentiment === 'negative'
                                      ? `rgba(244, 63, 94, ${0.1 + intensity * 0.4})`
                                      : `rgba(100, 116, 139, ${0.1 + intensity * 0.4})`
                                    : 'transparent',
                              }}
                            >
                              <span className="font-bold text-slate-900 dark:text-white">{cell.count}</span>
                              <span className="text-[10px] text-slate-500 block">({cell.percentage}%)</span>
                            </div>
                          </td>
                        );
                      })}
                      <td className="py-3 px-4 text-right font-bold text-slate-900 dark:text-white">
                        {row.total}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Sentiment × Topic Breakdown Table */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm space-y-4">
            <div>
              <h3 className="font-bold text-base text-slate-900 dark:text-white flex items-center gap-2">
                <Layers className="w-5 h-5 text-indigo-600" />
                Sentiment × Topic Cross-Matrix & Net Sentiment
              </h3>
              <p className="text-xs text-slate-500">
                Detailed satisfaction breakdown and Net Sentiment Score (NSS) evaluated per topic cluster.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500">
                    <th className="py-3 px-4 uppercase font-bold">Topic Cluster</th>
                    <th className="py-3 px-4 uppercase font-bold text-center">Volume</th>
                    <th className="py-3 px-4 uppercase font-bold text-center text-emerald-600">Positive</th>
                    <th className="py-3 px-4 uppercase font-bold text-center text-slate-500">Neutral</th>
                    <th className="py-3 px-4 uppercase font-bold text-center text-rose-600">Negative</th>
                    <th className="py-3 px-4 uppercase font-bold text-right">Net Sentiment</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono">
                  {crossMatrices.sentiment_topic.topics.map((t) => (
                    <tr key={t.topic_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-sans font-semibold text-slate-900 dark:text-white max-w-xs truncate">
                        {t.topic_label}
                      </td>
                      <td className="py-3 px-4 text-center font-bold text-slate-700 dark:text-slate-300">
                        {t.total_count}
                      </td>
                      <td className="py-3 px-4 text-center text-emerald-600 dark:text-emerald-400">
                        {t.positive_count} ({t.positive_percentage}%)
                      </td>
                      <td className="py-3 px-4 text-center text-slate-500">
                        {t.neutral_count} ({t.neutral_percentage}%)
                      </td>
                      <td className="py-3 px-4 text-center text-rose-600 dark:text-rose-400">
                        {t.negative_count} ({t.negative_percentage}%)
                      </td>
                      <td className="py-3 px-4 text-right font-bold">
                        <span
                          className={`px-2 py-0.5 rounded-md ${
                            t.net_sentiment_score > 0
                              ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                              : t.net_sentiment_score < 0
                              ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                              : 'bg-slate-500/10 text-slate-600'
                          }`}
                        >
                          {t.net_sentiment_score > 0 ? '+' : ''}
                          {t.net_sentiment_score}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: DYNAMIC TEMPORAL SENTIMENT TRENDS */}
      {activeTab === 'temporal' && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="font-bold text-base text-slate-900 dark:text-white flex items-center gap-2">
                <Calendar className="w-5 h-5 text-indigo-600" />
                Time-Series Sentiment Trajectory
              </h3>
              <p className="text-xs text-slate-500">
                Historical sentiment trajectory aggregated securely across timestamps.
              </p>
            </div>

            {temporal?.available && (
              <div className="flex items-center gap-1.5 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl">
                {['auto', 'day', 'week', 'month'].map((iv) => (
                  <button
                    key={iv}
                    onClick={() => handleTemporalIntervalChange(iv)}
                    className={`px-3 py-1 rounded-lg text-xs font-bold capitalize transition-all ${
                      temporalInterval === iv
                        ? 'bg-white dark:bg-slate-900 text-indigo-600 shadow-sm'
                        : 'text-slate-500 hover:text-slate-900'
                    }`}
                  >
                    {iv}
                  </button>
                ))}
              </div>
            )}
          </div>

          {!temporal?.available ? (
            <div className="p-8 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-center space-y-2">
              <Info className="w-8 h-8 text-slate-400 mx-auto" />
              <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200">
                Temporal Analytics Unavailable
              </h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                {temporal?.reason || 'No valid date or timestamp column detected in source dataset.'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Timeline Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {temporal.timeline.map((point) => (
                  <div
                    key={point.period}
                    className="p-4 rounded-2xl bg-slate-50/50 dark:bg-slate-800/30 border border-slate-200 dark:border-slate-800 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-slate-900 dark:text-white">
                        {point.period}
                      </span>
                      <span
                        className={`text-xs font-mono font-bold px-1.5 py-0.5 rounded ${
                          point.net_sentiment_score >= 0
                            ? 'bg-emerald-500/10 text-emerald-600'
                            : 'bg-rose-500/10 text-rose-600'
                        }`}
                      >
                        {point.net_sentiment_score > 0 ? '+' : ''}
                        {point.net_sentiment_score} NSS
                      </span>
                    </div>

                    <div className="space-y-1 text-xs text-slate-500">
                      <div className="flex justify-between">
                        <span>Volume:</span>
                        <span className="font-mono font-bold text-slate-700 dark:text-slate-300">
                          {point.total_count}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Leading Emotion:</span>
                        <span className="font-semibold capitalize text-indigo-600 dark:text-indigo-400">
                          {point.dominant_emotion}
                        </span>
                      </div>
                    </div>

                    {/* Proportional Sentiment Bar */}
                    <div className="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full flex overflow-hidden">
                      <div
                        className="bg-emerald-500 h-full"
                        style={{ width: `${(point.positive_count / point.total_count) * 100}%` }}
                      />
                      <div
                        className="bg-slate-400 h-full"
                        style={{ width: `${(point.neutral_count / point.total_count) * 100}%` }}
                      />
                      <div
                        className="bg-rose-500 h-full"
                        style={{ width: `${(point.negative_count / point.total_count) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: CATEGORICAL DIMENSION BREAKDOWNS */}
      {activeTab === 'categorical' && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="font-bold text-base text-slate-900 dark:text-white flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-indigo-600" />
                Categorical Segment Performance
              </h3>
              <p className="text-xs text-slate-500">
                Segment performance evaluated across metadata dimensions (Channel, Tier, Region).
              </p>
            </div>

            {categorical?.available && categorical.categorical_columns.length > 1 && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500 font-medium">Dimension:</span>
                <select
                  value={selectedCategoryCol}
                  onChange={(e) => handleCategoryColChange(e.target.value)}
                  className="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-bold text-slate-800 dark:text-white"
                >
                  {categorical.categorical_columns.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {!categorical?.available ? (
            <div className="p-8 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-center space-y-2">
              <Info className="w-8 h-8 text-slate-400 mx-auto" />
              <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200">
                Categorical Dimensions Unavailable
              </h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                {categorical?.reason || 'No categorical dimension columns detected in source dataset.'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {categorical.breakdown.map((item) => (
                <div
                  key={item.category_value}
                  className="p-5 rounded-2xl bg-slate-50/50 dark:bg-slate-800/30 border border-slate-200 dark:border-slate-800 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-900 dark:text-white truncate max-w-[160px]">
                      {item.category_value}
                    </span>
                    <span
                      className={`text-xs font-mono font-bold px-2 py-0.5 rounded-md ${
                        item.net_sentiment_score >= 0
                          ? 'bg-emerald-500/10 text-emerald-600'
                          : 'bg-rose-500/10 text-rose-600'
                      }`}
                    >
                      {item.net_sentiment_score > 0 ? '+' : ''}
                      {item.net_sentiment_score} NSS
                    </span>
                  </div>

                  <div className="space-y-1.5 text-xs text-slate-500">
                    <div className="flex justify-between">
                      <span>Volume:</span>
                      <span className="font-mono font-bold text-slate-700 dark:text-slate-300">
                        {item.total_count} items
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Leading Emotion:</span>
                      <span className="font-semibold capitalize text-indigo-600 dark:text-indigo-400">
                        {item.dominant_emotion}
                      </span>
                    </div>
                  </div>

                  {/* Proportional Segment Bar */}
                  <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full flex overflow-hidden">
                    <div
                      className="bg-emerald-500 h-full"
                      style={{ width: `${item.positive_percentage}%` }}
                      title={`Positive: ${item.positive_percentage}%`}
                    />
                    <div
                      className="bg-slate-400 h-full"
                      style={{ width: `${item.neutral_percentage}%` }}
                      title={`Neutral: ${item.neutral_percentage}%`}
                    />
                    <div
                      className="bg-rose-500 h-full"
                      style={{ width: `${item.negative_percentage}%` }}
                      title={`Negative: ${item.negative_percentage}%`}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
