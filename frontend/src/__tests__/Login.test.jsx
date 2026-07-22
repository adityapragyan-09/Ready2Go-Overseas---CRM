import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import Login from '../pages/Auth/Login';

const mockLogin = vi.fn();

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: null,
    loading: false,
    login: mockLogin,
    logout: vi.fn(),
    isAuthenticated: false,
  }),
}));

vi.mock('react-hot-toast', () => ({
  default: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

function renderLogin() {
  return render(
    <MemoryRouter>
      <Login />
    </MemoryRouter>
  );
}

describe('Login Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders login form with all required elements', () => {
    renderLogin();

    // Portal heading
    expect(screen.getByRole('heading', { name: /administrator portal/i })).toBeInTheDocument();

    // Tab buttons
    expect(screen.getByRole('button', { name: /admin login/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /employee login/i })).toBeInTheDocument();

    // Form with accessible label
    expect(screen.getByRole('form', { name: /login form/i })).toBeInTheDocument();

    // Input fields
    expect(screen.getByPlaceholderText('admin@ready2gooverseas.com')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();

    // Submit button
    expect(screen.getByRole('button', { name: /authenticate admin/i })).toBeInTheDocument();
  });

  test('shows validation errors for empty fields on submit', async () => {
    const user = userEvent.setup();
    renderLogin();

    // Submit the form without filling in any fields
    await user.click(screen.getByRole('button', { name: /authenticate admin/i }));

    // Zod validation errors should appear
    expect(await screen.findByText('Email is required')).toBeInTheDocument();
    expect(screen.getByText('Password must be at least 6 characters')).toBeInTheDocument();
  });

  test('calls login API on valid form submission', async () => {
    mockLogin.mockResolvedValue({ success: true, user: { role: 'admin' } });
    const user = userEvent.setup();
    renderLogin();

    // Fill in form fields
    await user.type(screen.getByPlaceholderText('admin@ready2gooverseas.com'), 'admin@test.com');
    await user.type(screen.getByPlaceholderText('••••••••'), 'password123');

    // Submit
    await user.click(screen.getByRole('button', { name: /authenticate admin/i }));

    // Verify login was called with the entered credentials
    expect(mockLogin).toHaveBeenCalledTimes(1);
    expect(mockLogin).toHaveBeenCalledWith('admin@test.com', 'password123');
  });
});
