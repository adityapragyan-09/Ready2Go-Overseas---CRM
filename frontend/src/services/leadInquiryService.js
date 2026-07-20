import api from '../config/api';

const leadInquiryService = {
  async getLeads(params = {}) {
    const response = await api.get('/lead-inquiries', { params });
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to fetch leads');
  },

  async getLead(id) {
    const response = await api.get(`/lead-inquiries/${id}`);
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to fetch lead');
  },

  async createLead(data) {
    const response = await api.post('/lead-inquiries', data);
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to create lead');
  },

  async updateLead(id, data) {
    const response = await api.put(`/lead-inquiries/${id}`, data);
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to update lead');
  },

  async deleteLead(id) {
    const response = await api.delete(`/lead-inquiries/${id}`);
    if (response.data && response.data.success) {
      return response.data;
    }
    throw new Error(response.data?.message || 'Failed to delete lead');
  },

  async updateStatus(id, status) {
    const response = await api.patch(`/lead-inquiries/${id}/status`, { status });
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to update status');
  },

  async assignLead(id, employeeId) {
    const response = await api.patch(`/lead-inquiries/${id}/assign`, { employee_id: employeeId });
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to assign lead');
  },
};

export default leadInquiryService;
