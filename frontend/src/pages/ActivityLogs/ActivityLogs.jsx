import React, { useState, useEffect, useCallback } from 'react';
import {
  Search, RefreshCw, Download, X, ChevronRight,
  Filter, Eye, Clock, AlertTriangle, CheckCircle2,
  Info, AlertOctagon, ShieldAlert, Users, FileText,
  PhoneCall, MessageSquare, Briefcase, Bell, Server,
  Calendar, Globe, User as UserIcon, BookOpen,
  Activity
} from 'lucide-react';
import api from '../../config/api';
import PageHeader from '../../components/PageHeader';
import Card from '../../components/Card';
import LoadingSpinner from '../../components/LoadingSpinner';
import EmptyState from '../../components/EmptyState';
import useDocumentTitle from '../../hooks/useDocumentTitle';
import toast from 'react-hot-toast';

// ── Constants ──────────────────────────────────

const CATEGORIES = [
  { value: '', label: 'All Categories' },
  { value: 'employee_management', label: 'Employee Management', icon: Users, color: 'bg-blue-50 text-blue-600 border-blue-200' },
  { value: 'applicant_management', label: 'Applicant Management', icon: FileText, color: 'bg-emerald-50 text-emerald-600 border-emerald-200' },
  { value: 'lead_management', label: 'Lead Management', icon: PhoneCall, color: 'bg-purple-50 text-purple-600 border-purple-200' },
  { value: 'documents', label: 'Documents', icon: BookOpen, color: 'bg-orange-50 text-orange-600 border-orange-200' },
  { value: 'communication', label: 'Communication', icon: MessageSquare, color: 'bg-teal-50 text-teal-600 border-teal-200' },
  { value: 'leave_hr', label: 'Leave & HR', icon: Briefcase, color: 'bg-amber-50 text-amber-600 border-amber-200' },
  { value: 'notifications', label: 'Notifications', icon: Bell, color: 'bg-pink-50 text-pink-600 border-pink-200' },
  { value: 'security', label: 'Security', icon: ShieldAlert, color: 'bg-red-50 text-red-600 border-red-200' },
  { value: 'system', label: 'System', icon: Server, color: 'bg-slate-50 text-slate-600 border-slate-200' },
];

