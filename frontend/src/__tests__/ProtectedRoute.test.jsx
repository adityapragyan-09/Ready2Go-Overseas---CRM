import React from 'react';
import { render, screen } from '../test/test-utils';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from '../routes/ProtectedRoute';

// Use a mutable container so tests can change auth state between runs.
// The vi.mock factory closes over the container reference.
const mockAuthState = { value: { isAuthenticated: false, loading: false, user: null } };

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => mockAuthState.value,
}));

describe('ProtectedRoute', () => {
  function renderWithRoutes(initialEntry = '/dashboard') {
    return render(
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route path="/403" element={<div>Forbidden Page</div>} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <div>Dashboard Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );
  }

  test('redirects to /login when not authenticated', () => {
    mockAuthState.value = { isAuthenticated: false, loading: false, user: null };
    renderWithRoutes();

    // Should redirect to login and not show protected content
    expect(screen.getByText('Login Page')).toBeInTheDocument();
    expect(screen.queryByText('Dashboard Content')).not.toBeInTheDocument();
  });

  test('renders children when authenticated', () => {
    mockAuthState.value = { isAuthenticated: true, loading: false, user: { role: 'admin' } };
    renderWithRoutes();

    // Should show protected content and not redirect
    expect(screen.getByText('Dashboard Content')).toBeInTheDocument();
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument();
  });

  test('shows loading spinner while checking authentication', () => {
    mockAuthState.value = { isAuthenticated: false, loading: true, user: null };
    renderWithRoutes();

    // Loading state should render spinner text and neither protected content nor redirect
    expect(screen.getByText(/loading crm portal/i)).toBeInTheDocument();
    expect(screen.queryByText('Dashboard Content')).not.toBeInTheDocument();
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument();
  });

  test('redirects to /403 when user lacks admin role and requireAdmin is true', () => {
    mockAuthState.value = { isAuthenticated: true, loading: false, user: { role: 'employee' } };

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route path="/403" element={<div>Forbidden Page</div>} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute requireAdmin>
                <div>Dashboard Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Forbidden Page')).toBeInTheDocument();
    expect(screen.queryByText('Dashboard Content')).not.toBeInTheDocument();
  });
});
