'use client';

import React, { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { AssistantView } from '@/components/assistant/AssistantView';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

function AssistantContent() {
  const searchParams = useSearchParams();
  const datasetIdParam = searchParams.get('datasetId');
  const analysisIdParam = searchParams.get('analysisId');

  const datasetId = datasetIdParam ? parseInt(datasetIdParam, 10) : undefined;
  const analysisId = analysisIdParam ? parseInt(analysisIdParam, 10) : undefined;

  return (
    <AssistantView
      initialDatasetId={datasetId}
      initialAnalysisId={analysisId}
    />
  );
}

export default function AssistantPage() {
  return (
    <Suspense
      fallback={
        <div className="py-24 flex flex-col items-center justify-center space-y-3">
          <LoadingSpinner size="lg" className="text-indigo-500" />
          <p className="text-xs text-slate-400 font-mono">
            Loading AI Assistant...
          </p>
        </div>
      }
    >
      <AssistantContent />
    </Suspense>
  );
}
