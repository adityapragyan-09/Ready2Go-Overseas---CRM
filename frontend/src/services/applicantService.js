import api from '../config/api';
import { API_ENDPOINTS } from '../constants/apiEndpoints';

const applicantService = {
  /**
   * List applicants with optional filters, search, and pagination
   */
  async list(params = {}) {
    const response = await api.get(API_ENDPOINTS.APPLICANTS.BASE, { params });
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to fetch applicants');
  },

  /**
   * Retrieve a single applicant by ID
   */
  async get(id) {
    const response = await api.get(API_ENDPOINTS.APPLICANTS.DETAIL(id));
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to fetch applicant details');
  },

  /**
   * Create a new applicant record
   */
  async create(data) {
    const response = await api.post(API_ENDPOINTS.APPLICANTS.BASE, data);
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to create applicant');
  },

  /**
   * Update an existing applicant record
   */
  async update(id, data) {
    const response = await api.put(API_ENDPOINTS.APPLICANTS.DETAIL(id), data);
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to update applicant');
  },

  /**
   * Delete an applicant record
   */
  async delete(id) {
    const response = await api.delete(API_ENDPOINTS.APPLICANTS.DETAIL(id));
    if (response.data && response.data.success) {
      return response.data;
    }
    throw new Error(response.data?.message || 'Failed to delete applicant');
  }
};

export default applicantService;
