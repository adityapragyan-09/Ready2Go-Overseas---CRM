import React from 'react';
import { User, ArrowRight, MessageSquare, Terminal } from 'lucide-react';

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

export const ProgressRemarkCard = ({ entry }) => {
  const isTransition = entry.previous_status !== entry.current_status;
  
  const formattedDate = new Date(entry.updated_at).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  const formattedTime = new Date(entry.updated_at).toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="bg-slate-50/50 hover:bg-slate-50 transition-colors duration-200 border border-slate-100 rounded-xl p-5 flex flex-col gap-3">
      {/* Upper header */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {/* Status Label badge */}
          {isTransition ? (
            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700 bg-white border border-slate-200 px-2.5 py-1 rounded-lg">
              <span>{STATUS_LABELS[entry.previous_status] || 'None'}</span>
              <ArrowRight className="w-3 h-3 text-slate-400" />
              <span className="text-brand-orange">{STATUS_LABELS[entry.current_status]}</span>
            </div>
          ) : (
            <div className="text-xs font-bold text-slate-700 bg-white border border-slate-200 px-2.5 py-1 rounded-lg flex items-center gap-1">
              <MessageSquare className="w-3.5 h-3.5 text-brand-orange" />
              <span>Note in {STATUS_LABELS[entry.current_status]}</span>
            </div>
          )}

          {entry.is_system_generated && (
            <span className="text-[10px] bg-slate-200 text-slate-600 px-2 py-0.5 rounded-full font-bold uppercase flex items-center gap-1">
              <Terminal className="w-2.5 h-2.5" /> System
            </span>
          )}
        </div>

        {/* Date and Time */}
        <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">
          {formattedDate} — {formattedTime}
        </div>
      </div>

      {/* Remark Box */}
      <div className="bg-white border border-slate-100/50 rounded-xl p-4 text-sm text-slate-700 font-medium leading-relaxed shadow-sm">
        {entry.remarks}
      </div>

      {/* Footer metadata */}
      <div className="flex items-center gap-2 text-xs text-slate-400 font-semibold uppercase">
        <User className="w-3.5 h-3.5 text-slate-400" />
        <span>Updated By:</span>
        <span className="text-slate-700 font-bold">{entry.updated_by_name || 'System'}</span>
      </div>
    </div>
  );
};

export default ProgressRemarkCard;
