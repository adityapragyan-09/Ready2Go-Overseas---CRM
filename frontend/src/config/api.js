import axios from 'axios';

// Resolve Backend base API URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 seconds timeout to prevent hanging connections
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Automatically attach JWT access token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Catch 401 Unauthorized and auto-logout
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 1. Network level error or timeout
    if (!error.response) {
      console.error('Network/Server offline error:', error.message);
      return Promise.reject(new Error('Network error. Unable to connect to server.'));
    }

    // 2. 401 Unauthorized handling
    if (error.response.status === 401) {
      // Clear client session
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      
      // Prevent infinite redirect loops on the login page
      if (!window.location.pathname.endsWith('/login')) {
        window.location.href = '/login?expired=true';
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
