import React from 'react';
import logoImg from './logo.png';

/**
 * Ready2Go Overseas Official Logo Component
 * Loads the official branded image and renders it with responsive dimensions.
 */
export const Logo = ({ className = 'h-12 w-auto', variant = 'default' }) => {
  const isLight = variant === 'light';

  return (
    <div className="flex items-center gap-3 select-none">
      {/* Official Branded Logo Image */}
      <div className={`p-1.5 rounded-xl bg-white ${isLight ? 'shadow-sm shadow-white/10' : 'shadow-sm shadow-slate-100'}`}>
        <img
          src={logoImg}
          alt="Ready2Go Overseas Logo"
          className={className}
          style={{ objectFit: 'contain' }}
        />
      </div>
      
      {/* Professional Brand Text */}
      <div className="flex flex-col text-left">
        <span className={`font-display font-extrabold text-base leading-none tracking-tight ${isLight ? 'text-white' : 'text-slate-800'}`}>
          Ready2Go
        </span>
        <span className="text-[9px] uppercase font-bold tracking-widest text-brand-orange mt-1">
          Overseas Consultancy
        </span>
      </div>
    </div>
  );
};

export default Logo;
