import React from 'react';
import {
  HelpCircle,
  Clock,
  FileCheck,
  Cpu,
  Eye,
  Calendar,
  CheckCircle2,
  XCircle,
  Check,
  FileText,
  AlertOctagon,
  MinusCircle,
  Sparkles
} from 'lucide-react';

const statusConfig = {
  inquiry: {
    label: 'Inquiry',
    bg: 'bg-blue-50 text-blue-700 border-blue-100',
    icon: HelpCircle
  },
  documents_pending: {
    label: 'Docs Pending',
    bg: 'bg-amber-50 text-amber-700 border-amber-100',
    icon: Clock
  },
  documents_submitted: {
    label: 'Docs Submitted',
    bg: 'bg-indigo-50 text-indigo-700 border-indigo-100',
    icon: FileCheck
  },
  application_processing: {
    label: 'Processing',
    bg: 'bg-purple-50 text-purple-700 border-purple-100',
    icon: Cpu
  },
  under_review: {
    label: 'Under Review',
    bg: 'bg-sky-50 text-sky-700 border-sky-100',
    icon: Eye
  },
  interview_scheduled: {
    label: 'Interview Set',
    bg: 'bg-teal-50 text-teal-700 border-teal-100',
    icon: Calendar
  },
  visa_approved: {
    label: 'Visa Approved',
    bg: 'bg-emerald-50 text-emerald-700 border-emerald-100',
    icon: CheckCircle2
  },
  visa_rejected: {
    label: 'Visa Rejected',
    bg: 'bg-rose-50 text-rose-700 border-rose-100',
    icon: XCircle
  },
  approved: {
    label: 'Approved',
    bg: 'bg-emerald-50 text-emerald-700 border-emerald-100',
    icon: Check
  },
  visa_issued: {
    label: 'Visa Issued',
    bg: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    icon: Sparkles
  },
  rejected: {
    label: 'Rejected',
    bg: 'bg-rose-50 text-rose-700 border-rose-100',
    icon: AlertOctagon
  },
  cancelled: {
    label: 'Cancelled',
    bg: 'bg-slate-100 text-slate-600 border-slate-200',
    icon: MinusCircle
  },
  completed: {
    label: 'Completed',
    bg: 'bg-slate-100 text-slate-800 border-slate-200',
    icon: FileText
  }
};

export const StatusBadge = ({ status }) => {
  const normalizedStatus = status?.toLowerCase() || 'inquiry';
  const config = statusConfig[normalizedStatus] || {
    label: status || 'Unknown',
    bg: 'bg-slate-50 text-slate-600 border-slate-100',
    icon: HelpCircle
  };

  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border ${config.bg}`}>
      <Icon size={12} className="shrink-0" />
      {config.label}
    </span>
  );
};

export default StatusBadge;
