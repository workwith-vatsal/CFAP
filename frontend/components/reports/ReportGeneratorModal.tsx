'use client';

import React, { useEffect, useState } from 'react';
import {
  FileText,
  BarChart3,
  Check,
  Sparkles,
  AlertCircle,
  Loader2,
  Layers,
} from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { ReportType } from '@/types/report';
import { Dataset } from '@/types/dataset';
import { getDatasets } from '@/lib/api/datasets';
import { analysisApi } from '@/lib/api/analysis';
import { reportsApi } from '@/lib/api/reports';

interface ReportGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onReportCreated?: () => void;
  initialDatasetId?: number;
  initialAnalysisId?: number;
}

const REPORT_TYPE_CONFIGS: Record<
  string,
  {
    title: string;
    description: string;
    icon: React.ReactNode;
    sections: string[];
  }
> = {
  FULL: {
    title: 'Full Intelligence Report',
    description: 'Comprehensive 360° analytics including deep cross-dimensional matrices, SHAP explainability, and AI assistant highlights.',
    icon: <Layers className="w-5 h-5 text-indigo-600" />,
    sections: [
      'Cover & Dataset Metadata',
      'Executive Summary & KPIs',
      'Dataset Validation & Data Quality Foundation',
      'AI/NLP Pipeline Architecture & Methodology',
      'Sentiment Analysis & Polarity Distribution',
      'Discrete Emotion Spectrum (7 Emotions)',
      'Discovered Topic Clusters & Semantic Groupings',
      'Cross-Dimensional Analytics (Sentiment × Emotion, Sentiment × Topic)',
      'Temporal Analytics & Volume Trends (if available)',
      'Categorical Dimension Breakdowns (if available)',
      'Deterministic Strategic Insights & Recommendations',
      'SHAP Model Explainability & Feature Attribution',
      'Grounded AI Assistant Highlights',
    ],
  },
  EXECUTIVE: {
    title: 'Executive Summary Brief',
    description: 'High-level decision briefing designed for leadership, focusing on core KPIs, brand health, and strategic recommendations.',
    icon: <Sparkles className="w-5 h-5 text-purple-600" />,
    sections: [
      'Cover & Dataset Metadata',
      'Executive Summary & 4 Key KPI Cards',
      'High-Level Feedback Distribution Visualizations',
      'Key Analytical Findings & Strategic Recommendations',
      'Dataset & Data Quality Summary',
      'Governance & Non-Causal Analytics Disclaimer',
    ],
  },
  ANALYSIS: {
    title: 'Deep Analytical Report',
    description: 'Detailed technical report focusing on topic distributions, discrete emotion breakdowns, and model explainability.',
    icon: <BarChart3 className="w-5 h-5 text-blue-600" />,
    sections: [
      'Cover & Dataset Metadata',
      'Executive Summary & Core Metrics',
      'Sentiment Analysis & Polarity Distribution',
      'Discrete Emotion Spectrum & Breakdown',
      'Discovered Topic Clusters & Outlier Analysis',
      'Cross-Dimensional Correlation Matrices',
      'Temporal & Categorical Dimension Analytics',
      'SHAP Model Attribution & Feature Weights',
    ],
  },
};

