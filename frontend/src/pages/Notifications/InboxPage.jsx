import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Inbox, CheckCheck, Trash2, Search, Mail, MailOpen, Clock, UserPlus, FileText, MessageSquare, Shield, RefreshCw, MessageCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import api from '../../config/api';
import { useAuth } from '../../hooks/useAuth';
import { useNotifications } from '../../context/NotificationContext';
import Card from '../../components/Card';
import PageHeader from '../../components/PageHeader';
import LoadingSpinner from '../../components/LoadingSpinner';
import EmptyState from '../../components/EmptyState';
import ConfirmationModal from '../../components/ConfirmationModal';

// Admin categories — full set
const ADMIN_CATEGORIES = [
  { key: 'all', label: 'All', icon: Inbox },
  { key: 'applicant', label: 'Lead Updates', icon: UserPlus },
  { key: 'assignment', label: 'Assignments', icon: UserPlus },
  { key: 'employee', label: 'Staff Updates', icon: Shield },
  { key: 'document', label: 'Documents', icon: FileText },
  { key: 'chat', label: 'Student Chats', icon: MessageSquare },
  { key: 'internal_chat', label: 'Internal Chats', icon: MessageCircle },
  { key: 'authentication', label: 'System', icon: Shield },
];

// Employee categories — limited
const EMPLOYEE_CATEGORIES = [
  { key: 'all', label: 'All', icon: Inbox },
  { key: 'applicant', label: 'Lead Updates', icon: UserPlus },
  { key: 'assignment', label: 'Assignments', icon: UserPlus },
  { key: 'document', label: 'Documents', icon: FileText },
  { key: 'chat', label: 'Student Chats', icon: MessageSquare },
  { key: 'internal_chat', label: 'Internal Chats', icon: MessageCircle },
];

const MODULE_LABELS = {
  applicant: 'Lead', lead: 'Lead', assignment: 'Assignment', employee: 'Staff',
  document: 'Document', chat: 'Student Chat', internal_chat: 'Internal Chat',
  authentication: 'System', system: 'System', progress: 'Progress',
};

const MODULE_STYLES = {
  applicant: 'bg-blue-50 text-blue-600', lead: 'bg-blue-50 text-blue-600',
  assignment: 'bg-amber-50 text-amber-600', employee: 'bg-amber-50 text-amber-600',
  document: 'bg-purple-50 text-purple-600',
  chat: 'bg-emerald-50 text-emerald-600', internal_chat: 'bg-emerald-50 text-emerald-600',
  authentication: 'bg-slate-50 text-slate-600', system: 'bg-slate-50 text-slate-600',
  progress: 'bg-indigo-50 text-indigo-600',
};

const ICON_MAP = {
  applicant: UserPlus, lead: UserPlus, assignment: UserPlus,
  employee: Shield, document: FileText, chat: MessageSquare,
  internal_chat: MessageCircle, authentication: Shield,
  progress: Clock,
};

