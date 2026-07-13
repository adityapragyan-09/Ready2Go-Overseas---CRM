import React, { useState, useEffect } from 'react';
import api from '../../config/api';
import { useAuth } from '../../hooks/useAuth';
import { 
  Plus, 
  Trash2, 
  UserPlus, 
  CheckCircle2, 
  Copy, 
  UserCheck, 
  AlertCircle, 
  Key,
  ShieldAlert
} from 'lucide-react';
import toast from 'react-hot-toast';

import Card from '../../components/Card';
import Button from '../../components/Button';
import Input from '../../components/Input';
import PageHeader from '../../components/PageHeader';
import LoadingSpinner from '../../components/LoadingSpinner';

const EmployeeManagement = () => {
  const { user } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Creation modal/states
  const [createOpen, setCreateOpen] = useState(false);
  const [formName, setFormName] = useState('');
  const [formEmail, setFormEmail] = useState('');
  const [formPhone, setFormPhone] = useState('');
  const [formPassword, setFormPassword] = useState('');
  const [formRole, setFormRole] = useState('employee');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Success credentials display
  const [newCredentials, setNewCredentials] = useState(null);

  // Fetch employees
  const fetchEmployees = async () => {
    try {
      setIsLoading(true);
      const res = await api.get('/employees');
      if (res.data && res.data.success) {
        setEmployees(res.data.data);
      }
    } catch (err) {
      toast.error('Failed to load employee registry.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  // Handle employee registration
  const handleCreate = async (e) => {
    e.preventDefault();
    if (!formName || !formEmail || !formPassword) {
      toast.error('Name, email, and password are required.');
      return;
    }

    try {
      setIsSubmitting(true);
      const res = await api.post('/employees', {
        name: formName,
        email: formEmail,
        phone: formPhone || null,
        password: formPassword,
        role: formRole
      });

      if (res.data && res.data.success) {
        toast.success('Employee created successfully!');
        
        // Save credentials to display to the admin
        setNewCredentials({
          name: formName,
          email: formEmail.toLowerCase(),
          password: formPassword,
          role: formRole
        });

        // Reset form
        setFormName('');
        setFormEmail('');
        setFormPhone('');
        setFormPassword('');
        setFormRole('employee');
        setCreateOpen(false);

        // Reload list
        fetchEmployees();
      }
    } catch (err) {
      const errMsg = err.response?.data?.detail || 'Failed to create employee.';
      toast.error(errMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle employee deletion
  const handleDelete = async (id, name) => {
    if (id === user?.id) {
      toast.error('You cannot delete your own logged-in account.');
      return;
    }

    if (!window.confirm(`Are you sure you want to delete employee "${name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      const res = await api.delete(`/employees/${id}`);
      if (res.data && res.data.success) {
        toast.success(`Account for "${name}" has been deleted.`);
        fetchEmployees();
      }
    } catch (err) {
      const errMsg = err.response?.data?.detail || 'Failed to delete employee.';
      toast.error(errMsg);
    }
  };

  // Helper to generate a random password
  const generateRandomPassword = () => {
    const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*";
    let pass = "";
    for (let i = 0; i < 10; i++) {
      pass += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setFormPassword(pass);
  };

  // Copy details to clipboard
  const handleCopyCredentials = () => {
    if (!newCredentials) return;
    const details = `Ready2Go CRM Credentials:\nPortal: http://localhost:5173/\nEmail: ${newCredentials.email}\nPassword: ${newCredentials.password}\nRole: ${newCredentials.role}`;
    navigator.clipboard.writeText(details);
    toast.success('Credentials copied to clipboard!');
  };

  return (
    <div className="space-y-6 text-left">
      <PageHeader 
        title="Employee Management" 
        subtitle="Provision, audit, and revoke advisor accounts"
        breadcrumbs={[{ label: 'Home', path: '/dashboard' }, { label: 'Employees' }]}
        action={
          <Button onClick={() => setCreateOpen(true)} variant="secondary" className="flex items-center gap-2">
            <Plus size={16} />
            Add Employee
          </Button>
        }
      />

      {/* ── Success Dialog Banner for Newly Created Employee ── */}
      {newCredentials && (
        <div className="p-6 rounded-2xl border border-emerald-200 bg-emerald-50/50 backdrop-blur-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4 animate-slide-up">
          <div className="flex gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-600 shrink-0">
              <CheckCircle2 size={24} />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-800">Newly Created Credentials</h4>
              <p className="text-xs text-slate-500 mt-0.5">Copy and securely send these access details to the employee.</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-1 mt-3 bg-white p-3 rounded-xl border border-slate-100 max-w-lg">
                <p className="text-xs text-slate-600"><strong>Name:</strong> {newCredentials.name}</p>
                <p className="text-xs text-slate-600"><strong>Role:</strong> <span className="uppercase text-[10px] font-bold text-brand-orange">{newCredentials.role}</span></p>
                <p className="text-xs text-slate-600"><strong>Email:</strong> {newCredentials.email}</p>
                <p className="text-xs text-slate-600"><strong>Password:</strong> <code className="bg-slate-50 px-1.5 py-0.5 rounded text-red-600 font-bold font-mono">{newCredentials.password}</code></p>
              </div>
            </div>
          </div>
          <div className="flex gap-2 w-full md:w-auto">
            <Button onClick={handleCopyCredentials} variant="outline" size="sm" className="flex items-center gap-1.5 w-full md:w-auto">
              <Copy size={14} />
              Copy details
            </Button>
            <Button onClick={() => setNewCredentials(null)} variant="primary" size="sm" className="w-full md:w-auto">
              Dismiss
            </Button>
          </div>
        </div>
      )}

      {/* ── Employee Table Grid ── */}
      <Card>
        {isLoading ? (
          <div className="py-12 flex justify-center">
            <LoadingSpinner label="Loading staff registry..." />
          </div>
        ) : employees.length === 0 ? (
          <div className="py-12 text-center text-slate-400">
            No employees registered in the system.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 text-xs font-bold text-slate-400 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Employee</th>
                  <th className="py-3.5 px-4">Role</th>
                  <th className="py-3.5 px-4">Phone</th>
                  <th className="py-3.5 px-4">Registered Date</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50 text-sm">
                {employees.map((emp) => (
                  <tr key={emp.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-brand-blue/5 border border-brand-blue/10 flex items-center justify-center text-brand-blue font-bold">
                          {emp.name.substring(0, 2).toUpperCase()}
                        </div>
                        <div className="flex flex-col">
                          <span className="font-bold text-slate-800">{emp.name}</span>
                          <span className="text-xs text-slate-400 font-medium">{emp.email}</span>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold uppercase tracking-wider
                        ${emp.role === 'admin' 
                          ? 'bg-red-50 text-red-600 border border-red-100' 
                          : 'bg-brand-orange/5 text-brand-orange border border-brand-orange/10'
                        }
                      `}>
                        {emp.role}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-slate-500 font-medium">
                      {emp.phone || '--'}
                    </td>
                    <td className="py-4 px-4 text-slate-400 text-xs">
                      {new Date(emp.created_at).toLocaleDateString(undefined, { 
                        year: 'numeric', 
                        month: 'short', 
                        day: 'numeric' 
                      })}
                    </td>
                    <td className="py-4 px-4 text-right">
                      {emp.id === user?.id ? (
                        <span className="text-xs text-slate-400 italic pr-3 font-semibold select-none flex items-center gap-1.5 justify-end">
                          <UserCheck size={14} className="text-emerald-500" />
                          Logged In
                        </span>
                      ) : (
                        <button
                          onClick={() => handleDelete(emp.id, emp.name)}
                          className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all duration-200"
                          title="Delete Employee"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* ── Creation Side-Modal / Drawer ── */}
      {createOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
          {/* Backdrop */}
          <div 
            onClick={() => setCreateOpen(false)}
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
          ></div>
          
          {/* Modal Panel */}
          <div className="relative w-full max-w-md bg-white h-full shadow-2xl flex flex-col justify-between p-6 animate-slide-left z-10 border-l border-slate-100 text-left">
            <div className="space-y-6 flex-1 overflow-y-auto pr-1">
              <div>
                <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                  <UserPlus className="text-brand-orange" size={20} />
                  Provision Staff Member
                </h3>
                <p className="text-xs text-slate-400 mt-1">Create counselor or administrator credentials.</p>
              </div>

              <form onSubmit={handleCreate} className="space-y-5">
                <Input
                  label="Full Name"
                  placeholder="Rahul Sharma"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  required
                />
                
                <Input
                  label="Email Address"
                  type="email"
                  placeholder="counselor@ready2gooverseas.com"
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  required
                />

                <Input
                  label="Phone Number"
                  placeholder="+91 98765 43210"
                  value={formPhone}
                  onChange={(e) => setFormPhone(e.target.value)}
                />

                {/* Password Generation Row */}
                <div className="relative">
                  <Input
                    label="Access Password"
                    placeholder="Minimum 6 characters"
                    value={formPassword}
                    onChange={(e) => setFormPassword(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    onClick={generateRandomPassword}
                    className="absolute right-3 top-[37px] px-2 py-1 bg-slate-50 border border-slate-200 text-slate-500 rounded-lg text-[10px] font-bold uppercase hover:bg-slate-100 transition-colors flex items-center gap-1"
                  >
                    <Key size={10} />
                    Auto
                  </button>
                </div>

                {/* Role selection toggle */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-slate-600 uppercase tracking-wider">
                    Role Privilege
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setFormRole('employee')}
                      className={`px-4 py-3 rounded-xl border text-sm font-semibold text-center transition-all duration-200
                        ${formRole === 'employee' 
                          ? 'border-brand-orange bg-brand-orange/5 text-brand-orange font-bold' 
                          : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                        }
                      `}
                    >
                      Counselor (Staff)
                    </button>
                    <button
                      type="button"
                      onClick={() => setFormRole('admin')}
                      className={`px-4 py-3 rounded-xl border text-sm font-semibold text-center transition-all duration-200
                        ${formRole === 'admin' 
                          ? 'border-red-500 bg-red-50/50 text-red-600 font-bold' 
                          : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                        }
                      `}
                    >
                      Administrator
                    </button>
                  </div>
                </div>

                {/* Alert warning */}
                <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-100 flex items-start gap-2.5 text-amber-700">
                  <ShieldAlert size={16} className="shrink-0 mt-0.5" />
                  <p className="text-[11px] leading-relaxed">
                    Credentials generated are active immediately. Copy and distribute them securely.
                  </p>
                </div>
              </form>
            </div>

            <div className="flex gap-3 pt-6 border-t border-slate-100 mt-6 shrink-0">
              <Button 
                onClick={() => setCreateOpen(false)} 
                variant="outline" 
                className="w-1/3"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button 
                onClick={handleCreate} 
                variant="secondary" 
                className="w-2/3"
                isLoading={isSubmitting}
              >
                Confirm Account
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EmployeeManagement;
