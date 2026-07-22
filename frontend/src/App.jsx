import React, { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import { NotificationProvider } from './context/NotificationContext';
import ProtectedRoute from './routes/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import LoadingSpinner from './components/LoadingSpinner';
import DashboardLayout from './layouts/DashboardLayout';
import Login from './pages/Auth/Login';

// Route-level code splitting — each page is a separate chunk
const Dashboard = lazy(() => import('./pages/Dashboard/Dashboard'));
const EmployeeManagement = lazy(() => import('./pages/Employees/EmployeeManagement'));
const ApplicantsPage = lazy(() => import('./pages/Applicants/ApplicantsPage'));
const LeadInquiriesPage = lazy(() => import('./pages/LeadInquiries/LeadInquiriesPage'));
const ActivityLogs = lazy(() => import('./pages/ActivityLogs/ActivityLogs'));
const AssignmentRequestsPage = lazy(() => import('./pages/AssignmentRequests/AssignmentRequestsPage'));
const InboxPage = lazy(() => import('./pages/Notifications/InboxPage'));
const Forbidden = lazy(() => import('./pages/Errors/Forbidden'));
const NotFound = lazy(() => import('./pages/Errors/NotFound'));
const ServerError = lazy(() => import('./pages/Errors/ServerError'));

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
                primary: '#f68b1e',
                secondary: '#fff',
              },
            },
          }}
        />

        <ErrorBoundary>
          <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
              <LoadingSpinner label="Loading Ready2Go CRM..." size="lg" />
            </div>
          }>
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
              <Route path="/inbox" element={<InboxPage />} />
              <Route path="/activity-logs" element={<ProtectedRoute requireAdmin><ActivityLogs /></ProtectedRoute>} />
            </Route>

            {/* System Error Views */}
            <Route path="/403" element={<Forbidden />} />
            <Route path="/500" element={<ServerError />} />
            <Route path="/404" element={<NotFound />} />

            {/* Catch-all Routing */}
            <Route path="*" element={<Navigate to="/404" replace />} />
          </Routes>
          </Suspense>
        </ErrorBoundary>
        </NotificationProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
