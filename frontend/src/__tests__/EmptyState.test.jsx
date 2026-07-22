import React from 'react';
import { render, screen } from '../test/test-utils';
import EmptyState from '../components/EmptyState';

describe('EmptyState', () => {
  test('renders default title and description', () => {
    render(<EmptyState />);

    expect(screen.getByText('No records found')).toBeInTheDocument();
    expect(
      screen.getByText('There are no active records in this view.')
    ).toBeInTheDocument();
  });

  test('renders custom title and description', () => {
    render(
      <EmptyState
        title="No applicants"
        description="There are no applicants matching your filters."
      />
    );

    expect(screen.getByText('No applicants')).toBeInTheDocument();
    expect(
      screen.getByText('There are no applicants matching your filters.')
    ).toBeInTheDocument();
  });

  test('renders optional action button', () => {
    render(
      <EmptyState
        actionButton={<button>Add Applicant</button>}
      />
    );

    expect(
      screen.getByRole('button', { name: /add applicant/i })
    ).toBeInTheDocument();
  });

  test('does not render action button slot when not provided', () => {
    render(<EmptyState />);

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
