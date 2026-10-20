'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Archive,
  RotateCcw,
  Trash2,
  Edit2,
  Sparkles,
  ShieldCheck,
} from 'lucide-react';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { AnalysisDashboard } from '@/components/analysis/AnalysisDashboard';
import {
  Dataset,
  DataPreviewResponse,
  ColumnQualityInfo,
} from '@/types';
import {
  getDataset,
  getDatasetPreview,
  renameDataset,
  archiveDataset,
  restoreDataset,
  deleteDataset,
} from '@/lib/api/datasets';

export default function DatasetDetailsPage() {
  const { t } = useLanguage();
  const { showToast } = useToast();
  const params = useParams();
  const router = useRouter();

  const datasetId = Number(params?.id);

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [preview, setPreview] = useState<DataPreviewResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'analysis' | 'quality'>('analysis');

  // Rename Modal
  const [isRenameOpen, setIsRenameOpen] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const [isRenaming, setIsRenaming] = useState(false);

  // Delete Modal
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function loadDataset() {
      if (!datasetId || isNaN(datasetId)) {
        if (isMounted) {
          setError('Invalid dataset identifier.');
          setIsLoading(false);
        }
        return;
      }

      try {
        const data = await getDataset(datasetId);
        if (isMounted) {
          setDataset(data);
          setRenameValue(data.name);
        }

        if (data.status === 'READY') {
          try {
            const prev = await getDatasetPreview(datasetId);
            if (isMounted) {
              setPreview(prev);
            }
          } catch {
            // Preview failure is non-blocking
          }
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg =
            err instanceof Error
              ? err.message
              : 'Failed to load dataset details.';
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadDataset();

    return () => {
      isMounted = false;
    };
  }, [datasetId]);

  const handleRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dataset || !renameValue.trim()) return;

    setIsRenaming(true);
    try {
      const updated = await renameDataset(dataset.id, renameValue.trim());
      setDataset(updated);
      showToast('Dataset renamed.', 'success');
      setIsRenameOpen(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Rename failed.';
      showToast(msg, 'error');
    } finally {
      setIsRenaming(false);
    }
  };

  const handleArchiveToggle = async () => {
    if (!dataset) return;
    try {
      if (dataset.status === 'ARCHIVED') {
        const restored = await restoreDataset(dataset.id);
        setDataset(restored);
        showToast('Dataset restored.', 'success');
      } else {
        const archived = await archiveDataset(dataset.id);
        setDataset(archived);
        showToast('Dataset archived.', 'info');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Operation failed.';
      showToast(msg, 'error');
    }
  };

  const handleDeleteConfirm = async () => {
    if (!dataset) return;
    setIsDeleting(true);
    try {
      await deleteDataset(dataset.id);
      showToast('Dataset deleted.', 'success');
      router.push('/dashboard/datasets');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Deletion failed.';
      showToast(msg, 'error');
      setIsDeleting(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getDetectedTypeBadge = (type: string) => {
    switch (type) {
      case 'feedback':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-indigo-950/80 border border-indigo-700/60 text-indigo-300">
            feedback text
          </span>
        );
      case 'rating':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-amber-950/80 border border-amber-700/60 text-amber-300">
            rating
          </span>
        );
      case 'date':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-cyan-950/80 border border-cyan-700/60 text-cyan-300">
            date
          </span>
        );
      case 'category':
      case 'product':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-violet-950/80 border border-violet-700/60 text-violet-300">
            {type}
          </span>
        );
      case 'sensitive':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-rose-950/80 border border-rose-700/60 text-rose-300 flex items-center gap-1 w-fit">
            <ShieldCheck className="w-2.5 h-2.5" />
            <span>sensitive PII</span>
          </span>
        );
      case 'numeric':
      case 'boolean':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-slate-800 border border-slate-700 text-slate-300">
            {type}
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-slate-900 border border-slate-800 text-slate-400">
            {type}
          </span>
        );
    }
  };

  if (isLoading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center space-y-3">
        <LoadingSpinner size="lg" className="text-indigo-500" />
        <p className="text-xs text-slate-400 font-mono">Loading dataset analysis...</p>
      </div>
    );
  }

  if (error || !dataset) {
    return (
      <div className="space-y-4 max-w-2xl mx-auto py-12">
        <Alert variant="error">{error || 'Dataset not found.'}</Alert>
        <Link href="/dashboard/datasets">
          <Button variant="ghost" size="sm" leftIcon={<ArrowLeft className="w-3.5 h-3.5" />}>
            {t.datasetDetails.backToDatasets}
          </Button>
        </Link>
      </div>
    );
  }

  const quality = dataset.quality_report;
  const columnsDetail: ColumnQualityInfo[] =
    quality?.columns || quality?.columns_detail || [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Back Link & Header */}
      <div>
        <Link
          href="/dashboard/datasets"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors mb-4"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>{t.datasetDetails.backToDatasets}</span>
        </Link>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-white">
                {dataset.name}
              </h1>
              <span className="uppercase text-[10px] font-mono font-semibold px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700 text-slate-300">
                {dataset.file_type}
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">
              {dataset.original_filename} • {formatBytes(dataset.file_size_bytes)} • Created on{' '}
              {new Date(dataset.created_at).toLocaleDateString()}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Edit2 className="w-3.5 h-3.5" />}
              onClick={() => setIsRenameOpen(true)}
            >
              {t.datasets.actionRename}
            </Button>
            <Button
              variant="outline"
              size="sm"
              leftIcon={
                dataset.status === 'ARCHIVED' ? (
                  <RotateCcw className="w-3.5 h-3.5" />
                ) : (
                  <Archive className="w-3.5 h-3.5" />
                )
              }
              onClick={handleArchiveToggle}
            >
              {dataset.status === 'ARCHIVED'
                ? t.datasets.actionRestore
                : t.datasets.actionArchive}
            </Button>
            <Button
              variant="danger"
              size="sm"
              leftIcon={<Trash2 className="w-3.5 h-3.5" />}
              onClick={() => setIsDeleteOpen(true)}
            >
              {t.datasets.actionDelete}
            </Button>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-3 pt-4 border-b border-slate-800/80">
          <button
            onClick={() => setActiveTab('analysis')}
            className={`pb-3 px-1 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'analysis'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>{t.analysis.tabTitle}</span>
          </button>
          <button
            onClick={() => setActiveTab('quality')}
            className={`pb-3 px-1 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'quality'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>{t.datasetDetails.qualityMetrics}</span>
          </button>
        </div>
      </div>

      {activeTab === 'analysis' ? (
        <AnalysisDashboard dataset={dataset} />
      ) : (
        <>
          {/* Overview Metrics Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
          <span className="text-[11px] font-medium text-slate-400 block mb-1">
            Total Rows
          </span>
          <div className="text-xl font-bold font-mono text-slate-100">
            {dataset.row_count.toLocaleString()}
          </div>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
          <span className="text-[11px] font-medium text-slate-400 block mb-1">
            Total Columns
          </span>
          <div className="text-xl font-bold font-mono text-slate-100">
            {dataset.column_count}
          </div>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
          <span className="text-[11px] font-medium text-slate-400 block mb-1">
            {t.datasetDetails.usableRows}
          </span>
          <div className="text-xl font-bold font-mono text-emerald-400">
            {quality ? quality.usable_rows.toLocaleString() : '—'}
          </div>
          <span className="text-[10px] text-slate-500">Ready for NLP</span>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
          <span className="text-[11px] font-medium text-slate-400 block mb-1">
            {t.datasetDetails.invalidRows}
          </span>
          <div className="text-xl font-bold font-mono text-rose-400">
            {quality ? quality.invalid_rows.toLocaleString() : '—'}
          </div>
          <span className="text-[10px] text-slate-500">Missing/Empty</span>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
          <span className="text-[11px] font-medium text-slate-400 block mb-1">
            {t.datasetDetails.duplicateRows}
          </span>
          <div className="text-xl font-bold font-mono text-amber-400">
            {quality ? quality.duplicate_rows.toLocaleString() : '—'}
          </div>
          <span className="text-[10px] text-slate-500">Full Duplicates</span>
        </div>
      </div>

      {/* Quality Score & Feedback Detection Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quality Score Breakdown Card */}
        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/50 flex flex-col justify-between space-y-6">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
                {t.datasetDetails.qualityScore}
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-800 text-slate-400">
                Deterministic 0-100
              </span>
            </div>

            <div className="flex items-baseline gap-3 mb-4">
              <span className="text-4xl font-extrabold font-mono text-indigo-400">
                {dataset.quality_score !== null && dataset.quality_score !== undefined
                  ? `${dataset.quality_score.toFixed(1)}%`
                  : '—'}
              </span>
              <span className="text-xs text-slate-400">Overall Health</span>
            </div>

            {quality?.score_breakdown && (
              <div className="space-y-2.5 pt-2 border-t border-slate-800/80 text-xs">
                <div className="flex items-center justify-between text-slate-300">
                  <span>Usable Feedback (40%)</span>
                  <span className="font-mono text-indigo-400">
                    {quality.score_breakdown.usable_feedback_score} pts
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-300">
                  <span>Completeness (25%)</span>
                  <span className="font-mono text-indigo-400">
                    {quality.score_breakdown.completeness_score} pts
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-300">
                  <span>Uniqueness (20%)</span>
                  <span className="font-mono text-indigo-400">
                    {quality.score_breakdown.uniqueness_score} pts
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-300">
                  <span>Structure (15%)</span>
                  <span className="font-mono text-indigo-400">
                    {quality.score_breakdown.structure_score} pts
                  </span>
                </div>
              </div>
            )}
          </div>

          <p className="text-[11px] text-slate-500 leading-relaxed border-t border-slate-800 pt-3">
            Score is computed deterministically from text completeness, row uniqueness, and valid review structure.
          </p>
        </div>

        {/* Feedback Column Detection Panel */}
        <div className="lg:col-span-2 p-6 rounded-2xl border border-slate-800 bg-slate-900/50 space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-600/20 text-indigo-400 flex items-center justify-center">
                <Sparkles className="w-4 h-4" />
              </div>
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
                {t.datasetDetails.feedbackDetection}
              </h2>
            </div>
            {dataset.feedback_confidence && (
              <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-emerald-950/80 border border-emerald-800/60 text-emerald-300">
                {(dataset.feedback_confidence * 100).toFixed(0)}% Confidence
              </span>
            )}
          </div>

          {dataset.feedback_column ? (
            <div className="p-4 rounded-xl border border-indigo-500/30 bg-indigo-950/20 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400 block mb-0.5">
                    {t.datasetDetails.detectedFeedbackCol}
                  </span>
                  <span className="text-base font-bold font-mono text-indigo-300">
                    {dataset.feedback_column}
                  </span>
                </div>
                <span className="text-[11px] text-slate-400 font-mono">
                  Primary Text Target
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Dynamic NLP heuristics identified this column based on natural language text length, token diversity, and vocabulary characteristics.
              </p>
            </div>
          ) : (
            <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-950/20 text-xs text-amber-200">
              <p className="font-semibold mb-1">{t.datasetDetails.noFeedbackDetected}</p>
              <p className="text-amber-300/80 text-[11px]">
                The dataset was parsed successfully, but no column exhibited sufficient natural language feedback length. It can be viewed but is not flagged analysis-ready.
              </p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 text-xs pt-1">
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-slate-400 text-[11px] block mb-1">
                {t.datasetDetails.missingFeedback}
              </span>
              <span className="font-mono font-semibold text-slate-200">
                {quality ? quality.missing_feedback.toLocaleString() : '0'} rows
              </span>
            </div>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-slate-400 text-[11px] block mb-1">
                {t.datasetDetails.blankFeedback}
              </span>
              <span className="font-mono font-semibold text-slate-200">
                {quality ? quality.blank_feedback.toLocaleString() : '0'} rows
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Column Quality & Schema Analysis */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
          {t.datasetDetails.columnAnalysis}
        </h2>

        <div className="border border-slate-800 rounded-xl bg-slate-900/40 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800 text-[11px] uppercase tracking-wider font-semibold">
                <tr>
                  <th className="py-3 px-4">{t.datasetDetails.colName}</th>
                  <th className="py-3 px-4">{t.datasetDetails.colDetectedType}</th>
                  <th className="py-3 px-4">{t.datasetDetails.colRawType}</th>
                  <th className="py-3 px-4">{t.datasetDetails.colNulls}</th>
                  <th className="py-3 px-4">{t.datasetDetails.colNullPct}</th>
                  <th className="py-3 px-4">{t.datasetDetails.colUnique}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {columnsDetail.map((col, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-slate-100">
                      {col.name}
                    </td>
                    <td className="py-3 px-4">
                      {getDetectedTypeBadge(col.detected_type)}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400 text-[11px]">
                      {col.raw_dtype}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {col.null_count.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-mono">
                      <span
                        className={
                          col.null_percentage > 20
                            ? 'text-rose-400'
                            : col.null_percentage > 5
                            ? 'text-amber-400'
                            : 'text-slate-300'
                        }
                      >
                        {col.null_percentage.toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {col.unique_count.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Sanitized Data Preview Table */}
      {preview && preview.rows.length > 0 && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
              {t.datasetDetails.dataPreview}
            </h2>
            <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>{t.datasetDetails.previewNotice}</span>
            </p>
          </div>

          <div className="border border-slate-800 rounded-xl bg-slate-900/40 overflow-hidden">
            <div className="overflow-x-auto max-h-96">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900/95 sticky top-0 text-slate-400 border-b border-slate-800 text-[11px] font-mono">
                  <tr>
                    <th className="py-2.5 px-3 bg-slate-950 text-slate-500 w-12 text-center">
                      #
                    </th>
                    {preview.columns.map((col, idx) => (
                      <th key={idx} className="py-2.5 px-4 font-semibold text-slate-200">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                  {preview.rows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 text-slate-500 text-center bg-slate-950/40">
                        {rIdx + 1}
                      </td>
                      {preview.columns.map((col, cIdx) => (
                        <td
                          key={cIdx}
                          className="py-2.5 px-4 text-slate-300 max-w-xs truncate"
                          title={String(row[col] ?? '')}
                        >
                          {row[col] !== null && row[col] !== undefined ? (
                            String(row[col])
                          ) : (
                            <span className="text-slate-600 italic">null</span>
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
        </>
      )}

      {/* Rename Modal */}
      <Modal
        isOpen={isRenameOpen}
        onClose={() => setIsRenameOpen(false)}
        title={t.datasets.renameModalTitle}
        maxWidth="sm"
      >
        <form onSubmit={handleRenameSubmit} className="space-y-4">
          <Input
            label={t.datasets.renameInputLabel}
            required
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
          />
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={isRenaming}
              onClick={() => setIsRenameOpen(false)}
            >
              {t.common.cancel}
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isRenaming}
              disabled={!renameValue.trim() || isRenaming}
            >
              {t.common.save}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        title={t.datasets.deleteConfirmTitle}
        description={t.datasets.deleteConfirmMessage}
        maxWidth="sm"
        confirmText={t.datasets.actionDelete}
        confirmVariant="danger"
        cancelText={t.common.cancel}
        onConfirm={handleDeleteConfirm}
        isConfirmLoading={isDeleting}
      >
        <p className="text-xs text-slate-300">
          Dataset: <span className="font-semibold text-slate-100 font-mono">{dataset.name}</span>
        </p>
      </Modal>
    </div>
  );
}
