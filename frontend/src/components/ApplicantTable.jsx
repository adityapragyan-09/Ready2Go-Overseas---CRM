import React from 'react';
import { Eye, Edit2, Trash2, GraduationCap, Compass, Plane, Briefcase, HelpCircle, ChevronLeft, ChevronRight, Hash } from 'lucide-react';
import StatusBadge from './StatusBadge';

const visaTypeConfig = {
  student: { label: 'Student', icon: GraduationCap, text: 'text-indigo-600 bg-indigo-50 border-indigo-100' },
  visit: { label: 'Visit', icon: Compass, text: 'text-sky-600 bg-sky-50 border-sky-100' },
  tourist: { label: 'Tourist', icon: Plane, text: 'text-amber-600 bg-amber-50 border-amber-100' },
  business: { label: 'Business', icon: Briefcase, text: 'text-emerald-600 bg-emerald-50 border-emerald-100' }
};

export const ApplicantTable = ({
  applicants = [],
  employees = [],
  onView,
  onEdit,
  onDelete,
  pagination = {},
  onPageChange
}) => {
  const getEmployeeName = (id) => {
    if (!id) return null;
    const emp = employees.find(e => e.id === Number(id) || e.id === id);
    return emp ? (emp.full_name || emp.name || `Advisor #${id}`) : `Advisor #${id}`;
  };

  const getVisaBadge = (type) => {
    const config = visaTypeConfig[type?.toLowerCase()] || {
      label: type || 'Unknown',
      icon: HelpCircle,
      text: 'text-slate-600 bg-slate-50 border-slate-100'
    };
    const Icon = config.icon;
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold border ${config.text}`}>
        <Icon size={12} className="shrink-0" />
        {config.label}
      </span>
    );
  };

  const { page = 1, totalPages = 1, total = 0 } = pagination;

  return (
    <div className="flex flex-col gap-4 text-left">
      <div className="overflow-x-auto -mx-6 px-6">
        <table className="w-full text-left border-collapse min-w-[1000px]">
          <thead>
            <tr className="border-b border-slate-100 text-xs font-bold text-slate-400 uppercase tracking-wider">
              <th scope="col" className="py-3.5 px-4">Applicant Name</th>
              <th scope="col" className="py-3.5 px-4">Code</th>
              <th scope="col" className="py-3.5 px-4">Contact Detail</th>
              <th scope="col" className="py-3.5 px-4">Country</th>
              <th scope="col" className="py-3.5 px-4">Visa Type</th>
              <th scope="col" className="py-3.5 px-4">Status</th>
              <th scope="col" className="py-3.5 px-4">Employee Handling</th>
              <th scope="col" className="py-3.5 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50 text-sm">
            {applicants.map((applicant) => (
              <tr key={applicant.id} className="hover:bg-slate-50/50 transition-colors group">
                {/* Clickable Applicant Name */}
                <td className="py-4 px-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-brand-blue/5 border border-brand-blue/10 flex items-center justify-center text-brand-blue font-bold shrink-0">
                      {applicant.full_name.substring(0, 2).toUpperCase()}
                    </div>
                    <div className="flex flex-col text-left">
                      <button
                        onClick={() => onView(applicant.id)}
                        className="font-bold text-slate-800 hover:text-brand-orange text-left transition-colors focus:outline-none hover:underline"
                      >
                        {applicant.full_name}
                      </button>
                      <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">
                        Database ID: #{applicant.id}
                      </span>
                    </div>
                  </div>
                </td>
                
                {/* Applicant Code */}
                <td className="py-4 px-4">
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-xs font-bold text-slate-700 font-mono">
                    <Hash size={10} className="text-slate-400" />
                    {applicant.applicant_code || `APP-${String(applicant.id).padStart(6, '0')}`}
                  </span>
                </td>

                <td className="py-4 px-4">
                  <div className="flex flex-col">
                    <span className="font-semibold text-slate-700">{applicant.email || '--'}</span>
                    <span className="text-xs text-slate-400 font-medium">{applicant.phone || '--'}</span>
                  </div>
                </td>
                
                <td className="py-4 px-4 text-slate-600 font-semibold">
                  {applicant.country || '--'}
                </td>
                
                <td className="py-4 px-4">
                  {getVisaBadge(applicant.visa_type)}
                </td>
                
                <td className="py-4 px-4">
                  <StatusBadge status={applicant.status} />
                </td>
                
                <td className="py-4 px-4">
                  {applicant.assigned_to ? (
                    <div className="flex items-center gap-1.5">
                      <div className="w-5 h-5 rounded-md bg-slate-100 flex items-center justify-center text-slate-500 text-[10px] font-bold">
                        {(getEmployeeName(applicant.assigned_to) || 'NA').substring(0, 2).toUpperCase()}
                      </div>
                      <span className="font-semibold text-slate-700 text-xs">
                        {getEmployeeName(applicant.assigned_to) || 'Advisor'}
                      </span>
                    </div>
                  ) : (
                    <span className="text-xs text-slate-400 italic font-medium">Unassigned</span>
                  )}
                </td>
                
                <td className="py-4 px-4 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => onView(applicant.id)}
                      className="p-2 text-slate-400 hover:text-brand-blue hover:bg-brand-blue/5 rounded-xl transition-all duration-200"
                      title="View Details"
                      aria-label={`View details for ${applicant.full_name}`}
                    >
                      <Eye size={16} />
                    </button>
                    <button
                      onClick={() => onEdit(applicant.id)}
                      className="p-2 text-slate-400 hover:text-brand-orange hover:bg-brand-orange/5 rounded-xl transition-all duration-200"
                      title="Edit Applicant"
                      aria-label={`Edit ${applicant.full_name}`}
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={() => onDelete(applicant.id, applicant.full_name)}
                      className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all duration-200"
                      title="Delete Record"
                      aria-label={`Delete ${applicant.full_name}`}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-slate-100 pt-4 mt-2">
          <p className="text-xs font-semibold text-slate-400">
            Showing Page <span className="text-slate-700 font-bold">{page}</span> of{' '}
            <span className="text-slate-700 font-bold">{totalPages}</span> ({total} applicants)
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page === 1}
              aria-label="Previous page"
              className="p-2 border border-slate-200 rounded-xl bg-white hover:bg-slate-50 active:scale-[0.97] transition-all disabled:opacity-50 disabled:pointer-events-none text-slate-600"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page === totalPages}
              aria-label="Next page"
              className="p-2 border border-slate-200 rounded-xl bg-white hover:bg-slate-50 active:scale-[0.97] transition-all disabled:opacity-50 disabled:pointer-events-none text-slate-600"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApplicantTable;
