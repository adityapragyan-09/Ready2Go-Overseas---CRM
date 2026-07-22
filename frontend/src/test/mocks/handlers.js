/**
 * Mock API response data for tests.
 *
 * These objects mirror the shape of real backend responses so that
 * vi.mock('../../config/api') can resolve with them, and they double
 * as the payloads for an optional MSW server (see server.js).
 */

export const mockAuth = {
  loginSuccess: {
    success: true,
    data: {
      token: 'mock-jwt-token',
      user: {
        id: 1,
        email: 'admin@test.com',
        role: 'admin',
        name: 'Admin User',
      },
    },
  },
  loginFailure: {
    success: false,
    message: 'Invalid email or password.',
  },
  me: {
    success: true,
    data: {
      id: 1,
      email: 'admin@test.com',
      role: 'admin',
      name: 'Admin User',
    },
  },
  meUnauthenticated: {
    success: false,
    message: 'Unauthenticated.',
  },
};

export const mockApplicants = {
  list: {
    success: true,
    data: {
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
      total_pages: 0,
    },
  },
  detail: {
    success: true,
    data: {
      id: 1,
      name: 'John Doe',
      email: 'john@example.com',
      status: 'active',
    },
  },
};

export const mockNotifications = {
  unreadCount: {
    success: true,
    data: { unread_count: 3 },
  },
};

export const mockDashboard = {
  summary: {
    success: true,
    data: {
      total_applicants: 124,
      active_cases: 67,
      pending_documents: 31,
      upcoming_deadlines: 12,
    },
  },
};
