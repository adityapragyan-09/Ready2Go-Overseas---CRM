import api from '../config/api';

const authService = {
  /**
   * Authenticate user credentials and save token/profile
   */
  async login(email, password) {
    const response = await api.post('/auth/login', { email, password });
    
    if (response.data && response.data.success) {
      const { token, user } = response.data.data;
      localStorage.setItem('access_token', token);
      localStorage.setItem('user', JSON.stringify(user));
      return { success: true, user };
    }
    
    return { success: false, message: response.data.message || 'Login failed' };
  },

  /**
   * Call backend logout and purge local storage credentials
   */
  async logout() {
    try {
      await api.post('/auth/logout');
    } catch (err) {
      console.error('Backend logout call failed, forcing client cleanup:', err);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
    }
  },

  /**
   * Retrieve currently authenticated user profile
   */
  async getCurrentUser() {
    const response = await api.get('/auth/me');
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error('Failed to fetch user profile');
  },

  /**
   * Synchronously check if token exists in client storage
   */
  isAuthenticated() {
    return !!localStorage.getItem('access_token');
  },

  /**
   * Read stored user profile details
   */
  getStoredUser() {
    const userStr = localStorage.getItem('user');
    try {
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  }
};

export default authService;
