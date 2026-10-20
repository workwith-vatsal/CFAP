'use client';

import React from 'react';
import Link from 'next/link';
import {
  Sparkles,
  ArrowRight,
  Brain,
  Layers,
  Search,
  BarChart3,
  ShieldCheck,
  Lock,
  Upload,
  Cpu,
  FileCheck2,
  Share2,
} from 'lucide-react';
import { useAuth } from '@/lib/auth/AuthContext';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { Button } from '@/components/ui/Button';
import { LanguageSelector } from '@/components/ui/LanguageSelector';

export default function LandingPage() {
  const { isAuthenticated } = useAuth();
  const { t } = useLanguage();

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white">
      {/* Navigation Bar */}
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

      {/* Hero Section */}
      <section className="relative pt-24 pb-20 md:pt-32 md:pb-28 overflow-hidden">
        {/* Background glow effects */}
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-1/2 right-1/4 w-[400px] h-[400px] bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-indigo-500/30 bg-indigo-950/40 text-indigo-300 text-xs font-medium mb-6 shadow-xs">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>{t.landing.heroBadge}</span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-white leading-tight mb-6">
            {t.landing.heroTitlePrefix}{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-cyan-400 to-emerald-400">
              {t.landing.heroTitleHighlight}
            </span>
          </h1>

          <p className="text-base sm:text-lg text-slate-300 max-w-3xl mx-auto mb-10 leading-relaxed font-normal">
            {t.landing.heroSubtitle}
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href={isAuthenticated ? '/dashboard' : '/auth/register'}>
              <Button size="lg" variant="primary" rightIcon={<ArrowRight className="w-4 h-4" />}>
                {isAuthenticated ? t.nav.dashboard : t.landing.primaryCta}
              </Button>
            </Link>
            <a href="#features">
              <Button size="lg" variant="secondary">
                {t.landing.secondaryCta}
              </Button>
            </a>
          </div>
        </div>
      </section>

      {/* Intelligence Pillars Section */}
      <section id="features" className="py-20 border-t border-slate-900 bg-slate-950/60 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-3">
              {t.landing.pillarsTitle}
            </h2>
            <p className="text-sm text-slate-400 leading-relaxed">
              {t.landing.pillarsSubtitle}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all group">
              <div className="w-10 h-10 rounded-xl bg-indigo-950/80 border border-indigo-800/60 flex items-center justify-center text-indigo-400 mb-4 group-hover:scale-105 transition-transform">
                <Brain className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-slate-100 mb-2">
                {t.landing.pillar1Title}
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                {t.landing.pillar1Desc}
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all group">
              <div className="w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-800/60 flex items-center justify-center text-cyan-400 mb-4 group-hover:scale-105 transition-transform">
                <Layers className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-slate-100 mb-2">
                {t.landing.pillar2Title}
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                {t.landing.pillar2Desc}
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all group">
              <div className="w-10 h-10 rounded-xl bg-emerald-950/80 border border-emerald-800/60 flex items-center justify-center text-emerald-400 mb-4 group-hover:scale-105 transition-transform">
                <Search className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-slate-100 mb-2">
                {t.landing.pillar3Title}
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                {t.landing.pillar3Desc}
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all group">
              <div className="w-10 h-10 rounded-xl bg-violet-950/80 border border-violet-800/60 flex items-center justify-center text-violet-400 mb-4 group-hover:scale-105 transition-transform">
                <BarChart3 className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-slate-100 mb-2">
                {t.landing.pillar4Title}
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                {t.landing.pillar4Desc}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Workflow Section */}
      <section id="workflow" className="py-20 border-t border-slate-900 bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-3">
              {t.landing.workflowTitle}
            </h2>
            <p className="text-sm text-slate-400 leading-relaxed">
              {t.landing.workflowSubtitle}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
            <div className="p-6 rounded-2xl border border-slate-800/80 bg-slate-900/30">
              <div className="w-8 h-8 rounded-lg bg-indigo-600/20 text-indigo-400 flex items-center justify-center mb-3 text-xs font-bold">
                <Upload className="w-4 h-4" />
              </div>
              <h4 className="text-sm font-semibold text-slate-100 mb-1.5">
                {t.landing.step1Title}
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                {t.landing.step1Desc}
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-slate-800/80 bg-slate-900/30">
              <div className="w-8 h-8 rounded-lg bg-cyan-600/20 text-cyan-400 flex items-center justify-center mb-3 text-xs font-bold">
                <Cpu className="w-4 h-4" />
              </div>
              <h4 className="text-sm font-semibold text-slate-100 mb-1.5">
                {t.landing.step2Title}
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                {t.landing.step2Desc}
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-slate-800/80 bg-slate-900/30">
              <div className="w-8 h-8 rounded-lg bg-emerald-600/20 text-emerald-400 flex items-center justify-center mb-3 text-xs font-bold">
                <FileCheck2 className="w-4 h-4" />
              </div>
              <h4 className="text-sm font-semibold text-slate-100 mb-1.5">
                {t.landing.step3Title}
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                {t.landing.step3Desc}
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-slate-800/80 bg-slate-900/30">
              <div className="w-8 h-8 rounded-lg bg-violet-600/20 text-violet-400 flex items-center justify-center mb-3 text-xs font-bold">
                <Share2 className="w-4 h-4" />
              </div>
              <h4 className="text-sm font-semibold text-slate-100 mb-1.5">
                {t.landing.step4Title}
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                {t.landing.step4Desc}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Security Section */}
      <section id="security" className="py-20 border-t border-slate-900 bg-slate-950/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-14">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-3">
              {t.landing.securityTitle}
            </h2>
            <p className="text-sm text-slate-400 leading-relaxed">
              {t.landing.securitySubtitle}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div className="flex gap-4 p-6 rounded-2xl border border-slate-800 bg-slate-900/40">
              <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-emerald-400 shrink-0">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-100 mb-1">
                  {t.landing.sec1Title}
                </h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {t.landing.sec1Desc}
                </p>
              </div>
            </div>

            <div className="flex gap-4 p-6 rounded-2xl border border-slate-800 bg-slate-900/40">
              <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-indigo-400 shrink-0">
                <Lock className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-100 mb-1">
                  {t.landing.sec2Title}
                </h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {t.landing.sec2Desc}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="py-20 border-t border-slate-900 bg-gradient-to-b from-slate-950 to-indigo-950/20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white mb-4">
            {t.landing.ctaBannerTitle}
          </h2>
          <p className="text-sm text-slate-300 mb-8 max-w-xl mx-auto">
            {t.landing.ctaBannerSubtitle}
          </p>
          <Link href={isAuthenticated ? '/dashboard' : '/auth/register'}>
            <Button size="lg" variant="primary" rightIcon={<ArrowRight className="w-4 h-4" />}>
              {isAuthenticated ? t.nav.dashboard : t.landing.ctaBannerButton}
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-900 py-8 bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span className="font-mono font-bold text-slate-400">{t.appName}</span>
            <span>—</span>
            <span>{t.appFullName}</span>
          </div>
          <div>© {new Date().getFullYear()} CFAP Platform. All rights reserved.</div>
        </div>
      </footer>
    </div>
  );
}
