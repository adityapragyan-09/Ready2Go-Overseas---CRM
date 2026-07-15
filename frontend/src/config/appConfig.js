/**
 * Ready2Go CRM — Centralized Frontend Configuration
 *
 * All values are loaded from VITE_* environment variables at build time.
 * In production, VITE_API_BASE_URL must be set via the hosting platform
 * environment variables (Netlify Dashboard → Environment).
 *
 * Fallback values are for local development only — production builds
 * will not have localhost fallbacks available.
 */

export const appConfig = {
  APP_NAME: import.meta.env.VITE_APP_NAME || 'Ready2Go CRM',

  // API Base URL: Production value set at build time by Netlify env vars.
  // Falls back to localhost for local `npm run dev` without a .env file.
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
