import React, { useState, useEffect } from 'react';
import { X, Save, AlertCircle, MessageSquare } from 'lucide-react';
import toast from 'react-hot-toast';
import progressService from '../services/progressService';

const VALID_TRANSITIONS = {
  inquiry: ['documents_pending', 'cancelled'],
  documents_pending: ['documents_submitted', 'cancelled'],
  documents_submitted: ['application_processing', 'cancelled'],
  application_processing: ['interview_scheduled', 'visa_approved', 'visa_rejected', 'cancelled'],
  interview_scheduled: ['visa_approved', 'visa_rejected', 'cancelled'],
  visa_approved: ['completed', 'cancelled'],
  completed: [],
  visa_rejected: [],
  cancelled: [],
};

const STATUS_LABELS = {
  inquiry: 'Inquiry',
  documents_pending: 'Documents Pending',
  documents_submitted: 'Documents Submitted',
  application_processing: 'Application Processing',
  under_review: 'Under Review',
  interview_scheduled: 'Interview Scheduled',
  visa_approved: 'Visa Approved',
  visa_rejected: 'Visa Rejected',
  completed: 'Completed',
  cancelled: 'Cancelled',
};

export const StatusUpdateModal = ({ isOpen, onClose, applicant, mode, onSaveSuccess }) => {
  const [selectedStatus, setSelectedStatus] = useState('');
  const [remarks, setRemarks] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const currentStatus = applicant?.status || 'inquiry';
  const allowedNext = VALID_TRANSITIONS[currentStatus] || [];

  // Reset fields on open
  useEffect(() => {
    if (isOpen) {
      setRemarks('');
      if (allowedNext.length > 0) {
        setSelectedStatus(allowedNext[0]);
      } else {
        setSelectedStatus('');
      }
    }
  }, [isOpen, currentStatus]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!remarks.trim()) {
      toast.error('Remarks are required.');
      return;
    }
    if (mode === 'status' && !selectedStatus) {
      toast.error('Please select a target status.');
      return;
    }

    setIsSubmitting(true);
    try {
      if (mode === 'status') {
        await progressService.updateStatus(applicant.id, selectedStatus, remarks);
        toast.success(`Applicant status successfully updated to ${STATUS_LABELS[selectedStatus]}.`);
      } else {
        await progressService.addNote(applicant.id, remarks);
        toast.success('Progress note appended successfully.');
      }
      onSaveSuccess();
      onClose();
    } catch (err) {
      toast.error(err.message || 'Operation failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-brand-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-100 animate-scale-up" role="dialog" aria-modal="true" aria-labelledby="status-modal-title">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-100 bg-slate-50/50">
          <h3 id="status-modal-title" className="text-base font-bold text-slate-800 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-brand-orange" />
            {mode === 'status' ? 'Transition Status Stage' : 'Append Progress Remark Note'}
          </h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 transition-colors p-1 rounded-lg hover:bg-slate-100"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit}>
          <div className="p-6 flex flex-col gap-5">
            {/* Current Stage */}
            <div>
              <label className="text-xs text-slate-400 font-bold uppercase tracking-wider block mb-1">
                Current Status Stage
              </label>
              <div className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-700">
                {STATUS_LABELS[currentStatus]}
              </div>
            </div>

            {/* Target Status Selector (Status mode only) */}
            {mode === 'status' && (
              <div>
                <label className="text-xs text-slate-400 font-bold uppercase tracking-wider block mb-1.5">
                  Target Status Stage
                </label>
                {allowedNext.length > 0 ? (
                  <select
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value)}
                    className="w-full bg-white border border-slate-200 focus:border-brand-orange focus:ring-1 focus:ring-brand-orange/20 rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-700 transition-all outline-none"
                  >
                    {allowedNext.map((key) => (
                      <option key={key} value={key}>
                        {STATUS_LABELS[key]}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="flex items-start gap-2 bg-rose-50 border border-rose-100 text-rose-700 rounded-xl p-3.5 text-xs font-semibold">
                    <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                    <span>
                      Applicant has reached the terminal stage ({STATUS_LABELS[currentStatus]}).
                      No further transitions can be executed.
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* Remarks Input */}
            <div>
              <label className="text-xs text-slate-400 font-bold uppercase tracking-wider block mb-1.5">
                Remarks / Comments <span className="text-rose-500">*</span>
              </label>
              <textarea
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                placeholder={
                  mode === 'status'
                    ? 'Enter reasons and descriptions for this status progression...'
                    : 'Enter audit comments or check-in notes to add to this stage...'
                }
                rows={4}
                required
                className="w-full bg-white border border-slate-200 focus:border-brand-orange focus:ring-1 focus:ring-brand-orange/20 rounded-xl px-4 py-3 text-sm font-medium text-slate-700 placeholder:text-slate-400 transition-all outline-none resize-none"
              />
            </div>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-3 p-5 border-t border-slate-100 bg-slate-50/50">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-xs font-bold text-slate-500 hover:text-slate-700 bg-white border border-slate-200 rounded-xl transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || (mode === 'status' && allowedNext.length === 0)}
              className="flex items-center gap-2 px-5 py-2 text-xs font-bold text-white bg-brand-orange hover:bg-orange-600 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm shadow-orange-100"
            >
              {isSubmitting ? (
                'Saving...'
              ) : (
                <>
                  <Save className="w-3.5 h-3.5" /> Save Changes
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default StatusUpdateModal;
