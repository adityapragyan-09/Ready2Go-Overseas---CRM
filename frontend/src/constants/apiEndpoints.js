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
  DOCUMENTS: {
    UPLOAD: '/documents/upload',
    APPLICANT: (applicantId) => `/documents/applicant/${applicantId}`,
    DOWNLOAD: (documentId) => `/documents/${documentId}/download`,
    VIEW: (documentId) => `/documents/${documentId}/view`,
    DETAIL: (documentId) => `/documents/${documentId}`,
  },
  PROGRESS: {
    TIMELINE: (applicantId) => `/progress/applicant/${applicantId}`,
    UPDATE: (applicantId) => `/progress/applicant/${applicantId}`,
    NOTE: '/progress/note',
    LATEST: (applicantId) => `/progress/latest/${applicantId}`,
  },
  CHAT: {
    CONVERSATION: (applicantId) => `/chat/applicant/${applicantId}`,
    CREATE: (applicantId) => `/chat/applicant/${applicantId}`,
    DELETE: (messageId) => `/chat/${messageId}`,
    LATEST: (applicantId) => `/chat/latest/${applicantId}`,
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
