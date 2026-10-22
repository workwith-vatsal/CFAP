'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Sparkles,
  LayoutDashboard,
  Database,
  LineChart,
  Brain,
  Bot,
  Scale,
  FileText,
  History,
  Settings,
  User as UserIcon,
  LogOut,
  Menu,
  X,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react';
import { useAuth } from '@/lib/auth/AuthContext';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { LanguageSelector } from '@/components/ui/LanguageSelector';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const { t } = useLanguage();
  const pathname = usePathname();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/auth/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 text-slate-100">
        <LoadingSpinner size="lg" className="text-indigo-500 mb-4" />
        <p className="text-xs text-slate-400 font-mono">Loading workspace...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  interface NavItem {
    label: string;
    href: string;
    icon: React.ComponentType<{ className?: string }>;
  }

  const navItems: NavItem[] = [
    { label: t.dashboard.overview, href: '/dashboard', icon: LayoutDashboard },
    { label: t.dashboard.datasets, href: '/dashboard/datasets', icon: Database },
    { label: t.dashboard.analysis, href: '/dashboard/analysis', icon: LineChart },
    { label: t.dashboard.insights, href: '/dashboard/insights', icon: Brain },
    { label: t.dashboard.assistant, href: '/dashboard/assistant', icon: Bot },
    { label: t.dashboard.benchmarking, href: '/dashboard/benchmarking', icon: Scale },
    { label: t.dashboard.reports, href: '/dashboard/reports', icon: FileText },
    { label: t.dashboard.history, href: '/dashboard/history', icon: History },
  ];

  const secondaryNav: NavItem[] = [
    { label: t.nav.profile, href: '/profile', icon: UserIcon },
    { label: t.dashboard.settings, href: '/dashboard/settings', icon: Settings },
  ];

  if (user?.role === 'admin') {
    secondaryNav.push({
      label: 'Admin Portal',
      href: '/dashboard/admin',
      icon: ShieldAlert,
    });
  }

  const getPageTitle = (path: string): string => {
    if (path === '/dashboard') return t.dashboard.overview;
    if (path.startsWith('/dashboard/datasets')) return t.dashboard.datasets;
    if (path === '/dashboard/analysis') return t.dashboard.analysis;
    if (path === '/dashboard/insights') return `${t.dashboard.insights} & Executive BI`;
    if (path === '/dashboard/assistant') return t.dashboard.assistant;
    if (path === '/dashboard/benchmarking') return t.dashboard.benchmarking;
    if (path === '/dashboard/reports') return t.dashboard.reports;
    if (path === '/dashboard/history') return t.dashboard.history;
    if (path === '/dashboard/settings') return t.dashboard.settings;
    if (path === '/dashboard/admin') return 'Admin Portal';
    if (path === '/profile') return t.nav.profile;
    return 'Workspace';
  };

  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex flex-col w-64 border-r border-slate-800/80 bg-slate-950/90 shrink-0">
        {/* Brand */}
        <div className="h-16 flex items-center px-6 border-b border-slate-800/80">
          <Link href="/dashboard" className="flex items-center gap-2.5 group focus:outline-none">
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
        </div>

        {/* Primary Navigation */}
        <div className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            Analytics Platform
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === '/dashboard'
                ? pathname === '/dashboard'
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900'
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </Link>
            );
          })}

          <div className="pt-6 px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            Preferences
          </div>
          {secondaryNav.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900'
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>

        {/* User Card & Logout */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-900/30">
          <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800/80">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-xs font-semibold text-indigo-300 shrink-0">
                {user?.first_name?.charAt(0) || 'U'}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-medium text-slate-200 truncate">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-[10px] text-slate-400 truncate">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={() => logout()}
              className="p-1.5 rounded-md text-slate-400 hover:text-red-400 hover:bg-slate-800 transition-colors cursor-pointer"
              title={t.nav.logout}
              aria-label={t.nav.logout}
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="h-16 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md px-4 sm:px-6 lg:px-8 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-900"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="font-medium text-slate-400">{t.appName}</span>
              <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
              <span className="text-slate-100 font-semibold">
                {getPageTitle(pathname)}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <LanguageSelector />
            <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full border border-slate-800 bg-slate-900 text-[11px] text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>{user?.role?.toUpperCase() || 'USER'}</span>
            </div>
          </div>
        </header>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-b border-slate-800 bg-slate-950 p-4 space-y-1">
            {[...navItems, ...secondaryNav].map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === '/dashboard'
                  ? pathname === '/dashboard'
                  : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium ${
                    isActive
                      ? 'bg-indigo-600/15 text-indigo-400'
                      : 'text-slate-400 hover:bg-slate-900'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
            <button
              onClick={() => logout()}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium text-red-400 hover:bg-slate-900 text-left mt-2"
            >
              <LogOut className="w-4 h-4" />
              <span>{t.nav.logout}</span>
            </button>
          </div>
        )}

        {/* Main Body */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
