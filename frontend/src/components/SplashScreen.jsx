import { useState, useEffect } from 'react';

export default function SplashScreen({ onComplete }) {
  const [visible, setVisible] = useState(true);
  const [fading, setFading] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setFading(true);
      setTimeout(() => {
        setVisible(false);
        onComplete?.();
      }, 500);
    }, 1600);
    return () => clearTimeout(timer);
  }, [onComplete]);

  if (!visible) return null;

  return (
    <div
      className={`fixed inset-0 z-[9999] flex items-center justify-center transition-all duration-500 ${
        fading ? 'opacity-0 scale-105' : 'opacity-100 scale-100'
      }`}
      style={{
        background: 'linear-gradient(135deg, #0b2e5e 0%, #0b1a2e 50%, #162d50 100%)',
      }}
    >
      <div className="text-center px-6">
        {/* Logo mark */}
        <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-white/10 backdrop-blur-xl border border-white/10 flex items-center justify-center shadow-2xl animate-fade-in">
          <svg viewBox="0 0 40 40" className="w-10 h-10" fill="none">
            <path d="M20 4L36 12V28L20 36L4 28V12L20 4Z" stroke="#f68b1e" strokeWidth="2"/>
            <path d="M20 12L28 16V24L20 28L12 24V16L20 12Z" fill="#f68b1e" opacity="0.8"/>
            <circle cx="20" cy="20" r="3" fill="white"/>
          </svg>
        </div>

        {/* Title */}
        <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight mb-2 animate-slide-up">
          Ready2Go CRM
        </h1>

        {/* Subtitle */}
        <p className="text-white/60 text-sm font-medium tracking-wide mb-8 animate-slide-up" style={{ animationDelay: '0.1s' }}>
          Ready2Go Overseas Consultancy
        </p>

        {/* Loader */}
        <div className="flex justify-center gap-1.5 mb-6">
          {[0, 1, 2].map(i => (
            <div
              key={i}
              className="w-2 h-2 rounded-full bg-brand-orange animate-bounce"
              style={{ animationDelay: `${i * 0.15}s`, animationDuration: '0.8s' }}
            />
          ))}
        </div>

        {/* Status */}
        <p className="text-white/40 text-xs font-medium animate-pulse">
          Preparing your workspace...
        </p>
      </div>
    </div>
  );
}
