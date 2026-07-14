import React from 'react';
import { FileText, RefreshCw, UserPlus, Info } from 'lucide-react';

export const SystemMessage = ({ message }) => {
  const content = message.message || '';
  
  // Decide icon based on contents
  const getSystemIcon = () => {
    if (content.includes('registered') || content.includes('created')) {
      return <UserPlus className="w-3.5 h-3.5 text-blue-600" />;
    }
    if (content.includes('transitioned') || content.includes('Status')) {
      return <RefreshCw className="w-3.5 h-3.5 text-orange-600 animate-spin" style={{ animationDuration: '6s' }} />;
    }
    if (content.includes('uploaded') || content.includes('Document')) {
      return <FileText className="w-3.5 h-3.5 text-indigo-600" />;
    }
    return <Info className="w-3.5 h-3.5 text-slate-500" />;
  };

  return (
    <div className="flex justify-center my-3 animate-fade-in">
      <div className="flex items-center gap-2 px-4 py-2 bg-slate-50 border border-slate-100 rounded-2xl text-xs font-semibold text-slate-500 max-w-[85%] text-center shadow-sm">
        <div className="bg-white p-1 rounded-lg border border-slate-100 shrink-0">
          {getSystemIcon()}
        </div>
        <span className="italic leading-normal">{content}</span>
      </div>
    </div>
  );
};

export default SystemMessage;
