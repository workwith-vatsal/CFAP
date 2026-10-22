'use client';

import React from 'react';
import { Globe } from 'lucide-react';
import { useLanguage } from '@/lib/i18n/LanguageContext';

export function LanguageSelector({ className = '' }: { className?: string }) {
  const { language, setLanguage } = useLanguage();

  return (
    <div className={`flex items-center gap-1.5 text-xs text-slate-400 ${className}`}>
      <Globe className="w-3.5 h-3.5 text-slate-400 shrink-0" />
      <div className="flex bg-slate-900 border border-slate-700/80 rounded-lg p-0.5 shadow-sm">
        <button
          type="button"
          onClick={() => setLanguage('en')}
          className={`px-2 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer ${
            language === 'en'
              ? 'bg-indigo-600 text-white shadow-xs'
              : 'text-slate-400 hover:text-slate-200'
          }`}
          aria-label="Switch to English"
        >
          EN
        </button>
        <button
          type="button"
          onClick={() => setLanguage('hi')}
          className={`px-2 py-1 rounded-md text-xs font-medium transition-colors cursor-pointer ${
            language === 'hi'
              ? 'bg-indigo-600 text-white shadow-xs'
              : 'text-slate-400 hover:text-slate-200'
          }`}
          aria-label="Switch to Hindi"
        >
          हिन्दी
        </button>
      </div>
    </div>
  );
}