export const ReportGeneratorModal: React.FC<ReportGeneratorModalProps> = ({
  isOpen,
  onClose,
  onReportCreated,
  initialDatasetId,
  initialAnalysisId,
}) => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | ''>(initialDatasetId || '');
  const [analysisId, setAnalysisId] = useState<number | null>(initialAnalysisId || null);
  const [selectedType, setSelectedType] = useState<ReportType>('FULL');

  const [loadingDatasets, setLoadingDatasets] = useState(false);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    let isMounted = true;

    async function initializeModal() {
      try {
        setLoadingDatasets(true);
        setError(null);
        const res = await getDatasets(false);
        const readyDatasets = (res.datasets || []).filter((d) => d.status === 'READY');
        if (!isMounted) return;
        setDatasets(readyDatasets);

        const targetId = initialDatasetId || (readyDatasets.length > 0 ? readyDatasets[0].id : null);
        if (targetId) {
          setSelectedDatasetId(targetId);
          if (initialAnalysisId) {
            setAnalysisId(initialAnalysisId);
          } else {
            setLoadingAnalysis(true);
            try {
              const analysis = await analysisApi.getLatestAnalysis(targetId);
              if (isMounted && analysis && (analysis.status.toLowerCase() === 'completed' || (analysis.status as string) === 'COMPLETED')) {
                setAnalysisId(analysis.id);
              } else if (isMounted) {
                setAnalysisId(null);
                setError('No completed AI analysis found for this dataset. Please run analysis first.');
              }
            } catch {
              if (isMounted) {
                setAnalysisId(null);
                setError('No completed analysis found for the selected dataset.');
              }
            } finally {
              if (isMounted) setLoadingAnalysis(false);
            }
          }
        }
      } catch {
        if (isMounted) setError('Failed to load datasets.');
      } finally {
        if (isMounted) setLoadingDatasets(false);
      }
    }

    initializeModal();
    return () => {
      isMounted = false;
    };
  }, [isOpen, initialDatasetId, initialAnalysisId]);

  const handleDatasetChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = Number(e.target.value);
    setSelectedDatasetId(val);
    if (!val) {
      setAnalysisId(null);
      return;
    }

    try {
      setLoadingAnalysis(true);
      setError(null);
      const analysis = await analysisApi.getLatestAnalysis(val);
      if (analysis && (analysis.status.toLowerCase() === 'completed' || (analysis.status as string) === 'COMPLETED')) {
        setAnalysisId(analysis.id);
      } else {
        setAnalysisId(null);
        setError('No completed AI analysis found for this dataset. Please run analysis first.');
      }
    } catch {
      setAnalysisId(null);
      setError('No completed analysis found for the selected dataset.');
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const handleGenerate = async () => {
    if (!selectedDatasetId || !analysisId) {
      setError('Please select a dataset with a completed analysis.');
      return;
    }

    try {
      setGenerating(true);
      setError(null);
      await reportsApi.createReport({
        dataset_id: Number(selectedDatasetId),
        analysis_id: analysisId,
        report_type: selectedType,
      });

      if (onReportCreated) onReportCreated();
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to generate report.';
      setError(msg);
    } finally {
      setGenerating(false);
    }
  };

  const currentConfig = REPORT_TYPE_CONFIGS[selectedType.toUpperCase()] || REPORT_TYPE_CONFIGS.FULL;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Generate Intelligence Report">
      <div className="space-y-6">
        {/* Error Notification */}
        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Dataset Selector */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-1.5">
            Select Dataset
          </label>
          <select
            value={selectedDatasetId}
            onChange={handleDatasetChange}
            disabled={loadingDatasets || generating}
            className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 text-slate-100 rounded-lg focus:outline-none focus:border-indigo-500 disabled:opacity-50 cursor-pointer"
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.row_count} rows)
              </option>
            ))}
          </select>
          {loadingAnalysis && (
            <p className="text-xs text-slate-400 mt-1 flex items-center gap-1.5 font-mono">
              <Loader2 className="w-3 h-3 animate-spin text-indigo-400" /> Verifying completed analysis...
            </p>
          )}
          {analysisId && !loadingAnalysis && (
            <p className="text-xs text-emerald-400 mt-1 font-medium flex items-center gap-1">
              ✓ Verified Analysis #{analysisId} (Ready for reporting)
            </p>
          )}
        </div>

        {/* Report Type Selector Cards */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
            Choose Report Template
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {(['FULL', 'EXECUTIVE', 'ANALYSIS'] as ReportType[]).map((typeKey) => {
              const cfg = REPORT_TYPE_CONFIGS[typeKey];
              const isSelected = selectedType.toUpperCase() === typeKey;
              return (
                <button
                  key={typeKey}
                  type="button"
                  onClick={() => setSelectedType(typeKey)}
                  className={`text-left p-3.5 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'border-indigo-500 bg-indigo-950/40 shadow-sm ring-1 ring-indigo-500/50'
                      : 'border-slate-800 hover:border-slate-700 bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1.5">
                    {cfg.icon}
                    <span className="font-semibold text-xs text-slate-100">{cfg.title}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    {cfg.description}
                  </p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Included Sections Preview */}
        <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Included Report Sections ({currentConfig.sections.length})
            </span>
            <span className="text-[10px] text-slate-500 font-mono">Auto-formatted PDF Flowables</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-1.5">
            {currentConfig.sections.map((sec, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs text-slate-300">
                <Check className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                <span className="truncate">{sec}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Observational Notice */}
        <div className="p-3 bg-amber-950/40 border border-amber-500/30 rounded-lg text-[11px] text-amber-300 leading-relaxed">
          <b>Governance Note:</b> Reports are strictly observational and non-causal. Server-side PDF generation compiles verified outputs from Phases 3–6 with zero artificial recalculations.
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
          <button
            type="button"
            onClick={onClose}
            disabled={generating}
            className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={generating || !analysisId}
            className="inline-flex items-center gap-2 px-5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-sm transition-colors disabled:opacity-50 cursor-pointer"
          >
            {generating ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Generating Report...
              </>
            ) : (
              <>
                <FileText className="w-3.5 h-3.5" />
                Generate PDF Report
              </>
            )}
          </button>
        </div>
      </div>
    </Modal>
  );
};
