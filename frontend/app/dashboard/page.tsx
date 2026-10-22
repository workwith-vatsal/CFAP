'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Upload,
  LineChart,
  FileText,
  Clock,
  ArrowRight,
  Database,
  CheckCircle2,
  Sparkles,
  Brain,
  Bot,
  Scale,
} from 'lucide-react';
import { useAuth } from '@/lib/auth/AuthContext';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { EmptyState } from '@/components/ui/EmptyState';
import { Dataset } from '@/types/dataset';
import { getDatasets } from '@/lib/api/datasets';
import { analysisApi } from '@/lib/api/analysis';

export default function DashboardOverviewPage() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [datasetCount, setDatasetCount] = useState<number>(0);
  const [analysisCount, setAnalysisCount] = useState<number>(0);

  useEffect(() => {
    let isMounted = true;
    (async () => {
      try {
        const res = await getDatasets(false);
        const dsList: Dataset[] = res.datasets || [];
        if (isMounted) {
          setDatasets(dsList);
          setDatasetCount(res.total ?? dsList.length);
        }

        // Calculate total completed analyses across user datasets
        if (dsList.length > 0) {
          const analysesPromises = dsList.slice(0, 10).map(async (d) => {
            try {
              const h = await analysisApi.getAnalysisHistory(d.id);
              return h ? h.length : 0;
            } catch {
              return 0;
            }
          });
          const counts = await Promise.all(analysesPromises);
          const totalAnalyses = counts.reduce((acc, c) => acc + c, 0);
          if (isMounted) {
            setAnalysisCount(totalAnalyses);
          }
        }
      } catch {
        // Fallback gracefully
      }
    })();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Welcome Banner */}
      <div className="p-6 sm:p-8 rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 relative overflow-hidden backdrop-blur-sm shadow-xl">
        <div className="max-w-3xl relative z-10">
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full border border-indigo-500/30 bg-indigo-950/60 text-indigo-300 text-[11px] font-medium mb-3">
            <Sparkles className="w-3 h-3 text-indigo-400" />
            <span>Cognitive Analytics Suite Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-2">
            {t.dashboard.welcome},{' '}
            <span className="text-indigo-400">{user?.first_name || 'Analyst'}</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Your intelligence workspace is ready. Ingest multi-channel customer reviews, discover emerging semantic topics via BERTopic, inspect token attributions with SHAP, and consult with your dataset-grounded AI assistant.
          </p>
        </div>
      </div>

      {/* Real Account Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium text-slate-400">
              {t.dashboard.totalDatasets}
            </span>
            <div className="w-8 h-8 rounded-lg bg-indigo-950/60 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Database className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100">
            {datasetCount}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            {datasetCount === 1 ? '1 active dataset' : `${datasetCount} active datasets`}
          </p>
        </div>

        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium text-slate-400">
              {t.dashboard.totalAnalyses}
            </span>
            <div className="w-8 h-8 rounded-lg bg-cyan-950/60 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <LineChart className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100">
            {analysisCount}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            {analysisCount === 0 ? 'No completed runs yet' : `${analysisCount} pipeline executions`}
          </p>
        </div>

        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium text-slate-400">
              {t.profile.accountStatus}
            </span>
            <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-800/60 flex items-center justify-center text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-sm font-semibold text-emerald-400 capitalize">
            {user?.is_verified ? t.profile.verified : 'Unverified'}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1.5">
            Role: <span className="font-mono text-indigo-300 font-semibold uppercase">{user?.role || 'USER'}</span>
          </p>
        </div>
      </div>

      {/* Quick Action Navigation Grid */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold tracking-wide text-slate-200 uppercase">
          {t.dashboard.quickActions}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            href="/dashboard/datasets"
            className="group p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900/90 transition-all flex flex-col justify-between backdrop-blur-sm"
          >
            <div>
              <div className="w-9 h-9 rounded-lg bg-indigo-600/20 text-indigo-400 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
                <Upload className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-100 mb-1">
                {t.dashboard.uploadDataset}
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Upload CSV or Excel customer review datasets with automated schema and quality checks.
              </p>
            </div>
            <div className="flex items-center gap-1 text-xs text-indigo-400 font-medium mt-4 group-hover:translate-x-0.5 transition-transform">
              <span>View Datasets</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Link>

          <Link
            href="/dashboard/analysis"
            className="group p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900/90 transition-all flex flex-col justify-between backdrop-blur-sm"
          >
            <div>
              <div className="w-9 h-9 rounded-lg bg-cyan-600/20 text-cyan-400 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
                <LineChart className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-100 mb-1">
                {t.dashboard.runAnalysis}
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Execute BERT emotion inference, BERTopic clustering, and SHAP explainability.
              </p>
            </div>
            <div className="flex items-center gap-1 text-xs text-cyan-400 font-medium mt-4 group-hover:translate-x-0.5 transition-transform">
              <span>Analysis Engine</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Link>

          <Link
            href="/dashboard/insights"
            className="group p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900/90 transition-all flex flex-col justify-between backdrop-blur-sm"
          >
            <div>
              <div className="w-9 h-9 rounded-lg bg-purple-600/20 text-purple-400 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
                <Brain className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-100 mb-1">
                {t.dashboard.insights}
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Inspect cross-matrices, net sentiment trends, and multi-dimensional categorical drivers.
              </p>
            </div>
            <div className="flex items-center gap-1 text-xs text-purple-400 font-medium mt-4 group-hover:translate-x-0.5 transition-transform">
              <span>Executive BI</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Link>

          <Link
            href="/dashboard/assistant"
            className="group p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900/90 transition-all flex flex-col justify-between backdrop-blur-sm"
          >
            <div>
              <div className="w-9 h-9 rounded-lg bg-emerald-600/20 text-emerald-400 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
                <Bot className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-100 mb-1">
                {t.dashboard.assistant}
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Consult with the AI Assistant using answers strictly grounded in verified analytics.
              </p>
            </div>
            <div className="flex items-center gap-1 text-xs text-emerald-400 font-medium mt-4 group-hover:translate-x-0.5 transition-transform">
              <span>Ask Assistant</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Link>

          <Link
            href="/dashboard/benchmarking"
            className="group p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900/90 transition-all flex flex-col justify-between backdrop-blur-sm"
          >
            <div>
              <div className="w-9 h-9 rounded-lg bg-amber-600/20 text-amber-400 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
                <Scale className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-100 mb-1">
                {t.dashboard.benchmarking}
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Compare cohort performance against anonymized platform industry benchmarks.
              </p>
            </div>
            <div className="flex items-center gap-1 text-xs text-amber-400 font-medium mt-4 group-hover:translate-x-0.5 transition-transform">
              <span>View Benchmarks</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Link>

          <Link
            href="/dashboard/reports"
            className="group p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900/90 transition-all flex flex-col justify-between backdrop-blur-sm"
          >
            <div>
              <div className="w-9 h-9 rounded-lg bg-violet-600/20 text-violet-400 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
                <FileText className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-100 mb-1">
                {t.dashboard.viewReports}
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Access executive PDF digests, cross-cohort comparisons, and AI recommendations.
              </p>
            </div>
            <div className="flex items-center gap-1 text-xs text-violet-400 font-medium mt-4 group-hover:translate-x-0.5 transition-transform">
              <span>Explore Reports</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Datasets / Activity */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold tracking-wide text-slate-200 uppercase">
            {t.dashboard.recentActivity}
          </h2>
          {datasets.length > 0 && (
            <Link
              href="/dashboard/datasets"
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1"
            >
              <span>View all datasets</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          )}
        </div>

        {datasets.length === 0 ? (
          <EmptyState
            icon={<Clock className="w-5 h-5" />}
            title={t.dashboard.noActivity}
            description={t.dashboard.noDatasetsDesc}
          />
        ) : (
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden backdrop-blur-sm">
            <div className="divide-y divide-slate-800/60">
              {datasets.slice(0, 5).map((dataset) => (
                <div
                  key={dataset.id}
                  className="p-4 flex items-center justify-between hover:bg-slate-850/40 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-950/60 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                      <Database className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-100">{dataset.name}</p>
                      <p className="text-[11px] text-slate-400">
                        {dataset.row_count?.toLocaleString()} rows • Uploaded {new Date(dataset.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                        dataset.status === 'READY'
                          ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-500/30'
                          : dataset.status === 'FAILED'
                          ? 'bg-rose-950/60 text-rose-400 border border-rose-500/30'
                          : 'bg-amber-950/60 text-amber-400 border border-amber-500/30'
                      }`}
                    >
                      {dataset.status}
                    </span>

                    <Link
                      href={`/dashboard/datasets/${dataset.id}`}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                    >
                      Details →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
