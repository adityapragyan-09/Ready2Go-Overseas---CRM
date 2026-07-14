import axios from 'axios';
import { appConfig } from './appConfig';

const api = axios.create({
  baseURL: appConfig.API_BASE_URL,
  timeout: appConfig.API_TIMEOUT_MS,
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
      return Promise.reject(new Error('Network error. Unable to connect to server.'));
    }

    // 2. 401 Unauthorized handling
    if (error.response.status === 401) {
      // Clear client session
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      
      // BUG FIX: Use history.pushState + popstate event instead of
      // window.location.href which causes a full page reload, destroys the
      // React app state, and leaves the Login page title on the /dashboard URL.
      // React Router's BrowserRouter listens to the popstate event and will
      // re-render the correct route without a hard reload.
      if (!window.location.pathname.endsWith('/login')) {
        window.history.pushState({}, '', '/login?expired=true');
        window.dispatchEvent(new PopStateEvent('popstate'));
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
