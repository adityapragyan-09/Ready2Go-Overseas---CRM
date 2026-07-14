import React, { createContext, useState, useEffect, useContext } from 'react';
import authService from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    // Check if user is already logged in on mount
    const checkAuth = async () => {
      if (authService.isAuthenticated()) {
        try {
          // Attempt to load profile from backend to verify token is valid
          const profile = await authService.getCurrentUser();
          if (!isMounted) return;
          setUser(profile);
          // Sync stored user with fresh profile details
          localStorage.setItem('user', JSON.stringify(profile));
        } catch (error) {
          if (!isMounted) return;
          setUser(null);
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
        }
      }
      if (isMounted) setLoading(false);
    };

    checkAuth();
    return () => { isMounted = false; };
  }, []);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const result = await authService.login(email, password);
      if (result.success) {
        setUser(result.user);
        return { success: true, user: result.user };
      }
      return { success: false, message: result.message };
    } catch (error) {
      const errMsg = error.response?.data?.message || 'Invalid email or password.';
      return { success: false, message: errMsg };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    await authService.logout();
    setUser(null);
    setLoading(false);
  };

  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
};
