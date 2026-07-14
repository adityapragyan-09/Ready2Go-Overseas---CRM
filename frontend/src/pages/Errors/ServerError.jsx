import React from 'react';
import { RefreshCw } from 'lucide-react';
import Button from '../../components/Button';
import Logo from '../../assets/logo/Logo';
import useDocumentTitle from '../../hooks/useDocumentTitle';

/**
 * 500 Server Error Page
 */
const ServerError = () => {
  useDocumentTitle('500 Server Error');
  const handleReload = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-slate-50 text-center">
      <div className="mb-8">
        <Logo variant="default" className="h-10 w-auto" />
      </div>
      
      <div className="max-w-md bg-white p-8 rounded-2xl border border-slate-100 shadow-xl shadow-brand-blue/5 space-y-6" role="alert">
        <div className="w-16 h-16 mx-auto rounded-full bg-red-50 border border-red-100 flex items-center justify-center text-red-600">
          <RefreshCw size={32} className="animate-spin" style={{ animationDuration: '6s' }} />
        </div>
        
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold font-display text-slate-800">500: Server Error</h1>
          <p className="text-sm text-slate-500 leading-relaxed">
            Our authentication database or API endpoints returned a critical failure. The system logs have been generated. Try refreshing the page.
          </p>
        </div>

        <Button onClick={handleReload} variant="primary" className="w-full">
          Refresh Connection
        </Button>
      </div>
      
      <span className="text-xs text-slate-400 mt-12">&copy; Ready2Go Overseas. CRM Systems Control.</span>
    </div>
  );
};

export default ServerError;
