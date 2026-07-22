import React, { useState, useEffect, useCallback } from 'react';
import { Clock, RefreshCw, Monitor, Globe } from 'lucide-react';
// Checked: Clock (lines 119, 128), RefreshCw (line 70), Monitor (line 146), Globe (line 142) — all used.
import api from '../../config/api';
import PageHeader from '../../components/PageHeader';
import Card from '../../components/Card';
import LoadingSpinner from '../../components/LoadingSpinner';
import EmptyState from '../../components/EmptyState';
import useDocumentTitle from '../../hooks/useDocumentTitle';
import toast from 'react-hot-toast';

export const ActivityLogs = () => {
  useDocumentTitle('System Activity Logs');

  const [logs, setLogs] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDeleteDate, setSelectedDeleteDate] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const fetchLogs = useCallback(async () => {
    try {
      setIsLoading(true);
      const res = await api.get('/activity-logs', {
        params: {
          page,
          page_size: pageSize
        }
      });
      if (res.data && res.data.success) {
        setLogs(res.data.data.items || []);
        setTotalCount(res.data.data.total || res.data.data.total_count || 0);
      }
    } catch (err) {
      toast.error('Failed to load system activity audit logs.');
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // Format Helper
  const formatTime = (timeStr) => {
    if (!timeStr) return null;
    return new Date(timeStr).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="space-y-6 text-left animate-fade-in">
      <PageHeader 
        title="System Activity Logs" 
        subtitle="Real-time audit trails of staff portal authentications and active sessions"
        breadcrumbs={[{ label: 'Home', path: '/dashboard' }, { label: 'Audit logs' }]}
        action={
          <button
            onClick={fetchLogs}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-xl shadow-sm hover:shadow active:scale-[0.98] transition-all disabled:opacity-50"
          >
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
            Refresh Logs
          </button>
        }
      />

      {/* ── DELETE LOGS BY DATE ── */}
      <div className="bg-amber-50/50 border border-amber-100 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="flex-1">
          <p className="text-xs font-bold text-amber-800">Delete Activity Logs</p>
          <p className="text-[10px] text-amber-600">Select a date to permanently remove all logs from that day.</p>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={selectedDeleteDate}
            onChange={(e) => setSelectedDeleteDate(e.target.value)}
            className="px-3 py-2 border border-amber-200 bg-white rounded-xl text-xs font-semibold text-slate-700 focus:border-amber-500 outline-none"
          />
          <button
            onClick={() => setShowDeleteConfirm(true)}
            disabled={!selectedDeleteDate}
            className="px-4 py-2 rounded-xl bg-red-500 text-white text-xs font-bold hover:bg-red-600 transition-all disabled:opacity-50"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div onClick={() => setShowDeleteConfirm(false)} className="absolute inset-0 bg-black/40 backdrop-blur-sm"></div>
          <div className="relative bg-white rounded-2xl shadow-2xl p-6 max-w-sm w-full mx-4 text-left z-10">
            <h3 className="text-sm font-bold text-slate-800">Confirm Deletion</h3>
            <p className="text-xs text-slate-500 mt-2">
              Are you sure you want to delete all activity logs from <strong>{selectedDeleteDate}</strong>? This action cannot be undone.
            </p>
            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowDeleteConfirm(false)} className="flex-1 px-4 py-2 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50 transition-all">
                Cancel
              </button>
              <button onClick={async () => {
                try {
                  const res = await api.delete(`/activity-logs/date/${selectedDeleteDate}`);
                  if (res.data?.success) {
                    toast.success(res.data.message || 'Logs deleted successfully.');
                    setShowDeleteConfirm(false);
                    setSelectedDeleteDate('');
                    fetchLogs();
                  } else {
                    toast.error(res.data?.message || 'Failed to delete logs.');
                  }
                } catch (err) {
                  toast.error(err.response?.data?.message || 'Failed to delete logs.');
                }
              }} className="flex-1 px-4 py-2 rounded-xl bg-red-500 text-white text-xs font-bold hover:bg-red-600 transition-all">
                Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}

      <Card>
        {isLoading ? (
          <div className="py-24 flex justify-center">
            <LoadingSpinner label="Loading audit logs..." />
          </div>
        ) : logs.length === 0 ? (
          <EmptyState 
            title="No Activity Logs Recorded" 
            description="All employee portal authentications will be audit logged here." 
          />
        ) : (
          <div className="flex flex-col gap-4 text-left">
            <div className="overflow-x-auto -mx-6 px-6">
              <table className="w-full text-left border-collapse min-w-[800px]">
                <thead>
                  <tr className="border-b border-slate-100 text-xs font-bold text-slate-400 uppercase tracking-wider">
                    <th className="py-3.5 px-4">Employee Registry</th>
                    <th className="py-3.5 px-4">Authentication Login</th>
                    <th className="py-3.5 px-4">Session Logout</th>
                    <th className="py-3.5 px-4">Device & IP Address</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50 text-sm">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50/50 transition-colors">
                      {/* Name & Code */}
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-brand-orange/10 flex items-center justify-center text-brand-orange font-bold text-xs shrink-0">
                            {log.employee_name ? log.employee_name.substring(0, 2).toUpperCase() : 'ST'}
                          </div>
                          <div className="flex flex-col text-left">
                            <span className="font-bold text-slate-800">{log.employee_name}</span>
                            <span className="text-[10px] text-slate-400 font-mono font-bold">
                              {log.employee_code || `EMP-#${log.user_id}`}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Login */}
                      <td className="py-4 px-4 font-semibold text-slate-600">
                        <span className="flex items-center gap-1.5">
                          <Clock size={12} className="text-slate-400" />
                          {formatTime(log.login_time)}
                        </span>
                      </td>

                      {/* Logout */}
                      <td className="py-4 px-4 font-semibold">
                        {log.logout_time ? (
                          <span className="flex items-center gap-1.5 text-slate-500">
                            <Clock size={12} className="text-slate-400" />
                            {formatTime(log.logout_time)}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-600 border border-emerald-100 text-[10px] font-bold uppercase tracking-wider">
                            Active Session
                          </span>
                        )}
                      </td>

                      {/* Device Metadata */}
                      <td className="py-4 px-4">
                        <div className="flex flex-col gap-1 text-[11px] text-slate-500">
                          <span className="flex items-center gap-1 font-semibold">
                            <Globe size={11} className="text-slate-400" />
                            {log.ip_address || 'Internal Network'}
                          </span>
                          <span className="flex items-center gap-1 text-slate-400 font-medium truncate max-w-[280px]" title={log.browser || 'Unknown Client'}>
                            <Monitor size={11} className="text-slate-400 shrink-0" />
                            {log.browser ? log.browser.split(' ')[0] : 'Unknown Browser'}
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between border-t border-slate-100 pt-4 mt-2">
                <p className="text-xs font-semibold text-slate-400">
                  Showing Page <span className="text-slate-700 font-bold">{page}</span> of{' '}
                  <span className="text-slate-700 font-bold">{totalPages}</span> ({totalCount} total audit records)
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage(prev => Math.max(1, prev - 1))}
                    disabled={page === 1}
                    className="px-3 py-1.5 border border-slate-200 rounded-xl bg-white hover:bg-slate-50 disabled:opacity-50 text-xs font-bold text-slate-600"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={page === totalPages}
                    className="px-3 py-1.5 border border-slate-200 rounded-xl bg-white hover:bg-slate-50 disabled:opacity-50 text-xs font-bold text-slate-600"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
};
