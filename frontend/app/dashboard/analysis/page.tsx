'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Sparkles,
  Database,
  ChevronDown,
  AlertCircle,
} from 'lucide-react';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Button } from '@/components/ui/Button';
import { Dataset } from '@/types/dataset';
import { getDatasets } from '@/lib/api/datasets';
import { AnalysisDashboard } from '@/components/analysis/AnalysisDashboard';

export default function AnalysisHubPage() {
  const { t } = useLanguage();

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDatasets() {
      try {
        const res = await getDatasets(false);
        const readyDatasets = (res.datasets || []).filter((d) => d.status === 'READY');
        setDatasets(readyDatasets);
        if (readyDatasets.length > 0) {
          setSelectedDatasetId(readyDatasets[0].id);
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to load datasets.';
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    }

    loadDatasets();
  }, []);

  if (isLoading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center space-y-3">
        <LoadingSpinner size="lg" className="text-indigo-500" />
        <p className="text-xs text-slate-400 font-mono">Loading feedback datasets...</p>
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
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-12 text-center max-w-2xl mx-auto my-12 shadow-sm space-y-5">
        <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mx-auto">
          <Database className="w-8 h-8" />
        </div>
        <h3 className="text-xl font-bold text-slate-900 dark:text-white">
          No Ready Datasets Available
        </h3>
        <p className="text-slate-600 dark:text-slate-400 text-sm max-w-md mx-auto leading-relaxed">
          Upload a CSV or Excel customer feedback dataset first to run BERT Sentiment Analysis, Emotion Classification, and BERTopic Discovery.
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
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                {t.analysis.tabTitle} Engine
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Deep NLP Transformer Pipelines: Sentiment, Emotion & BERTopic
              </p>
            </div>
          </div>
        </div>

        {/* Dataset Selector Dropdown */}
        <div className="flex items-center gap-3">
          <label htmlFor="dataset-selector" className="text-xs font-semibold text-slate-500 dark:text-slate-400">
            Target Dataset:
          </label>
          <div className="relative">
            <select
              id="dataset-selector"
              value={selectedDatasetId || ''}
              onChange={(e) => setSelectedDatasetId(Number(e.target.value))}
              className="appearance-none pl-3 pr-9 py-2 rounded-xl text-xs font-semibold bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.row_count} rows &bull; col: {d.feedback_column || 'None'})
                </option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-slate-400 absolute right-2.5 top-2.5 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Render Active Dataset Analysis Dashboard */}
      {activeDataset && (
        <AnalysisDashboard
          key={activeDataset.id}
          dataset={activeDataset}
        />
      )}
    </div>
  );
}
