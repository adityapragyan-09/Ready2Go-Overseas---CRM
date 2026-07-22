import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PageHeader from '../components/PageHeader';

/**
 * PageHeader renders optional <Link> components when breadcrumbs
 * include a path, so it must be inside a Router context.
 */
function renderWithRouter(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('PageHeader', () => {
  test('renders title', () => {
    renderWithRouter(<PageHeader title="Dashboard" />);

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  test('renders subtitle', () => {
    renderWithRouter(<PageHeader title="Dashboard" subtitle="Welcome back, Admin" />);

    expect(screen.getByText('Welcome back, Admin')).toBeInTheDocument();
  });

  test('renders breadcrumbs with links and current page', () => {
    renderWithRouter(
      <PageHeader
        title="Applicants"
        breadcrumbs={[
          { label: 'Home', path: '/' },
          { label: 'CRM' },
        ]}
      />
    );

    // Breadcrumb with a path should render as a link
    const homeLink = screen.getByText('Home');
    expect(homeLink).toBeInTheDocument();
    expect(homeLink.closest('a')).toHaveAttribute('href', '/');

    // Breadcrumb without a path should render as plain text
    expect(screen.getByText('CRM')).toBeInTheDocument();
  });

  test('renders action slot', () => {
    renderWithRouter(
      <PageHeader
        title="Applicants"
        action={<button>Add New</button>}
      />
    );

    expect(
      screen.getByRole('button', { name: /add new/i })
    ).toBeInTheDocument();
  });

  test('does not render breadcrumbs when none are provided', () => {
    renderWithRouter(<PageHeader title="Dashboard" />);

    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });
});
