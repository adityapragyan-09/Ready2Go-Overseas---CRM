import React from 'react';
import { CheckCircle2, Circle, Clock, AlertCircle } from 'lucide-react';

const statusFlow = [
  { value: 'inquiry', label: 'Inquiry', matches: ['inquiry'] },
  { value: 'documents_pending', label: 'Documents Pending', matches: ['documents_pending'] },
  { value: 'documents_submitted', label: 'Documents Submitted', matches: ['documents_submitted'] },
  { value: 'application_processing', label: 'Application Processing', matches: ['application_processing', 'under_review'] },
  { value: 'interview_scheduled', label: 'Interview Scheduled', matches: ['interview_scheduled'] },
  { value: 'visa_approved', label: 'Visa Approved', matches: ['visa_approved', 'visa_rejected', 'approved', 'rejected', 'visa_issued'] },
  { value: 'completed', label: 'Completed', matches: ['completed', 'cancelled'] }
];

export const StatusTimeline = ({ currentStatus }) => {
  const normalizedCurrent = currentStatus?.toLowerCase() || 'inquiry';
  
  // Find current index in flow based on matches
  const currentIndex = statusFlow.findIndex(s => s.matches.includes(normalizedCurrent));
  const activeIndex = currentIndex === -1 ? 0 : currentIndex;
  
  const isFailureStatus = ['visa_rejected', 'rejected', 'cancelled'].includes(normalizedCurrent);

  return (
    <div className="w-full py-6 text-left">
      <div className="relative flex flex-col md:flex-row justify-between items-start md:items-center gap-6 md:gap-4">
        
        {/* Connection Line (Desktop) */}
        <div className="absolute top-[18px] left-4 right-4 h-0.5 bg-slate-200 hidden md:block z-0">
          <div 
            className="h-full bg-emerald-500 transition-all duration-500" 
            style={{ 
              width: `${(activeIndex / (statusFlow.length - 1)) * 100}%` 
            }}
          />
        </div>
        
        {statusFlow.map((step, idx) => {
          const isCompleted = idx < activeIndex;
          const isActive = idx === activeIndex;
          
          // Determine custom label if failure state
          let displayLabel = step.label;
          if (isActive && isFailureStatus) {
            if (normalizedCurrent === 'cancelled') {
              displayLabel = 'Cancelled';
            } else {
              displayLabel = 'Visa Rejected';
            }
          }

          return (
            <div key={step.value} className="flex md:flex-col items-center gap-4 md:gap-2.5 z-10 w-full md:w-auto">
              
              {/* Node Indicator */}
              <div className="shrink-0 flex items-center justify-center">
                {isCompleted ? (
                  <div className="w-9 h-9 rounded-full bg-emerald-500 text-white flex items-center justify-center border-4 border-emerald-50 shadow-md">
                    <CheckCircle2 size={16} />
                  </div>
                ) : isActive ? (
                  <div className={`w-9 h-9 rounded-full ${isFailureStatus ? 'bg-red-500' : 'bg-brand-orange'} text-white flex items-center justify-center border-4 ${isFailureStatus ? 'border-red-50' : 'border-brand-orange/20'} shadow-md animate-pulse`}>
                    {isFailureStatus ? <AlertCircle size={16} /> : <Clock size={16} />}
                  </div>
                ) : (
                  <div className="w-9 h-9 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center border-4 border-white shadow-sm">
                    <Circle size={14} />
                  </div>
                )}
              </div>

              {/* Step Info */}
              <div className="flex flex-col md:items-center text-left md:text-center min-w-0">
                <span className={`text-xs font-bold ${isActive ? 'text-slate-800' : isCompleted ? 'text-slate-600' : 'text-slate-400'}`}>
                  {displayLabel}
                </span>
                {isActive && (
                  <span className={`text-[9px] font-extrabold uppercase tracking-wider px-1.5 py-0.5 rounded mt-0.5 ${isFailureStatus ? 'bg-red-50 text-red-600' : 'bg-brand-orange/10 text-brand-orange'}`}>
                    {isFailureStatus ? 'Terminated' : 'Active Status'}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StatusTimeline;
