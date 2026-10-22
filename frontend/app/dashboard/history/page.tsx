'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  History,
  Clock,
  Database,
  LineChart,
  Brain,
  Bot,
  FileText,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
  Search,
  Filter,
} from 'lucide-react';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Button } from '@/components/ui/Button';
import { Dataset } from '@/types/dataset';
import { AnalysisSummary } from '@/types/analysis';
import { getDatasets } from '@/lib/api/datasets';
import { analysisApi } from '@/lib/api/analysis';

interface RunItem extends AnalysisSummary {
  datasetName: string;
  datasetId: number;
}

export default function HistoryPage() {
  const { t } = useLanguage();
  const [runs, setRuns] = useState<RunItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  useEffect(() => {
    let isMounted = true;
    async function loadHistory() {
      try {
        const res = await getDatasets(false);
        const readyDatasets: Dataset[] = res.datasets || [];

        const runsPromises = readyDatasets.map(async (d) => {
          try {
            const dRuns = await analysisApi.getAnalysisHistory(d.id);
            return (dRuns || []).map((r) => ({
              ...r,
              datasetName: d.name,
              datasetId: d.id,
            }));
          } catch {
            return [];
          }
        });

        const allRunsArrays = await Promise.all(runsPromises);
        const allRuns = allRunsArrays.flat().sort((a, b) => {
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        });

        if (isMounted) {
          setRuns(allRuns);
        }
      } catch (err) {
        console.error('Failed to load history', err);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadHistory();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleRefresh = async () => {
    setIsLoading(true);
    try {
      const res = await getDatasets(false);
      const readyDatasets: Dataset[] = res.datasets || [];
      const runsPromises = readyDatasets.map(async (d) => {
        try {
          const dRuns = await analysisApi.getAnalysisHistory(d.id);
          return (dRuns || []).map((r) => ({
            ...r,
            datasetName: d.name,
            datasetId: d.id,
          }));
        } catch {
          return [];
        }
      });
      const allRunsArrays = await Promise.all(runsPromises);
      const allRuns = allRunsArrays.flat().sort((a, b) => {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
      setRuns(allRuns);
    } catch (err) {
      console.error('Failed to refresh history', err);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredRuns = runs.filter((run) => {
    const matchesSearch =
      run.datasetName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      String(run.id).includes(searchTerm);
    const matchesStatus =
      statusFilter === 'ALL' || run.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/60 text-emerald-300 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Completed
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-950/60 text-amber-300 border border-amber-500/30">
            <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin" />
            Processing
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-950/60 text-rose-300 border border-rose-500/30">
            <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
            Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-100">
                {t.dashboard.history}
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Audit trail of completed NLP pipelines, BERT inferences, and semantic clustering runs
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            className="p-2 text-slate-400 hover:text-indigo-400 hover:bg-slate-800 rounded-lg transition-colors border border-slate-800 cursor-pointer"
            title="Refresh history"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>

          <Link href="/dashboard/analysis">
            <Button variant="primary" size="sm" className="gap-2 shadow-sm cursor-pointer">
              <LineChart className="w-4 h-4" />
              New Analysis
            </Button>
          </Link>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by dataset name or run ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="COMPLETED">Completed</option>
            <option value="PROCESSING">Processing</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>
      </div>

      {/* Main Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden backdrop-blur-sm shadow-sm">
        {isLoading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3">
            <LoadingSpinner size="lg" className="text-indigo-500" />
            <p className="text-xs text-slate-400 font-mono">Aggregating historical analysis runs...</p>
          </div>
        ) : filteredRuns.length === 0 ? (
          <div className="py-16 text-center text-slate-400 p-8">
            <Clock className="w-8 h-8 mx-auto mb-2 text-slate-600" />
            <p className="font-medium text-slate-200 text-sm">No analysis runs recorded</p>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Execute an analysis pipeline on any ready customer feedback dataset to populate execution history.
            </p>
            <Link href="/dashboard/analysis" className="inline-block mt-4">
              <Button variant="primary" size="sm">
                Go to Analysis Engine
              </Button>
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                  <th className="py-3 px-4">Run ID</th>
                  <th className="py-3 px-4">Dataset Name</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Feedback Rows</th>
                  <th className="py-3 px-4">Execution Date</th>
                  <th className="py-3 px-4 text-right">Explore &amp; Act</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredRuns.map((run) => (
                  <tr key={run.id} className="hover:bg-slate-850/40 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-semibold text-slate-100">
                      Run #{run.id}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-200">
                      <div className="flex items-center gap-2">
                        <Database className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                        <span className="truncate max-w-xs">{run.datasetName}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      {getStatusBadge(run.status)}
                    </td>
                    <td className="py-3.5 px-4 text-slate-300 font-mono text-[11px]">
                      {run.usable_feedback_rows?.toLocaleString() || '—'} rows analyzed
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 font-mono text-[11px]">
                      {new Date(run.created_at).toLocaleString()}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {run.status === 'COMPLETED' && (
                          <>
                            <Link
                              href={`/dashboard/insights?datasetId=${run.datasetId}`}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-indigo-950/60 text-indigo-300 hover:bg-indigo-900/60 border border-indigo-500/30 font-medium text-[11px] transition-colors"
                              title="View Executive BI"
                            >
                              <Brain className="w-3 h-3" />
                              BI
                            </Link>

                            <Link
                              href={`/dashboard/assistant?datasetId=${run.datasetId}&analysisId=${run.id}`}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-purple-950/60 text-purple-300 hover:bg-purple-900/60 border border-purple-500/30 font-medium text-[11px] transition-colors"
                              title="Ask AI Assistant"
                            >
                              <Bot className="w-3 h-3" />
                              Assistant
                            </Link>

                            <Link
                              href="/dashboard/reports"
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-800 text-slate-200 hover:bg-slate-700 border border-slate-700 font-medium text-[11px] transition-colors"
                              title="Export Reports"
                            >
                              <FileText className="w-3 h-3" />
                              Report
                            </Link>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
