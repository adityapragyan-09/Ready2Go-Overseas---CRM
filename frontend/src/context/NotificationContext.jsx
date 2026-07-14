import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
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

  const fetchUnreadCount = useCallback(async () => {
    try {
      const res = await api.get('/notifications/unread-count');
      if (res.data?.success) {
        setUnreadCount(res.data.data.unread_count);
      }
    } catch (err) {
      // Silent fail - non-critical
    }
  }, []);

  const fetchNotifications = useCallback(async (page = 1) => {
    try {
      setIsLoading(true);
      const res = await api.get('/notifications', { params: { page, page_size: 20 } });
      if (res.data?.success) {
        setNotifications(res.data.data.items || []);
      }
    } catch (err) {
      // Silent fail
    } finally {
      setIsLoading(false);
    }
  }, []);

  const markAsRead = useCallback(async (id) => {
    try {
      await api.patch(`/notifications/${id}/read`);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) { /* silent */ }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      await api.patch('/notifications/read-all');
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) { /* silent */ }
  }, []);

  const deleteNotification = useCallback(async (id) => {
    try {
      const notif = notifications.find(n => n.id === id);
      await api.delete(`/notifications/${id}`);
      setNotifications(prev => prev.filter(n => n.id !== id));
      if (notif && !notif.is_read) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (err) { /* silent */ }
  }, [notifications]);

  // Poll unread count every 30 seconds
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  // Refetch on tab focus
  useEffect(() => {
    const handleFocus = () => fetchUnreadCount();
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [fetchUnreadCount]);

  return (
    <NotificationContext.Provider value={{
      unreadCount, notifications, isLoading,
      fetchUnreadCount, fetchNotifications,
      markAsRead, markAllAsRead, deleteNotification,
    }}>
      {children}
    </NotificationContext.Provider>
  );
};

export default NotificationProvider;
