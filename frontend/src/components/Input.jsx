import React, { forwardRef } from 'react';

/**
 * Reusable Form Input component with label and validation error support.
 */
export const Input = forwardRef(({
  label,
  type = 'text',
  error,
  placeholder,
  className = '',
  disabled = false,
  ...props
}, ref) => {
  return (
    <div className={`flex flex-col gap-1.5 text-left w-full ${className}`}>
      {label && (
        <label className="text-xs font-bold text-slate-600 uppercase tracking-wider">
          {label}
        </label>
      )}
      <input
        type={type}
        ref={ref}
        disabled={disabled}
        placeholder={placeholder}
        className={`
          w-full px-4 py-3 rounded-xl border bg-white/70 backdrop-blur-sm outline-none transition-all duration-200 text-sm text-slate-800 placeholder-slate-400
          ${error 
            ? 'border-red-300 focus:border-red-400 focus:ring-4 focus:ring-red-500/10' 
            : 'border-slate-200 focus:border-brand-blue focus:ring-4 focus:ring-brand-blue/10'
          }
          disabled:opacity-55 disabled:bg-slate-50
        `}
        {...props}
      />
      {error && (
        <span className="text-xs font-semibold text-red-500 animate-fade-in">
          {error.message || error}
        </span>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;
