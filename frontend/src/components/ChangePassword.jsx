import React, { useState } from 'react';
import { Lock, Eye, EyeOff, Save, X } from 'lucide-react';
import toast from 'react-hot-toast';
import authService from '../services/authService';
import Button from './Button';
import Input from './Input';

export const ChangePassword = ({ onCancel, onSuccess }) => {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState({ current: false, new: false, confirm: false });

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error('All password fields are required.');
      return;
    }

    if (newPassword.length < 6) {
      toast.error('New password must be at least 6 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error('New password and confirm password do not match.');
      return;
    }

    if (newPassword === currentPassword) {
      toast.error('New password must be different from current password.');
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await authService.changePassword(currentPassword, newPassword, confirmPassword);
      if (result.success) {
        toast.success('Password changed successfully!');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        if (onSuccess) onSuccess(result.user);
      } else {
        toast.error(result.message || 'Failed to change password.');
      }
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to change password. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleVisibility = (field) => {
    setShowPassword(prev => ({ ...prev, [field]: !prev[field] }));
  };

  const PasswordToggle = ({ field }) => (
    <button
      type="button"
      onClick={() => toggleVisibility(field)}
      className="absolute right-3.5 top-[38px] p-1 text-slate-400 hover:text-slate-600 transition-colors"
      aria-label={showPassword[field] ? 'Hide password' : 'Show password'}
    >
      {showPassword[field] ? <EyeOff size={18} /> : <Eye size={18} />}
    </button>
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="flex items-center gap-3 border-b border-slate-100 pb-4 mb-2">
        <div className="p-2 rounded-xl bg-brand-blue/5 text-brand-blue">
          <Lock size={20} />
        </div>
        <div>
          <h3 className="text-sm font-bold text-slate-800">Change Password</h3>
          <p className="text-xs text-slate-400">Update your account password</p>
        </div>
      </div>

      <div className="relative">
        <Input
          label="Current Password"
          type={showPassword.current ? 'text' : 'password'}
          placeholder="Enter current password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          disabled={isSubmitting}
        />
        <PasswordToggle field="current" />
      </div>

      <div className="relative">
        <Input
          label="New Password"
          type={showPassword.new ? 'text' : 'password'}
          placeholder="Enter new password (min. 6 characters)"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          disabled={isSubmitting}
        />
        <PasswordToggle field="new" />
      </div>

      <div className="relative">
        <Input
          label="Confirm New Password"
          type={showPassword.confirm ? 'text' : 'password'}
          placeholder="Re-enter new password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          disabled={isSubmitting}
        />
        <PasswordToggle field="confirm" />
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
