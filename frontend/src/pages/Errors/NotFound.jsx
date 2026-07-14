import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Compass } from 'lucide-react';
import Button from '../../components/Button';
import Logo from '../../assets/logo/Logo';
import useDocumentTitle from '../../hooks/useDocumentTitle';

/**
 * 404 Not Found Page
 */
const NotFound = () => {
  useDocumentTitle('404 Not Found');
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-slate-50 text-center">
      <div className="mb-8">
        <Logo variant="default" className="h-10 w-auto" />
      </div>
      
      <div className="max-w-md bg-white p-8 rounded-2xl border border-slate-100 shadow-xl shadow-brand-blue/5 space-y-6" role="alert">
        <div className="w-16 h-16 mx-auto rounded-full bg-brand-orange/5 border border-brand-orange/10 flex items-center justify-center text-brand-orange">
          <Compass size={32} className="animate-spin-slow" />
        </div>
        
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold font-display text-slate-800">404: Page Not Found</h1>
          <p className="text-sm text-slate-500 leading-relaxed">
            The workspace or resource link you followed may have been relocated, deleted, or you might have misspelled the URL.
          </p>
        </div>

        <Button onClick={() => navigate('/dashboard')} variant="primary" className="w-full">
          Return to Dashboard
        </Button>
      </div>
      
      <span className="text-xs text-slate-400 mt-12">&copy; Ready2Go Overseas. All rights reserved.</span>
    </div>
  );
};

export default NotFound;
