/**
 * Ready2Go CRM — API Endpoint Constants
 *
 * Defines all backend endpoint relative paths.
 * Import these whenever making API calls.
 */

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    ME: '/auth/me',
  },
  APPLICANTS: {
    BASE: '/applicants',
    DETAIL: (id) => `/applicants/${id}`,
    DOCUMENTS: (id) => `/applicants/${id}/documents`,
    MESSAGES: (id) => `/applicants/${id}/messages`,
    PROGRESS: (id) => `/applicants/${id}/progress`,
  },
  EMPLOYEES: {
    BASE: '/employees',
    DETAIL: (id) => `/employees/${id}`,
  },
  DASHBOARD: {
    STATS: '/dashboard/stats',
  },
  ACTIVITY_LOGS: {
    BASE: '/activity-logs',
  },
};

export default API_ENDPOINTS;
