'use client';

import React, { useEffect, useState } from 'react';
import {
  Filter,
  Eye,
  CheckCircle,
  XCircle,
  Shield,
} from 'lucide-react';
import { adminApi } from '@/lib/api/admin';
import { AdminAuditLogListItem } from '@/types';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export function AdminAuditLogsTable() {
  const [logs, setLogs] = useState<AdminAuditLogListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState('');
  const [resourceFilter, setResourceFilter] = useState('');
  const [selectedLog, setSelectedLog] = useState<AdminAuditLogListItem | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadLogs() {
      try {
        const res = await adminApi.listAuditLogs({
          page,
          limit: 20,
          action: actionFilter || undefined,
          resource_type: resourceFilter || undefined,
        });
        if (isMounted) {
          setLogs(res.items || []);
          setTotal(res.total || 0);
          setLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          console.error('Failed to load audit logs:', err);
          setLoading(false);
        }
      }
    }
    loadLogs();
    return () => {
      isMounted = false;
    };
  }, [page, actionFilter, resourceFilter]);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setPage(1);
            }}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Actions</option>
            <option value="LOGIN_SUCCESS">LOGIN_SUCCESS</option>
            <option value="LOGIN_FAILURE">LOGIN_FAILURE</option>
            <option value="DATASET_CREATED">DATASET_CREATED</option>
            <option value="DATASET_DELETED">DATASET_DELETED</option>
            <option value="ANALYSIS_STARTED">ANALYSIS_STARTED</option>
            <option value="REPORT_GENERATED">REPORT_GENERATED</option>
            <option value="BENCHMARK_ACCESS">BENCHMARK_ACCESS</option>
            <option value="ACCOUNT_ACTIVATED">ACCOUNT_ACTIVATED</option>
            <option value="ACCOUNT_DEACTIVATED">ACCOUNT_DEACTIVATED</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={resourceFilter}
            onChange={(e) => {
              setResourceFilter(e.target.value);
              setPage(1);
            }}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Resource Types</option>
            <option value="auth">Auth</option>
            <option value="user">User</option>
            <option value="dataset">Dataset</option>
            <option value="analysis">Analysis</option>
            <option value="report">Report</option>
            <option value="benchmark">Benchmark</option>
          </select>
        </div>
      </div>

      {/* Audit Log Table */}
      <Card className="border-slate-800 bg-slate-900/60 overflow-hidden">
        {loading ? (
          <div className="py-16 flex flex-col items-center justify-center text-slate-400">
            <LoadingSpinner size="md" className="text-indigo-500 mb-2" />
            <p className="text-xs font-mono">Loading security audit records...</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Resource</th>
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500">
                      No audit events recorded matching current filters.
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-800/20 transition-colors">
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 font-mono font-semibold text-slate-200">
                        {log.action}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] uppercase font-mono bg-slate-800 text-slate-300">
                          {log.resource_type} {log.resource_id ? `#${log.resource_id}` : ''}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-300">
                        {log.user_email || <span className="text-slate-500 italic">System</span>}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 text-[11px] font-medium ${
                            log.status === 'SUCCESS' ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {log.status === 'SUCCESS' ? (
                            <CheckCircle className="w-3.5 h-3.5" />
                          ) : (
                            <XCircle className="w-3.5 h-3.5" />
                          )}
                          {log.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        {log.metadata_json ? (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setSelectedLog(log)}
                            className="text-indigo-400 hover:text-indigo-300 p-1"
                            title="Inspect Metadata"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                        ) : (
                          <span className="text-slate-600 text-[10px]">—</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/40 flex items-center justify-between text-xs text-slate-400">
          <span>
            Total: <strong className="text-slate-200">{total}</strong> events
          </span>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="ghost"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <span className="font-mono text-slate-300">Page {page}</span>
            <Button
              size="sm"
              variant="ghost"
              disabled={logs.length < 20 || page * 20 >= total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      </Card>

      {/* Metadata Inspector Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="max-w-lg w-full p-6 border-slate-800 bg-slate-900 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Shield className="w-4 h-4 text-indigo-400" />
                <span>Audit Log #{selectedLog.id} Metadata</span>
              </h3>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Action:</span>
                <span className="font-mono font-semibold text-white">{selectedLog.action}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Resource:</span>
                <span className="font-mono text-slate-200">
                  {selectedLog.resource_type} {selectedLog.resource_id ? `(#${selectedLog.resource_id})` : ''}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Actor Email:</span>
                <span className="text-slate-200">{selectedLog.user_email || 'System'}</span>
              </div>
              {selectedLog.ip_hash && (
                <div className="flex justify-between">
                  <span className="text-slate-400">IP Hash (SHA-256):</span>
                  <span className="font-mono text-[10px] text-slate-400">{selectedLog.ip_hash.slice(0, 16)}...</span>
                </div>
              )}
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Sanitized Payload
              </label>
              <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto">
                {JSON.stringify(selectedLog.metadata_json, null, 2)}
              </pre>
            </div>

            <div className="pt-2 flex justify-end">
              <Button size="sm" variant="secondary" onClick={() => setSelectedLog(null)}>
                Close
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
