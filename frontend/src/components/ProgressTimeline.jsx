import React from 'react';
import { Check, Clock, AlertTriangle, AlertOctagon } from 'lucide-react';

const STEPS = [
  { key: 'inquiry', label: 'Inquiry', desc: 'Consultation & intake form' },
  { key: 'documents_pending', label: 'Documents Pending', desc: 'Compiling required documents' },
  { key: 'documents_submitted', label: 'Documents Submitted', desc: 'Files received & validated' },
  { key: 'application_processing', label: 'Application Processing', desc: 'Filing & lodging with embassy' },
  { key: 'interview_scheduled', label: 'Interview Scheduled', desc: 'Biometrics & interview prep' },
  { key: 'visa_approved', label: 'Visa Approved', desc: 'Visa granted by embassy' },
  { key: 'completed', label: 'Completed', desc: 'Pre-departure & visa handover' }
];

export const ProgressTimeline = ({ currentStatus }) => {
  // Determine index of current status
  const isTerminal = ['visa_rejected', 'cancelled'].includes(currentStatus);
  const currentStepIndex = STEPS.findIndex(s => s.key === currentStatus);

  // If status is terminal, we can assume it broke after some previous status
  // For safety, let's find the furthest history state or approximate it.
  // Let's render the standard steps with active/completed colors, and append the terminal status.
  
  return (
    <div className="bg-white rounded-2xl border border-slate-100 p-6 shadow-sm">
      <h3 className="text-base font-bold text-slate-800 mb-6">Workflow Progress Track</h3>
      <div className="relative pl-6 border-l-2 border-slate-100 space-y-8 ml-3">
        {STEPS.map((step, idx) => {
          let isCompleted = false;
          let isActive = false;
          let isPending = true;

          if (!isTerminal) {
            if (idx < currentStepIndex) {
              isCompleted = true;
              isPending = false;
            } else if (idx === currentStepIndex) {
              isActive = true;
              isPending = false;
            }
          } else {
            // If rejected/cancelled, everything is pending unless it was a previous state
            // Let's default to completed for everything up to where it was (or standard layout)
            // For general visualization:
            isPending = true;
          }

          // Node styling classes
          let nodeBg = 'bg-slate-100 text-slate-400 border-slate-200';
          let borderGlow = '';
          if (isCompleted) {
            nodeBg = 'bg-green-600 text-white border-green-600';
          } else if (isActive) {
            nodeBg = 'bg-brand-orange text-white border-brand-orange ring-4 ring-orange-50';
            borderGlow = 'font-bold text-slate-900';
          }

          return (
            <div key={step.key} className="relative flex items-start gap-4 group">
              {/* Timeline marker */}
              <div className={`absolute -left-[35px] w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs transition-all duration-300 ${nodeBg}`}>
                {isCompleted ? (
                  <Check className="w-3.5 h-3.5" />
                ) : isActive ? (
                  <Clock className="w-3.5 h-3.5 animate-spin" style={{ animationDuration: '3s' }} />
                ) : (
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                )}
              </div>

              {/* Step info */}
              <div>
                <p className={`text-sm font-semibold transition-colors duration-200 ${isActive ? 'text-brand-orange' : isCompleted ? 'text-slate-800' : 'text-slate-400'}`}>
                  {step.label}
                </p>
                <p className="text-xs text-slate-400 mt-0.5">{step.desc}</p>
              </div>
            </div>
          );
        })}

        {/* Append Terminal State if active */}
        {currentStatus === 'visa_rejected' && (
          <div className="relative flex items-start gap-4 group">
            <div className="absolute -left-[35px] w-6 h-6 rounded-full border-2 bg-rose-600 text-white border-rose-600 flex items-center justify-center ring-4 ring-rose-50">
              <AlertOctagon className="w-3.5 h-3.5" />
            </div>
            <div>
              <p className="text-sm font-bold text-rose-600">Visa Rejected</p>
              <p className="text-xs text-slate-400 mt-0.5">Embassy application rejected</p>
            </div>
          </div>
        )}

        {currentStatus === 'cancelled' && (
          <div className="relative flex items-start gap-4 group">
            <div className="absolute -left-[35px] w-6 h-6 rounded-full border-2 bg-slate-600 text-white border-slate-600 flex items-center justify-center ring-4 ring-slate-50">
              <AlertTriangle className="w-3.5 h-3.5" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-700">Application Cancelled</p>
              <p className="text-xs text-slate-400 mt-0.5">Journey terminated by user/admin</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgressTimeline;
