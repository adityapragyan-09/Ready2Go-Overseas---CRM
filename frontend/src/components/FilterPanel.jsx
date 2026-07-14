import React from 'react';
import { Filter, RotateCcw } from 'lucide-react';
import Button from './Button';

const visaTypes = [
  { value: 'student', label: 'Student Visa' },
  { value: 'visit', label: 'Visit Visa' },
  { value: 'tourist', label: 'Tourist Visa' },
  { value: 'business', label: 'Business Visa' }
];

const statuses = [
  { value: 'inquiry', label: 'Inquiry' },
  { value: 'documents_pending', label: 'Documents Pending' },
  { value: 'documents_submitted', label: 'Documents Submitted' },
  { value: 'application_processing', label: 'Application Processing' },
  { value: 'under_review', label: 'Under Review' },
  { value: 'interview_scheduled', label: 'Interview Scheduled' },
  { value: 'visa_approved', label: 'Visa Approved' },
  { value: 'visa_rejected', label: 'Visa Rejected' },
  { value: 'approved', label: 'Approved' },
  { value: 'visa_issued', label: 'Visa Issued' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'completed', label: 'Completed' }
];

export const FilterPanel = ({
  filters,
  onChange,
  onReset,
  employees = [],
  hideVisaType = false // Optional prop to hide visa_type selector if filtering inside specific tab
}) => {
  const handleSelectChange = (key, value) => {
    onChange({
      ...filters,
      [key]: value || ''
    });
  };

  return (
    <div className="bg-slate-50/50 p-5 rounded-2xl border border-slate-100 flex flex-col gap-4 text-left">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
          <Filter size={14} className="text-brand-orange" />
          Filter Pipeline
        </h4>
        <button
          onClick={onReset}
          className="text-xs font-semibold text-slate-400 hover:text-brand-orange transition-colors flex items-center gap-1.5 focus:outline-none"
        >
          <RotateCcw size={12} />
          Reset Filters
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        {/* Visa Type Selector */}
        {!hideVisaType && (
          <div className="flex flex-col gap-1.5">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Visa Type</span>
            <select
              value={filters.visaType || ''}
              onChange={(e) => handleSelectChange('visaType', e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-white/95 focus:border-brand-blue focus:ring-4 focus:ring-brand-blue/5 outline-none transition-all duration-200 text-xs font-semibold text-slate-700"
            >
              <option value="">All Visas</option>
              {visaTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Application Status Selector */}
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Status Stage</span>
          <select
            value={filters.status || ''}
            onChange={(e) => handleSelectChange('status', e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-white/95 focus:border-brand-blue focus:ring-4 focus:ring-brand-blue/5 outline-none transition-all duration-200 text-xs font-semibold text-slate-700"
          >
            <option value="">All Statuses</option>
            {statuses.map((status) => (
              <option key={status.value} value={status.value}>
                {status.label}
              </option>
            ))}
          </select>
        </div>

        {/* Country Search Filter */}
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Destination / Country</span>
          <input
            type="text"
            value={filters.country || ''}
            onChange={(e) => handleSelectChange('country', e.target.value)}
            placeholder="e.g. Canada, Germany"
            className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-white/95 focus:border-brand-blue focus:ring-4 focus:ring-brand-blue/5 outline-none transition-all duration-200 text-xs font-semibold text-slate-700 placeholder-slate-400"
          />
        </div>

        {/* Assigned Counselors Dropdown */}
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Assigned Advisor</span>
          <select
            value={filters.assignedEmployee || ''}
            onChange={(e) => handleSelectChange('assignedEmployee', e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-white/95 focus:border-brand-blue focus:ring-4 focus:ring-brand-blue/5 outline-none transition-all duration-200 text-xs font-semibold text-slate-700"
          >
            <option value="">All Counselors</option>
            {employees.map((emp) => (
              <option key={emp.id} value={emp.id}>
                {emp.name} ({emp.role === 'admin' ? 'Admin' : 'Counselor'})
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
};

export default FilterPanel;
