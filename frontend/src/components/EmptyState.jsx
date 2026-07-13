import React from 'react';
import { Inbox } from 'lucide-react';

/**
 * Reusable component displayed when lists or search queries return empty.
 */
export const EmptyState = ({
  title = 'No records found',
  description = 'There are no active records in this view.',
  icon: Icon = Inbox,
  className = '',
  actionButton
}) => {
  return (
    <div className={`flex flex-col items-center justify-center text-center p-8 border border-dashed border-slate-200 rounded-2xl bg-white/40 backdrop-blur-sm ${className}`}>
      <div className="w-12 h-12 rounded-xl bg-brand-blue/5 border border-brand-blue/10 flex items-center justify-center text-brand-blue mb-4">
        <Icon size={24} />
      </div>
      <h3 className="text-base font-bold text-slate-800 font-display">{title}</h3>
      <p className="text-xs text-slate-400 max-w-xs mt-1.5 leading-relaxed">{description}</p>
      {actionButton && (
        <div className="mt-5">{actionButton}</div>
      )}
    </div>
  );
};

export default EmptyState;
