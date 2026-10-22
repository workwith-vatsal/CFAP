'use client';

import React from 'react';
import Link from 'next/link';
import { Sparkles, ArrowRight } from 'lucide-react';
import { useAuth } from '@/lib/auth/AuthContext';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { Button } from '@/components/ui/Button';
import { LanguageSelector } from '@/components/ui/LanguageSelector';

export function Navbar() {
  const { isAuthenticated } = useAuth();
  const { t } = useLanguage();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 group focus:outline-none">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shadow-md shadow-indigo-600/20 group-hover:bg-indigo-500 transition-colors">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-bold tracking-tight text-white font-mono leading-none">
              {t.appName}
            </span>
            <span className="text-[8px] uppercase tracking-widest text-slate-400 font-medium">
              Cognitive Analytics
            </span>
          </div>
        </Link>

        <nav className="hidden md:flex items-center gap-8 text-xs font-medium text-slate-300">
          <a href="#features" className="hover:text-white transition-colors">
            {t.nav.features}
          </a>
          <a href="#workflow" className="hover:text-white transition-colors">
            {t.nav.howItWorks}
          </a>
          <a href="#security" className="hover:text-white transition-colors">
            {t.nav.security}
          </a>
        </nav>

        <div className="flex items-center gap-4">
          <LanguageSelector />
          {isAuthenticated ? (
            <Link href="/dashboard">
              <Button size="sm" variant="primary" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                {t.nav.dashboard}
              </Button>
            </Link>
          ) : (
            <div className="flex items-center gap-2.5">
              <Link href="/auth/login">
                <Button size="sm" variant="ghost">
                  {t.nav.signIn}
                </Button>
              </Link>
              <Link href="/auth/register">
                <Button size="sm" variant="primary">
                  {t.nav.getStarted}
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
