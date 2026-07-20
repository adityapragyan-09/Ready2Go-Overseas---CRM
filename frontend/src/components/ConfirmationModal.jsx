import React, { useEffect, useRef } from 'react';
import { AlertTriangle, X } from 'lucide-react';

/**
 * Reusable enterprise confirmation dialog.
 * Replaces all window.confirm() and browser-native dialogs.
 *
 * Usage:
 *   const [showConfirm, setShowConfirm] = useState(false);
 *   <ConfirmationModal
 *     visible={showConfirm}
 *     title="Confirm Deletion"
 *     message="Are you sure you want to delete this item?"
 *     confirmText="Delete"
 *     confirmVariant="danger"
 *     onConfirm={() => { ... }}
 *     onCancel={() => setShowConfirm(false)}
 *   />
 *
 * Props:
 *   visible          - boolean (show/hide)
 *   title            - modal heading
 *   message          - main body text
 *   warning          - optional warning text shown below message
 *   confirmText      - confirm button label (default: "Confirm")
 *   cancelText       - cancel button label (default: "Cancel")
 *   confirmVariant   - "danger" | "warning" | "primary" (default: "danger")
 *   loading          - disables buttons when true
 *   onConfirm        - called when confirm is clicked
 *   onCancel         - called when cancel/outside is clicked
 *   children         - optional extra content between message and buttons
 */

const variantStyles = {
  danger: 'bg-red-500 hover:bg-red-600 text-white',
  warning: 'bg-amber-500 hover:bg-amber-600 text-white',
  primary: 'bg-brand-blue hover:bg-brand-blue/90 text-white',
};

export const ConfirmationModal = ({
  visible,
  title = 'Confirm Action',
  message = 'Are you sure?',
  warning,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmVariant = 'danger',
  loading = false,
  onConfirm,
  onCancel,
  children,
}) => {
  const dialogRef = useRef(null);

  // Close on Escape key
  useEffect(() => {
    if (!visible) return;
    const handleKey = (e) => {
      if (e.key === 'Escape' && onCancel) onCancel();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [visible, onCancel]);

  // Trap focus inside modal
  useEffect(() => {
    if (visible && dialogRef.current) {
      dialogRef.current.focus();
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-fade-in"
        onClick={onCancel}
      />

      {/* Modal */}
      <div
        ref={dialogRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        className="relative bg-white rounded-2xl shadow-2xl p-6 max-w-md w-full mx-4 text-left z-10 animate-scale-up"
      >
        {/* Close button */}
        <button
          onClick={onCancel}
          className="absolute top-4 right-4 p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-50 transition-all"
          aria-label="Close"
        >
          <X size={16} />
        </button>

        {/* Icon */}
        <div className="flex items-center gap-3 mb-4">
          <div className={`p-2.5 rounded-full ${
            confirmVariant === 'danger' ? 'bg-red-50 text-red-500' :
            confirmVariant === 'warning' ? 'bg-amber-50 text-amber-500' :
            'bg-brand-blue/10 text-brand-blue'
          }`}>
            <AlertTriangle size={24} />
          </div>
          <div>
            <h3 id="confirm-title" className="text-sm font-bold text-slate-800">{title}</h3>
          </div>
        </div>

        {/* Message */}
        <p className="text-xs text-slate-600 leading-relaxed">{message}</p>

        {/* Optional warning */}
        {warning && (
          <div className="mt-3 p-3 rounded-xl bg-amber-50 border border-amber-100 text-xs text-amber-700">
            {warning}
          </div>
        )}

        {/* Extra content */}
        {children && <div className="mt-4">{children}</div>}

        {/* Buttons */}
        <div className="flex gap-3 mt-6">
          <button
            onClick={onCancel}
            disabled={loading}
            className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50 transition-all disabled:opacity-50"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className={`flex-1 px-4 py-2.5 rounded-xl text-xs font-bold transition-all disabled:opacity-50 ${variantStyles[confirmVariant] || variantStyles.danger}`}
          >
            {loading ? 'Processing...' : confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationModal;
