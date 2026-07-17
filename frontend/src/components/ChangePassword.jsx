import React, { useState, useMemo } from 'react';
import { Lock, Eye, EyeOff, Save, X, Shield, ShieldAlert, ShieldCheck } from 'lucide-react';
import toast from 'react-hot-toast';
import authService from '../services/authService';
import Button from './Button';
import Input from './Input';

const StrengthIcon = ({ level }) => {
  if (level === 3) return <ShieldCheck size={18} className="text-emerald-500" />;
  if (level === 2) return <Shield size={18} className="text-amber-500" />;
  return <ShieldAlert size={18} className="text-red-500" />;
};

export const ChangePassword = ({ onCancel, onSuccess }) => {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState({ current: false, new: false, confirm: false });

  const strength = useMemo(() => {
    const pwd = newPassword;
    let score = 0;
    if (pwd.length >= 8) score++;
    if (pwd.length >= 12) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[a-z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(pwd)) score++;
    if (pwd.length >= 16) score++;
    if (score <= 3) return { level: 0, label: 'Weak', color: 'bg-red-500', width: '25%' };
    if (score <= 5) return { level: 1, label: 'Fair', color: 'bg-amber-500', width: '50%' };
    if (score <= 7) return { level: 2, label: 'Good', color: 'bg-blue-500', width: '75%' };
    return { level: 3, label: 'Strong', color: 'bg-emerald-500', width: '100%' };
  }, [newPassword]);

  const validationErrors = useMemo(() => {
    const errors = [];
    const pwd = newPassword;
    if (pwd && pwd.length < 8) errors.push('At least 8 characters');
    if (pwd && !/[A-Z]/.test(pwd)) errors.push('One uppercase letter');
    if (pwd && !/[a-z]/.test(pwd)) errors.push('One lowercase letter');
    if (pwd && !/[0-9]/.test(pwd)) errors.push('One number');
    if (pwd && !/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(pwd)) errors.push('One special character');
    return errors;
  }, [newPassword]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error('All password fields are required.');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error('New password and confirm password do not match.');
      return;
    }
    if (validationErrors.length > 0) {
      toast.error('Please meet all password requirements.');
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await authService.changePassword(currentPassword, newPassword, confirmPassword);
      if (result.success) {
        toast.success('Password changed successfully!');
        setCurrentPassword(''); setNewPassword(''); setConfirmPassword('');
        if (onSuccess) onSuccess(result.user);
      } else {
        toast.error(result.message || 'Failed to change password.');
      }
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to change password.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggle = (f) => setShowPassword(p => ({ ...p, [f]: !p[f] }));

  const ToggleBtn = ({ field, label }) => (
    <button type="button" onClick={() => toggle(field)}
      className="absolute right-3.5 top-[38px] p-1 text-slate-400 hover:text-slate-600 transition-colors"
      aria-label={label}>
      {showPassword[field] ? <EyeOff size={18} /> : <Eye size={18} />}
    </button>
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="flex items-center gap-3 border-b border-slate-100 pb-4 mb-2">
        <div className="p-2 rounded-xl bg-brand-blue/5 text-brand-blue"><Lock size={20} /></div>
        <div>
          <h3 className="text-sm font-bold text-slate-800">Change Password</h3>
          <p className="text-xs text-slate-400">Must be at least 8 characters with uppercase, lowercase, number, and special character</p>
        </div>
      </div>

      <div className="relative">
        <Input label="Current Password" type={showPassword.current ? 'text' : 'password'}
          placeholder="Enter current password" value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)} disabled={isSubmitting} />
        <ToggleBtn field="current" label="Toggle current password" />
      </div>

      <div className="relative">
        <Input label="New Password" type={showPassword.new ? 'text' : 'password'}
          placeholder="Enter new password" value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)} disabled={isSubmitting} />
        <ToggleBtn field="new" label="Toggle new password" />

        {newPassword && (
          <div className="mt-3 space-y-2">
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
                <div className={`h-full rounded-full transition-all duration-300 ${strength.color}`} style={{ width: strength.width }} />
              </div>
              <span className="text-xs font-bold text-slate-500 min-w-[50px] text-right">{strength.label}</span>
              <StrengthIcon level={strength.level} />
            </div>
            <div className="grid grid-cols-2 gap-1">
              {validationErrors.map((err, i) => (
                <span key={i} className="text-[10px] font-medium text-amber-600 flex items-center gap-1">
                  <span className="w-1 h-1 rounded-full bg-amber-400 shrink-0" /> {err}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="relative">
        <Input label="Confirm New Password" type={showPassword.confirm ? 'text' : 'password'}
          placeholder="Re-enter new password" value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)} disabled={isSubmitting} />
        <ToggleBtn field="confirm" label="Toggle confirm password" />
        {confirmPassword && newPassword !== confirmPassword && (
          <span className="text-xs font-semibold text-red-500 mt-1">Passwords do not match</span>
        )}
      </div>

      <div className="flex gap-3 pt-2">
        {onCancel && (
          <Button onClick={onCancel} variant="outline" type="button" disabled={isSubmitting} className="w-1/3">
            <X size={16} /> Cancel
          </Button>
        )}
        <Button type="submit" variant="primary" isLoading={isSubmitting} className="w-2/3">
          <Save size={16} /> Save Password
        </Button>
      </div>
    </form>
  );
};

export default ChangePassword;
