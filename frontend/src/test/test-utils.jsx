import React from 'react';
import { render } from '@testing-library/react';

/**
 * Create default mock AuthContext value.
 * Override any field by passing an object.
 */
export function createMockAuthContextValue(overrides = {}) {
  return {
    user: null,
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
    isAuthenticated: false,
    ...overrides,
  };
}

/**
 * Create default mock NotificationContext value.
 * Override any field by passing an object.
 */
export function createMockNotificationContextValue(overrides = {}) {
  return {
    unreadCount: 0,
    notifications: [],
    isLoading: false,
    fetchErrorCount: 0,
    fetchUnreadCount: vi.fn(),
    fetchNotifications: vi.fn(),
    markAsRead: vi.fn(),
    markAllAsRead: vi.fn(),
    deleteNotification: vi.fn(),
    ...overrides,
  };
}

/**
 * Custom render — use this when a component needs router context.
 * Otherwise, wrap manually in test files:
 *
 *   render(<MemoryRouter><YourComponent /></MemoryRouter>);
 */
export { render as customRender };

// Re-export @testing-library/react so tests can import everything from one place
export * from '@testing-library/react';
