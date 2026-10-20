'use client';

import React, { useState } from 'react';
import {
  FileText,
  Download,
  Trash2,
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
  Search,
  Filter,
} from 'lucide-react';
import { ReportItem } from '@/types/report';
import { reportsApi } from '@/lib/api/reports';

interface ReportHistoryTableProps {
  reports: ReportItem[];
  loading?: boolean;
  onRefresh?: () => void;
  onOpenGenerator?: () => void;
}

export const ReportHistoryTable: React.FC<ReportHistoryTableProps> = ({
  reports,
  loading = false,
  onRefresh,
  onOpenGenerator,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [downloadingId, setDownloadingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const formatFileSize = (bytes?: number | null): string => {
    if (!bytes || bytes <= 0) return '—';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatDate = (dateStr?: string | null): string => {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  const handleDownload = async (report: ReportItem) => {
    if (report.status !== 'COMPLETED') return;
    try {
      setDownloadingId(report.id);
      const rtype = (report.report_type || 'full').toLowerCase();
      const fname = `CFAP_${rtype.toUpperCase()}_Report_${report.analysis_id}.pdf`;
      await reportsApi.downloadReportPdf(report.id, fname);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to download PDF.');
    } finally {
      setDownloadingId(null);
    }
  };

  const handleDelete = async (reportId: number) => {
    if (!confirm('Are you sure you want to delete this report?')) return;
    try {
      setDeletingId(reportId);
      await reportsApi.deleteReport(reportId);
      if (onRefresh) onRefresh();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete report.');
    } finally {
      setDeletingId(null);
    }
  };

  const filteredReports = reports.filter((r) => {
    const matchesSearch =
      r.id.toString().includes(searchTerm) ||
      r.analysis_id.toString().includes(searchTerm) ||
      r.dataset_id.toString().includes(searchTerm) ||
      r.report_type.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesType =
      typeFilter === 'ALL' || r.report_type.toUpperCase() === typeFilter;

    const matchesStatus =
      statusFilter === 'ALL' || r.status.toUpperCase() === statusFilter;

    return matchesSearch && matchesType && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Completed
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Loader2 className="w-3.5 h-3.5 text-amber-600 animate-spin" />
            Generating
          </span>
        );
      case 'QUEUED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-950/60 text-indigo-300 border border-indigo-500/30">
            <Clock className="w-3.5 h-3.5 text-indigo-400" />
            Queued
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
        return <span>{status}</span>;
    }
  };

  const getTypeBadge = (type: string) => {
    const rtype = (type || 'full').toUpperCase();
    let style = 'bg-indigo-950/60 text-indigo-300 border-indigo-500/30';
    if (rtype === 'EXECUTIVE') {
      style = 'bg-purple-950/60 text-purple-300 border-purple-500/30';
    } else if (rtype === 'ANALYSIS') {
      style = 'bg-blue-950/60 text-blue-300 border-blue-500/30';
    }
    return (
      <span className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider border ${style}`}>
        {rtype}
      </span>
    );
  };

  return (
    <div className="bg-slate-900/60 rounded-xl border border-slate-800 shadow-sm overflow-hidden backdrop-blur-sm">
      {/* Table Header Controls */}
      <div className="p-4 border-b border-slate-800 flex flex-col md:flex-row items-center justify-between gap-3 bg-slate-950/40">
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search reports by ID or type..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <div className="flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="text-xs bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Templates</option>
              <option value="FULL">Full Report</option>
              <option value="EXECUTIVE">Executive Summary</option>
              <option value="ANALYSIS">Analysis Report</option>
            </select>
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="COMPLETED">Completed</option>
            <option value="PROCESSING">Generating</option>
            <option value="QUEUED">Queued</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>
      </div>

      {/* Reports Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
              <th className="py-3 px-4">Report ID</th>
              <th className="py-3 px-4">Template Type</th>
              <th className="py-3 px-4">Associated Run</th>
              <th className="py-3 px-4">Created At</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">File Size</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {loading ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-400">
                  <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-indigo-400" />
                  Loading report records...
                </td>
              </tr>
            ) : filteredReports.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-slate-400">
                  <FileText className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                  <p className="font-medium text-slate-200 text-sm">No reports found</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Generate a new intelligence report from any completed analysis.
                  </p>
                  {onOpenGenerator && (
                    <button
                      onClick={onOpenGenerator}
                      className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-medium text-xs hover:bg-indigo-500 transition-colors cursor-pointer"
                    >
                      Generate New Report
                    </button>
                  )}
                </td>
              </tr>
            ) : (
              filteredReports.map((report) => (
                <tr key={report.id} className="hover:bg-slate-850/40 transition-colors">
                  <td className="py-3.5 px-4 font-mono font-semibold text-slate-100">
                    #{report.id}
                  </td>
                  <td className="py-3.5 px-4">
                    {getTypeBadge(report.report_type)}
                  </td>
                  <td className="py-3.5 px-4 text-slate-300">
                    Dataset #{report.dataset_id} • Analysis #{report.analysis_id}
                  </td>
                  <td className="py-3.5 px-4 text-slate-400 font-mono text-[11px]">
                    {formatDate(report.created_at)}
                  </td>
                  <td className="py-3.5 px-4">
                    {getStatusBadge(report.status)}
                  </td>
                  <td className="py-3.5 px-4 text-slate-300 font-mono text-[11px]">
                    {formatFileSize(report.file_size_bytes)}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      {report.status === 'COMPLETED' && (
                        <button
                          onClick={() => handleDownload(report)}
                          disabled={downloadingId === report.id}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-indigo-950/60 text-indigo-300 hover:bg-indigo-900/60 border border-indigo-500/30 font-medium text-xs transition-colors disabled:opacity-50 cursor-pointer"
                        >
                          {downloadingId === report.id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Download className="w-3.5 h-3.5" />
                          )}
                          Download
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(report.id)}
                        disabled={deletingId === report.id}
                        className="p-1 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded transition-colors disabled:opacity-50 cursor-pointer"
                        title="Delete report"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
