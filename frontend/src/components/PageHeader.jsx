import React from 'react';

/**
 * Reusable header component for all CRM module pages carrying breadcrumbs and CTA buttons.
 */
export const PageHeader = ({
  title,
  subtitle,
  breadcrumbs = [],
  action,
  className = '',
}) => {
  return (
    <div className={`flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6 text-left ${className}`}>
      
      {/* Title & Breadcrumbs */}
      <div>
        {breadcrumbs.length > 0 && (
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 mb-1.5">
            {breadcrumbs.map((crumb, idx) => (
              <React.Fragment key={idx}>
                {idx > 0 && <span className="text-[10px] text-slate-300">/</span>}
                {crumb.path ? (
                  <a href={crumb.path} className="hover:text-brand-orange transition-colors">
                    {crumb.label}
                  </a>
                ) : (
                  <span className="text-slate-500 font-bold">{crumb.label}</span>
                )}
              </React.Fragment>
            ))}
          </div>
        )}
        <h2 className="text-xl font-extrabold text-slate-800 font-display leading-tight">{title}</h2>
        {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
      </div>

      {/* CTA Button Slot */}
      {action && (
        <div className="shrink-0 flex items-center">
          {action}
        </div>
      )}
      
    </div>
  );
};

export default PageHeader;
