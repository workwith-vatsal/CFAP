'use client';

import React from 'react';
import Link from 'next/link';
import { Globe, Shield, ArrowRight } from 'lucide-react';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { LanguageSelector } from '@/components/ui/LanguageSelector';

export default function SettingsPage() {
  const { t } = useLanguage();

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-xl font-bold text-slate-100 tracking-tight">
          {t.dashboard.settings}
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Platform configurations, preferences, and account controls.
        </p>
      </div>

      <div className="space-y-4">
        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-slate-400">
              <Globe className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100">
                {t.profile.languagePref}
              </h3>
              <p className="text-xs text-slate-400">
                {t.profile.languageDesc}
              </p>
            </div>
          </div>
          <LanguageSelector />
        </div>

        <Link
          href="/profile"
          className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 hover:border-slate-700 transition-colors flex items-center justify-between group block"
        >
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-indigo-400 group-hover:scale-105 transition-transform">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100">
                {t.profile.securitySettings}
              </h3>
              <p className="text-xs text-slate-400">
                Update account password and manage security preferences.
              </p>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 transition-colors" />
        </Link>
      </div>
    </div>
  );
}
