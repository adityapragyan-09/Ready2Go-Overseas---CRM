/**
 * Ready2Go CRM — Visa Type Constants
 *
 * Single source of truth for all visa type configurations.
 */

export const VISA_TYPES = ['student', 'visit', 'tourist', 'business'];

export const VISA_LABELS = {
  student: 'Student Visa',
  visit: 'Visit Visa',
  tourist: 'Tourist Visa',
  business: 'Business Visa',
};

export const VISA_ICONS = {
  student: 'GraduationCap',
  visit: 'Compass',
  tourist: 'Plane',
  business: 'Briefcase',
};

export const VISA_OPTIONS = VISA_TYPES.map((v) => ({
  value: v,
  label: VISA_LABELS[v],
}));

export default VISA_OPTIONS;
