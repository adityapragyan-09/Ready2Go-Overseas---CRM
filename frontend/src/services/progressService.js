import api from '../config/api';
import { API_ENDPOINTS } from '../constants/apiEndpoints';

const progressService = {
  /**
   * Fetch full progress history timeline for an applicant
   */
  async getTimeline(applicantId) {
    const response = await api.get(API_ENDPOINTS.PROGRESS.TIMELINE(applicantId));
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to fetch progress history timeline.');
  },

  /**
   * Transition applicant status with mandatory remarks
   */
  async updateStatus(applicantId, status, remarks) {
    const response = await api.put(API_ENDPOINTS.PROGRESS.UPDATE(applicantId), {
      status,
      remarks,
    });
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to update applicant workflow status.');
  },

  /**
   * Append an additional remark/comment note to current status
   */
  async addNote(applicantId, remarks) {
    const response = await api.post(API_ENDPOINTS.PROGRESS.NOTE, {
      applicant_id: applicantId,
      remarks,
    });
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to append progress note.');
  },

  /**
   * Fetch the latest progress timeline record
   */
  async getLatest(applicantId) {
    const response = await api.get(API_ENDPOINTS.PROGRESS.LATEST(applicantId));
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to fetch latest progress status.');
  },
};

export default progressService;
