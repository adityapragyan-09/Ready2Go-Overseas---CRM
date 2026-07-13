import React from 'react';

/**
 * Reusable layout card with glassmorphism border and soft shadows.
 */
export const Card = ({ children, className = '', title = '', subtitle = '' }) => {
  return (
    <div className={`bg-white/80 backdrop-blur-md border border-slate-100/80 shadow-xl shadow-brand-blue/5 rounded-2xl p-6 ${className}`}>
      {(title || subtitle) && (
        <div className="border-b border-slate-100 pb-4 mb-5 text-left">
          {title && <h3 className="text-lg font-bold text-slate-800 font-display">{title}</h3>}
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  );
};

export default Card;
