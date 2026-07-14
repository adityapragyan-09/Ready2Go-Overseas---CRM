import React from 'react';
import { MessageSquare } from 'lucide-react';

export const EmptyChatState = () => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center border border-dashed border-slate-200 rounded-2xl bg-slate-50/20">
      <div className="w-12 h-12 bg-orange-50 border border-orange-100 rounded-2xl flex items-center justify-center text-brand-orange mb-4 shadow-sm">
        <MessageSquare className="w-6 h-6" />
      </div>
      <h4 className="text-sm font-bold text-slate-800">No Chat Logs Registered</h4>
      <p className="text-xs text-slate-400 font-medium max-w-xs mt-1 leading-normal">
        Colleagues and admins can coordinate and post internal remarks about this applicant file.
      </p>
    </div>
  );
};

export default EmptyChatState;
