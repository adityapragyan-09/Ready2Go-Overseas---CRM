import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

/**
 * Route guard component that protects sub-routes from unauthenticated users.
 */
const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { isAuthenticated, loading, user } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-4">
          {/* Custom brand-themed premium spinner */}
          <div className="relative w-12 h-12">
            <div className="absolute inset-0 rounded-full border-4 border-slate-100"></div>
            <div className="absolute inset-0 rounded-full border-4 border-brand-orange border-t-transparent animate-spin"></div>
          </div>
          <span className="text-sm font-medium text-slate-500 animate-pulse">Loading CRM Portal...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Save the location they were trying to access to redirect them back after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireAdmin && user?.role !== 'admin') {
    return <Navigate to="/403" replace />;
  }

  return children;
};

export default ProtectedRoute;
