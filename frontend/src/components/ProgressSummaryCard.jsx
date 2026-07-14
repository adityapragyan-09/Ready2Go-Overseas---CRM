import React from 'react';
import { User, Calendar, Award, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

const STATUS_CONFIGS = {
  inquiry: { label: 'Inquiry', percentage: 10, bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', barColor: 'bg-blue-600' },
  documents_pending: { label: 'Documents Pending', percentage: 25, bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', barColor: 'bg-amber-500' },
  documents_submitted: { label: 'Documents Submitted', percentage: 40, bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200', barColor: 'bg-indigo-600' },
  application_processing: { label: 'Application Processing', percentage: 60, bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200', barColor: 'bg-purple-600' },
  under_review: { label: 'Under Review', percentage: 70, bg: 'bg-violet-50', text: 'text-violet-700', border: 'border-violet-200', barColor: 'bg-violet-600' },
  interview_scheduled: { label: 'Interview Scheduled', percentage: 80, bg: 'bg-pink-50', text: 'text-pink-700', border: 'border-pink-200', barColor: 'bg-pink-600' },
  visa_approved: { label: 'Visa Approved', percentage: 95, bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', barColor: 'bg-emerald-500' },
  completed: { label: 'Completed', percentage: 100, bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200', barColor: 'bg-green-600' },
  visa_rejected: { label: 'Visa Rejected', percentage: 100, bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200', barColor: 'bg-rose-600' },
  cancelled: { label: 'Cancelled', percentage: 100, bg: 'bg-slate-50', text: 'text-slate-700', border: 'border-slate-200', barColor: 'bg-slate-500' },
};

export const ProgressSummaryCard = ({ applicant, latestHistory }) => {
  const status = applicant?.status || 'inquiry';
  const config = STATUS_CONFIGS[status] || STATUS_CONFIGS.inquiry;
  
  const formattedDate = latestHistory
    ? new Date(latestHistory.updated_at).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : null;

  const formattedTime = latestHistory
    ? new Date(latestHistory.updated_at).toLocaleTimeString(undefined, {
        hour: '2-digit',
        minute: '2-digit',
      })
    : null;

  const renderStatusIcon = () => {
    if (status === 'completed' || status === 'visa_approved') {
      return <CheckCircle2 className="w-5 h-5 text-green-600" />;
    }
    if (status === 'visa_rejected') {
      return <XCircle className="w-5 h-5 text-rose-600" />;
    }
    if (status === 'cancelled') {
      return <AlertTriangle className="w-5 h-5 text-slate-600" />;
    }
    return <Award className="w-5 h-5 text-brand-orange animate-pulse" />;
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-md">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-brand-black via-slate-800 to-brand-orange p-6 text-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-xs uppercase tracking-wider font-semibold opacity-75">
              Visa Journey Status
            </span>
            <h2 className="text-xl font-bold mt-1 flex items-center gap-2">
              {config.label}
              <div className="bg-white/10 p-1 rounded-lg backdrop-blur-md">
                {renderStatusIcon()}
              </div>
            </h2>
          </div>
          <div className="text-right">
            <span className="text-xs opacity-75 block uppercase font-semibold">
              Completion Progress
            </span>
            <span className="text-3xl font-extrabold tracking-tight">
              {config.percentage}%
            </span>
          </div>
        </div>

        {/* Progress Bar Container */}
        <div className="mt-4">
          <div className="w-full bg-white/20 rounded-full h-3 overflow-hidden backdrop-blur-sm">
            <div
              className={`h-full ${config.barColor} transition-all duration-1000 ease-out`}
              style={{ width: `${config.percentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Details Section */}
      <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Current status info */}
        <div className="flex items-start gap-3">
          <div className="p-3 bg-slate-50 text-slate-600 rounded-xl">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-semibold uppercase">Current Stage</p>
            <p className="text-sm font-bold text-slate-800 mt-1">{config.label}</p>
          </div>
        </div>

        {/* Counselor info */}
        <div className="flex items-start gap-3">
          <div className="p-3 bg-slate-50 text-slate-600 rounded-xl">
            <User className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-semibold uppercase">Assigned Counselor</p>
            <p className="text-sm font-bold text-slate-800 mt-1">
              {applicant?.assigned_employee_name || 'Unassigned'}
            </p>
          </div>
        </div>

        {/* Last updated info */}
        <div className="flex items-start gap-3">
          <div className="p-3 bg-slate-50 text-slate-600 rounded-xl">
            <Calendar className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-semibold uppercase">Last Updated</p>
            {formattedDate ? (
              <div className="mt-1">
                <p className="text-sm font-bold text-slate-800">
                  {formattedDate} at {formattedTime}
                </p>
                <p className="text-[10px] text-slate-400 font-semibold uppercase mt-0.5">
                  By {latestHistory?.updated_by_name || 'System'}
                </p>
              </div>
            ) : (
              <p className="text-sm font-semibold text-slate-500 mt-1">—</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProgressSummaryCard;
