import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Navigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  Plus, Search, UserCheck, UserX, ShieldAlert, X,
  Briefcase, Mail, Phone, Clock, CheckCircle2, Copy,
  Eye, Lock, AlertTriangle, Users, RefreshCw,
  ChevronRight, Calendar
} from 'lucide-react';

import api from '../../config/api';
import { useAuth } from '../../hooks/useAuth';
import Card from '../../components/Card';
import Button from '../../components/Button';
import Input from '../../components/Input';
import PageHeader from '../../components/PageHeader';
import LoadingSpinner from '../../components/LoadingSpinner';
import ConfirmationModal from '../../components/ConfirmationModal';
import EmptyState from '../../components/EmptyState';

// ── Constants ──────────────────────────────────
const LEAVE_REASONS = ['Annual Leave', 'Sick Leave', 'Personal Leave'];
const ARCHIVE_REASONS = [
  'Annual Leave',
  'Sick Leave',
  'Personal Leave',
  'Resigned',
  'Terminated',
  'Inactive',
];

// ── 1. Status Badge Component ────────────────────
export const EmployeeStatusBadge = ({ isActive, archivedAt }) => {
  if (archivedAt) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border bg-slate-100 text-slate-500 border-slate-200">
        <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
        Archived
      </span>
    );
  }
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
      isActive
        ? 'bg-emerald-50 text-emerald-600 border-emerald-100'
        : 'bg-amber-50 text-amber-600 border-amber-200'
    }`}>
      <span className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
      {isActive ? 'Active' : 'Inactive'}
    </span>
  );
};


// ── 2. Filters Toolbar Component ─────────────────
const EmployeeFilters = ({
  search, setSearch,
  role, setRole,
  dept, setDept,
  status, setStatus,
  onReset
}) => {
  return (
    <div className="bg-slate-50/50 p-4 rounded-2xl border border-slate-100 flex flex-col gap-3">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs font-semibold">
        <div className="relative">
          <Search size={14} className="absolute inset-y-0 my-auto left-3 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by code, name, email..."
            className="w-full pl-9 pr-3 py-2.5 border border-slate-200 bg-white rounded-xl focus:border-brand-orange outline-none transition-all"
          />
        </div>

        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          className="px-3 py-2.5 border border-slate-200 bg-white rounded-xl text-slate-600 outline-none focus:border-brand-orange"
        >
          <option value="">All Roles</option>
          <option value="admin">Administrator</option>
          <option value="employee">Counselor</option>
        </select>

        <input
          type="text"
          value={dept}
          onChange={(e) => setDept(e.target.value)}
          placeholder="Filter by department..."
          className="px-3 py-2.5 border border-slate-200 bg-white rounded-xl text-slate-600 outline-none focus:border-brand-orange"
        />

        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="px-3 py-2.5 border border-slate-200 bg-white rounded-xl text-slate-600 outline-none focus:border-brand-orange"
        >
          <option value="">All Statuses</option>
          <option value="active">Active Only</option>
          <option value="inactive">Inactive Only</option>
          <option value="archived">Archived</option>
        </select>
      </div>

      <div className="flex justify-end">
        <button
          onClick={onReset}
          className="text-xs font-bold text-slate-400 hover:text-brand-orange transition-all"
        >
          Clear All Filters
        </button>
      </div>
    </div>
  );
};

// ── 3. Assignment Panel Component ───────────────
const EmployeeAssignmentPanel = ({ employeeId }) => {
  const navigate = useNavigate();
  const [applicants, setApplicants] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchAssigned = async () => {
      if (!employeeId) return;
      try {
        setLoading(true);
        const res = await api.get(`/applicants?assigned_to=${employeeId}`);
        if (res.data && res.data.success) {
          setApplicants(res.data.data.items || []);
        }
      } catch {
        // Silent
      } finally {
        setLoading(false);
      }
    };
    fetchAssigned();
  }, [employeeId]);

  if (loading) {
    return <div className="py-6 flex justify-center"><LoadingSpinner label="Loading assignments..." /></div>;
  }

  return (
    <div className="space-y-3.5">
      <div className="flex justify-between items-center bg-slate-50 p-3 rounded-xl border border-slate-100">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Active Accounts</span>
        <span className="bg-brand-orange text-white px-2 py-0.5 rounded-lg text-xs font-black">{applicants.length}</span>
      </div>

      {applicants.length === 0 ? (
        <p className="text-xs text-slate-400 italic">No applicants currently assigned to this counselor.</p>
      ) : (
        <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
          {applicants.map((app) => (
            <div
              key={app.id}
              onClick={() => navigate('/applicants')}
              className="p-3 bg-white border border-slate-100 hover:border-brand-orange/40 rounded-xl flex items-center justify-between text-xs font-semibold cursor-pointer transition-all shadow-sm group"
            >
              <div>
                <p className="text-slate-800 font-bold group-hover:text-brand-orange transition-colors">{app.full_name}</p>
                <p className="text-[10px] text-slate-400 font-medium">{app.visa_type} &bull; {app.country}</p>
              </div>
              <span className="text-[9px] bg-slate-150 text-slate-600 px-1.5 py-0.5 rounded font-black uppercase">
                {app.status.replace('_', ' ')}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ── 4. Details Drawer Component ──────────────────
const EmployeeDetailsDrawer = ({ employee, onClose }) => {
  const formattedDate = (dateStr) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      <div onClick={onClose} className="absolute inset-0 bg-black/40 backdrop-blur-sm"></div>

      <div className="relative w-full max-w-md bg-white h-full shadow-2xl flex flex-col justify-between p-6 animate-slide-left z-10 border-l border-slate-100 text-left">
        <div className="space-y-6 flex-1 overflow-y-auto pr-1">
          <div className="flex justify-between items-start border-b border-slate-100 pb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest">Employee Registry File</h3>
              <h2 className="text-lg font-black text-slate-800 mt-1">{employee.full_name}</h2>
            </div>
            <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-600 rounded-lg bg-slate-50 border border-slate-100">
              <X size={16} />
            </button>
          </div>

          <div className="flex gap-4 p-4 bg-slate-50 border border-slate-100 rounded-2xl">
            <div className="w-14 h-14 rounded-full border border-slate-200 flex items-center justify-center bg-white text-brand-orange text-lg font-black shrink-0">
              {employee.profile_photo ? (
                <img src={employee.profile_photo} alt="" className="w-full h-full object-cover rounded-full" />
              ) : (
                employee.full_name.substring(0, 2).toUpperCase()
              )}
            </div>
            <div className="space-y-1">
              <span className="text-[10px] font-mono font-bold text-slate-400 bg-white border border-slate-200 px-1.5 py-0.5 rounded">
                {employee.employee_code || 'EMP-XXXXXX'}
              </span>
              <p className="text-xs font-black text-slate-700">{employee.designation || 'Staff Counselor'}</p>
              <p className="text-[10px] font-bold text-slate-400">{employee.department || 'Advising'}</p>
            </div>
          </div>

          <div className="space-y-3.5 border-b border-slate-100 pb-5 text-xs font-semibold text-slate-500">
            <div className="flex justify-between">
              <span className="flex items-center gap-1.5"><Mail size={13} /> Email</span>
              <span className="text-slate-700">{employee.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="flex items-center gap-1.5"><Phone size={13} /> Phone</span>
              <span className="text-slate-700">{employee.phone || '--'}</span>
            </div>
            <div className="flex justify-between">
              <span className="flex items-center gap-1.5"><Briefcase size={13} /> Role</span>
              <span className="text-slate-700 uppercase font-black">{employee.role}</span>
            </div>
            <div className="flex justify-between">
              <span className="flex items-center gap-1.5"><Clock size={13} /> Last Login</span>
              <span className="text-slate-700">{formattedDate(employee.last_login)}</span>
            </div>
            <div className="flex justify-between">
              <span className="flex items-center gap-1.5"><Clock size={13} /> Last Logout</span>
              <span className="text-slate-700">{formattedDate(employee.last_logout)}</span>
            </div>
            {employee.archived_at && (
              <div className="flex justify-between text-amber-600">
                <span className="flex items-center gap-1.5"><Calendar size={13} /> Archived</span>
                <span>{formattedDate(employee.archived_at)}</span>
              </div>
            )}
            {employee.archived_reason && (
              <div className="flex justify-between text-amber-600">
                <span className="flex items-center gap-1.5"><AlertTriangle size={13} /> Reason</span>
                <span>{employee.archived_reason}</span>
              </div>
            )}
          </div>

          <div>
            <h4 className="text-xs font-black text-slate-800 mb-3.5 uppercase tracking-wider">Assigned Applicants Queue</h4>
            <EmployeeAssignmentPanel employeeId={employee.id} />
          </div>
        </div>

        <div className="pt-6 border-t border-slate-100 flex justify-end shrink-0">
          <Button onClick={onClose} variant="outline" className="w-full">Close Drawer</Button>
        </div>
      </div>
    </div>
  );
};

// ── 5. Archive Modal Component ──────────────────
const ArchiveEmployeeModal = ({ employee, onClose, onConfirm, employees, loading }) => {
  const [reason, setReason] = useState('Annual Leave');
  const [leaveStart, setLeaveStart] = useState('');
  const [leaveEnd, setLeaveEnd] = useState('');
  const [reassignMode, setReassignMode] = useState(null); // 'auto' | 'manual' | null
  const [targetEmployeeId, setTargetEmployeeId] = useState('');
  const [applicantCount, setApplicantCount] = useState(0);
  const [checking, setChecking] = useState(true);

  const isLeaveReason = LEAVE_REASONS.includes(reason);
  const showDates = isLeaveReason;
  const hasApplicants = applicantCount > 0;

  // Fetch applicant count on mount
  useEffect(() => {
    const fetchCount = async () => {
      try {
        setChecking(true);
        const res = await api.get(`/applicants?assigned_to=${employee.id}&page_size=1`);
        setApplicantCount(res.data?.data?.total || 0);
      } catch {
        setApplicantCount(0);
      } finally {
        setChecking(false);
      }
    };
    fetchCount();
  }, [employee.id]);

  const activeEmployees = (employees || []).filter(
    e => e.id !== employee.id && e.is_active && !e.archived_at
  );

  const handleConfirm = () => {
    if (hasApplicants && !reassignMode) {
      toast.error('Please select a reassignment option for the assigned applicants.');
      return;
    }
    if (reassignMode === 'manual' && !targetEmployeeId) {
      toast.error('Please select a target employee for manual reassignment.');
      return;
    }
    if (showDates && leaveStart && leaveEnd && new Date(leaveEnd) < new Date(leaveStart)) {
      toast.error('Leave end date must be after the start date.');
      return;
    }

    onConfirm({
      reason,
      leave_start: showDates ? leaveStart || null : null,
      leave_end: showDates ? leaveEnd || null : null,
      reassignment_mode: hasApplicants ? reassignMode : null,
      target_employee_id: reassignMode === 'manual' ? Number(targetEmployeeId) : null,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div onClick={onClose} className="absolute inset-0 bg-black/40 backdrop-blur-sm"></div>
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-lg w-full mx-4 text-left z-10 animate-scale-up overflow-hidden">
        {/* Header */}
        <div className="p-6 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-full bg-amber-50 text-amber-500">
              <UserX size={24} />
            </div>
            <div>
              <h3 className="text-lg font-extrabold text-slate-800 font-display">Archive Employee</h3>
              <p className="text-xs text-slate-500 mt-0.5">{employee.full_name} &bull; {employee.employee_code || 'EMP-XXXXXX'}</p>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5 max-h-[60vh] overflow-y-auto">
          {checking ? (
            <div className="flex items-center justify-center py-8">
              <div className="w-6 h-6 border-2 border-brand-orange border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : (
            <>
              {/* Applicant Alert */}
              {hasApplicants && (
                <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-3">
                  <AlertTriangle size={18} className="text-amber-500 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-bold text-amber-800">
                      This employee is currently assigned to <span className="text-amber-600">{applicantCount}</span> Applicant{applicantCount !== 1 ? 's' : ''}
                    </p>
                    <p className="text-xs text-amber-700 mt-1">
                      Before archiving, these applicants must be reassigned to another advisor.
                    </p>
                  </div>
                </div>
              )}

              {!hasApplicants && (
                <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-start gap-3">
                  <CheckCircle2 size={18} className="text-emerald-500 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-bold text-emerald-800">No assigned applicants</p>
                    <p className="text-xs text-emerald-700 mt-1">
                      This employee has no active applicants. They will be archived immediately.
                    </p>
                  </div>
                </div>
              )}

              {/* Reason */}
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wider">Reason for Archive</label>
                <select
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full px-3 py-2.5 border border-slate-200 rounded-xl text-xs font-semibold outline-none focus:border-brand-orange bg-white"
                >
                  {ARCHIVE_REASONS.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>

              {/* Conditional Leave Dates */}
              {showDates && (
                <div className="p-4 rounded-xl bg-blue-50 border border-blue-100 space-y-3">
                  <p className="text-xs font-bold text-blue-700 uppercase tracking-wider flex items-center gap-1.5">
                    <Calendar size={14} /> Leave Period
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[10px] font-bold text-slate-500 mb-1">Start Date</label>
                      <input
                        type="date"
                        value={leaveStart}
                        onChange={(e) => setLeaveStart(e.target.value)}
                        className="w-full px-3 py-2.5 border border-slate-200 rounded-xl text-xs outline-none focus:border-brand-orange bg-white"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-slate-500 mb-1">End Date</label>
                      <input
                        type="date"
                        value={leaveEnd}
                        onChange={(e) => setLeaveEnd(e.target.value)}
                        className="w-full px-3 py-2.5 border border-slate-200 rounded-xl text-xs outline-none focus:border-brand-orange bg-white"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Reassignment Options (only if has applicants) */}
              {hasApplicants && (
                <div className="space-y-3">
                  <p className="text-xs font-bold text-slate-600 uppercase tracking-wider">
                    Reassign Applicants
                  </p>

                  {/* Auto-distribute */}
                  <label
                    className={`flex items-start gap-3 p-4 rounded-xl border-2 cursor-pointer transition-all ${
                      reassignMode === 'auto'
                        ? 'border-brand-orange bg-brand-orange/[0.03]'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="reassign"
                      checked={reassignMode === 'auto'}
                      onChange={() => setReassignMode('auto')}
                      className="mt-0.5 accent-brand-orange"
                    />
                    <div>
                      <p className="text-sm font-bold text-slate-800">Automatically distribute evenly</p>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Applicants will be distributed among active advisors based on current workload.
                      </p>
                      <div className="flex items-center gap-2 mt-2 text-[10px] text-slate-400">
                        <RefreshCw size={12} />
                        <span>Even workload distribution</span>
                      </div>
                    </div>
                  </label>

                  {/* Manual assignment */}
                  <label
                    className={`flex items-start gap-3 p-4 rounded-xl border-2 cursor-pointer transition-all ${
                      reassignMode === 'manual'
                        ? 'border-brand-orange bg-brand-orange/[0.03]'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="reassign"
                      checked={reassignMode === 'manual'}
                      onChange={() => setReassignMode('manual')}
                      className="mt-0.5 accent-brand-orange"
                    />
                    <div className="flex-1">
                      <p className="text-sm font-bold text-slate-800">Assign all applicants to</p>
                      {reassignMode === 'manual' && (
                        <div className="mt-2">
                          <select
                            value={targetEmployeeId}
                            onChange={(e) => setTargetEmployeeId(e.target.value)}
                            onClick={(e) => e.stopPropagation()}
                            className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs outline-none focus:border-brand-orange bg-white"
                          >
                            <option value="">Select employee...</option>
                            {activeEmployees
                              .sort((a, b) => (a.full_name || '').localeCompare(b.full_name || ''))
                              .map((e) => (
                                <option key={e.id} value={e.id}>{e.full_name}</option>
                              ))
                            }
                          </select>
                        </div>
                      )}
                      {reassignMode !== 'manual' && (
                        <p className="text-xs text-slate-500 mt-0.5">
                          Select a specific advisor to receive all applicants.
                        </p>
                      )}
                    </div>
                  </label>

                  {/* Summary */}
                  {reassignMode && (
                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600">
                      <span className="font-bold text-slate-800">{applicantCount}</span> Applicant{applicantCount !== 1 ? 's' : ''} will be{' '}
                      {reassignMode === 'auto' ? (
                        <span className="text-brand-orange font-bold">automatically distributed</span>
                      ) : (
                        <span>assigned to <span className="text-brand-orange font-bold">
                          {activeEmployees.find(e => e.id === Number(targetEmployeeId))?.full_name || 'selected advisor'}
                        </span></span>
                      )}
                      , then the employee will be archived.
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 pt-4 border-t border-slate-100 flex gap-3">
          <button
            onClick={onClose}
            disabled={loading}
            className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50 transition-all disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading || checking || (hasApplicants && !reassignMode) || (reassignMode === 'manual' && !targetEmployeeId)}
            className="flex-1 px-4 py-2.5 rounded-xl bg-amber-500 text-white text-xs font-bold hover:bg-amber-600 transition-all disabled:opacity-50 inline-flex items-center justify-center gap-2"
          >
            {loading ? (
              <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div> Processing...</>
            ) : (
              <><UserX size={14} /> {hasApplicants ? 'Reassign & Archive' : 'Archive Employee'}</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

// ── 6. Employee Form Component ──────────────────
const EmployeeForm = ({ employee, isSubmitting, onSubmit, onCancel }) => {
  const [name, setName] = useState(employee?.full_name || '');
  const [email, setEmail] = useState(employee?.email || '');
  const [phone, setPhone] = useState(employee?.phone || '');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState(employee?.role || 'employee');
  const [designation, setDesignation] = useState(employee?.designation || '');
  const [department, setDepartment] = useState(employee?.department || '');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (employee) {
      onSubmit({ full_name: name, phone, role, designation, department });
    } else {
      onSubmit({ full_name: name, email, phone, password, role, designation, department });
    }
  };

  const generateAutoPassword = () => {
    const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*";
    let pass = "";
    for (let i = 0; i < 10; i++) {
      pass += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setPassword(pass);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Input label="Full Name" placeholder="Rahul Sharma" value={name} onChange={(e) => setName(e.target.value)} required />
        <Input label="Email Address" type="email" placeholder="counselor@ready2gooverseas.com" value={email} onChange={(e) => setEmail(e.target.value)} required disabled={!!employee} />
        <Input label="Phone Number" placeholder="+91 98765 43210" value={phone} onChange={(e) => setPhone(e.target.value)} />

        {!employee && (
          <div className="relative">
            <Input label="Access Password" placeholder="Minimum 6 characters" value={password} onChange={(e) => setPassword(e.target.value)} required />
            <button type="button" onClick={generateAutoPassword}
              className="absolute right-3 top-[37px] px-2.5 py-1 bg-slate-50 border border-slate-200 text-slate-500 rounded-lg text-[10px] font-bold uppercase hover:bg-slate-100 transition-colors">
              Auto
            </button>
          </div>
        )}

        <Input label="Designation" placeholder="e.g. Senior Counselor" value={designation} onChange={(e) => setDesignation(e.target.value)} />
        <Input label="Department" placeholder="e.g. Australia Admissions" value={department} onChange={(e) => setDepartment(e.target.value)} />
      </div>

      <div className="flex flex-col gap-2">
        <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Role Privilege</label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button type="button" onClick={() => setRole('employee')}
            className={`px-4 py-3.5 rounded-xl border text-xs font-bold text-center transition-all duration-200 ${
              role === 'employee'
                ? 'border-brand-orange bg-brand-orange/5 text-brand-orange shadow-sm'
                : 'border-slate-200 text-slate-500 hover:bg-slate-50'
            }`}>
            Counselor (Staff)
          </button>
          <button type="button" onClick={() => setRole('admin')}
            className={`px-4 py-3.5 rounded-xl border text-xs font-bold text-center transition-all duration-200 ${
              role === 'admin'
                ? 'border-rose-500 bg-rose-50 text-rose-600 shadow-sm'
                : 'border-slate-200 text-slate-500 hover:bg-slate-50'
            }`}>
            Administrator
          </button>
        </div>
      </div>

      <div className="flex gap-3 pt-4 border-t border-slate-100">
        <Button onClick={onCancel} variant="outline" className="w-1/3" disabled={isSubmitting} type="button">Cancel</Button>
        <Button type="submit" variant="secondary" className="w-2/3" isLoading={isSubmitting}>
          {employee ? 'Save Changes' : 'Confirm & Create Account'}
        </Button>
      </div>
    </form>
  );
};

// ── 7. Employee Profile Component ────────────────
const EmployeeProfile = ({ currentUser }) => {
  const [phone, setPhone] = useState(currentUser?.phone || '');
  const [photo, setPhoto] = useState(currentUser?.profile_photo || '');
  const [designation, setDesignation] = useState(currentUser?.designation || '');
  const [department, setDepartment] = useState(currentUser?.department || '');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    try {
      setIsSubmitting(true);
      const res = await api.put('/employees/profile/me', { phone, profile_photo: photo, designation, department });
      if (res.data && res.data.success) {
        toast.success('Your profile has been updated successfully!');
      }
    } catch {
      toast.error('Failed to update profile.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const isAdmin = currentUser?.role === 'admin';

  return (
    <Card className="max-w-xl text-left border border-slate-100">
      <div className="flex gap-4 items-center border-b border-slate-100 pb-5 mb-5">
        <div className="w-16 h-16 rounded-full border flex items-center justify-center text-xl font-bold bg-slate-50 text-brand-orange">
          {photo ? <img src={photo} alt="" className="w-full h-full object-cover rounded-full" />
            : (currentUser?.name || 'US').substring(0, 2).toUpperCase()}
        </div>
        <div>
          <h3 className="text-sm font-black text-slate-800">{currentUser?.name || 'User'}</h3>
          <p className="text-xs text-slate-400 font-semibold">{currentUser?.email} &bull; <span className="uppercase text-brand-orange font-bold">{currentUser?.role}</span></p>
        </div>
      </div>

      <form onSubmit={handleSaveProfile} className="space-y-4">
        <Input label="Phone Number" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+91 98765 43210" />
        <Input label="Profile Photo URL" value={photo} onChange={(e) => setPhoto(e.target.value)} placeholder="https://..." />
        <Input label="Designation" value={designation} onChange={(e) => setDesignation(e.target.value)} placeholder="Counselor designation" disabled={!isAdmin} />
        <Input label="Department" value={department} onChange={(e) => setDepartment(e.target.value)} placeholder="Counselor department" disabled={!isAdmin} />
        <div className="flex justify-end pt-3">
          <Button type="submit" variant="secondary" isLoading={isSubmitting}>Save Profile Settings</Button>
        </div>
      </form>
    </Card>
  );
};


// ── 8. Main Employee Management Page ─────────────
export const EmployeeManagement = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [activeTab, setActiveTab] = useState('profile');

  useEffect(() => {
    if (isAdmin) setActiveTab('directory');
  }, [isAdmin]);

  // List states
  const [employees, setEmployees] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);

  // Filters State
  const [search, setSearch] = useState('');
  const [role, setRole] = useState('');
  const [dept, setDept] = useState('');
  const [status, setStatus] = useState('');

  // Modals & Panels
  const [activeEmployee, setActiveEmployee] = useState(null);
  const [detailsEmployee, setDetailsEmployee] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [archiveModal, setArchiveModal] = useState(null);
  const [confirmAction, setConfirmAction] = useState(null);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [passwordResetTarget, setPasswordResetTarget] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [newCredentials, setNewCredentials] = useState(null);

  // Deep-link
  const [searchParams, setSearchParams] = useSearchParams();
  const view = searchParams.get('view') || 'list';
  const editId = searchParams.get('id');
  const navigate = useNavigate();

  useEffect(() => {
    if (searchParams.get('action') === 'add' && isAdmin) {
      searchParams.delete('action');
      searchParams.set('view', 'add');
      setSearchParams(searchParams, { replace: true });
    }
  }, [isAdmin]);

  useEffect(() => {
    if (view === 'edit' && editId && !activeEmployee && employees.length > 0) {
      const emp = employees.find(e => e.id === Number(editId) || e.id === editId);
      if (emp) setActiveEmployee(emp);
      else navigate('/employees');
    }
  }, [view, editId, employees, activeEmployee]);

  const fetchEmployees = async () => {
    if (!isAdmin) return;
    try {
      setIsLoading(true);
      let isActiveVal;
      let includeArchived = false;
      if (status === 'active') isActiveVal = true;
      else if (status === 'inactive') { isActiveVal = false; includeArchived = true; }
      else if (status === 'archived') { isActiveVal = undefined; includeArchived = true; }
      else { isActiveVal = undefined; }

      const res = await api.get('/employees', {
        params: {
          search: search || undefined,
          role: role || undefined,
          department: dept || undefined,
          is_active: isActiveVal,
          include_archived: includeArchived,
          page
        }
      });
      if (res.data && res.data.success) {
        setEmployees(res.data.data.items || []);
        setTotalCount(res.data.data.total || 0);
      }
    } catch {
      toast.error('Failed to load staff directory.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, [search, role, dept, status, page, activeTab, isAdmin]);

  const handleResetFilters = () => {
    setSearch('');
    setRole('');
    setDept('');
    setStatus('');
    setPage(1);
  };

  const handleArchiveEmployee = (emp) => {
    setArchiveModal(emp);
  };

  const handleConfirmArchive = async (archiveData) => {
    if (!archiveModal) return;
    try {
      setIsSubmitting(true);
      const res = await api.patch(`/employees/${archiveModal.id}/archive`, archiveData);
      if (res.data?.success) {
        const result = res.data.data?.archive_result || {};
        const reassignMsg = result.reassignment
          ? ` ${result.reassignment.total_transferred || ''} applicant(s) reassigned.`
          : '';
        toast.success(`"${archiveModal.full_name}" archived.${reassignMsg}`);
        setArchiveModal(null);
        fetchEmployees();
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to archive employee.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRestoreEmployee = (emp) => {
    setConfirmAction({
      title: 'Restore Employee',
      message: `Are you sure you want to restore "${emp.full_name}"? They will be reactivated.`,
      warning: emp.archived_reason ? `Previous archive reason: ${emp.archived_reason}` : undefined,
      confirmText: 'Restore',
      confirmVariant: 'primary',
      employee: emp,
      action: 'restore',
    });
  };

  const handleConfirmAction = async () => {
    if (!confirmAction) return;
    setConfirmLoading(true);
    const emp = confirmAction.employee;
    try {
      if (confirmAction.action === 'restore') {
        const res = await api.patch(`/employees/${emp.id}/unarchive`);
        if (res.data?.success) toast.success(`"${emp.full_name}" restored.`);
      } else if (confirmAction.action === 'status') {
        const res = await api.patch(`/employees/${emp.id}/status`, confirmAction.payload);
        if (res.data?.success) toast.success(`"${emp.full_name}" status updated.`);
      }
      setConfirmAction(null);
      fetchEmployees();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Action failed.');
    } finally {
      setConfirmLoading(false);
    }
  };

  const handlePasswordReset = async () => {
    const emp = passwordResetTarget;
    if (!emp) return;
    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters long.');
      return;
    }
    try {
      const res = await api.patch(`/employees/${emp.id}/reset-password`, { password: newPassword });
      if (res.data && res.data.success) {
        toast.success(`Password reset successfully for "${emp.full_name}".`);
        setPasswordResetTarget(null);
        setNewPassword('');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to reset password.');
    }
  };

  const handleFormSubmit = async (payload) => {
    setIsSubmitting(true);
    try {
      if (activeEmployee) {
        const res = await api.put(`/employees/${activeEmployee.id}`, payload);
        if (res.data?.success) {
          toast.success('Employee updated.');
          setSearchParams({ view: 'list' });
          setActiveEmployee(null);
          fetchEmployees();
        }
      } else {
        const res = await api.post('/employees', payload);
        if (res.data?.success) {
          toast.success('Employee provisioned successfully.');
          setNewCredentials({
            name: payload.full_name,
            email: payload.email,
            password: payload.password,
            role: payload.role
          });
          setSearchParams({ view: 'list' });
          fetchEmployees();
        }
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save employee.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const copyCredsToClipboard = () => {
    if (!newCredentials) return;
    const body = `Ready2Go CRM Staff Credentials:\nEmail: ${newCredentials.email}\nPassword: ${newCredentials.password}\nRole: ${newCredentials.role}`;
    navigator.clipboard.writeText(body);
    toast.success('Credentials copied to clipboard!');
  };

  // ── RENDER: Add/Edit Full-Page Form View ──────
  if (view === 'add' || view === 'edit') {
    if (!isAdmin) return <Navigate to="/403" replace />;
    return (
      <div className="space-y-6 text-left animate-fade-in">
        <PageHeader
          title={view === 'add' ? 'Add Staff Account' : 'Edit Staff Account'}
          subtitle={view === 'add' ? 'Provision a new staff member with CRM access credentials' : 'Updating staff profile'}
          breadcrumbs={[
            { label: 'Home', path: '/dashboard' },
            { label: 'Employees', path: '/employees' },
            { label: view === 'add' ? 'New Account' : 'Edit' }
          ]}
        />
        <Card>
          <EmployeeForm employee={activeEmployee} isSubmitting={isSubmitting} onSubmit={handleFormSubmit}
            onCancel={() => { setActiveEmployee(null); navigate('/employees'); }} />
        </Card>
      </div>
    );
  }

  // ── RENDER: Main Directory / Profile View ────
  return (
    <div className="space-y-6 text-left">
      <PageHeader
        title="Employee Registry"
        subtitle="Manage access, credentials, and portfolios for staff advisors"
        breadcrumbs={[{ label: 'Home', path: '/dashboard' }, { label: 'Employees' }]}
        action={
          isAdmin && activeTab === 'directory' && (
            <Button onClick={() => { setActiveEmployee(null); setSearchParams({ view: 'add' }); }}
              variant="secondary" className="flex items-center gap-2">
              <Plus size={15} /> Add Staff Account
            </Button>
          )
        }
      />

      {/* Tab Switcher */}
      <div className="flex border-b border-slate-100 gap-6">
        {isAdmin && (
          <button onClick={() => setActiveTab('directory')}
            className={`pb-3 text-xs font-bold uppercase tracking-wider border-b-2 transition-all ${
              activeTab === 'directory' ? 'border-brand-orange text-brand-orange' : 'border-transparent text-slate-400 hover:text-slate-600'
            }`}>
            Staff Directory
          </button>
        )}
        <button onClick={() => setActiveTab('profile')}
          className={`pb-3 text-xs font-bold uppercase tracking-wider border-b-2 transition-all ${
            activeTab === 'profile' ? 'border-brand-orange text-brand-orange' : 'border-transparent text-slate-400 hover:text-slate-600'
          }`}>
          My Profile
        </button>
      </div>

      {activeTab === 'directory' && isAdmin && (
        <div className="space-y-5">
          {newCredentials && (
            <div className="p-4 border border-emerald-100 bg-emerald-50/50 backdrop-blur-md rounded-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4 animate-scale-up">
              <div className="flex gap-3">
                <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 rounded-xl flex items-center justify-center shrink-0">
                  <CheckCircle2 size={20} />
                </div>
                <div className="text-left">
                  <p className="text-sm font-bold text-emerald-700">Account Created Successfully</p>
                  <p className="text-xs text-emerald-600 font-mono mt-0.5">
                    {newCredentials.email} / <span className="font-black">{newCredentials.password}</span>
                  </p>
                </div>
              </div>
              <div className="flex gap-2 shrink-0">
                <Button onClick={copyCredsToClipboard} variant="outline" className="text-xs flex items-center gap-1.5">
                  <Copy size={12} /> Copy
                </Button>
                <button onClick={() => setNewCredentials(null)}
                  className="p-2 text-slate-400 hover:text-slate-600 rounded-lg border border-slate-200 hover:bg-slate-50 transition-all">
                  <X size={14} />
                </button>
              </div>
            </div>
          )}

          <EmployeeFilters
            search={search} setSearch={setSearch}
            role={role} setRole={setRole}
            dept={dept} setDept={setDept}
            status={status} setStatus={setStatus}
            onReset={handleResetFilters}
          />

          <Card>
            {isLoading ? (
              <div className="py-24 flex justify-center"><LoadingSpinner label="Loading employee directory..." /></div>
            ) : employees.length === 0 ? (
              <EmptyState title="No Employees Found" description="Adjust your filters or create a new staff account." />
            ) : (
              <div className="overflow-x-auto -mx-6 px-6">
                <table className="w-full text-left border-collapse min-w-[800px]">
                  <thead>
                    <tr className="border-b border-slate-100 text-xs font-bold text-slate-400 uppercase tracking-wider">
                      <th className="py-3.5 px-4">Employee Code</th>
                      <th className="py-3.5 px-4">Name / Contact</th>
                      <th className="py-3.5 px-4">Role</th>
                      <th className="py-3.5 px-4">Department / Title</th>
                      <th className="py-3.5 px-4">Status</th>
                      <th className="py-3.5 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50 text-sm">
                    {employees.map((emp) => (
                      <tr key={emp.id} className={`group hover:bg-slate-50/50 transition-colors cursor-pointer ${
                        emp.archived_at ? 'opacity-60 hover:opacity-80' : ''
                      }`}
                          onClick={() => setDetailsEmployee(emp)}>
                        <td className="py-4 px-4">
                          <span className={`text-xs font-mono font-bold px-2 py-1 rounded ${
                            emp.archived_at
                              ? 'bg-slate-100 text-slate-400 border border-slate-200'
                              : 'bg-slate-100 text-slate-500 border border-slate-200/60'
                          }`}>
                            {emp.employee_code || 'EMP-NEW'}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 ${
                              emp.archived_at
                                ? 'bg-slate-200 text-slate-400'
                                : 'bg-brand-orange/10 text-brand-orange'
                            }`}>
                              {emp.full_name?.substring(0, 2).toUpperCase() || 'ST'}
                            </div>
                            <div className="flex flex-col text-left">
                              <span className="font-bold text-slate-800">{emp.full_name}</span>
                              <span className="text-[10px] text-slate-400 font-medium">{emp.email}</span>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border ${
                            emp.role === 'admin'
                              ? 'text-rose-600 bg-rose-50 border-rose-100'
                              : 'text-sky-600 bg-sky-50 border-sky-100'
                          }`}>
                            <ShieldAlert size={10} />
                            {emp.role === 'admin' ? 'Administrator' : 'Counselor'}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex flex-col text-left">
                            <span className="font-semibold text-slate-700 text-xs">{emp.designation || 'Staff Counselor'}</span>
                            <span className="text-[10px] text-slate-400">{emp.department || 'General'}</span>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <EmployeeStatusBadge isActive={emp.is_active} archivedAt={emp.archived_at} />
                          {emp.archived_reason && (
                            <p className="text-[9px] text-slate-400 mt-0.5">{emp.archived_reason}</p>
                          )}
                        </td>
                        <td className="py-4 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                          <div className="flex items-center justify-end gap-1.5 flex-wrap">
                            <button onClick={() => setDetailsEmployee(emp)}
                              className="px-2.5 py-1.5 text-[10px] font-bold rounded-lg border border-blue-200 text-blue-600 bg-blue-50 hover:bg-blue-100 transition-all">
                              View
                            </button>
                            <button onClick={() => { setActiveEmployee(emp); setSearchParams({ view: 'edit', id: emp.id }); }}
                              className="px-2.5 py-1.5 text-[10px] font-bold rounded-lg bg-brand-orange text-white hover:bg-brand-orange/90 transition-all">
                              Edit
                            </button>
                            <button onClick={() => setPasswordResetTarget(emp)}
                              className="px-2.5 py-1.5 text-[10px] font-bold rounded-lg border border-purple-200 text-purple-600 bg-purple-50 hover:bg-purple-100 transition-all">
                              Password
                            </button>
                            {!emp.archived_at ? (
                              <button onClick={() => handleArchiveEmployee(emp)}
                                disabled={emp.id === user?.id}
                                className="px-2.5 py-1.5 text-[10px] font-bold rounded-lg border border-amber-200 text-amber-600 bg-amber-50 hover:bg-amber-100 transition-all disabled:opacity-40">
                                Archive
                              </button>
                            ) : (
                              <button onClick={() => handleRestoreEmployee(emp)}
                                className="px-2.5 py-1.5 text-[10px] font-bold rounded-lg border border-emerald-200 text-emerald-600 bg-emerald-50 hover:bg-emerald-100 transition-all">
                                Restore
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      )}

      {activeTab === 'profile' && <EmployeeProfile currentUser={user} />}

      {detailsEmployee && (
        <EmployeeDetailsDrawer employee={detailsEmployee} onClose={() => setDetailsEmployee(null)} />
      )}

      {/* Archive Modal */}
      {archiveModal && (
        <ArchiveEmployeeModal
          employee={archiveModal}
          employees={employees}
          loading={isSubmitting}
          onClose={() => setArchiveModal(null)}
          onConfirm={handleConfirmArchive}
        />
      )}

      {/* Confirmation Modal */}
      <ConfirmationModal
        visible={!!confirmAction}
        title={confirmAction?.title || ''}
        message={confirmAction?.message || ''}
        warning={confirmAction?.warning}
        confirmText={confirmAction?.confirmText || 'Confirm'}
        confirmVariant={confirmAction?.confirmVariant || 'danger'}
        loading={confirmLoading}
        onConfirm={handleConfirmAction}
        onCancel={() => setConfirmAction(null)}
      />

      {/* Password Reset Dialog */}
      <ConfirmationModal
        visible={!!passwordResetTarget}
        title="Reset Employee Password"
        message={`Enter a new access password for "${passwordResetTarget?.full_name || 'Employee'}".`}
        confirmText="Reset Password"
        confirmVariant="primary"
        loading={false}
        onConfirm={handlePasswordReset}
        onCancel={() => { setPasswordResetTarget(null); setNewPassword(''); }}
      >
        <div className="mt-3">
          <label className="block text-xs font-bold text-slate-600 mb-1.5">New Password</label>
          <input
            type="text"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="Minimum 6 characters"
            minLength={6}
            autoFocus
            className="w-full px-3 py-2.5 rounded-xl border border-slate-200 bg-white text-xs font-semibold outline-none focus:border-brand-blue focus:ring-4 focus:ring-brand-blue/10 transition-all placeholder-slate-400"
          />
        </div>
      </ConfirmationModal>
    </div>
  );
};

export default EmployeeManagement;
