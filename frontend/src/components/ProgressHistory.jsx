import React from 'react';
import ProgressRemarkCard from './ProgressRemarkCard';
import { PlusCircle, MessageSquarePlus } from 'lucide-react';

export const ProgressHistory = ({ timeline, onOpenUpdateModal, onOpenNoteModal }) => {
  // Sort newest first
  const sortedTimeline = [...timeline].reverse();

  return (
    <div className="bg-white rounded-2xl border border-slate-100 p-6 shadow-sm flex flex-col gap-6">
      {/* Header action bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-slate-800">Timeline Activity Log</h3>
          <p className="text-xs text-slate-400 font-medium">Audit logs of all transitions and remarks</p>
        </div>
        <div className="flex items-center gap-2">
          {/* Add Remark Note Button */}
          <button
            onClick={onOpenNoteModal}
            className="flex items-center gap-2 text-xs font-bold text-slate-700 bg-slate-50 hover:bg-slate-100 px-4 py-2.5 rounded-xl border border-slate-200 transition-colors duration-200"
          >
            <MessageSquarePlus className="w-4 h-4 text-slate-500" /> Add Note
          </button>
          
          {/* Update Status Button */}
          <button
            onClick={onOpenUpdateModal}
            className="flex items-center gap-2 text-xs font-bold text-white bg-brand-orange hover:bg-orange-600 px-4 py-2.5 rounded-xl transition-colors duration-200 shadow-sm shadow-orange-100"
          >
            <PlusCircle className="w-4 h-4" /> Update Status
          </button>
        </div>
      </div>

      {/* Timeline entries list */}
      <div className="flex flex-col gap-4">
        {sortedTimeline.length > 0 ? (
          sortedTimeline.map((entry) => (
            <ProgressRemarkCard key={entry.id} entry={entry} />
          ))
        ) : (
          <div className="border border-dashed border-slate-200 rounded-xl p-12 text-center">
            <p className="text-sm font-semibold text-slate-400">No activity logs recorded for this applicant.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgressHistory;
