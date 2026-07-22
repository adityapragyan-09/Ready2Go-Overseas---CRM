import React, { useState, useEffect, useCallback } from 'react';
import { Inbox, CheckCheck, Trash2, Search, Mail, MailOpen, Clock, UserPlus, FileText, MessageSquare, Shield, RefreshCw, MessageCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import api from '../../config/api';
import { useAuth } from '../../hooks/useAuth';
import Card from '../../components/Card';
import PageHeader from '../../components/PageHeader';
import LoadingSpinner from '../../components/LoadingSpinner';
import EmptyState from '../../components/EmptyState';
import ConfirmationModal from '../../components/ConfirmationModal';

const CATEGORIES = [
  { key: 'all', label: 'All', icon: Inbox },
  { key: 'applicant', label: 'Lead Updates', icon: UserPlus },
  { key: 'assignment', label: 'Assignments', icon: UserPlus },
  { key: 'employee', label: 'Staff Updates', icon: Shield },
  { key: 'document', label: 'Documents', icon: FileText },
  { key: 'chat', label: 'Student Chats', icon: MessageSquare },
  { key: 'internal_chat', label: 'Internal Chats', icon: MessageCircle },
  { key: 'authentication', label: 'System', icon: Shield },
];

export const InboxPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [notifications, setNotifications] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');
  const [unreadCount, setUnreadCount] = useState(0);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const moduleFilter = category === 'all' ? undefined : category;

  const fetchNotifications = useCallback(async () => {
    try {
      setIsLoading(true);
      const res = await api.get('/notifications', {
        params: { page, page_size: pageSize, module: moduleFilter, search: search || undefined },
      });
      if (res.data?.success) {
        setNotifications(res.data.data.items || []);
        setTotalCount(res.data.data.total || res.data.data.total_count || 0);
      }
    } catch {
      toast.error('Failed to load inbox.');
    } finally {
      setIsLoading(false);
    }
  }, [page, moduleFilter, search]);

  const fetchUnread = useCallback(async () => {
    try {
      const res = await api.get('/notifications/unread-count');
      if (res.data?.success) {
        setUnreadCount(res.data.data.unread_count || 0);
      }
    } catch { /* silent */ }
  }, []);

  useEffect(() => { fetchNotifications(); fetchUnread(); }, [fetchNotifications, fetchUnread]);

  const handleMarkRead = async (id) => {
    try {
      await api.patch(`/notifications/${id}/read`);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch { toast.error('Failed to mark as read.'); }
  };

  const handleMarkAllRead = async () => {
    try {
      const res = await api.patch('/notifications/read-all');
      if (res.data?.success) {
        setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
        setUnreadCount(0);
        toast.success('All marked as read.');
      }
    } catch { toast.error('Failed to mark all as read.'); }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setActionLoading(true);
    try {
      await api.delete(`/notifications/${deleteTarget.id}`);
      setNotifications(prev => prev.filter(n => n.id !== deleteTarget.id));
      setTotalCount(prev => prev - 1);
      if (!deleteTarget.is_read) setUnreadCount(prev => Math.max(0, prev - 1));
      toast.success('Deleted.');
    } catch { toast.error('Failed to delete.'); }
    finally { setActionLoading(false); setDeleteTarget(null); }
  };

  const catCounts = {};
  notifications.forEach(n => {
    const mod = n.module || 'system';
    catCounts[mod] = (catCounts[mod] || 0) + (n.is_read ? 0 : 1);
  });

  return (
    <div className="space-y-6 text-left animate-fade-in">
      <PageHeader title="Inbox" subtitle="View and manage all important CRM updates"
        breadcrumbs={[{ label: 'Home', path: '/dashboard' }, { label: 'Inbox' }]}
        action={
          unreadCount > 0 && (
            <button onClick={handleMarkAllRead} className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-xl transition-all">
              <CheckCheck size={14} /> Mark All Read
            </button>
          )
        }
      />

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar Categories */}
        <div className="lg:w-56 shrink-0 space-y-1">
          {CATEGORIES.map(cat => {
            const Icon = cat.icon;
            const count = cat.key === 'all' ? unreadCount : (catCounts[cat.key] || 0);
            return (
              <button key={cat.key}
                onClick={() => { setCategory(cat.key); setPage(1); }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-bold transition-all text-left ${category === cat.key ? 'bg-brand-blue text-white shadow-sm' : 'text-slate-600 hover:bg-slate-50'}`}
              >
                <Icon size={16} />
                <span className="flex-1">{cat.label}</span>
                {count > 0 && <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${category === cat.key ? 'bg-white/20' : 'bg-brand-orange text-white'}`}>{count}</span>}
              </button>
            );
          })}
        </div>

        {/* Notification Feed */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
                placeholder="Search inbox..."
                className="w-full pl-10 pr-4 py-2 border border-slate-200 bg-white rounded-xl text-xs font-semibold focus:border-brand-blue outline-none" />
            </div>
            <button onClick={() => { setPage(1); fetchNotifications(); }} className="px-3 py-2 rounded-xl border border-slate-200 hover:bg-slate-50"><RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} /></button>
          </div>

          {isLoading ? (
            <div className="py-24 flex justify-center"><LoadingSpinner label="Loading inbox..." /></div>
          ) : notifications.length === 0 ? (
            <EmptyState title="Inbox Empty" description={search ? 'Try a different search term.' : 'No notifications yet.'} />
          ) : (
            <div className="space-y-2">
              {notifications.map(n => {
                const IconMap = { applicant: UserPlus, assignment: UserPlus, employee: Shield, document: FileText, chat: MessageSquare, internal_chat: MessageCircle, authentication: Shield, progress: Clock };
                const Icon = IconMap[n.module] || Inbox;
                const CategoryBadge = ({ module }) => {
                  const styles = {
                    applicant: 'bg-blue-50 text-blue-600', lead: 'bg-blue-50 text-blue-600',
                    assignment: 'bg-amber-50 text-amber-600', employee: 'bg-amber-50 text-amber-600',
                    document: 'bg-purple-50 text-purple-600',
                    chat: 'bg-emerald-50 text-emerald-600', internal_chat: 'bg-emerald-50 text-emerald-600',
                    authentication: 'bg-slate-50 text-slate-600', system: 'bg-slate-50 text-slate-600',
                    progress: 'bg-indigo-50 text-indigo-600',
                  };
                  const labels = { applicant: 'Lead', lead: 'Lead', assignment: 'Assignment', employee: 'Staff',
                    document: 'Document', chat: 'Student Chat', internal_chat: 'Internal Chat',
                    authentication: 'System', system: 'System', progress: 'Progress' };
                  return <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${styles[module] || 'bg-slate-50 text-slate-500'}`}>{labels[module] || module}</span>;
                };

                return (
                  <div key={n.id}
                    className={`group flex items-start gap-4 p-4 rounded-2xl border transition-all cursor-pointer hover:shadow-sm ${n.is_read ? 'bg-white border-slate-100' : 'bg-brand-blue/5 border-brand-blue/20'}`}
                    onClick={() => {
                      if (n.reference_type === 'lead' && n.reference_id) {
                        navigate(`/lead-inquiries`);
                      } else if (n.reference_type === 'document' && n.reference_id) {
                        navigate(`/applicants`);
                      } else if (n.reference_type === 'user') {
                        navigate(`/employees`);
                      } else {
                        navigate(`/inbox`);
                      }
                      if (!n.is_read) handleMarkRead(n.id);
                    }}
                  >
                    <div className={`p-2.5 rounded-full shrink-0 ${n.is_read ? 'bg-slate-50 text-slate-400' : 'bg-brand-blue/10 text-brand-blue'}`}>
                      <Icon size={18} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <p className={`text-xs ${n.is_read ? 'font-semibold text-slate-700' : 'font-bold text-slate-800'}`}>{n.title}</p>
                            <CategoryBadge module={n.module} />
                          </div>
                          <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">{n.message}</p>
                        </div>
                        {!n.is_read && <span className="w-2 h-2 rounded-full bg-brand-orange shrink-0 mt-1.5"></span>}
                      </div>
                      <div className="flex items-center gap-3 mt-2">
                        <span className="text-[10px] text-slate-400 flex items-center gap-1"><Clock size={10} /> {new Date(n.created_at).toLocaleString()}</span>
                        {n.priority === 'high' && <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-red-50 text-red-500">High</span>}
                        {n.priority === 'medium' && <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-amber-50 text-amber-500">Medium</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" onClick={e => e.stopPropagation()}>
                      {n.is_read ? (
                        <button onClick={() => handleMarkRead(n.id)} className="p-1.5 text-slate-400 hover:text-brand-blue rounded-lg hover:bg-slate-50" title="Unread"><MailOpen size={14} /></button>
                      ) : (
                        <button onClick={() => handleMarkRead(n.id)} className="p-1.5 text-slate-400 hover:text-brand-blue rounded-lg hover:bg-slate-50" title="Read"><Mail size={14} /></button>
                      )}
                      <button onClick={() => setDeleteTarget(n)} className="p-1.5 text-slate-400 hover:text-red-500 rounded-lg hover:bg-red-50" title="Delete"><Trash2 size={14} /></button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {totalCount > pageSize && (
            <div className="flex justify-center gap-2 mt-6">
              <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1.5 rounded-lg border text-xs font-bold disabled:opacity-30 hover:bg-slate-50">Prev</button>
              <span className="px-3 py-1.5 text-xs text-slate-500">{page} of {Math.ceil(totalCount / pageSize)}</span>
              <button disabled={page >= Math.ceil(totalCount / pageSize)} onClick={() => setPage(p => p + 1)} className="px-3 py-1.5 rounded-lg border text-xs font-bold disabled:opacity-30 hover:bg-slate-50">Next</button>
            </div>
          )}
        </div>
      </div>

      <ConfirmationModal visible={!!deleteTarget} title="Delete" message="Delete this notification?" confirmText="Delete" confirmVariant="danger" loading={actionLoading} onConfirm={handleDelete} onCancel={() => setDeleteTarget(null)} />
    </div>
  );
};

export default InboxPage;
