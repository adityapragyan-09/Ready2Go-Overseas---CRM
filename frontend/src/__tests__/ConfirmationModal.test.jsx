import React from 'react';
import { render, screen, fireEvent } from '../test/test-utils';
import userEvent from '@testing-library/user-event';
import ConfirmationModal from '../components/ConfirmationModal';

describe('ConfirmationModal', () => {
  test('does NOT render when visible is false', () => {
    render(<ConfirmationModal visible={false} />);

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.queryByText('Confirm Action')).not.toBeInTheDocument();
  });

  test('renders with title and message when visible is true', () => {
    render(
      <ConfirmationModal
        visible={true}
        title="Delete Record"
        message="Are you sure you want to delete this record?"
      />
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Delete Record')).toBeInTheDocument();
    expect(
      screen.getByText('Are you sure you want to delete this record?')
    ).toBeInTheDocument();
  });

  test('renders confirm and cancel buttons with default labels', () => {
    render(<ConfirmationModal visible={true} />);

    expect(screen.getByRole('button', { name: /confirm/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
  });

  test('calls onConfirm when the confirm button is clicked', async () => {
    const onConfirm = vi.fn();
    const user = userEvent.setup();

    render(
      <ConfirmationModal visible={true} onConfirm={onConfirm} />
    );

    await user.click(screen.getByRole('button', { name: /confirm/i }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  test('calls onCancel when the cancel button is clicked', async () => {
    const onCancel = vi.fn();
    const user = userEvent.setup();

    render(
      <ConfirmationModal visible={true} onCancel={onCancel} />
    );

    await user.click(screen.getByRole('button', { name: /cancel/i }));

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  test('calls onCancel when the Escape key is pressed', () => {
    const onCancel = vi.fn();

    render(
      <ConfirmationModal visible={true} onCancel={onCancel} />
    );

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  test('renders custom button labels', () => {
    render(
      <ConfirmationModal
        visible={true}
        confirmText="Yes, Delete"
        cancelText="No, Keep"
      />
    );

    expect(
      screen.getByRole('button', { name: /yes, delete/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /no, keep/i })
    ).toBeInTheDocument();
  });

  test('shows warning text when provided', () => {
    render(
      <ConfirmationModal
        visible={true}
        warning="This action cannot be undone."
      />
    );

    expect(
      screen.getByText('This action cannot be undone.')
    ).toBeInTheDocument();
  });

  test('disables confirm and cancel buttons when loading is true', () => {
    render(
      <ConfirmationModal visible={true} loading={true} />
    );

    // When loading, the confirm button renders "Processing..."
    // The close button (aria-label="Close") is always enabled, so we only
    // check the two action buttons.
    const confirmBtn = screen.getByRole('button', { name: /processing/i });
    const cancelBtn = screen.getByRole('button', { name: /cancel/i });

    expect(confirmBtn).toBeDisabled();
    expect(cancelBtn).toBeDisabled();
  });

  test('renders children content between message and buttons', () => {
    render(
      <ConfirmationModal visible={true}>
        <div>Extra Content Here</div>
      </ConfirmationModal>
    );

    expect(screen.getByText('Extra Content Here')).toBeInTheDocument();
  });
});
