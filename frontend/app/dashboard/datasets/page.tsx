'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import {
  Database,
  Plus,
  Search,
  Upload,
  FileSpreadsheet,
  FileText,
  CheckCircle2,
  AlertCircle,
  Archive,
  RotateCcw,
  Trash2,
  Edit2,
  ExternalLink,
  Sparkles,
} from 'lucide-react';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { Dataset, DatasetStatus } from '@/types';
import {
  getDatasets,
  uploadDataset,
  renameDataset,
  archiveDataset,
  restoreDataset,
  deleteDataset,
} from '@/lib/api/datasets';

export default function DatasetsPage() {
  const { t } = useLanguage();
  const { showToast } = useToast();

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'active' | 'archived'>('active');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Upload Modal State
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadName, setUploadName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Rename Modal State
  const [editingDataset, setEditingDataset] = useState<Dataset | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [isRenaming, setIsRenaming] = useState(false);

  // Delete Modal State
  const [deletingDataset, setDeletingDataset] = useState<Dataset | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchDatasetList = useCallback(async () => {
    try {
      const res = await getDatasets(activeTab === 'archived');
      setDatasets(res.datasets || []);
    } catch {
      showToast('Failed to load datasets.', 'error');
    } finally {
      setIsLoading(false);
    }
  }, [activeTab, showToast]);

  useEffect(() => {
    let isMounted = true;
    (async () => {
      try {
        const res = await getDatasets(activeTab === 'archived');
        if (isMounted) {
          setDatasets(res.datasets || []);
        }
      } catch {
        if (isMounted) {
          showToast('Failed to load datasets.', 'error');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    })();

    return () => {
      isMounted = false;
    };
  }, [activeTab, showToast]);

  // File Drop & Selection Handlers
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setUploadFile(file);
      if (!uploadName) {
        setUploadName(file.name.replace(/\.[^/.]+$/, ''));
      }
      setUploadError(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (ext !== 'csv' && ext !== 'xlsx') {
        setUploadError('Only .csv and .xlsx files are supported.');
        return;
      }
      setUploadFile(file);
      if (!uploadName) {
        setUploadName(file.name.replace(/\.[^/.]+$/, ''));
      }
      setUploadError(null);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setUploadError('Please select a file to upload.');
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      await uploadDataset(uploadFile, uploadName);
      showToast(t.datasets.uploadSuccess, 'success');
      setIsUploadOpen(false);
      setUploadFile(null);
      setUploadName('');
      fetchDatasetList();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed.';
      setUploadError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const handleRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingDataset || !renameValue.trim()) return;

    setIsRenaming(true);
    try {
      await renameDataset(editingDataset.id, renameValue.trim());
      showToast('Dataset renamed successfully.', 'success');
      setEditingDataset(null);
      fetchDatasetList();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to rename.';
      showToast(msg, 'error');
    } finally {
      setIsRenaming(false);
    }
  };

  const handleArchiveToggle = async (dataset: Dataset) => {
    try {
      if (dataset.status === 'ARCHIVED') {
        await restoreDataset(dataset.id);
        showToast('Dataset restored.', 'success');
      } else {
        await archiveDataset(dataset.id);
        showToast('Dataset archived.', 'info');
      }
      fetchDatasetList();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Operation failed.';
      showToast(msg, 'error');
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deletingDataset) return;
    setIsDeleting(true);
    try {
      await deleteDataset(deletingDataset.id);
      showToast('Dataset deleted permanently.', 'success');
      setDeletingDataset(null);
      fetchDatasetList();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Deletion failed.';
      showToast(msg, 'error');
    } finally {
      setIsDeleting(false);
    }
  };

  // Filter datasets by search query
  const filteredDatasets = datasets.filter((d) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      d.name.toLowerCase().includes(q) ||
      d.original_filename.toLowerCase().includes(q) ||
      (d.feedback_column && d.feedback_column.toLowerCase().includes(q))
    );
  });

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getStatusBadge = (status: DatasetStatus) => {
    switch (status) {
      case 'READY':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-950/80 border border-emerald-800/60 text-emerald-300">
            <CheckCircle2 className="w-3 h-3" />
            <span>{t.datasets.statusReady}</span>
          </span>
        );
      case 'PROCESSING':
      case 'UPLOADING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-indigo-950/80 border border-indigo-800/60 text-indigo-300">
            <LoadingSpinner size="sm" className="w-2.5 h-2.5" />
            <span>{t.datasets.statusProcessing}</span>
          </span>
        );
      case 'ARCHIVED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-800 border border-slate-700 text-slate-300">
            <Archive className="w-3 h-3" />
            <span>{t.datasets.statusArchived}</span>
          </span>
        );
      case 'FAILED':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-rose-950/80 border border-rose-800/60 text-rose-300">
            <AlertCircle className="w-3 h-3" />
            <span>{t.datasets.statusFailed}</span>
          </span>
        );
    }
  };

  const getQualityBadge = (score: number | null | undefined) => {
    if (score === null || score === undefined) return <span className="text-slate-500 font-mono text-xs">—</span>;

    let color = 'text-emerald-400 bg-emerald-950/40 border-emerald-800/60';
    if (score < 60) color = 'text-rose-400 bg-rose-950/40 border-rose-800/60';
    else if (score < 80) color = 'text-amber-400 bg-amber-950/40 border-amber-800/60';

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border font-mono font-semibold text-xs ${color}`}>
        {score.toFixed(1)}%
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-100 tracking-tight">
            {t.datasets.title}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            {t.datasets.subtitle}
          </p>
        </div>
        <Button
          variant="primary"
          size="md"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => {
            setIsUploadOpen(true);
            setUploadError(null);
            setUploadFile(null);
            setUploadName('');
          }}
        >
          {t.datasets.uploadButton}
        </Button>
      </div>

      {/* Tabs & Search Filter */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('active')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
              activeTab === 'active'
                ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            {t.datasets.allTab}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('archived')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
              activeTab === 'archived'
                ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            {t.datasets.archivedTab}
          </button>
        </div>

        <div className="relative max-w-xs w-full">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder={t.datasets.searchPlaceholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
          />
        </div>
      </div>

      {/* Datasets Table / Cards */}
      {isLoading ? (
        <div className="py-20 flex flex-col items-center justify-center space-y-3">
          <LoadingSpinner size="lg" className="text-indigo-500" />
          <p className="text-xs text-slate-400 font-mono">Loading datasets...</p>
        </div>
      ) : filteredDatasets.length === 0 ? (
        <EmptyState
          icon={<Database className="w-6 h-6" />}
          title={
            searchQuery
              ? 'No matching datasets found'
              : activeTab === 'archived'
              ? t.datasets.noArchivedTitle
              : t.datasets.noDatasetsTitle
          }
          description={
            searchQuery
              ? 'Try modifying your search term.'
              : activeTab === 'archived'
              ? t.datasets.noArchivedDesc
              : t.datasets.noDatasetsDesc
          }
          actionLabel={
            activeTab === 'active' && !searchQuery
              ? t.datasets.uploadButton
              : undefined
          }
          onAction={
            activeTab === 'active' && !searchQuery
              ? () => setIsUploadOpen(true)
              : undefined
          }
        />
      ) : (
        <div className="border border-slate-800 rounded-xl bg-slate-900/40 overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800 text-[11px] uppercase tracking-wider font-semibold">
                <tr>
                  <th className="py-3 px-4">{t.datasets.colDataset}</th>
                  <th className="py-3 px-4">{t.datasets.colFormat}</th>
                  <th className="py-3 px-4">{t.datasets.colRows}</th>
                  <th className="py-3 px-4">{t.datasets.colColumns}</th>
                  <th className="py-3 px-4">{t.datasets.colFeedback}</th>
                  <th className="py-3 px-4">{t.datasets.colQuality}</th>
                  <th className="py-3 px-4">{t.datasets.colStatus}</th>
                  <th className="py-3 px-4 text-right">{t.datasets.colActions}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {filteredDatasets.map((d) => (
                  <tr
                    key={d.id}
                    className="hover:bg-slate-800/40 transition-colors group"
                  >
                    <td className="py-3.5 px-4 font-medium text-slate-100 max-w-xs">
                      <Link
                        href={`/dashboard/datasets/${d.id}`}
                        className="hover:text-indigo-400 transition-colors block truncate"
                        title={d.name}
                      >
                        {d.name}
                      </Link>
                      <span className="text-[10px] text-slate-500 font-mono block truncate">
                        {d.original_filename} ({formatBytes(d.file_size_bytes)})
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono">
                      <span className="inline-flex items-center gap-1 uppercase text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700 text-slate-300">
                        {d.file_type === 'csv' ? (
                          <FileText className="w-3 h-3 text-cyan-400" />
                        ) : (
                          <FileSpreadsheet className="w-3 h-3 text-emerald-400" />
                        )}
                        <span>{d.file_type}</span>
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-200">
                      {d.row_count.toLocaleString()}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-200">
                      {d.column_count}
                    </td>
                    <td className="py-3.5 px-4">
                      {d.feedback_column ? (
                        <span
                          className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-md bg-indigo-950/60 border border-indigo-800/50 text-indigo-300 truncate max-w-[140px]"
                          title={`Detected with ${(d.feedback_confidence ? d.feedback_confidence * 100 : 0).toFixed(0)}% confidence`}
                        >
                          <Sparkles className="w-2.5 h-2.5 text-indigo-400 shrink-0" />
                          <span className="truncate">{d.feedback_column}</span>
                        </span>
                      ) : (
                        <span className="text-[11px] text-slate-500 italic">None</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      {getQualityBadge(d.quality_score)}
                    </td>
                    <td className="py-3.5 px-4">
                      {getStatusBadge(d.status)}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Link href={`/dashboard/datasets/${d.id}`}>
                          <button
                            type="button"
                            className="p-1.5 rounded-md text-slate-400 hover:text-indigo-400 hover:bg-slate-800 transition-colors cursor-pointer"
                            title={t.datasets.actionView}
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </button>
                        </Link>
                        <button
                          type="button"
                          onClick={() => {
                            setEditingDataset(d);
                            setRenameValue(d.name);
                          }}
                          className="p-1.5 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors cursor-pointer"
                          title={t.datasets.actionRename}
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleArchiveToggle(d)}
                          className="p-1.5 rounded-md text-slate-400 hover:text-amber-400 hover:bg-slate-800 transition-colors cursor-pointer"
                          title={d.status === 'ARCHIVED' ? t.datasets.actionRestore : t.datasets.actionArchive}
                        >
                          {d.status === 'ARCHIVED' ? (
                            <RotateCcw className="w-3.5 h-3.5" />
                          ) : (
                            <Archive className="w-3.5 h-3.5" />
                          )}
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeletingDataset(d)}
                          className="p-1.5 rounded-md text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors cursor-pointer"
                          title={t.datasets.actionDelete}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Upload Dataset Modal */}
      <Modal
        isOpen={isUploadOpen}
        onClose={() => {
          if (!isUploading) {
            setIsUploadOpen(false);
            setUploadFile(null);
            setUploadError(null);
          }
        }}
        title={t.datasets.uploadModalTitle}
        description={t.datasets.uploadModalDesc}
        maxWidth="lg"
      >
        <form onSubmit={handleUploadSubmit} className="space-y-4">
          {uploadError && (
            <Alert variant="error" onClose={() => setUploadError(null)}>
              {uploadError}
            </Alert>
          )}

          {/* Drag & Drop Box */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
              uploadFile
                ? 'border-indigo-500 bg-indigo-950/20'
                : 'border-slate-700 hover:border-slate-500 bg-slate-900/50 hover:bg-slate-900'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".csv,.xlsx"
              className="hidden"
            />
            {uploadFile ? (
              <div className="flex flex-col items-center space-y-2">
                <div className="w-10 h-10 rounded-lg bg-indigo-600/30 border border-indigo-500/40 text-indigo-400 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div className="text-xs font-medium text-slate-100">
                  {uploadFile.name}
                </div>
                <div className="text-[11px] text-slate-400 font-mono">
                  {formatBytes(uploadFile.size)}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center space-y-2">
                <div className="w-10 h-10 rounded-lg bg-slate-800 text-slate-400 flex items-center justify-center">
                  <Upload className="w-5 h-5" />
                </div>
                <div className="text-xs font-medium text-slate-200">
                  {t.datasets.dropzonePrompt}
                </div>
                <div className="text-[10px] text-slate-500">
                  {t.datasets.dropzoneLimits}
                </div>
              </div>
            )}
          </div>

          <Input
            label={t.datasets.datasetNameLabel}
            placeholder={t.datasets.datasetNamePlaceholder}
            value={uploadName}
            onChange={(e) => setUploadName(e.target.value)}
          />

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={isUploading}
              onClick={() => setIsUploadOpen(false)}
            >
              {t.common.cancel}
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isUploading}
              loadingText={t.datasets.uploading}
              disabled={!uploadFile || isUploading}
            >
              {t.datasets.uploadButton}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Rename Modal */}
      <Modal
        isOpen={!!editingDataset}
        onClose={() => setEditingDataset(null)}
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
              onClick={() => setEditingDataset(null)}
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
        isOpen={!!deletingDataset}
        onClose={() => setDeletingDataset(null)}
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
          Dataset: <span className="font-semibold text-slate-100 font-mono">{deletingDataset?.name}</span>
        </p>
      </Modal>
    </div>
  );
}
