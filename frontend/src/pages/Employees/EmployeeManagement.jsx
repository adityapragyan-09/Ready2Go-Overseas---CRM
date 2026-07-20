import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Navigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  Plus, Search, UserCheck, UserX, ShieldAlert, X,
  Briefcase, Mail, Phone, Clock, CheckCircle2, Copy,
  Eye, Lock
} from 'lucide-react';

import api from '../../config/api';
import { useAuth } from '../../hooks/useAuth';
import Card from '../../components/Card';
import Button from '../../components/Button';
import Input from '../../components/Input';
import PageHeader from '../../components/PageHeader';
import LoadingSpinner from '../../components/LoadingSpinner';
import ConfirmationModal from '../../components/ConfirmationModal';

// ── 1. Status Badge Component ────────────────────
export const EmployeeStatusBadge = ({ isActive }) => {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
      isActive 
        ? 'bg-emerald-50 text-emerald-600 border-emerald-100' 
        : 'bg-slate-50 text-slate-400 border-slate-200'
    }`}>
      <span className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-emerald-500' : 'bg-slate-400'}`}></span>
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
        {/* Search */}
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

        {/* Role */}
        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          className="px-3 py-2.5 border border-slate-200 bg-white rounded-xl text-slate-600 outline-none focus:border-brand-orange"
        >
          <option value="">All Roles</option>
          <option value="admin">Administrator</option>
          <option value="employee">Counselor</option>
        </select>

        {/* Department */}
        <input
          type="text"
          value={dept}
          onChange={(e) => setDept(e.target.value)}
          placeholder="Filter by department..."
          className="px-3 py-2.5 border border-slate-200 bg-white rounded-xl text-slate-600 outline-none focus:border-brand-orange"
        />

        {/* Status */}
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="px-3 py-2.5 border border-slate-200 bg-white rounded-xl text-slate-600 outline-none focus:border-brand-orange"
        >
          <option value="">All Statuses</option>
          <option value="active">Active Only</option>
          <option value="inactive">Inactive Only</option>
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
      } catch (err) {
        // Silent fail - assignments panel is secondary content
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

          {/* Core Profile Card */}
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

          {/* Details Metadata List */}
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
          </div>

          {/* Assignment panel */}
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

// ── 5. Employee Form Component (Full-Page) ──────────────────
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
      {/* Two-column grid for fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Input
          label="Full Name"
          placeholder="Rahul Sharma"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />

        <Input
          label="Email Address"
          type="email"
          placeholder="counselor@ready2gooverseas.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          disabled={!!employee}
        />

        <Input
          label="Phone Number"
          placeholder="+91 98765 43210"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
        />

        {!employee && (
          <div className="relative">
            <Input
              label="Access Password"
              placeholder="Minimum 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <button
              type="button"
              onClick={generateAutoPassword}
              className="absolute right-3 top-[37px] px-2.5 py-1 bg-slate-50 border border-slate-200 text-slate-500 rounded-lg text-[10px] font-bold uppercase hover:bg-slate-100 transition-colors"
            >
              Auto
            </button>
          </div>
        )}

        <Input
          label="Designation"
          placeholder="e.g. Senior Counselor"
          value={designation}
          onChange={(e) => setDesignation(e.target.value)}
        />

        <Input
          label="Department"
          placeholder="e.g. Australia Admissions"
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
        />
      </div>

      {/* Role Privilege Selection */}
      <div className="flex flex-col gap-2">
        <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
          Role Privilege
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button
            type="button"
            onClick={() => setRole('employee')}
            className={`px-4 py-3.5 rounded-xl border text-xs font-bold text-center transition-all duration-200
              ${role === 'employee'
                ? 'border-brand-orange bg-brand-orange/5 text-brand-orange shadow-sm shadow-brand-orange/10'
                : 'border-slate-200 text-slate-500 hover:bg-slate-50'
              }
            `}
          >
            Counselor (Staff)
          </button>
          <button
            type="button"
            onClick={() => setRole('admin')}
            className={`px-4 py-3.5 rounded-xl border text-xs font-bold text-center transition-all duration-200
              ${role === 'admin'
                ? 'border-rose-500 bg-rose-50 text-rose-600 shadow-sm shadow-rose-500/10'
                : 'border-slate-200 text-slate-500 hover:bg-slate-50'
              }
            `}
          >
            Administrator
          </button>
        </div>
      </div>

      {/* Form Action Buttons */}
      <div className="flex gap-3 pt-4 border-t border-slate-100">
        <Button onClick={onCancel} variant="outline" className="w-1/3" disabled={isSubmitting} type="button">Cancel</Button>
        <Button type="submit" variant="secondary" className="w-2/3" isLoading={isSubmitting}>
          {employee ? 'Save Changes' : 'Confirm & Create Account'}
        </Button>
      </div>
    </form>
  );
};

