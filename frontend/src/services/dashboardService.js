import api from '../config/api';

const dashboardService = {
  /**
   * Fetch high-level overview metrics
   */
  async getSummary() {
    const response = await api.get('/dashboard/summary');
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch summary');
  },

  /**
   * Fetch visual charts datasets
   */
  async getCharts() {
    const response = await api.get('/dashboard/charts');
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch charts');
  },

  /**
   * Fetch recent CRM events activities feed
   */
  async getRecent() {
    const response = await api.get('/dashboard/recent');
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch recent events');
  },

  /**
   * Fetch counselor analytics workloads
   */
  async getEmployees() {
    const response = await api.get('/dashboard/employees');
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch employee workload');
  },

  /**
   * Fetch system and database parameters
   */
  async getSystem() {
    const response = await api.get('/dashboard/system');
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch system details');
  }
};

export default dashboardService;
