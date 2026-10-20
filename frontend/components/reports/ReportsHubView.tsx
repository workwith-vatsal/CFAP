'use client';

import React, { useEffect, useState } from 'react';
import {
  FileText,
  Plus,
  RefreshCw,
  HardDrive,
  CheckCircle2,
  LayoutGrid,
  List,
  Layers,
} from 'lucide-react';
import { ReportItem } from '@/types/report';
import { reportsApi } from '@/lib/api/reports';
import { ReportCard } from './ReportCard';
import { ReportHistoryTable } from './ReportHistoryTable';
import { ReportGeneratorModal } from './ReportGeneratorModal';

export const ReportsHubView: React.FC = () => {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');

  const fetchReports = async () => {
    try {
      const res = await reportsApi.listReports();
      setReports(res.items);
    } catch (err) {
      console.error('Failed to fetch reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    async function loadInitial() {
      try {
        const res = await reportsApi.listReports();
        if (isMounted) {
          setReports(res.items);
          setLoading(false);
        }
      } catch (err) {
        console.error('Failed to load initial reports:', err);
        if (isMounted) setLoading(false);
      }
    }
    loadInitial();
    return () => {
      isMounted = false;
    };
  }, []);

  // Poll for status updates if any report is QUEUED or PROCESSING
  useEffect(() => {
    const hasInFlight = reports.some(
      (r) => r.status === 'QUEUED' || r.status === 'PROCESSING'
    );

    if (!hasInFlight) return;

    const interval = setInterval(() => {
      fetchReports();
    }, 3500);

    return () => clearInterval(interval);
  }, [reports]);

  const totalReports = reports.length;
  const completedReports = reports.filter((r) => r.status === 'COMPLETED').length;
  const totalSizeBytes = reports.reduce(
    (acc, r) => acc + (r.file_size_bytes || 0),
    0
  );

  const formatStorage = (bytes: number): string => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2.5">
            <FileText className="w-7 h-7 text-indigo-400" />
            Intelligence Reports &amp; Export
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Generate and download publication-grade PDF intelligence reports with verified metrics, charts, and explainability.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setLoading(true);
              fetchReports();
            }}
            className="p-2 text-slate-400 hover:text-indigo-400 hover:bg-slate-800 rounded-lg transition-colors border border-slate-800 cursor-pointer"
            title="Refresh list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <div className="flex items-center bg-slate-900 p-0.5 rounded-lg border border-slate-800">
            <button
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded-md text-xs font-medium transition-colors cursor-pointer ${
                viewMode === 'table'
                  ? 'bg-slate-800 text-indigo-400 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Table View"
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('cards')}
              className={`p-1.5 rounded-md text-xs font-medium transition-colors cursor-pointer ${
                viewMode === 'cards'
                  ? 'bg-slate-800 text-indigo-400 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Card View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Generate New Report
          </button>
        </div>
      </div>

      {/* KPI Stats Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900/60 rounded-xl border border-slate-800 p-4 shadow-sm backdrop-blur-sm flex items-center gap-3.5">
          <div className="p-3 bg-indigo-950/60 text-indigo-400 border border-indigo-500/20 rounded-xl">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold font-mono text-slate-100">{totalReports}</div>
            <div className="text-xs text-slate-400">Total Generated Reports</div>
          </div>
        </div>

        <div className="bg-slate-900/60 rounded-xl border border-slate-800 p-4 shadow-sm backdrop-blur-sm flex items-center gap-3.5">
          <div className="p-3 bg-emerald-950/60 text-emerald-400 border border-emerald-500/20 rounded-xl">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold font-mono text-slate-100">{completedReports}</div>
            <div className="text-xs text-slate-400">Completed &amp; Downloadable</div>
          </div>
        </div>

        <div className="bg-slate-900/60 rounded-xl border border-slate-800 p-4 shadow-sm backdrop-blur-sm flex items-center gap-3.5">
          <div className="p-3 bg-purple-950/60 text-purple-400 border border-purple-500/20 rounded-xl">
            <HardDrive className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold font-mono text-slate-100">{formatStorage(totalSizeBytes)}</div>
            <div className="text-xs text-slate-400">Total PDF Storage Used</div>
          </div>
        </div>
      </div>

      {/* Main Reports View */}
      {viewMode === 'table' ? (
        <ReportHistoryTable
          reports={reports}
          loading={loading}
          onRefresh={fetchReports}
          onOpenGenerator={() => setIsModalOpen(true)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {reports.map((report) => (
            <ReportCard
              key={report.id}
              report={report}
              onDeleted={() => fetchReports()}
            />
          ))}
          {reports.length === 0 && !loading && (
            <div className="col-span-full py-12 text-center text-slate-400 bg-slate-900/60 rounded-xl border border-slate-800 p-8 backdrop-blur-sm">
              <FileText className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              <p className="font-medium text-slate-200 text-sm">No reports generated yet</p>
              <p className="text-xs text-slate-400 mt-0.5">
                Generate a publication-grade PDF from any completed dataset analysis.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Generator Modal */}
      <ReportGeneratorModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onReportCreated={() => {
          fetchReports();
        }}
      />
    </div>
  );
};