// ── 6. Employee Profile Component (Self-Edit) ──────
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
      const res = await api.put('/employees/profile/me', {
        phone,
        profile_photo: photo,
        designation,
        department
      });
      if (res.data && res.data.success) {
        toast.success('Your profile has been updated successfully!');
      }
    } catch (err) {
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
          {photo ? <img src={photo} alt="" className="w-full h-full object-cover rounded-full" /> : (currentUser?.name || currentUser?.full_name || 'US').substring(0, 2).toUpperCase()}
        </div>
        <div>
          <h3 className="text-sm font-black text-slate-800">{currentUser?.name || currentUser?.full_name || 'User'}</h3>
          <p className="text-xs text-slate-400 font-semibold">{currentUser?.email} &bull; <span className="uppercase text-brand-orange font-bold">{currentUser?.role}</span></p>
        </div>
      </div>

      <form onSubmit={handleSaveProfile} className="space-y-4">
        <Input
          label="Phone Number"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="+91 98765 43210"
        />

        <Input
          label="Profile Photo URL"
          value={photo}
          onChange={(e) => setPhoto(e.target.value)}
          placeholder="https://..."
        />

        <Input
          label="Designation"
          value={designation}
          onChange={(e) => setDesignation(e.target.value)}
          placeholder="Counselor designation"
          disabled={!isAdmin} // only admin can edit designation
        />

        <Input
          label="Department"
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
          placeholder="Counselor department"
          disabled={!isAdmin} // only admin can edit department
        />

        <div className="flex justify-end pt-3">
          <Button type="submit" variant="secondary" isLoading={isSubmitting}>
            Save Profile Settings
          </Button>
        </div>
      </form>
    </Card>
  );
};