const SEVERITIES = [
  { value: '', label: 'All Levels' },
  { value: 'INFO', label: 'Info', color: 'bg-blue-100 text-blue-700 border-blue-200' },
  { value: 'SUCCESS', label: 'Success', color: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
  { value: 'WARNING', label: 'Warning', color: 'bg-amber-100 text-amber-700 border-amber-200' },
  { value: 'ERROR', label: 'Error', color: 'bg-red-100 text-red-700 border-red-200' },
  { value: 'CRITICAL', label: 'Critical', color: 'bg-rose-200 text-rose-800 border-rose-300' },
];

const TARGET_TYPES = [
  { value: '', label: 'All Targets' },
  { value: 'applicant', label: 'Applicant' },
  { value: 'employee', label: 'Employee' },
  { value: 'lead', label: 'Lead' },
  { value: 'document', label: 'Document' },
  { value: 'notification', label: 'Notification' },
];

// ── Helpers ────────────────────────────────────

const formatTimestamp = (ts) => {
  if (!ts) return '—';
  return new Date(ts).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
};

const formatRelative = (ts) => {
  if (!ts) return '';
  const now = Date.now();
  const diff = now - new Date(ts).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return formatTimestamp(ts);
};

const getCategoryBadge = (cat) => {
  const found = CATEGORIES.find(c => c.value === cat);
  if (!found) return { label: cat || 'Unknown', color: 'bg-slate-50 text-slate-600 border-slate-200', Icon: Activity };
  return { label: found.label, color: found.color, Icon: found.icon || Activity };
};

const getSeverityBadge = (sev) => {
  const found = SEVERITIES.find(s => s.value === sev);
  if (!found) return { label: sev || 'Unknown', color: 'bg-slate-100 text-slate-700 border-slate-200' };
  return { label: found.label, color: found.color };
};

const getSeverityIcon = (sev) => {
  switch (sev) {
    case 'CRITICAL': return AlertOctagon;
    case 'ERROR': return AlertTriangle;
    case 'WARNING': return AlertTriangle;
    case 'SUCCESS': return CheckCircle2;
    default: return Info;
  }
};


// ── Main Component ─────────────────────────────

export const ActivityLogs = () => {
  useDocumentTitle('Audit Center');

  // Data state
  const [logs, setLogs] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [isLoading, setIsLoading] = useState(true);
  const [employees, setEmployees] = useState([]);

  // Filters
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [severity, setSeverity] = useState('');
  const [employeeId, setEmployeeId] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [targetType, setTargetType] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Details drawer
  const [selectedLog, setSelectedLog] = useState(null);

  // Fetch employees for filter dropdown
  useEffect(() => {
    const fetchEmps = async () => {
      try {
        const res = await api.get('/employees', { params: { include_archived: true, page_size: 100 } });
        if (res.data?.success) setEmployees(res.data.data.items || []);
      } catch { /* silent */ }
    };
    fetchEmps();
  }, []);

  // Fetch audit logs
  const fetchLogs = useCallback(async () => {
    try {
      setIsLoading(true);
      const params = { page, page_size: pageSize };
      if (category) params.category = category;
      if (severity) params.severity = severity;
      if (employeeId) params.employee_id = Number(employeeId);
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (targetType) params.target_type = targetType;
      if (search) params.search = search;

      const res = await api.get('/activity-logs/audit', { params });
      if (res.data?.success) {
        setLogs(res.data.data.items || []);
        setTotalCount(res.data.data.total || 0);
      }
    } catch {
      toast.error('Failed to load audit logs.');
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, category, severity, employeeId, dateFrom, dateTo, targetType, search]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleResetFilters = () => {
    setSearch('');
    setCategory('');
    setSeverity('');
    setEmployeeId('');
    setDateFrom('');
    setDateTo('');
    setTargetType('');
    setPage(1);
  };

  const handleExport = async () => {
    try {
      const params = {};
      if (category) params.category = category;
      if (severity) params.severity = severity;
      if (employeeId) params.employee_id = Number(employeeId);
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (targetType) params.target_type = targetType;
      if (search) params.search = search;

      const res = await api.get('/activity-logs/export', { params, responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit_logs_export_${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success('Audit logs exported successfully.');
    } catch {
      toast.error('Failed to export audit logs.');
    }
  };

  const totalPages = Math.ceil(totalCount / pageSize);
  const hasActiveFilters = category || severity || employeeId || dateFrom || dateTo || targetType || search;

  return (
    <div className="space-y-6 text-left animate-fade-in">
      <PageHeader
        title="Audit Center"
        subtitle="Enterprise-wide activity audit trail with categorized events, severity levels, and structured metadata"
        breadcrumbs={[{ label: 'Home', path: '/dashboard' }, { label: 'Audit Center' }]}
        action={
          <div className="flex items-center gap-2">
            <button
              onClick={handleExport}
              disabled={isLoading || logs.length === 0}
              className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-xl transition-all disabled:opacity-50"
              title="Export as CSV"
            >
              <Download size={14} />
              Export
            </button>
            <button
              onClick={fetchLogs}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-xl transition-all disabled:opacity-50"
            >
              <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>
        }
      />

      {/* ── Filter Bar ───────────────────────────── */}
      <div className="bg-white border border-slate-100 rounded-2xl shadow-sm overflow-hidden">
        {/* Quick search row */}
        <div className="p-4 flex items-center gap-3 flex-wrap">
          <div className="relative flex-1 min-w-[200px]">
            <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="Search actions, descriptions, names..."
              className="w-full pl-10 pr-4 py-2.5 border border-slate-200 bg-white rounded-xl text-xs font-semibold outline-none focus:border-brand-orange focus:ring-4 focus:ring-brand-orange/10 transition-all placeholder:text-slate-400"
            />
          </div>

          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border text-xs font-bold transition-all ${
              hasActiveFilters
                ? 'bg-brand-orange text-white border-brand-orange'
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <Filter size={14} />
            Filters
            {hasActiveFilters && <span className="bg-white/20 px-1.5 py-0.5 rounded text-[9px]">ON</span>}
          </button>

          {hasActiveFilters && (
            <button
              onClick={handleResetFilters}
              className="flex items-center gap-1.5 px-3 py-2.5 text-xs font-bold text-slate-400 hover:text-red-500 transition-all"
            >
              <X size={14} />
              Reset
            </button>
          )}
        </div>

        {/* Expanded filter grid */}
        {showFilters && (
          <div className="px-4 pb-4 border-t border-slate-100 pt-4">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              <div>
                <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Category</label>
                <select value={category} onChange={(e) => { setCategory(e.target.value); setPage(1); }}
                  className="w-full px-3 py-2.5 border border-slate-200 bg-white rounded-xl text-xs font-semibold outline-none focus:border-brand-orange">
                  {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Severity</label>
                <select value={severity} onChange={(e) => { setSeverity(e.target.value); setPage(1); }}
                  className="w-full px-3 py-2.5 border border-slate-200 bg-white rounded-xl text-xs font-semibold outline-none focus:border-brand-orange">
                  {SEVERITIES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Employee</label>
                <select value={employeeId} onChange={(e) => { setEmployeeId(e.target.value); setPage(1); }}
                  className="w-full px-3 py-2.5 border border-slate-200 bg-white rounded-xl text-xs font-semibold outline-none focus:border-brand-orange">
                  <option value="">All Employees</option>
                  {employees.map(e => (
                    <option key={e.id} value={e.id}>{e.full_name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Target Type</label>
                <select value={targetType} onChange={(e) => { setTargetType(e.target.value); setPage(1); }}
                  className="w-full px-3 py-2.5 border border-slate-200 bg-white rounded-xl text-xs font-semibold outline-none focus:border-brand-orange">
                  {TARGET_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">From Date</label>
                <input type="date" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
                  className="w-full px-3 py-2.5 border border-slate-200 bg-white rounded-xl text-xs outline-none focus:border-brand-orange" />
              </div>
              <div>
                <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">To Date</label>
                <input type="date" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setPage(1); }}
                  className="w-full px-3 py-2.5 border border-slate-200 bg-white rounded-xl text-xs outline-none focus:border-brand-orange" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Audit Table ──────────────────────────── */}
      <Card>
        {isLoading ? (
          <div className="py-24 flex justify-center">
            <LoadingSpinner label="Loading audit trail..." />
          </div>
        ) : logs.length === 0 ? (
          <EmptyState
            title="No Audit Logs Found"
            description={hasActiveFilters ? 'No entries match your current filters. Try adjusting them.' : 'No audit events have been recorded yet. They will appear here as actions are performed.'}
          />
        ) : (
          <div className="flex flex-col gap-4">
            <div className="overflow-x-auto -mx-6 px-6">
              <table className="w-full text-left border-collapse min-w-[900px]">
                <thead>
                  <tr className="border-b border-slate-100 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    <th className="py-3.5 px-3">Timestamp</th>
                    <th className="py-3.5 px-3">Category</th>
                    <th className="py-3.5 px-3">Severity</th>
                    <th className="py-3.5 px-3">Action</th>
                    <th className="py-3.5 px-3">Performed By</th>
                    <th className="py-3.5 px-3">Target</th>
                    <th className="py-3.5 px-3 text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50 text-sm">
                  {logs.map((log) => {
                    const cat = getCategoryBadge(log.category);
                    const sev = getSeverityBadge(log.severity);
                    const SevIcon = getSeverityIcon(log.severity);
                    const CatIcon = cat.Icon;

                    return (
                      <tr key={log.id}
                        onClick={() => setSelectedLog(log)}
                        className="hover:bg-slate-50/70 transition-colors cursor-pointer group"
                      >
                        {/* Timestamp */}
                        <td className="py-3.5 px-3 whitespace-nowrap">
                          <div className="flex flex-col">
                            <span className="text-xs font-semibold text-slate-700">
                              {formatTimestamp(log.created_at)}
                            </span>
                            <span className="text-[10px] text-slate-400">
                              {formatRelative(log.created_at)}
                            </span>
                          </div>
                        </td>

                        {/* Category Badge */}
                        <td className="py-3.5 px-3">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[9px] font-bold uppercase border ${cat.color}`}>
                            <CatIcon size={10} />
                            {cat.label === 'Employee Management' ? 'HR' :
                             cat.label === 'Applicant Management' ? 'Applicant' :
                             cat.label === 'Lead Management' ? 'Lead' : cat.label}
                          </span>
                        </td>

                        {/* Severity Badge */}
                        <td className="py-3.5 px-3">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[9px] font-bold uppercase border ${sev.color}`}>
                            <SevIcon size={10} />
                            {sev.label}
                          </span>
                        </td>

                        {/* Action */}
                        <td className="py-3.5 px-3">
                          <span className="text-xs font-bold text-slate-800">{log.action}</span>
                          {log.description && (
                            <p className="text-[10px] text-slate-400 mt-0.5 line-clamp-1 max-w-[220px]">{log.description}</p>
                          )}
                        </td>

                        {/* Performer */}
                        <td className="py-3.5 px-3">
                          <span className="text-xs font-semibold text-slate-700">
                            {log.performed_by_name || 'System'}
                          </span>
                          {log.ip_address && (
                            <p className="text-[9px] text-slate-400 flex items-center gap-1 mt-0.5">
                              <Globe size={8} /> {log.ip_address}
                            </p>
                          )}
                        </td>

                        {/* Target */}
                        <td className="py-3.5 px-3">
                          {log.target_name ? (
                            <div className="flex flex-col">
                              <span className="text-xs font-semibold text-slate-700 capitalize">
                                {log.target_type}: {log.target_name}
                              </span>
                            </div>
                          ) : (
                            <span className="text-xs text-slate-400">—</span>
                          )}
                        </td>

                        {/* Details button */}
                        <td className="py-3.5 px-3 text-right">
                          <button
                            onClick={(e) => { e.stopPropagation(); setSelectedLog(log); }}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-bold text-brand-blue bg-brand-blue/5 hover:bg-brand-blue/10 transition-all opacity-0 group-hover:opacity-100"
                          >
                            <Eye size={12} /> View
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-100 pt-4 mt-2">
                <div className="flex items-center gap-3 text-xs font-semibold text-slate-400">
                  <span>{totalCount} total records</span>
                  <span className="text-slate-300">|</span>
                  <span>Page {page} of {totalPages}</span>
                  <select
                    value={pageSize}
                    onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
                    className="px-2 py-1 border border-slate-200 rounded-lg text-[10px] font-bold text-slate-600 outline-none"
                  >
                    <option value={20}>20 / page</option>
                    <option value={50}>50 / page</option>
                    <option value={100}>100 / page</option>
                  </select>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                    className="px-3 py-1.5 border border-slate-200 rounded-xl bg-white hover:bg-slate-50 disabled:opacity-50 text-xs font-bold text-slate-600 transition-all">
                    Previous
                  </button>
                  <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                    className="px-3 py-1.5 border border-slate-200 rounded-xl bg-white hover:bg-slate-50 disabled:opacity-50 text-xs font-bold text-slate-600 transition-all">
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* ── Details Drawer ────────────────────────── */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
          <div onClick={() => setSelectedLog(null)} className="absolute inset-0 bg-black/40 backdrop-blur-sm"></div>
          <div className="relative w-full max-w-lg bg-white h-full shadow-2xl flex flex-col animate-slide-left z-10 border-l border-slate-100">
            {/* Drawer Header */}
            <div className="p-6 border-b border-slate-100 flex justify-between items-start">
              <div>
                <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Audit Log Detail</h3>
                <h2 className="text-lg font-black text-slate-800 mt-1">{selectedLog.action}</h2>
              </div>
              <button onClick={() => setSelectedLog(null)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-50 transition-all">
                <X size={18} />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {selectedLog.description && (
                <div className="p-4 bg-slate-50 border border-slate-100 rounded-xl text-sm text-slate-700 leading-relaxed">
                  {selectedLog.description}
                </div>
              )}

              {/* Key-Value Details Grid */}
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-slate-400 uppercase">Timestamp</p>
                  <p className="font-semibold text-slate-800">{formatTimestamp(selectedLog.created_at)}</p>
                  <p className="text-[10px] text-slate-400">{formatRelative(selectedLog.created_at)}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-slate-400 uppercase">Category</p>
                  {(() => { const c = getCategoryBadge(selectedLog.category); return (
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[9px] font-bold uppercase border ${c.color}`}>
                      <c.Icon size={10} />
                      {c.label}
                    </span>
                  ); })()}
                </div>
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-slate-400 uppercase">Severity</p>
                  {(() => { const s = getSeverityBadge(selectedLog.severity); const SevI = getSeverityIcon(selectedLog.severity); return (
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[9px] font-bold uppercase border ${s.color}`}>
                      <SevI size={10} />
                      {s.label}
                    </span>
                  ); })()}
                </div>
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-slate-400 uppercase">Performed By</p>
                  <p className="font-semibold text-slate-800 flex items-center gap-1.5">
                    <UserIcon size={12} className="text-slate-400" />
                    {selectedLog.performed_by_name || 'System'}
                  </p>
                </div>
                {selectedLog.target_type && (
                  <div className="space-y-1">
                    <p className="text-[10px] font-bold text-slate-400 uppercase">Target Type</p>
                    <p className="font-semibold text-slate-800 capitalize">{selectedLog.target_type}</p>
                  </div>
                )}
                {selectedLog.target_name && (
                  <div className="space-y-1">
                    <p className="text-[10px] font-bold text-slate-400 uppercase">Target</p>
                    <p className="font-semibold text-slate-800">{selectedLog.target_name}</p>
                  </div>
                )}
                {selectedLog.ip_address && (
                  <div className="space-y-1">
                    <p className="text-[10px] font-bold text-slate-400 uppercase">IP Address</p>
                    <p className="font-semibold text-slate-800 flex items-center gap-1">
                      <Globe size={10} className="text-slate-400" />
                      {selectedLog.ip_address}
                    </p>
                  </div>
                )}
                {selectedLog.request_id && (
                  <div className="space-y-1">
                    <p className="text-[10px] font-bold text-slate-400 uppercase">Request ID</p>
                    <p className="font-mono text-[10px] text-slate-600 break-all">{selectedLog.request_id}</p>
                  </div>
                )}
              </div>

              {/* Old / New Values */}
              {(selectedLog.old_value || selectedLog.new_value) && (
                <div className="space-y-3">
                  <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Value Changes</h4>
                  <div className="grid grid-cols-2 gap-3">
                    {selectedLog.old_value && (
                      <div className="p-3 rounded-xl bg-red-50 border border-red-100">
                        <p className="text-[9px] font-bold text-red-500 uppercase mb-1">Previous</p>
                        <p className="text-xs font-semibold text-red-700">{selectedLog.old_value}</p>
                      </div>
                    )}
                    {selectedLog.new_value && (
                      <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-100">
                        <p className="text-[9px] font-bold text-emerald-500 uppercase mb-1">New</p>
                        <p className="text-xs font-semibold text-emerald-700">{selectedLog.new_value}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Metadata JSON */}
              {selectedLog.metadata && Object.keys(selectedLog.metadata).length > 0 && (
                <details className="group">
                  <summary className="text-[10px] font-bold text-slate-400 uppercase tracking-wider cursor-pointer hover:text-slate-600 transition-colors list-none flex items-center gap-1.5">
                    <ChevronRight size={12} className="group-open:rotate-90 transition-transform" />
                    Metadata
                  </summary>
                  <pre className="mt-2 p-3 bg-slate-50 border border-slate-100 rounded-xl text-[10px] text-slate-600 font-mono overflow-auto max-h-48 whitespace-pre-wrap">
                    {JSON.stringify(selectedLog.metadata, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ActivityLogs;
