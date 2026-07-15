/**
 * Ready2Go CRM — API Endpoint Constants
 *
 * Defines all backend endpoint relative paths used across services.
 * Services import these to ensure API path consistency.
 *
 * All paths are relative — the axios baseURL (VITE_API_BASE_URL)
 * prefixes them automatically.
 */

export const API_ENDPOINTS = {
  APPLICANTS: {
    BASE: '/applicants',
    DETAIL: (id) => `/applicants/${id}`,
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
};

export default API_ENDPOINTS;
