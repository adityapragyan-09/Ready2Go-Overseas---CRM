import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Check, CheckCheck, Trash2, X, Users, FileText, MessageSquare, TrendingUp, Shield, Settings, LogIn } from 'lucide-react';
import { useNotifications } from '../context/NotificationContext';

// ── Module icon mapping ──
const MODULE_ICONS = {
  authentication: LogIn,
  applicant: Users,
  document: FileText,
  progress: TrendingUp,
  chat: MessageSquare,
  employee: Shield,
  system: Settings,
};

const MODULE_COLORS = {
  authentication: 'text-indigo-500 bg-indigo-50 border-indigo-100',
  applicant: 'text-brand-blue bg-brand-blue/5 border-brand-blue/10',
  document: 'text-emerald-600 bg-emerald-50 border-emerald-100',
  progress: 'text-amber-600 bg-amber-50 border-amber-100',
  chat: 'text-purple-600 bg-purple-50 border-purple-100',
  employee: 'text-rose-600 bg-rose-50 border-rose-100',
  system: 'text-slate-500 bg-slate-50 border-slate-200',
};

const PRIORITY_COLORS = {
  low: 'bg-slate-100 text-slate-500',
  medium: 'bg-blue-50 text-blue-600',
  high: 'bg-amber-50 text-amber-700',
  critical: 'bg-red-50 text-red-600',
};

// ── Time-ago formatter ──
const timeAgo = (dateStr) => {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
};

// ── Navigation resolver ──
const getNavigationPath = (notif) => {
  switch (notif.module) {
    case 'applicant':
    case 'progress':
    case 'chat':
    case 'document':
      return '/applicants';
    case 'employee':
      return '/employees';
    case 'authentication':
      return '/activity-logs';
    default:
      return '/dashboard';
  }
};

// ── NotificationCard ──
const NotificationCard = ({ notification, onRead, onDelete, onNavigate }) => {
  const Icon = MODULE_ICONS[notification.module] || Settings;
  const colorClass = MODULE_COLORS[notification.module] || MODULE_COLORS.system;
  const priorityClass = PRIORITY_COLORS[notification.priority] || PRIORITY_COLORS.medium;

  return (
    <div
      onClick={() => {
        if (!notification.is_read) onRead(notification.id);
        onNavigate(notification);
      }}
      className={`relative px-4 py-3 flex gap-3 cursor-pointer transition-all duration-200 border-b border-slate-50 last:border-0 group
        ${notification.is_read ? 'bg-white hover:bg-slate-50/50' : 'bg-brand-orange/[0.02] hover:bg-brand-orange/[0.04]'}
      `}
    >
      {/* Unread dot */}
      {!notification.is_read && (
        <span className="absolute left-1.5 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-brand-orange"></span>
      )}

      {/* Module icon */}
      <div className={`w-8 h-8 rounded-lg border flex items-center justify-center shrink-0 ${colorClass}`}>
        <Icon size={14} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className={`text-[11px] leading-snug ${notification.is_read ? 'text-slate-600' : 'text-slate-800 font-bold'}`}>
            {notification.title}
          </p>
          <span className="text-[9px] text-slate-400 shrink-0 mt-0.5">{timeAgo(notification.created_at)}</span>
        </div>
        <p className="text-[10px] text-slate-400 mt-0.5 leading-snug line-clamp-2">{notification.message}</p>
        <div className="flex items-center gap-1.5 mt-1.5">
          <span className={`text-[8px] font-black uppercase tracking-wider px-1.5 py-0.5 rounded ${priorityClass}`}>
            {notification.priority}
          </span>
          <span className="text-[8px] font-bold uppercase tracking-wider text-slate-400 bg-slate-50 px-1.5 py-0.5 rounded">
            {notification.module}
          </span>
        </div>
      </div>

      {/* Delete button */}
      <button
        onClick={(e) => { e.stopPropagation(); onDelete(notification.id); }}
        className="p-1 rounded-lg text-slate-300 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-all shrink-0 self-center"
      >
        <Trash2 size={12} />
      </button>
    </div>
  );
};

// ── NotificationBell (main export) ──
const NotificationBell = () => {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const { unreadCount, notifications, isLoading, fetchNotifications, markAsRead, markAllAsRead, deleteNotification } = useNotifications();

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Fetch when opening
  useEffect(() => {
    if (open) fetchNotifications();
  }, [open, fetchNotifications]);

  const handleNavigate = (notif) => {
    setOpen(false);
    navigate(getNavigationPath(notif));
  };

  return (
    <div className="relative" ref={ref}>
      {/* Bell Button */}
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 rounded-xl hover:bg-slate-50 text-slate-500 hover:text-brand-orange transition-all"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 flex items-center justify-center rounded-full bg-brand-orange text-white text-[9px] font-black animate-scale-up">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {open && (
        <div className="absolute right-0 mt-2 w-96 max-h-[480px] bg-white border border-slate-100 rounded-2xl shadow-2xl shadow-slate-200/60 z-50 animate-fade-in flex flex-col overflow-hidden">
          {/* Header */}
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between shrink-0">
            <div>
              <h3 className="text-xs font-black text-slate-800 uppercase tracking-wider">Notifications</h3>
              {unreadCount > 0 && (
                <p className="text-[10px] text-slate-400 mt-0.5">{unreadCount} unread</p>
              )}
            </div>
            <div className="flex items-center gap-1.5">
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="flex items-center gap-1 px-2 py-1 text-[10px] font-bold text-brand-orange hover:bg-brand-orange/5 rounded-lg transition-all"
                >
                  <CheckCheck size={12} /> Mark all read
                </button>
              )}
              <button onClick={() => setOpen(false)} className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-50">
                <X size={14} />
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto [scrollbar-width:thin]">
            {isLoading ? (
              <div className="py-10 text-center">
                <div className="w-5 h-5 border-2 border-brand-orange/30 border-t-brand-orange rounded-full animate-spin mx-auto"></div>
                <p className="text-[10px] text-slate-400 mt-2">Loading notifications...</p>
              </div>
            ) : notifications.length === 0 ? (
              <div className="py-10 text-center">
                <Bell size={28} className="mx-auto text-slate-200 mb-2" />
                <p className="text-xs text-slate-400 font-semibold">No notifications yet</p>
                <p className="text-[10px] text-slate-300 mt-0.5">Activity alerts will appear here.</p>
              </div>
            ) : (
              notifications.map((notif) => (
                <NotificationCard
                  key={notif.id}
                  notification={notif}
                  onRead={markAsRead}
                  onDelete={deleteNotification}
                  onNavigate={handleNavigate}
                />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
