'use client';

import React from 'react';
import {
  Users,
  Database,
  LineChart,
  FileText,
  Server,
  Activity,
  CheckCircle2,
} from 'lucide-react';
import { AdminSystemOverviewResponse } from '@/types';
import { Card } from '@/components/ui/Card';

interface AdminOverviewViewProps {
  data: AdminSystemOverviewResponse | null;
}

export function AdminOverviewView({ data }: AdminOverviewViewProps) {
  if (!data) return null;

  return (
    <div className="space-y-6">
      {/* Top Level Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-slate-900/70 border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Registered Users</span>
            <Users className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {data.total_users.toLocaleString()}
          </div>
          <div className="flex items-center gap-3 mt-2 text-[11px] text-slate-400">
            <span className="text-emerald-400 font-medium">{data.active_users} active</span>
            <span>•</span>
            <span>{data.verified_users} verified</span>
            <span>•</span>
            <span className="text-indigo-400">{data.admin_users} admins</span>
          </div>
        </Card>

        <Card className="p-4 bg-slate-900/70 border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Total Datasets</span>
            <Database className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {data.total_datasets.toLocaleString()}
          </div>
          <div className="mt-2 text-[11px] text-slate-400">
            <span className="text-slate-300 font-mono font-medium">{data.total_dataset_rows.toLocaleString()}</span> total rows ingested
          </div>
        </Card>

        <Card className="p-4 bg-slate-900/70 border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Analysis Runs</span>
            <LineChart className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {data.total_analyses.toLocaleString()}
          </div>
          <div className="flex items-center gap-3 mt-2 text-[11px] text-slate-400">
            <span className="text-emerald-400 font-medium">{data.completed_analyses} completed</span>
            {data.failed_analyses > 0 && (
              <>
                <span>•</span>
                <span className="text-rose-400">{data.failed_analyses} failed</span>
              </>
            )}
          </div>
        </Card>

        <Card className="p-4 bg-slate-900/70 border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Reports Generated</span>
            <FileText className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {data.total_reports.toLocaleString()}
          </div>
          <div className="mt-2 text-[11px] text-emerald-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>PDF Engine Active</span>
          </div>
        </Card>
      </div>

      {/* Operational Health & Activity Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Health */}
        <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
              System Health & Infrastructure
            </h3>
            <Server className="w-4 h-4 text-indigo-400" />
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <span className="text-slate-300">Backend API Services</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Operational
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <span className="text-slate-300">PostgreSQL Database</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Connected
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <span className="text-slate-300">AI / NLP Model Stack</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Ready (BERT + SHAP)
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <span className="text-slate-300">Data Governance & Isolation</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Enforced (Tenant Partitioning)
              </span>
            </div>
          </div>
        </Card>

        {/* Recent Audit Activity */}
        <Card className="p-5 bg-slate-900/70 border-slate-800 lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
              Recent Security & Operational Audit Log
            </h3>
            <Activity className="w-4 h-4 text-indigo-400" />
          </div>

          <div className="divide-y divide-slate-800/60 text-xs">
            {data.recent_activities.length === 0 ? (
              <div className="py-6 text-center text-slate-500">No recent audit activity.</div>
            ) : (
              data.recent_activities.map((act) => (
                <div key={act.id} className="py-2.5 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2.5 overflow-hidden">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold shrink-0 ${
                        act.status === 'SUCCESS'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}
                    >
                      {act.action}
                    </span>
                    <span className="text-slate-300 truncate">{act.user_email}</span>
                  </div>
                  <span className="text-[11px] text-slate-400 shrink-0 font-mono">
                    {new Date(act.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
