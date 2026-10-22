'use client';

import React from 'react';
import Link from 'next/link';
import { Sparkles } from 'lucide-react';
import { LanguageSelector } from '@/components/ui/LanguageSelector';

interface AuthCardProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export function AuthCard({ title, subtitle, children, footer }: AuthCardProps) {
  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-slate-950 text-slate-100 relative overflow-hidden">
      {/* Background glow gradient */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Header / Language Switcher */}
      <div className="absolute top-6 right-6 z-10">
        <LanguageSelector />
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md z-10">
        <Link
          href="/"
          className="flex items-center justify-center gap-2.5 mb-6 group focus:outline-none"
        >
          <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center shadow-md shadow-indigo-600/20 group-hover:bg-indigo-500 transition-colors">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-xl font-bold tracking-tight text-white font-mono">
              CFAP
            </span>
            <span className="text-[9px] uppercase tracking-widest text-slate-400 font-medium -mt-1">
              Cognitive Analytics
            </span>
          </div>
        </Link>
        <h2 className="text-center text-xl font-bold tracking-tight text-slate-100">
          {title}
        </h2>
        <p className="mt-1 text-center text-xs text-slate-400 max-w-xs mx-auto">
          {subtitle}
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0 z-10">
        <div className="bg-slate-900/90 border border-slate-800 py-8 px-6 sm:px-8 shadow-xl rounded-2xl backdrop-blur-xs">
          {children}
        </div>
        {footer && <div className="mt-6 text-center text-xs">{footer}</div>}
      </div>
    </div>
  );
}
