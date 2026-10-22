'use client';

import React, { useEffect, useState } from 'react';
import {
  Scale,
  ShieldCheck,
  Info,
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle,
  AlertCircle,
  BarChart3,
  Layers,
  Sparkles,
} from 'lucide-react';
import { getDatasets } from '@/lib/api/datasets';
import { analysisApi } from '@/lib/api/analysis';
import { benchmarksApi } from '@/lib/api/benchmarks';
import { AnalysisSummary, BenchmarkSummaryResponse, Dataset } from '@/types';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export function BenchmarkView() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<number | null>(null);
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkSummaryResponse | null>(null);

  const [loading, setLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load datasets on mount
  useEffect(() => {
    let isMounted = true;
    async function loadDatasets() {
      try {
        const res = await getDatasets();
        if (isMounted) {
          setDatasets(res.datasets || []);
          if (res.datasets && res.datasets.length > 0) {
            setSelectedDatasetId(res.datasets[0].id);
          }
          setLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to load datasets.');
          setLoading(false);
        }
      }
    }
    loadDatasets();
    return () => {
      isMounted = false;
    };
  }, []);

  // Load completed analyses when dataset changes
  useEffect(() => {
    let isMounted = true;
    async function loadAnalyses() {
      if (!selectedDatasetId) {
        setAnalyses([]);
        setSelectedAnalysisId(null);
        return;
      }
      try {
        const res = await analysisApi.getAnalysisHistory(selectedDatasetId);
        if (isMounted) {
          const completed = (res || []).filter((a) => a.status === 'COMPLETED');
          setAnalyses(completed);
          if (completed.length > 0) {
            setSelectedAnalysisId(completed[0].id);
          } else {
            setSelectedAnalysisId(null);
            setBenchmarkData(null);
          }
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to load analyses.');
        }
      }
    }
    loadAnalyses();
    return () => {
      isMounted = false;
    };
  }, [selectedDatasetId]);

  // Load benchmark summary when analysis changes
  useEffect(() => {
    async function loadBenchmark() {
      if (!selectedAnalysisId) {
        setBenchmarkData(null);
        return;
      }
      try {
        setDataLoading(true);
        setError(null);
        const res = await benchmarksApi.getSummary(selectedAnalysisId);
        setBenchmarkData(res);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load benchmark data.');
        setBenchmarkData(null);
      } finally {
        setDataLoading(false);
      }
    }
    loadBenchmark();
  }, [selectedAnalysisId]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 text-xs font-mono font-medium uppercase tracking-wider mb-1">
            <Scale className="w-4 h-4" />
            <span>Cross-Platform Benchmarking</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Anonymized Analytics Benchmark
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Compare your dataset&apos;s sentiment, emotion, and quality indicators against privacy-preserving platform aggregates.
          </p>
        </div>

        {/* Dataset & Analysis Selector */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex flex-col">
            <label className="text-[10px] text-slate-400 font-medium uppercase tracking-wider mb-1">
              Dataset
            </label>
            <select
              value={selectedDatasetId || ''}
              onChange={(e) => setSelectedDatasetId(Number(e.target.value) || null)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              disabled={loading || datasets.length === 0}
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.row_count} rows)
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col">
            <label className="text-[10px] text-slate-400 font-medium uppercase tracking-wider mb-1">
              Completed Analysis
            </label>
            <select
              value={selectedAnalysisId || ''}
              onChange={(e) => setSelectedAnalysisId(Number(e.target.value) || null)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              disabled={analyses.length === 0}
            >
              {analyses.map((a) => (
                <option key={a.id} value={a.id}>
                  Analysis #{a.id} ({a.usable_feedback_rows} usable)
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-400 flex items-center gap-3">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading state */}
      {dataLoading && (
        <div className="py-20 flex flex-col items-center justify-center text-slate-400">
          <LoadingSpinner size="lg" className="text-indigo-500 mb-3" />
          <p className="text-xs font-mono">Aggregating cross-platform benchmarks...</p>
        </div>
      )}

      {/* Main Content */}
      {!dataLoading && benchmarkData && (
        <div className="space-y-6">
          {/* Privacy & Sample Size Banner */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="p-4 bg-slate-900/60 border-slate-800">
              <div className="flex items-center gap-2 text-indigo-400 mb-1 text-xs font-medium">
                <Layers className="w-4 h-4" />
                <span>Eligible Aggregate Sample</span>
              </div>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-bold font-mono text-white">
                  {benchmarkData.eligible_sample_size}
                </span>
                <span className="text-xs text-slate-400">
                  analyses (min required: {benchmarkData.min_required_sample_size})
                </span>
              </div>
              <div className="mt-2 flex items-center gap-1.5 text-[11px]">
                {benchmarkData.is_eligible ? (
                  <span className="text-emerald-400 flex items-center gap-1">
                    <CheckCircle className="w-3.5 h-3.5" /> Threshold Met (k-Anonymity Verified)
                  </span>
                ) : (
                  <span className="text-amber-400 flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" /> Insufficient Sample Size
                  </span>
                )}
              </div>
            </Card>

            <Card className="p-4 bg-slate-900/60 border-slate-800 md:col-span-2">
              <div className="flex items-center gap-2 text-slate-300 mb-1 text-xs font-medium">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Privacy & Anonymization Guarantee</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed mt-1">
                {benchmarkData.privacy_notice}
              </p>
            </Card>
          </div>

          {/* Ineligible Fallback State */}
          {!benchmarkData.is_eligible && (
            <Card className="p-8 text-center border-amber-500/20 bg-amber-500/5 space-y-3">
              <AlertCircle className="w-8 h-8 text-amber-400 mx-auto" />
              <h3 className="text-sm font-semibold text-slate-200">
                Benchmark Aggregate Unavailable
              </h3>
              <p className="text-xs text-slate-400 max-w-lg mx-auto">
                {benchmarkData.message || 'Benchmark comparison requires a minimum number of completed platform analyses to maintain statistical validity and privacy guarantees.'}
              </p>
            </Card>
          )}

          {/* Eligible Benchmark Comparisons */}
          {benchmarkData.is_eligible && benchmarkData.net_sentiment_score && (
            <>
              {/* Primary Metric Comparisons */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {/* NSS Metric Card */}
                <Card className="p-5 border-slate-800 bg-slate-900/70 relative overflow-hidden">
                  <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider mb-2">
                    Net Sentiment Score (NSS)
                  </div>
                  <div className="flex items-baseline justify-between">
                    <div>
                      <div className="text-xs text-slate-400">Your Dataset</div>
                      <div className="text-2xl font-bold font-mono text-white mt-0.5">
                        {benchmarkData.net_sentiment_score.user_value > 0 ? '+' : ''}
                        {benchmarkData.net_sentiment_score.user_value.toFixed(1)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-slate-400">Platform Median</div>
                      <div className="text-xl font-bold font-mono text-indigo-400 mt-0.5">
                        {benchmarkData.net_sentiment_score.platform_median > 0 ? '+' : ''}
                        {benchmarkData.net_sentiment_score.platform_median.toFixed(1)}
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                    <span className="text-slate-400">Delta vs. Median:</span>
                    <span
                      className={`font-semibold font-mono flex items-center gap-1 ${
                        benchmarkData.net_sentiment_score.difference > 0
                          ? 'text-emerald-400'
                          : benchmarkData.net_sentiment_score.difference < 0
                          ? 'text-rose-400'
                          : 'text-slate-300'
                      }`}
                    >
                      {benchmarkData.net_sentiment_score.difference > 0 ? (
                        <TrendingUp className="w-3.5 h-3.5" />
                      ) : benchmarkData.net_sentiment_score.difference < 0 ? (
                        <TrendingDown className="w-3.5 h-3.5" />
                      ) : (
                        <Minus className="w-3.5 h-3.5" />
                      )}
                      {benchmarkData.net_sentiment_score.difference > 0 ? '+' : ''}
                      {benchmarkData.net_sentiment_score.difference.toFixed(1)} pts
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-2 bg-slate-950/50 p-2 rounded-lg border border-slate-800/60">
                    {benchmarkData.net_sentiment_score.observation}
                  </p>
                </Card>

                {/* Data Quality Metric Card */}
                {benchmarkData.data_quality_score && (
                  <Card className="p-5 border-slate-800 bg-slate-900/70 relative overflow-hidden">
                    <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider mb-2">
                      Data Quality Score
                    </div>
                    <div className="flex items-baseline justify-between">
                      <div>
                        <div className="text-xs text-slate-400">Your Dataset</div>
                        <div className="text-2xl font-bold font-mono text-emerald-400 mt-0.5">
                          {benchmarkData.data_quality_score.user_value.toFixed(1)}%
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-slate-400">Platform Median</div>
                        <div className="text-xl font-bold font-mono text-indigo-400 mt-0.5">
                          {benchmarkData.data_quality_score.platform_median.toFixed(1)}%
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                      <span className="text-slate-400">Delta vs. Median:</span>
                      <span className="font-semibold font-mono text-slate-200">
                        {benchmarkData.data_quality_score.difference > 0 ? '+' : ''}
                        {benchmarkData.data_quality_score.difference.toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-2 bg-slate-950/50 p-2 rounded-lg border border-slate-800/60">
                      {benchmarkData.data_quality_score.observation}
                    </p>
                  </Card>
                )}

                {/* Feedback Volume Metric Card */}
                {benchmarkData.volume_comparison && (
                  <Card className="p-5 border-slate-800 bg-slate-900/70 relative overflow-hidden">
                    <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider mb-2">
                      Feedback Volume Sample
                    </div>
                    <div className="flex items-baseline justify-between">
                      <div>
                        <div className="text-xs text-slate-400">Your Usable Rows</div>
                        <div className="text-2xl font-bold font-mono text-white mt-0.5">
                          {benchmarkData.volume_comparison.user_value.toLocaleString()}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-slate-400">Platform Median</div>
                        <div className="text-xl font-bold font-mono text-indigo-400 mt-0.5">
                          {benchmarkData.volume_comparison.platform_median.toLocaleString()}
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                      <span className="text-slate-400">Platform 25th–75th %ile:</span>
                      <span className="font-mono text-slate-300">
                        {benchmarkData.volume_comparison.platform_p25.toLocaleString()} – {benchmarkData.volume_comparison.platform_p75.toLocaleString()}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-2 bg-slate-950/50 p-2 rounded-lg border border-slate-800/60">
                      {benchmarkData.volume_comparison.observation}
                    </p>
                  </Card>
                )}
              </div>

              {/* Sentiment & Emotion Distribution Comparisons */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Sentiment Distribution Comparison */}
                {benchmarkData.sentiment_distribution && (
                  <Card className="p-5 border-slate-800 bg-slate-900/70 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                        Sentiment Distribution Benchmark
                      </h3>
                      <BarChart3 className="w-4 h-4 text-indigo-400" />
                    </div>

                    <div className="space-y-4 text-xs">
                      {/* Positive */}
                      <div>
                        <div className="flex justify-between text-[11px] text-slate-300 mb-1">
                          <span>Positive Sentiment</span>
                          <span className="font-mono">
                            Your: <strong className="text-emerald-400">{benchmarkData.sentiment_distribution.positive_user_pct}%</strong> | Avg: {benchmarkData.sentiment_distribution.positive_platform_pct}%
                          </span>
                        </div>
                        <div className="h-2 bg-slate-950 rounded-full overflow-hidden flex gap-1">
                          <div
                            className="bg-emerald-500 rounded-full"
                            style={{ width: `${benchmarkData.sentiment_distribution.positive_user_pct}%` }}
                          />
                        </div>
                      </div>

                      {/* Neutral */}
                      <div>
                        <div className="flex justify-between text-[11px] text-slate-300 mb-1">
                          <span>Neutral Sentiment</span>
                          <span className="font-mono">
                            Your: <strong className="text-slate-200">{benchmarkData.sentiment_distribution.neutral_user_pct}%</strong> | Avg: {benchmarkData.sentiment_distribution.neutral_platform_pct}%
                          </span>
                        </div>
                        <div className="h-2 bg-slate-950 rounded-full overflow-hidden flex gap-1">
                          <div
                            className="bg-slate-400 rounded-full"
                            style={{ width: `${benchmarkData.sentiment_distribution.neutral_user_pct}%` }}
                          />
                        </div>
                      </div>

                      {/* Negative */}
                      <div>
                        <div className="flex justify-between text-[11px] text-slate-300 mb-1">
                          <span>Negative Sentiment</span>
                          <span className="font-mono">
                            Your: <strong className="text-rose-400">{benchmarkData.sentiment_distribution.negative_user_pct}%</strong> | Avg: {benchmarkData.sentiment_distribution.negative_platform_pct}%
                          </span>
                        </div>
                        <div className="h-2 bg-slate-950 rounded-full overflow-hidden flex gap-1">
                          <div
                            className="bg-rose-500 rounded-full"
                            style={{ width: `${benchmarkData.sentiment_distribution.negative_user_pct}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </Card>
                )}

                {/* Emotion Distribution Comparison */}
                {benchmarkData.emotion_distribution && (
                  <Card className="p-5 border-slate-800 bg-slate-900/70 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                        Discrete Emotion Spectrum Benchmark
                      </h3>
                      <Sparkles className="w-4 h-4 text-indigo-400" />
                    </div>

                    <div className="space-y-2.5 text-xs">
                      {benchmarkData.emotion_distribution.slice(0, 5).map((item) => (
                        <div key={item.emotion} className="flex items-center justify-between py-1 border-b border-slate-800/60 last:border-0">
                          <span className="text-slate-300 font-medium">{item.emotion}</span>
                          <div className="flex items-center gap-4 text-xs font-mono">
                            <span className="text-slate-400">
                              Your: <strong className="text-white">{item.user_percentage}%</strong>
                            </span>
                            <span className="text-slate-500">
                              Avg: {item.platform_average_percentage}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
              </div>

              {/* Methodology & Non-Causal Disclaimers */}
              <Card className="p-5 border-slate-800/80 bg-slate-950/60 space-y-3">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                  <Info className="w-4 h-4 text-indigo-400" />
                  <span>Benchmark Methodology & Governance Guidelines</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-[11px] text-slate-400 leading-relaxed">
                  <div>
                    <strong className="text-slate-300 block mb-0.5">Inclusion Criteria:</strong>
                    {benchmarkData.methodology.inclusion_criteria}
                  </div>
                  <div>
                    <strong className="text-slate-300 block mb-0.5">Observational Non-Causal Boundary:</strong>
                    {benchmarkData.methodology.non_causal_statement}
                  </div>
                </div>
              </Card>
            </>
          )}
        </div>
      )}
    </div>
  );
}
