import React from 'react';

/**
 * Reusable Loading Spinner with Brand Theme
 */
export const LoadingSpinner = ({ size = 'md', className = '', label = '' }) => {
  const sizeClasses = {
    sm: 'w-6 h-6 border-2',
    md: 'w-10 h-10 border-3',
    lg: 'w-16 h-16 border-4',
  };

  return (
    <div className={`flex flex-col items-center justify-center gap-3 ${className}`} role="status" aria-live="polite">
      <div className="relative">
        <div className={`rounded-full border-slate-100 ${sizeClasses[size]}`}></div>
        <div className={`absolute inset-0 rounded-full border-brand-orange border-t-transparent animate-spin ${sizeClasses[size]}`}></div>
      </div>
      {label && (
        <span className="text-xs font-semibold text-slate-500 animate-pulse">{label}</span>
      )}
    </div>
  );
};

export default LoadingSpinner;