const NotificationCard = React.memo(({ notification, onMarkRead, onDelete, onNavigate }) => {
  const n = notification;
  const Icon = ICON_MAP[n.module] || Inbox;
  const isUnread = !n.is_read;

  return (
    <div
      className={`group flex items-start gap-4 p-4 rounded-2xl border transition-all cursor-pointer hover:shadow-sm ${
        isUnread ? 'bg-brand-blue/5 border-brand-blue/20' : 'bg-white border-slate-100'
      }`}
      onClick={() => onNavigate(n)}
    >
      <div className={`p-2.5 rounded-full shrink-0 ${isUnread ? 'bg-brand-blue/10 text-brand-blue' : 'bg-slate-50 text-slate-400'}`}>
        <Icon size={18} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <p className={`text-xs ${isUnread ? 'font-bold text-slate-800' : 'font-semibold text-slate-700'}`}>{n.title}</p>
              <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${MODULE_STYLES[n.module] || 'bg-slate-50 text-slate-500'}`}>
                {MODULE_LABELS[n.module] || n.module}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">{n.message}</p>
          </div>
          {isUnread && <span className="w-2 h-2 rounded-full bg-brand-orange shrink-0 mt-1.5"></span>}
        </div>
        <div className="flex items-center gap-3 mt-2">
          <span className="text-[10px] text-slate-400 flex items-center gap-1"><Clock size={10} /> {new Date(n.created_at).toLocaleString()}</span>
          {n.priority === 'high' && <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-red-50 text-red-500">High</span>}
          {n.priority === 'medium' && <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-amber-50 text-amber-500">Medium</span>}
        </div>
      </div>
      <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" onClick={e => e.stopPropagation()}>
        {isUnread ? (
          <button onClick={() => onMarkRead(n.id)} className="p-1.5 text-slate-400 hover:text-brand-blue rounded-lg hover:bg-slate-50" title="Mark Read"><Mail size={14} /></button>
        ) : (
          <span className="p-1.5 text-slate-300"><MailOpen size={14} /></span>
        )}
        <button onClick={() => onDelete(n)} className="p-1.5 text-slate-400 hover:text-red-500 rounded-lg hover:bg-red-50" title="Delete"><Trash2 size={14} /></button>
      </div>
    </div>
  );
});

export const InboxPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isAdmin = user?.role === 'admin';

  // Use context for global state management
  const {
    unreadCount, fetchUnreadCount,
    markAsRead, markAllAsRead, deleteNotification,
  } = useNotifications();

  const [notifications, setNotifications] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const searchTimerRef = useRef(null);

  // Choose categories based on role
  const CATEGORIES = isAdmin ? ADMIN_CATEGORIES : EMPLOYEE_CATEGORIES;

  const moduleFilter = category === 'all' ? undefined : category;

  // Debounced search — only fires 300ms after user stops typing
  const [debouncedSearch, setDebouncedSearch] = useState('');
  useEffect(() => {
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => { if (searchTimerRef.current) clearTimeout(searchTimerRef.current); };
  }, [search]);

  const fetchNotifications = useCallback(async () => {
    try {
      setIsLoading(true);
      const params = { page, page_size: pageSize, module: moduleFilter, search: debouncedSearch || undefined };
      const res = await api.get('/notifications', { params });
      if (res.data?.success) {
        setNotifications(res.data.data.items || []);
        setTotalCount(res.data.data.total || 0);
      }
    } catch {
      toast.error('Failed to load inbox.');
    } finally {
      setIsLoading(false);
    }
  }, [page, moduleFilter, debouncedSearch]);

  useEffect(() => {
    fetchNotifications();
    // Fetch fresh unread count whenever the inbox loads or filters change
    fetchUnreadCount();
  }, [fetchNotifications, fetchUnreadCount]);

  const handleMarkRead = useCallback((id) => {
    markAsRead(id);
    window.dispatchEvent(new CustomEvent('notification-update'));
  }, [markAsRead]);

  const handleMarkAllRead = useCallback(async () => {
    try {
      await markAllAsRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      window.dispatchEvent(new CustomEvent('notification-update'));
      toast.success('All marked as read.');
    } catch { toast.error('Failed to mark all as read.'); }
  }, [markAllAsRead]);

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return;
    setActionLoading(true);
    const target = deleteTarget;
    try {
      await deleteNotification(target.id);
      setNotifications(prev => prev.filter(n => n.id !== target.id));
      setTotalCount(prev => Math.max(0, prev - 1));
      toast.success('Deleted.');
    } catch { toast.error('Failed to delete.'); }
    finally { setActionLoading(false); setDeleteTarget(null); }
  }, [deleteTarget, deleteNotification]);

  const handleNavigate = useCallback((n) => {
    if (n.reference_type === 'lead' && n.reference_id) navigate('/lead-inquiries');
    else if (n.reference_type === 'document' && n.reference_id) navigate('/applicants');
    else if (n.reference_type === 'user') navigate('/employees');
    else navigate('/inbox');
    if (!n.is_read) handleMarkRead(n.id);
  }, [navigate, handleMarkRead]);

  // Compute category counts (unread per module) using useMemo
  const catCounts = useMemo(() => {
    const counts = {};
    notifications.forEach(n => {
      const mod = n.module || 'system';
      counts[mod] = (counts[mod] || 0) + (n.is_read ? 0 : 1);
    });
    return counts;
  }, [notifications]);

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="space-y-6 text-left animate-fade-in">
      <PageHeader title="Inbox" subtitle="View and manage all important CRM updates"
        breadcrumbs={[{ label: 'Home', path: '/dashboard' }, { label: 'Inbox' }]}
        action={
          unreadCount > 0 && (
            <button onClick={handleMarkAllRead}
              className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-xl transition-all">
              <CheckCheck size={14} /> Mark All Read
            </button>
          )
        }
      />

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar Categories — role-filtered */}
        <div className="lg:w-56 shrink-0 space-y-1">
          {CATEGORIES.map(cat => {
            const Icon = cat.icon;
            const count = cat.key === 'all' ? unreadCount : (catCounts[cat.key] || 0);
            return (
              <button key={cat.key}
                onClick={() => { setCategory(cat.key); setPage(1); }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-bold transition-all text-left ${
                  category === cat.key
                    ? 'bg-brand-blue text-white shadow-sm'
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                <Icon size={16} />
                <span className="flex-1">{cat.label}</span>
                {count > 0 && (
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                    category === cat.key ? 'bg-white/20' : 'bg-brand-orange text-white'
                  }`}>{count}</span>
                )}
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
            <button onClick={() => fetchNotifications()}
              className="px-3 py-2 rounded-xl border border-slate-200 hover:bg-slate-50">
              <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
            </button>
          </div>

          {isLoading ? (
            <div className="py-24 flex justify-center"><LoadingSpinner label="Loading inbox..." /></div>
          ) : notifications.length === 0 ? (
            <EmptyState title="Inbox Empty" description={debouncedSearch ? 'Try a different search term.' : 'No notifications yet.'} />
          ) : (
            <div className="space-y-2">
              {notifications.map(n => (
                <NotificationCard
                  key={n.id}
                  notification={n}
                  onMarkRead={handleMarkRead}
                  onDelete={setDeleteTarget}
                  onNavigate={handleNavigate}
                />
              ))}
            </div>
          )}

          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6">
              <span className="text-[10px] text-slate-400 font-semibold">{totalCount} total</span>
              <div className="flex gap-2">
                <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
                  className="px-3 py-1.5 rounded-lg border text-xs font-bold disabled:opacity-30 hover:bg-slate-50 transition-all">Prev</button>
                <span className="px-3 py-1.5 text-xs text-slate-500">{page} / {totalPages}</span>
                <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}
                  className="px-3 py-1.5 rounded-lg border text-xs font-bold disabled:opacity-30 hover:bg-slate-50 transition-all">Next</button>
              </div>
            </div>
          )}
        </div>
      </div>

      <ConfirmationModal
        visible={!!deleteTarget}
        title="Delete Notification"
        message="Are you sure you want to delete this notification?"
        confirmText="Delete"
        confirmVariant="danger"
        loading={actionLoading}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
};

export default InboxPage;
