import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import { NotificationProvider } from './context/NotificationContext';
import ProtectedRoute from './routes/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import DashboardLayout from './layouts/DashboardLayout';
import Login from './pages/Auth/Login';
import EmployeeManagement from './pages/Employees/EmployeeManagement';
import ApplicantsPage from './pages/Applicants/ApplicantsPage';

import Dashboard from './pages/Dashboard/Dashboard';
// Error Views
import Forbidden from './pages/Errors/Forbidden';
import NotFound from './pages/Errors/NotFound';
import ServerError from './pages/Errors/ServerError';

import { ActivityLogs } from './pages/ActivityLogs/ActivityLogs';
import LeadInquiriesPage from './pages/LeadInquiries/LeadInquiriesPage';
import { AssignmentRequestsPage } from './pages/AssignmentRequests/AssignmentRequestsPage';

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

        <ErrorBoundary>
          <Routes>
            {/* Root Redirect */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* Public Auth */}
            <Route path="/login" element={<Login />} />

            {/* Protected Area wrapping DashboardLayout */}
            <Route element={<ProtectedRoute><ErrorBoundary><DashboardLayout /></ErrorBoundary></ProtectedRoute>}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/applicants" element={<ApplicantsPage />} />
              <Route path="/employees" element={<EmployeeManagement />} />
              <Route path="/lead-inquiries" element={<LeadInquiriesPage />} />
              <Route path="/assignment-requests" element={<ProtectedRoute requireAdmin><AssignmentRequestsPage /></ProtectedRoute>} />
              <Route path="/activity-logs" element={<ProtectedRoute requireAdmin><ActivityLogs /></ProtectedRoute>} />
            </Route>

            {/* System Error Views */}
            <Route path="/403" element={<Forbidden />} />
            <Route path="/500" element={<ServerError />} />
            <Route path="/404" element={<NotFound />} />

            {/* Catch-all Routing */}
            <Route path="*" element={<Navigate to="/404" replace />} />
          </Routes>
        </ErrorBoundary>
        </NotificationProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
