import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';
import Button from '../../components/Button';
import Logo from '../../assets/logo/Logo';
import useDocumentTitle from '../../hooks/useDocumentTitle';

/**
 * 403 Forbidden Error page for unauthorized role actions
 */
const Forbidden = () => {
  useDocumentTitle('403 Access Denied');
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-slate-50 text-center">
      <div className="mb-8">
        <Logo variant="default" className="h-10 w-auto" />
      </div>
      
      <div className="max-w-md bg-white p-8 rounded-2xl border border-slate-100 shadow-xl shadow-brand-blue/5 space-y-6" role="alert">
        <div className="w-16 h-16 mx-auto rounded-full bg-red-50 border border-red-100 flex items-center justify-center text-red-600 animate-pulse">
          <ShieldAlert size={32} />
        </div>
        
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold font-display text-slate-800">403: Access Denied</h1>
          <p className="text-sm text-slate-500 leading-relaxed">
            Your current account credentials do not have permission to view this resource. Contact system administration if you believe this is an error.
          </p>
        </div>

        <Button onClick={() => navigate('/dashboard')} variant="primary" className="w-full">
          Return to Dashboard
        </Button>
      </div>
      
      <span className="text-xs text-slate-400 mt-12">&copy; Ready2Go Overseas. CRM Security Control.</span>
    </div>
  );
};

export default Forbidden;
