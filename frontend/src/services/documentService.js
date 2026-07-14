import api from '../config/api';
import { API_ENDPOINTS } from '../constants/apiEndpoints';

const documentService = {
  /**
   * Upload a new document file for an applicant with progress tracking.
   */
  async upload(file, applicantId, documentType, onUploadProgress) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('applicant_id', applicantId);
    formData.append('document_type', documentType);

    const response = await api.post(API_ENDPOINTS.DOCUMENTS.UPLOAD, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(percentCompleted);
        }
      }
    });

    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to upload document');
  },

  /**
   * List all active documents for a given applicant.
   */
  async list(applicantId) {
    const response = await api.get(API_ENDPOINTS.DOCUMENTS.APPLICANT(applicantId));
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to retrieve documents');
  },

  /**
   * Generate secure download signed URL.
   */
  async download(documentId) {
    const response = await api.get(API_ENDPOINTS.DOCUMENTS.DOWNLOAD(documentId));
    if (response.data && response.data.success) {
      return response.data.data; // contains download_url, original_file_name, etc.
    }
    throw new Error(response.data?.message || 'Failed to get secure download link');
  },

  /**
   * Generate secure view signed URL.
   */
  async getPreviewUrl(documentId) {
    const response = await api.get(API_ENDPOINTS.DOCUMENTS.VIEW(documentId));
    if (response.data && response.data.success) {
      return response.data.data; // contains view_url, original_file_name, etc.
    }
    throw new Error(response.data?.message || 'Failed to get secure preview link');
  },

  /**
   * Soft delete a document by ID.
   */
  async delete(documentId) {
    const response = await api.delete(API_ENDPOINTS.DOCUMENTS.DETAIL(documentId));
    if (response.data && response.data.success) {
      return response.data;
    }
    throw new Error(response.data?.message || 'Failed to delete document');
  }
};

export default documentService;
