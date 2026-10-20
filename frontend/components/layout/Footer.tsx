'use client';

import React from 'react';
import { Sparkles, ShieldCheck, Lock } from 'lucide-react';
import { useLanguage } from '@/lib/i18n/LanguageContext';

export function Footer() {
  const { t } = useLanguage();

  return (
    <footer className="border-t border-slate-800/80 bg-slate-950 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6 text-xs text-slate-500">
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-md bg-indigo-600 flex items-center justify-center">
            <Sparkles className="w-3 h-3 text-white" />
          </div>
          <span className="font-semibold text-slate-300 font-mono">
            {t.appName}
          </span>
          <span className="text-slate-600">|</span>
          <span>{t.footer.rights}</span>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-1.5 text-slate-400">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>{t.footer.enterpriseGrade}</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400">
            <Lock className="w-3.5 h-3.5 text-indigo-400" />
            <span>{t.footer.isolatedTenancy}</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
