import React from 'react';
import Logo from '../assets/logo/Logo';
import { Compass } from 'lucide-react';

/**
 * Reusable layout for all Authentication pages with professional branding text.
 */
const AuthLayout = ({ children }) => {
  return (
    <div className="min-h-screen flex items-stretch justify-center overflow-hidden bg-slate-50 font-sans">
      
      {/* ── Left Side: Brand Showcase (Hidden on Mobile) ───────────────── */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-brand-dark overflow-hidden flex-col justify-between p-12 text-white">
        {/* Decorative background shapes */}
        <div className="absolute inset-0 z-0">
          <div className="absolute -top-36 -left-36 w-96 h-96 rounded-full bg-brand-blue/30 blur-3xl"></div>
          <div className="absolute top-1/2 right-0 w-80 h-80 rounded-full bg-brand-orange/15 blur-3xl"></div>
          <div className="absolute -bottom-24 left-1/4 w-96 h-96 rounded-full bg-blue-900/20 blur-3xl"></div>
          {/* Subtle grid pattern overlay */}
          <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:24px_24px]"></div>
        </div>

        {/* Branding header */}
        <div className="relative z-10">
          <Logo variant="light" className="h-8 w-auto" />
        </div>

        {/* Center illustration & copy */}
        <div className="relative z-10 max-w-md my-auto space-y-6">
          <h1 className="text-4xl font-extrabold font-display leading-tight tracking-tight">
            Global Mobility. <br />
            <span className="text-brand-orange">Managed Intelligently</span>.
          </h1>
          <p className="text-slate-300 text-sm leading-relaxed">
            Welcome to the Ready2Go Overseas unified operations portal. Connect client files, track processing milestones, and coordinate workflows in a single secure console.
          </p>
          <div className="flex items-center gap-4 p-4 rounded-xl border border-white/5 bg-white/[0.02] backdrop-blur-md max-w-sm">
            <div className="w-10 h-10 rounded-lg bg-brand-orange/10 flex items-center justify-center text-brand-orange shrink-0">
              <Compass className="animate-spin-slow" size={20} />
            </div>
            <div className="text-left">
              <p className="text-xs font-semibold text-white">Unified Case Operations</p>
              <p className="text-[11px] text-slate-400">Consolidated processing queue for Student, Visit, Tourist, and Business visas.</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="relative z-10 text-xs text-slate-500 flex items-center justify-between border-t border-white/5 pt-6">
          <span>&copy; {new Date().getFullYear()} Ready2Go Overseas.</span>
          <span>Operations Console v1.0.0</span>
        </div>
      </div>

      {/* ── Right Side: Main Form Panel ──────────────────────────────── */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 md:p-12 relative">
        {/* Soft background shape for mobile screens */}
        <div className="lg:hidden absolute top-0 right-0 w-80 h-80 rounded-full bg-brand-orange/5 blur-3xl -z-10"></div>
        <div className="lg:hidden absolute bottom-0 left-0 w-80 h-80 rounded-full bg-brand-blue/5 blur-3xl -z-10"></div>

        <div className="w-full max-w-md space-y-8 animate-slide-up">
          {/* Mobile logo header (hidden on large screens) */}
          <div className="lg:hidden flex justify-center">
            <Logo variant="default" className="h-10 w-auto" />
          </div>

          {children}
        </div>
      </div>
      
    </div>
  );
};

export default AuthLayout;
