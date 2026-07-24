import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import api from '../config/api';

const NotificationContext = createContext(null);

export const useNotifications = () => {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error('useNotifications must be used within NotificationProvider');
  return ctx;
};

export const NotificationProvider = ({ children }) => {
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [fetchErrorCount, setFetchErrorCount] = useState(0);
  const lastFetchRef = useRef(0);

  const fetchUnreadCount = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    try {
      const res = await api.get('/notifications/unread-count');
      if (res.data?.success) {
        setUnreadCount(res.data.data.unread_count);
      }
    } catch {
      setFetchErrorCount(prev => prev + 1);
    }
  }, []);

  const fetchNotifications = useCallback(async (page = 1, moduleFilter, search) => {
    try {
      setIsLoading(true);
      const params = { page, page_size: 20 };
      if (moduleFilter) params.module = moduleFilter;
      if (search) params.search = search;
      const res = await api.get('/notifications', { params });
      if (res.data?.success) {
        setNotifications(res.data.data.items || []);
      }
    } catch {
      setFetchErrorCount(prev => prev + 1);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const markAsRead = useCallback(async (id) => {
    try {
      await api.patch(`/notifications/${id}/read`);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch { /* silent */ }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      await api.patch('/notifications/read-all');
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch { /* silent */ }
  }, []);

  const deleteNotification = useCallback(async (id) => {
    try {
      const notif = notifications.find(n => n.id === id);
      await api.delete(`/notifications/${id}`);
      setNotifications(prev => prev.filter(n => n.id !== id));
      if (notif && !notif.is_read) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch { /* silent */ }
  }, [notifications]);

  // Poll unread count every 60 seconds (reduced from 30s to avoid over-fetching)
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 60000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  // Refetch on tab focus — but only if 30s have passed since last fetch
  useEffect(() => {
    const handleFocus = () => {
      const now = Date.now();
      if (now - lastFetchRef.current > 30000) {
        lastFetchRef.current = now;
        fetchUnreadCount();
      }
    };
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [fetchUnreadCount]);

  return (
    <NotificationContext.Provider value={{
      unreadCount, notifications, isLoading, fetchErrorCount,
      fetchUnreadCount, fetchNotifications,
      markAsRead, markAllAsRead, deleteNotification,
    }}>
      {children}
    </NotificationContext.Provider>
  );
};

export default NotificationProvider;
