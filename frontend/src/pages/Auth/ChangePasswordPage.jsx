import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, AlertTriangle } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import ChangePassword from '../../components/ChangePassword';
import Card from '../../components/Card';
import Logo from '../../assets/logo/Logo';

export const ChangePasswordPage = () => {
  const { updateUser, mustChangePassword } = useAuth();
  const navigate = useNavigate();

  const handleSuccess = (user) => {
    if (updateUser) updateUser(user);
    // Navigate to dashboard after successful password change
    navigate('/dashboard', { replace: true });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="w-full max-w-md space-y-6">
        {/* Logo */}
        <div className="flex justify-center">
          <Logo variant="default" className="h-10 w-auto" />
        </div>

        {mustChangePassword && (
          <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800">
            <AlertTriangle size={20} className="text-amber-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-bold">Password Change Required</p>
              <p className="text-xs mt-1 text-amber-700">
                Your password has been reset by an administrator. Please set a new password to continue.
              </p>
            </div>
          </div>
        )}

        <Card>
          <ChangePassword
            onSuccess={handleSuccess}
          />
        </Card>
      </div>
    </div>
  );
};

export default ChangePasswordPage;
