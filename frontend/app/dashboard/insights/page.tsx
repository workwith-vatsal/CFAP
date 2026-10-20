'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import {
  Brain,
  Database,
  ChevronDown,
  AlertCircle,
  Sparkles,
  LineChart,
} from 'lucide-react';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Button } from '@/components/ui/Button';
import { Dataset } from '@/types/dataset';
import { Analysis } from '@/types/analysis';
import { getDatasets } from '@/lib/api/datasets';
import { analysisApi } from '@/lib/api/analysis';
import { ExecutiveBIDashboard } from '@/components/analysis/ExecutiveBIDashboard';

function InsightsContent() {
  const { t } = useLanguage();
  const searchParams = useSearchParams();
  const initialDatasetParam = searchParams.get('datasetId');

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(
    initialDatasetParam ? parseInt(initialDatasetParam, 10) : null
  );
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load datasets on mount
  useEffect(() => {
    let isMounted = true;
    async function loadDatasets() {
      try {
        const res = await getDatasets(false);
        const readyDatasets = (res.datasets || []).filter((d) => d.status === 'READY');
        if (isMounted) {
          setDatasets(readyDatasets);
          setSelectedDatasetId((prev) => prev ?? (readyDatasets.length > 0 ? readyDatasets[0].id : null));
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : 'Failed to load datasets.';
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }
    loadDatasets();
    return () => {
      isMounted = false;
    };
  }, []);

  // Fetch analysis when selected dataset changes
  useEffect(() => {
    let isMounted = true;
    async function fetchAnalysis() {
      if (!selectedDatasetId) {
        if (isMounted) setAnalysis(null);
        return;
      }

      setIsLoadingAnalysis(true);
      try {
        const res = await analysisApi.getLatestAnalysis(selectedDatasetId);
        if (isMounted) {
          if (res && res.status === 'COMPLETED') {
            setAnalysis(res);
          } else {
            setAnalysis(null);
          }
        }
      } catch {
        if (isMounted) {
          setAnalysis(null);
        }
      } finally {
        if (isMounted) {
          setIsLoadingAnalysis(false);
        }
      }
    }

    if (selectedDatasetId) {
      fetchAnalysis();
    }
    return () => {
      isMounted = false;
    };
  }, [selectedDatasetId]);

  if (isLoading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center space-y-3">
        <LoadingSpinner size="lg" className="text-indigo-500" />
        <p className="text-xs text-slate-400 font-mono">Loading insights intelligence...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-400 max-w-xl mx-auto my-12 text-center">
        <AlertCircle className="w-8 h-8 mx-auto mb-3" />
        <h3 className="font-bold text-base">Error Loading Datasets</h3>
        <p className="text-xs mt-1">{error}</p>
      </div>
    );
  }

  if (datasets.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-12 text-center max-w-2xl mx-auto my-12 shadow-sm space-y-5 backdrop-blur-sm">
        <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto border border-indigo-500/20">
          <Database className="w-8 h-8" />
        </div>
        <h3 className="text-xl font-bold text-slate-100">
          No Ready Datasets Available
        </h3>
        <p className="text-slate-400 text-sm max-w-md mx-auto leading-relaxed">
          Upload a CSV or Excel customer feedback dataset first to view Executive BI analytics, cross-dimensional matrices, and temporal trends.
        </p>
        <Link href="/dashboard/datasets">
          <Button variant="primary" className="gap-2 shadow-lg shadow-indigo-500/20">
            <Database className="w-4 h-4" />
            Go to Datasets Manager
          </Button>
        </Link>
      </div>
    );
  }

  const activeDataset = datasets.find((d) => d.id === selectedDatasetId) || datasets[0];

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Page Header with Dataset Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-100">
                {t.dashboard.insights} &amp; Executive BI
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Cohort cross-matrices, sentiment drivers, temporal trajectory &amp; categorical breakdowns
              </p>
            </div>
          </div>
        </div>

        {/* Dataset Selector */}
        <div className="flex items-center gap-3 self-start md:self-auto">
          <span className="text-xs text-slate-400 font-medium whitespace-nowrap">
            Active Dataset:
          </span>
          <div className="relative">
            <select
              value={selectedDatasetId || ''}
              onChange={(e) => setSelectedDatasetId(Number(e.target.value))}
              className="appearance-none bg-slate-900 border border-slate-700 hover:border-slate-600 rounded-xl px-4 py-2 pr-9 text-xs font-semibold text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer shadow-sm"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.row_count} rows)
                </option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Main View */}
      {isLoadingAnalysis ? (
        <div className="py-24 flex flex-col items-center justify-center space-y-3">
          <LoadingSpinner size="lg" className="text-indigo-500" />
          <p className="text-xs text-slate-400 font-mono">Loading executive BI metrics...</p>
        </div>
      ) : analysis ? (
        <ExecutiveBIDashboard
          analysis={analysis}
          dataset={activeDataset}
        />
      ) : (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-12 text-center max-w-2xl mx-auto my-12 shadow-sm space-y-5 backdrop-blur-sm">
          <div className="w-16 h-16 rounded-2xl bg-amber-500/10 text-amber-400 flex items-center justify-center mx-auto border border-amber-500/20">
            <LineChart className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-bold text-slate-100">
            No Completed Analysis for this Dataset
          </h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto leading-relaxed">
            Run an analysis pipeline on <span className="text-indigo-400 font-semibold">{activeDataset.name}</span> to generate the Executive BI overview, cross-matrices, and temporal trends.
          </p>
          <div className="flex items-center justify-center gap-3 pt-2">
            <Link href="/dashboard/analysis">
              <Button variant="primary" className="gap-2 shadow-lg shadow-indigo-500/20">
                <Sparkles className="w-4 h-4" />
                Go to Analysis Engine
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

export default function InsightsPage() {
  return (
    <Suspense
      fallback={
        <div className="py-24 flex flex-col items-center justify-center space-y-3">
          <LoadingSpinner size="lg" className="text-indigo-500" />
          <p className="text-xs text-slate-400 font-mono">Loading insights module...</p>
        </div>
      }
    >
      <InsightsContent />
    </Suspense>
  );
}
