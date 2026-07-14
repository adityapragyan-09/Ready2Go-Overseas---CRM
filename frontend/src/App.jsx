import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import { NotificationProvider } from './context/NotificationContext';
import ProtectedRoute from './routes/ProtectedRoute';
import DashboardLayout from './layouts/DashboardLayout';
import Login from './pages/Auth/Login';
import EmployeeManagement from './pages/Employees/EmployeeManagement';
import ApplicantsPage from './pages/Applicants/ApplicantsPage';

import Dashboard from './pages/Dashboard/Dashboard';

// Reusable components
import Card from './components/Card';
import PageHeader from './components/PageHeader';
import useDocumentTitle from './hooks/useDocumentTitle';

// Error Views
import Forbidden from './pages/Errors/Forbidden';
import NotFound from './pages/Errors/NotFound';
import ServerError from './pages/Errors/ServerError';

import { ActivityLogs } from './pages/ActivityLogs/ActivityLogs';

function App() {
  return (
    <Router>
      <AuthProvider>
        <NotificationProvider>
        {/* Toast notifications rendering container */}
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            className: 'text-sm font-semibold text-slate-800 rounded-xl shadow-lg border border-slate-100 bg-white/95 backdrop-blur-md',
            success: {
              iconTheme: {
                primary: '#f68b1e', // Orange icon theme matching success response alerts
                secondary: '#fff',
              },
            },
          }}
        />

        <Routes>
          {/* Root Redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* Public Auth */}
          <Route path="/login" element={<Login />} />

          {/* Protected Area wrapping DashboardLayout */}
          <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/applicants" element={<ApplicantsPage />} />
            <Route path="/employees" element={<EmployeeManagement />} />
            <Route path="/activity-logs" element={<ActivityLogs />} />
          </Route>

          {/* System Error Views */}
          <Route path="/403" element={<Forbidden />} />
          <Route path="/500" element={<ServerError />} />
          <Route path="/404" element={<NotFound />} />

          {/* Catch-all Routing */}
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Routes>
        </NotificationProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
