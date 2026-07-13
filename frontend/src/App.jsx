import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './routes/ProtectedRoute';
import DashboardLayout from './layouts/DashboardLayout';
import Login from './pages/Auth/Login';
import EmployeeManagement from './pages/Employees/EmployeeManagement';

// Reusable components
import Card from './components/Card';
import PageHeader from './components/PageHeader';
import useDocumentTitle from './hooks/useDocumentTitle';

// Error Views
import Forbidden from './pages/Errors/Forbidden';
import NotFound from './pages/Errors/NotFound';
import ServerError from './pages/Errors/ServerError';

// Placeholder dashboards
const DashboardPlaceholder = () => {
  useDocumentTitle('Dashboard');
  return (
    <div className="space-y-6">
      <PageHeader 
        title="System Overview" 
        subtitle="Advisor metrics and applicant queues at a glance"
        breadcrumbs={[{ label: 'Home', path: '/dashboard' }]}
      />
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <span className="text-xs font-bold text-brand-orange uppercase tracking-wider">Applicant Queue</span>
          <h3 className="text-3xl font-extrabold text-slate-800 mt-2">--</h3>
          <p className="text-xs text-slate-400 mt-1">Active files under review</p>
        </Card>
        <Card>
          <span className="text-xs font-bold text-brand-orange uppercase tracking-wider">Document Checklist</span>
          <h3 className="text-3xl font-extrabold text-slate-800 mt-2">--</h3>
          <p className="text-xs text-slate-400 mt-1">Pending client uploads</p>
        </Card>
        <Card>
          <span className="text-xs font-bold text-brand-orange uppercase tracking-wider">Internal Chat Room</span>
          <h3 className="text-3xl font-extrabold text-slate-800 mt-2">--</h3>
          <p className="text-xs text-slate-400 mt-1">Unread advisor messages</p>
        </Card>
      </div>
    </div>
  );
};

const ApplicantsPlaceholder = () => {
  useDocumentTitle('Applicants Queue');
  return (
    <div className="space-y-6">
      <PageHeader 
        title="Applicant Management" 
        subtitle="Consolidated record list for all visa types"
        breadcrumbs={[{ label: 'Home', path: '/dashboard' }, { label: 'Applicants' }]}
      />
      <Card title="Applicant Records Queue">
        <p className="text-sm text-slate-500">This module is reserved for the consolidated visa applicant CRUD list view.</p>
      </Card>
    </div>
  );
};

const LogsPlaceholder = () => {
  useDocumentTitle('System Activity Logs');
  return (
    <div className="space-y-6">
      <PageHeader 
        title="Activity Logs" 
        subtitle="Real-time system login and event auditing"
        breadcrumbs={[{ label: 'Home', path: '/dashboard' }, { label: 'Audit logs' }]}
      />
      <Card title="Authentication Audit Stream">
        <p className="text-sm text-slate-500">Log history for internal security oversight.</p>
      </Card>
    </div>
  );
};

function App() {
  return (
    <Router>
      <AuthProvider>
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
            <Route path="/dashboard" element={<DashboardPlaceholder />} />
            <Route path="/applicants" element={<ApplicantsPlaceholder />} />
            <Route path="/employees" element={<EmployeeManagement />} />
            <Route path="/activity-logs" element={<LogsPlaceholder />} />
          </Route>

          {/* System Error Views */}
          <Route path="/403" element={<Forbidden />} />
          <Route path="/500" element={<ServerError />} />
          <Route path="/404" element={<NotFound />} />

          {/* Catch-all Routing */}
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
