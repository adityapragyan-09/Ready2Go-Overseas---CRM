import React from 'react';

/**
 * Reusable Button component supporting primary, secondary, danger, and outline variants.
 */
export const Button = ({
  children,
  type = 'button',
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled = false,
  className = '',
  onClick,
  ...props
}) => {
  const baseStyle = 'inline-flex items-center justify-center font-semibold rounded-xl transition-all duration-200 outline-none active:scale-[0.98] disabled:opacity-55 disabled:pointer-events-none disabled:active:scale-100';
  
  const variants = {
    primary: 'bg-brand-blue text-white hover:bg-brand-blue/95 hover:shadow-lg hover:shadow-brand-blue/10 focus:ring-4 focus:ring-brand-blue/15',
    secondary: 'bg-brand-orange text-white hover:bg-brand-orange/95 hover:shadow-lg hover:shadow-brand-orange/10 focus:ring-4 focus:ring-brand-orange/15',
    outline: 'border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 focus:ring-4 focus:ring-slate-100',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-4 focus:ring-red-100',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-5 py-2.5 text-sm',
    lg: 'px-6 py-3.5 text-base',
  };

  return (
    <button
      type={type}
      disabled={disabled || isLoading}
      onClick={onClick}
      className={`${baseStyle} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {isLoading ? (
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
          <span>Loading...</span>
        </div>
      ) : (
        children
      )}
    </button>
  );
};

export default Button;