// ── 7. Top-Level Employees Page Component ─────────
export const EmployeeManagement = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  // BUG FIX: Always initialize to 'profile' (safe default) to avoid the race
  // condition where user is null on first render. A separate useEffect below
  // syncs this to 'directory' once the admin role is confirmed from the API.
  const [activeTab, setActiveTab] = useState('profile');

  // BUG FIX: Sync activeTab to 'directory' once admin role is confirmed.
  // This handles the async auth check in AuthContext that resolves after mount.
  useEffect(() => {
    if (isAdmin) {
      setActiveTab('directory');
    }
  }, [isAdmin]);

  // List states
  const [employees, setEmployees] = useState([]);
  // BUG FIX: Initialize isLoading to false. The loading state is managed
  // entirely inside fetchEmployees which guards on isAdmin first — preventing
  // counselors from being stuck with isLoading=true indefinitely.
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
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [transferTarget, setTransferTarget] = useState(null);
  const [transferEmployeeId, setTransferEmployeeId] = useState('');
  const [confirmAction, setConfirmAction] = useState(null);
  const [confirmLoading, setConfirmLoading] = useState(false);

  // Deep-link: detect ?view=add from URL (used by Dashboard quick action)
  const [searchParams, setSearchParams] = useSearchParams();
  const view = searchParams.get('view') || 'list';
  const editId = searchParams.get('id');

  // If action=add is in URL (legacy deep-link from Dashboard), redirect to view=add
  useEffect(() => {
    if (searchParams.get('action') === 'add' && isAdmin) {
      searchParams.delete('action');
      searchParams.set('view', 'add');
      setSearchParams(searchParams, { replace: true });
    }
  }, [isAdmin]);

  // Sync activeEmployee if edit view is requested directly via URL query params
  useEffect(() => {
    if (view === 'edit' && editId && !activeEmployee && employees.length > 0) {
      const emp = employees.find(e => e.id === Number(editId) || e.id === editId);
      if (emp) {
        setActiveEmployee(emp);
      } else {
        // Fallback if employee is not found in local state list
        navigate('/employees');
      }
    }
  }, [view, editId, employees, activeEmployee]);

  // Reset Credentials Card
  const [newCredentials, setNewCredentials] = useState(null);

  const fetchEmployees = async () => {
    if (!isAdmin) return;
    try {
      setIsLoading(true);
      const is_active_val = status === 'active' ? true : status === 'inactive' ? false : undefined;
      const res = await api.get('/employees', {
        params: {
          search: search || undefined,
          role: role || undefined,
          department: dept || undefined,
          is_active: is_active_val,
          page
        }
      });
      if (res.data && res.data.success) {
        setEmployees(res.data.data.items || []);
        setTotalCount(res.data.data.total_count || 0);
      }
    } catch (err) {
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

  const handleStatusToggle = async (emp) => {
    if (emp.id === user?.id) {
      toast.error('You cannot deactivate your own account.');
      return;
    }
    const nextStatus = !emp.is_active;
    setConfirmAction({
      title: nextStatus ? 'Activate Employee' : 'Deactivate Employee',
      message: `Are you sure you want to ${nextStatus ? 'activate' : 'deactivate'} "${emp.full_name}"?`,
      confirmText: nextStatus ? 'Activate' : 'Deactivate',
      confirmVariant: nextStatus ? 'primary' : 'warning',
      employee: emp,
      action: 'status',
      payload: { is_active: nextStatus },
    });
  };

  const handlePasswordReset = async (emp) => {
    // Note: window.prompt is used here intentionally for simplicity. In a production
    // accessibility audit, replace with a modal dialog (aria-dialog) that includes an
    // aria-labelledby pointing to the employee name and an accessible password input.
    const password = window.prompt(`Enter new access password for "${emp.full_name}":`);
    if (!password) return;
    if (password.length < 6) {
      toast.error('Password must be at least 6 characters long.');
      return;
    }

    try {
      const res = await api.patch(`/employees/${emp.id}/reset-password`, { password });
      if (res.data && res.data.success) {
        toast.success(`Password reset successfully for "${emp.full_name}".`);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to reset password.');
    }
  };

  const handleArchiveEmployee = (emp) => {
    setConfirmAction({
      title: 'Archive Employee',
      message: `Are you sure you want to archive "${emp.full_name}"?`,
      warning: 'Archived employees cannot login or be assigned new applicants.',
      confirmText: 'Archive',
      confirmVariant: 'warning',
      employee: emp,
      action: 'archive',
    });
  };

  const handleRestoreEmployee = (emp) => {
    setConfirmAction({
      title: 'Restore Employee',
      message: `Are you sure you want to restore "${emp.full_name}"? They will be reactivated.`,
      confirmText: 'Restore',
      confirmVariant: 'primary',
      employee: emp,
      action: 'restore',
    });
  };

  const handleDeleteEmployee = async (emp) => {
    setDeleteTarget(emp);
    try {
      const res = await api.get(`/applicants?assigned_to=${emp.id}&page_size=1`);
      const assignedCount = res.data?.data?.total || 0;
      if (assignedCount > 0) {
        setTransferTarget(emp);
        setTransferEmployeeId('');
      } else {
        setConfirmAction({
          title: 'Delete Employee',
          message: `Are you sure you want to permanently delete "${emp.full_name}"?`,
          warning: 'This action cannot be undone. The employee record will be permanently removed.',
          confirmText: 'Delete',
          confirmVariant: 'danger',
          employee: emp,
          action: 'delete',
        });
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to check employee assignments.');
    }
  };

  const handleConfirmAction = async () => {
    if (!confirmAction) return;
    setConfirmLoading(true);
    const emp = confirmAction.employee;
    try {
      if (confirmAction.action === 'archive') {
        const res = await api.patch(`/employees/${emp.id}/archive`);
        if (res.data?.success) toast.success(`"${emp.full_name}" archived.`);
      } else if (confirmAction.action === 'restore') {
        const res = await api.patch(`/employees/${emp.id}/unarchive`);
        if (res.data?.success) toast.success(`"${emp.full_name}" restored.`);
      } else if (confirmAction.action === 'delete') {
        const res = await api.delete(`/employees/${emp.id}`);
        if (res.data?.success) {
          toast.success(`"${emp.full_name}" deleted permanently.`);
          setDeleteTarget(null);
        }
      } else if (confirmAction.action === 'cleanup') {
        const res = await api.post(`/employees/${emp.id}/cleanup`, { force: true });
        if (res.data?.success) {
          toast.success(`Production cleanup complete: "${emp.full_name}" removed.`);
          setDeleteTarget(null);
        }
      } else if (confirmAction.action === 'status') {
        const res = await api.patch(`/employees/${emp.id}/status`, confirmAction.payload);
        if (res.data?.success) toast.success(`"${emp.full_name}" status updated.`);
      }
      setConfirmAction(null);
      fetchEmployees();
    } catch (err) {
      const errorDetail = err.response?.data?.detail || err.response?.data?.message || `Failed to ${confirmAction.action} employee.`;
      // If delete failed due to FK constraints, offer cleanup option
      if (confirmAction.action === 'delete' && err.response?.status !== 400) {
        toast.error(errorDetail, { duration: 6000 });
        // Show cleanup option
        setConfirmAction({
          title: 'Production Cleanup',
          message: `"${emp.full_name}" has references in the database that prevent normal deletion.`,
          warning: 'Use Force Cleanup to remove this development employee AND all associated records.',
          confirmText: 'Force Delete Test Employee',
          confirmVariant: 'danger',
          employee: emp,
          action: 'cleanup',
        });
      } else {
        toast.error(errorDetail);
      }
    } finally {
      setConfirmLoading(false);
    }
  };

  const handleTransferAndDelete = async () => {
    if (!transferTarget || !transferEmployeeId) {
      toast.error('Please select a replacement employee.');
      return;
    }
    try {
      // Transfer applicants
      const transferRes = await api.post(`/employees/${transferTarget.id}/transfer-applicants`, {
        target_employee_id: Number(transferEmployeeId)
      });
      if (transferRes.data && transferRes.data.success) {
        // Delete the employee
        const delRes = await api.delete(`/employees/${transferTarget.id}`);
        if (delRes.data && delRes.data.success) {
          toast.success(`Applicants transferred and "${transferTarget.full_name}" deleted permanently.`);
          setTransferTarget(null);
          setTransferEmployeeId('');
          setDeleteTarget(null);
          fetchEmployees();
        }
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to transfer and delete.');
    }
  };

  const handleFormSubmit = async (payload) => {
    setIsSubmitting(true);
    try {
      if (activeEmployee) {
        // Edit Employee
        const res = await api.put(`/employees/${activeEmployee.id}`, payload);
        if (res.data && res.data.success) {
          toast.success('Employee updated.');
          setSearchParams({ view: 'list' });
          setActiveEmployee(null);
          fetchEmployees();
        }
      } else {
        // Create Employee
        const res = await api.post('/employees', payload);
        if (res.data && res.data.success) {
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
      toast.error(err.response?.data?.detail || 'Failed to save employee profile.');
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

  // ── RENDER: Add/Edit Full-Page Form View ──────────
  if (view === 'add' || view === 'edit') {
    if (!isAdmin) {
      return <Navigate to="/403" replace />;
    }
    return (
      <div className="space-y-6 text-left animate-fade-in">
        <PageHeader
          title={view === 'add' ? 'Add Staff Account' : 'Edit Staff Account'}
          subtitle={view === 'add' ? 'Provision a new staff member with CRM access credentials' : `Updating staff profile`}
          breadcrumbs={[
            { label: 'Home', path: '/dashboard' },
            { label: 'Employees', path: '/employees' },
            { label: view === 'add' ? 'New Account' : 'Edit' }
          ]}
        />
        <Card>
          <EmployeeForm
            employee={activeEmployee}
            isSubmitting={isSubmitting}
            onSubmit={handleFormSubmit}
            onCancel={() => { setActiveEmployee(null); navigate('/employees'); }}
          />
        </Card>
      </div>
    );
  }

  // ── RENDER: Main Directory / Profile View ────────
  return (
    <div className="space-y-6 text-left">
      <PageHeader 
        title="Employee Registry" 
        subtitle="Manage access, credentials, and portfolios for staff advisors"
        breadcrumbs={[{ label: 'Home', path: '/dashboard' }, { label: 'Employees' }]}
        action={
          isAdmin && activeTab === 'directory' && (
            <Button onClick={() => { setActiveEmployee(null); setSearchParams({ view: 'add' }); }} variant="secondary" className="flex items-center gap-2">
              <Plus size={15} /> Add Staff Account
            </Button>
          )
        }
      />

      {/* Tab Switcher Headers */}
      <div className="flex border-b border-slate-100 gap-6">
        {isAdmin && (
          <button
            onClick={() => setActiveTab('directory')}
            className={`pb-3 text-xs font-bold uppercase tracking-wider border-b-2 transition-all ${
              activeTab === 'directory' ? 'border-brand-orange text-brand-orange' : 'border-transparent text-slate-400 hover:text-slate-600'
            }`}
          >
            Staff Directory
          </button>
        )}
        <button
          onClick={() => setActiveTab('profile')}
          className={`pb-3 text-xs font-bold uppercase tracking-wider border-b-2 transition-all ${
            activeTab === 'profile' ? 'border-brand-orange text-brand-orange' : 'border-transparent text-slate-400 hover:text-slate-600'
          }`}
        >
          My Profile
        </button>
      </div>

      {/* Tab content conditional rendering */}
      {activeTab === 'directory' && isAdmin && (
        <div className="space-y-5">
          {/* Newly created employee creds card banner */}
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
                <button
                  onClick={() => setNewCredentials(null)}
                  className="p-2 text-slate-400 hover:text-slate-600 rounded-lg border border-slate-200 hover:bg-slate-50 transition-all"
                  title="Dismiss"
                >
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
              <div className="py-24 flex justify-center">
                <LoadingSpinner label="Loading employee directory..." />
              </div>
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
                      <tr key={emp.id} className="group hover:bg-slate-50/50 transition-colors cursor-pointer"
                          onClick={() => setDetailsEmployee(emp)}>
                        <td className="py-4 px-4">
                          <span className="text-xs font-mono font-bold text-slate-500 bg-slate-100 border border-slate-200/60 px-2 py-1 rounded">
                            {emp.employee_code || 'EMP-NEW'}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-brand-orange/10 flex items-center justify-center text-brand-orange font-bold text-xs shrink-0">
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
                          <EmployeeStatusBadge isActive={emp.is_active} />
                        </td>
                        <td className="py-4 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                          <div className="flex items-center justify-end gap-1.5 flex-wrap">
                            {/* View */}
                            <button
                              onClick={() => setDetailsEmployee(emp)}
                              className="px-2.5 py-1.5 text-[10px] font-bold rounded-lg border border-blue-200 text-blue-600 bg-blue-50 hover:bg-blue-100 transition-all"
                            >
                              View
                            </button>

                            {/* Edit */}
                            <button
                              onClick={() => { setActiveEmployee(emp); setSearchParams({ view: 'edit', id: emp.id }); }}
                              className="px-2.5 py-1.5 text-[10px] font-bold rounded-lg bg-brand-orange text-white hover:bg-brand-orange/90 transition-all"
                            >
                              Edit
                            </button>

                            {/* Archive / Restore */}
                            {emp.is_active ? (
                              <button
                                onClick={() => handleArchiveEmployee(emp)}
                                disabled={emp.id === user?.id}
                                className="px-2.5 py-1.5 text-[10px] font-bold rounded-lg border border-amber-200 text-amber-600 bg-amber-50 hover:bg-amber-100 transition-all disabled:opacity-40"
                              >
                                Archive
                              </button>
                            ) : (
                              <button
                                onClick={() => handleRestoreEmployee(emp)}
                                className="px-2.5 py-1.5 text-[10px] font-bold rounded-lg border border-emerald-200 text-emerald-600 bg-emerald-50 hover:bg-emerald-100 transition-all"
                              >
                                Restore
                              </button>
                            )}

                            {/* Delete */}
                            <button
                              onClick={() => handleDeleteEmployee(emp)}
                              disabled={emp.id === user?.id}
                              className="px-2.5 py-1.5 text-[10px] font-bold rounded-lg border border-red-200 text-red-600 bg-red-50 hover:bg-red-100 transition-all disabled:opacity-40"
                            >
                              Delete
                            </button>
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

      {activeTab === 'profile' && (
        <EmployeeProfile currentUser={user} />
      )}

      {/* Details drawer overlay */}
      {detailsEmployee && (
        <EmployeeDetailsDrawer
          employee={detailsEmployee}
          onClose={() => setDetailsEmployee(null)}
        />
      )}

      {/* Transfer & Delete Modal */}
      {transferTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div onClick={() => { setTransferTarget(null); setDeleteTarget(null); }} className="absolute inset-0 bg-black/40 backdrop-blur-sm"></div>
          <div className="relative bg-white rounded-2xl shadow-2xl p-6 max-w-md w-full mx-4 text-left z-10">
            <h3 className="text-sm font-bold text-slate-800">Transfer Applicants & Delete Employee</h3>
            <p className="text-xs text-slate-500 mt-2">
              This employee has assigned applicants. Select a replacement employee to transfer them to before deletion.
            </p>
            <div className="mt-4">
              <label className="text-xs font-bold text-slate-600 block mb-1.5">Transfer to:</label>
              <select
                value={transferEmployeeId}
                onChange={(e) => setTransferEmployeeId(e.target.value)}
                className="w-full px-3 py-2.5 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 outline-none focus:border-brand-orange"
              >
                <option value="">Select employee...</option>
                {employees
                  .filter(e => e.id !== transferTarget.id && e.is_active)
                  .sort((a, b) => (a.full_name || '').localeCompare(b.full_name || ''))
                  .map(e => (
                    <option key={e.id} value={e.id}>{e.full_name}</option>
                  ))
                }
              </select>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={() => { setTransferTarget(null); setDeleteTarget(null); }}
                className="flex-1 px-4 py-2 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50 transition-all">
                Cancel
              </button>
              <button onClick={handleTransferAndDelete}
                disabled={!transferEmployeeId}
                className="flex-1 px-4 py-2 rounded-xl bg-red-500 text-white text-xs font-bold hover:bg-red-600 transition-all disabled:opacity-50">
                Transfer & Delete
              </button>
            </div>
          </div>
        </div>
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
    </div>
  );
};


export default EmployeeManagement;
