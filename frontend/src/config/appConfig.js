/**
 * Ready2Go CRM — Centralized Frontend Configuration
 *
 * All values loaded from VITE_* environment variables.
 * In production, VITE_API_BASE_URL must be set to the deployed backend URL.
 * In development, fallback to localhost if no env vars are set.
 */

export const appConfig = {
  APP_NAME: import.meta.env.VITE_APP_NAME || 'Ready2Go CRM',

  // API Base URL: In production, VITE_API_BASE_URL MUST be set.
  // In development, defaults to localhost if not configured.
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL
    || import.meta.env.VITE_API_URL
    || (import.meta.env.PROD ? null : 'http://localhost:8000/api/v1'),

  MAX_UPLOAD_SIZE_MB: Number(import.meta.env.VITE_MAX_UPLOAD_SIZE_MB) || 500,
  ALLOWED_DOCUMENT_TYPES: (import.meta.env.VITE_ALLOWED_DOCUMENT_TYPES || 'pdf,jpg,jpeg,png,doc,docx')
    .split(',')
    .map((ext) => ext.trim().toLowerCase()),
  DEFAULT_PAGE_SIZE: Number(import.meta.env.VITE_DEFAULT_PAGE_SIZE) || 10,
  API_TIMEOUT_MS: Number(import.meta.env.VITE_API_TIMEOUT_MS) || 600000,
};

export default appConfig;
