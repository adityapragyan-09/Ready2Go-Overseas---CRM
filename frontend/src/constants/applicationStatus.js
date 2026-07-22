/**
 * Ready2Go CRM — Application Status Constants
 *
 * Single source of truth for all status values and their visual config.
 * Used across StatusBadge, FilterPanel, ApplicantForm, and tables.
 */

export const STATUSES = [
  'inquiry',
  'documents_pending',
  'documents_submitted',
  'application_processing',
  'under_review',
  'interview_scheduled',
  'visa_approved',
  'visa_rejected',
  'approved',
  'visa_issued',
  'rejected',
  'cancelled',
  'completed',
];

export const STATUS_LABELS = {
  inquiry: 'Inquiry',
  documents_pending: 'Docs Pending',
  documents_submitted: 'Docs Submitted',
  application_processing: 'Processing',
  under_review: 'Under Review',
  interview_scheduled: 'Interview Set',
  visa_approved: 'Visa Approved',
  visa_rejected: 'Visa Rejected',
  approved: 'Approved',
  visa_issued: 'Visa Issued',
  rejected: 'Rejected',
  cancelled: 'Cancelled',
  completed: 'Completed',
};

export const STATUS_OPTIONS = STATUSES.map((s) => ({
  value: s,
  label: STATUS_LABELS[s],
}));

export default STATUS_OPTIONS;
