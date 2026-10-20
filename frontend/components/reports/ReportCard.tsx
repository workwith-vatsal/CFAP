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
} from 'lucide-react';
import { ReportItem } from '@/types/report';
import { reportsApi } from '@/lib/api/reports';
import { useLanguage } from '@/lib/i18n/LanguageContext';

interface ReportCardProps {
  report: ReportItem;
  datasetName?: string;
  onDeleted?: (reportId: number) => void;
}

export const ReportCard: React.FC<ReportCardProps> = ({
  report,
  datasetName,
  onDeleted,
}) => {
  const { t } = useLanguage();
  const [downloading, setDownloading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const handleDownload = async () => {
    if (report.status !== 'COMPLETED') return;
    try {
      setDownloading(true);
      setError(null);
      const rtype = (report.report_type || 'full').toLowerCase();
      const fname = `CFAP_${rtype.toUpperCase()}_Report_${report.analysis_id}.pdf`;
      await reportsApi.downloadReportPdf(report.id, fname);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to download PDF.';
      setError(msg);
    } finally {
      setDownloading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this report?')) return;
    try {
      setDeleting(true);
      setError(null);
      await reportsApi.deleteReport(report.id);
      if (onDeleted) onDeleted(report.id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete report.';
      setError(msg);
      setDeleting(false);
    }
  };

  const getStatusBadge = () => {
    switch (report.status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/60 text-emerald-300 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            {t.reports.status.completed}
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-950/60 text-amber-300 border border-amber-500/30">
            <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin" />
            {t.reports.status.processing}
          </span>
        );
      case 'QUEUED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-950/60 text-indigo-300 border border-indigo-500/30">
            <Clock className="w-3.5 h-3.5 text-indigo-400" />
            {t.reports.status.queued}
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-950/60 text-rose-300 border border-rose-500/30">
            <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
            {t.reports.status.failed}
          </span>
        );
      default:
        return null;
    }
  };

  const getTypeBadge = () => {
    const rtype = (report.report_type || 'full').toUpperCase();
    let style = 'bg-indigo-950/60 text-indigo-300 border-indigo-500/30';
    if (rtype === 'EXECUTIVE') {
      style = 'bg-purple-950/60 text-purple-300 border-purple-500/30';
    } else if (rtype === 'ANALYSIS') {
      style = 'bg-blue-950/60 text-blue-300 border-blue-500/30';
    }
    return (
      <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider border ${style}`}>
        {rtype}
      </span>
    );
  };

  return (
    <div className="bg-slate-900/60 rounded-xl border border-slate-800 shadow-sm p-5 hover:border-slate-700 hover:shadow-md transition-all backdrop-blur-sm">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-950/60 text-indigo-400 border border-indigo-500/20 rounded-lg">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-semibold text-slate-100 text-sm">
                {datasetName || `Dataset #${report.dataset_id}`}
              </h4>
              {getTypeBadge()}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Analysis #{report.analysis_id} • Created {formatDate(report.created_at)}
            </p>
          </div>
        </div>
        <div>{getStatusBadge()}</div>
      </div>

      {error && (
        <div className="mb-3 p-2 rounded bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400">
          {error}
        </div>
      )}

      {report.error_message && report.status === 'FAILED' && (
        <div className="mb-3 p-2 rounded bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400">
          <b>Error:</b> {report.error_message}
        </div>
      )}

      <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 text-xs text-slate-400">
        <div>
          <span>Size: </span>
          <span className="font-mono font-medium text-slate-200">{formatFileSize(report.file_size_bytes)}</span>
        </div>

        <div className="flex items-center gap-2">
          {report.status === 'COMPLETED' && (
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-sm transition-colors disabled:opacity-50 cursor-pointer"
            >
              {downloading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Download className="w-3.5 h-3.5" />
              )}
              {t.reports.actions.download}
            </button>
          )}

          <button
            onClick={handleDelete}
            disabled={deleting}
            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
            title="Delete report"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
