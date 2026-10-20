'use client';

import React, { useEffect, useState } from 'react';
import {
  Search,
  Filter,
  CheckCircle,
  XCircle,
  AlertTriangle,
} from 'lucide-react';
import { adminApi } from '@/lib/api/admin';
import { useAuth } from '@/lib/auth/AuthContext';
import { AdminUserListItem } from '@/types';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export function AdminUsersTable() {
  const { user: currentAdmin } = useAuth();
  const [users, setUsers] = useState<AdminUserListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setActionError(null);
      const res = await adminApi.listUsers({
        page,
        limit: 15,
        search: search.trim() || undefined,
        role: roleFilter || undefined,
      });
      setUsers(res.items || []);
      setTotal(res.total || 0);
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to fetch users.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        const res = await adminApi.listUsers({
          page,
          limit: 15,
          search: search.trim() || undefined,
          role: roleFilter || undefined,
        });
        if (isMounted) {
          setUsers(res.items || []);
          setTotal(res.total || 0);
          setLoading(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setActionError(err instanceof Error ? err.message : 'Failed to fetch users.');
          setLoading(false);
        }
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, [page, roleFilter, search]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchUsers();
  };

  const handleToggleStatus = async (targetUser: AdminUserListItem) => {
    if (targetUser.id === currentAdmin?.id && targetUser.is_active) {
      setActionError('Administrators cannot deactivate their own account.');
      return;
    }

    try {
      setActionLoadingId(targetUser.id);
      setActionError(null);
      const updated = await adminApi.updateUserStatus(targetUser.id, !targetUser.is_active);
      setUsers((prev) =>
        prev.map((u) => (u.id === updated.id ? { ...u, is_active: updated.is_active } : u))
      );
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to update user status.');
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <div className="space-y-4">
      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 max-w-sm w-full">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <Button type="submit" size="sm" variant="secondary">
            Search
          </Button>
        </form>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={roleFilter}
            onChange={(e) => {
              setRoleFilter(e.target.value);
              setPage(1);
            }}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Roles</option>
            <option value="user">Users</option>
            <option value="admin">Administrators</option>
          </select>
        </div>
      </div>

      {actionError && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Users Table */}
      <Card className="border-slate-800 bg-slate-900/60 overflow-hidden">
        {loading ? (
          <div className="py-16 flex flex-col items-center justify-center text-slate-400">
            <LoadingSpinner size="md" className="text-indigo-500 mb-2" />
            <p className="text-xs font-mono">Loading user directory...</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Verified</th>
                  <th className="py-3 px-4">Datasets</th>
                  <th className="py-3 px-4">Analyses</th>
                  <th className="py-3 px-4">Joined</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {users.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-500">
                      No users found matching query.
                    </td>
                  </tr>
                ) : (
                  users.map((u) => {
                    const isSelf = u.id === currentAdmin?.id;
                    return (
                      <tr key={u.id} className="hover:bg-slate-800/20 transition-colors">
                        <td className="py-3 px-4">
                          <div className="font-medium text-slate-200">
                            {u.first_name} {u.last_name}
                            {isSelf && (
                              <span className="ml-2 px-1.5 py-0.5 rounded text-[10px] bg-indigo-500/20 text-indigo-300 font-normal">
                                You
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] text-slate-400">{u.email}</div>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                              u.role === 'admin'
                                ? 'bg-indigo-500/10 text-indigo-300 border border-indigo-500/20'
                                : 'bg-slate-800 text-slate-300'
                            }`}
                          >
                            {u.role.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center gap-1 text-[11px] font-medium ${
                              u.is_active ? 'text-emerald-400' : 'text-rose-400'
                            }`}
                          >
                            {u.is_active ? (
                              <>
                                <CheckCircle className="w-3.5 h-3.5" /> Active
                              </>
                            ) : (
                              <>
                                <XCircle className="w-3.5 h-3.5" /> Disabled
                              </>
                            )}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-300">
                          {u.is_verified ? 'Yes' : 'No'}
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-300">
                          {u.dataset_count}
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-300">
                          {u.analysis_count}
                        </td>
                        <td className="py-3 px-4 text-slate-400 text-[11px]">
                          {new Date(u.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Button
                            size="sm"
                            variant={u.is_active ? 'ghost' : 'secondary'}
                            disabled={isSelf || actionLoadingId === u.id}
                            onClick={() => handleToggleStatus(u)}
                            className={
                              u.is_active
                                ? 'text-rose-400 hover:text-rose-300 hover:bg-rose-500/10'
                                : 'text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10'
                            }
                            title={isSelf ? 'Cannot deactivate your own administrator account' : ''}
                          >
                            {actionLoadingId === u.id ? (
                              <LoadingSpinner size="sm" />
                            ) : u.is_active ? (
                              'Deactivate'
                            ) : (
                              'Activate'
                            )}
                          </Button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/40 flex items-center justify-between text-xs text-slate-400">
          <span>
            Total: <strong className="text-slate-200">{total}</strong> users
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
              disabled={users.length < 15 || page * 15 >= total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
