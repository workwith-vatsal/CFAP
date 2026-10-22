'use client';

import React, { useEffect, useState } from 'react';
import {
  ShieldAlert,
  Users,
  Activity,
  LayoutDashboard,
  Lock,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '@/lib/auth/AuthContext';
import { adminApi } from '@/lib/api/admin';
import { AdminSystemOverviewResponse } from '@/types';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { AdminOverviewView } from './AdminOverviewView';
import { AdminUsersTable } from './AdminUsersTable';
import { AdminAuditLogsTable } from './AdminAuditLogsTable';

type AdminTab = 'overview' | 'users' | 'audit_logs';

export function AdminHubView() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<AdminTab>('overview');
  const [overviewData, setOverviewData] = useState<AdminSystemOverviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOverview = async () => {
    if (user?.role !== 'admin') return;
    try {
      setLoading(true);
      setError(null);
      const res = await adminApi.getOverview();
      setOverviewData(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load system overview.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    if (user?.role !== 'admin') return;

    async function loadData() {
      try {
        const res = await adminApi.getOverview();
        if (isMounted) {
          setOverviewData(res);
          setLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to load system overview.');
          setLoading(false);
        }
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [user]);

  // Client-side role gate (backend enforces independently)
  if (user && user.role !== 'admin') {
    return (
      <div className="py-16 max-w-lg mx-auto text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mx-auto">
          <Lock className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-bold text-white tracking-tight">
          Admin Access Restricted
        </h2>
        <p className="text-xs text-slate-400 leading-relaxed">
          You do not have administrative privileges to access this area. If you require access, please contact your platform administrator.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Admin Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 text-xs font-mono font-medium uppercase tracking-wider mb-1">
            <ShieldAlert className="w-4 h-4" />
            <span>Administrator Control Center</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Platform Administration & Audit
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Monitor system operations, manage user accounts, and review security audit trails with strict privacy boundaries.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="secondary"
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
            onClick={fetchOverview}
            disabled={loading}
          >
            Refresh Metrics
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-colors cursor-pointer ${
            activeTab === 'overview'
              ? 'border-indigo-500 text-indigo-400 font-semibold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <LayoutDashboard className="w-4 h-4" />
          <span>System Overview</span>
        </button>

        <button
          onClick={() => setActiveTab('users')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-colors cursor-pointer ${
            activeTab === 'users'
              ? 'border-indigo-500 text-indigo-400 font-semibold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>User Management</span>
        </button>

        <button
          onClick={() => setActiveTab('audit_logs')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-colors cursor-pointer ${
            activeTab === 'audit_logs'
              ? 'border-indigo-500 text-indigo-400 font-semibold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>Audit Logs</span>
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === 'overview' && (
        loading && !overviewData ? (
          <div className="py-20 flex flex-col items-center justify-center text-slate-400">
            <LoadingSpinner size="lg" className="text-indigo-500 mb-3" />
            <p className="text-xs font-mono">Loading system metrics...</p>
          </div>
        ) : (
          <AdminOverviewView data={overviewData} />
        )
      )}

      {activeTab === 'users' && <AdminUsersTable />}

      {activeTab === 'audit_logs' && <AdminAuditLogsTable />}
    </div>
  );
}
