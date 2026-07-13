import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Eye, EyeOff, Shield, Users } from 'lucide-react';
import toast from 'react-hot-toast';

import AuthLayout from '../../layouts/AuthLayout';
import Button from '../../components/Button';
import Input from '../../components/Input';
import useDocumentTitle from '../../hooks/useDocumentTitle';

// Form validation schema using Zod
const loginSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

const Login = () => {
  const [portalRole, setPortalRole] = useState('admin'); // Defaulting to admin portal login
  
  // Set browser title dynamically based on active portal choice
  useDocumentTitle(portalRole === 'admin' ? 'Administrator Login' : 'Staff Login');

  const { login, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    }
  });

  // Calculate redirect destination
  const from = location.state?.from?.pathname || '/dashboard';

  // Watch for expired sessions
  useEffect(() => {
    if (location.search.includes('expired=true')) {
      toast.error('Session Expired. Please login again.', { id: 'session-expired' });
    }
  }, [location.search]);

  // Reset form inputs when switching portals
  const handlePortalSwitch = (role) => {
    setPortalRole(role);
    reset({
      email: '',
      password: ''
    });
  };

  const onSubmit = async (data) => {
    try {
      const result = await login(data.email, data.password);
      
      if (result.success) {
        // Enforce role-based login gate based on selected portal option
        if (result.user.role !== portalRole) {
          await logout(); // Wipe session token immediately
          toast.error(
            portalRole === 'admin' 
              ? 'Authorized Administrator credentials required for this portal.' 
              : 'Authorized Staff/Counselor credentials required for this portal.'
          );
          return;
        }

        toast.success(`${portalRole === 'admin' ? 'Administrator' : 'Staff'} Login Successful!`);
        navigate(from, { replace: true });
      } else {
        toast.error(result.message || 'Invalid Credentials');
      }
    } catch (err) {
      toast.error('Network Error. Please verify your connection.');
    }
  };

  return (
    <AuthLayout>
      {/* Heading */}
      <div className="text-left">
        <h2 className="text-2xl font-extrabold text-slate-800 font-display">
          {portalRole === 'admin' ? 'Administrator Portal' : 'Counselor Registry'}
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          {portalRole === 'admin' 
            ? 'Authenticate to manage staff registry & audit logs.' 
            : 'Access client applications & processing queues.'
          }
        </p>
      </div>

      {/* Login Form card */}
      <div className="bg-white p-6 md:p-8 rounded-2xl border border-slate-100 shadow-xl shadow-slate-100/50 space-y-6">
        
        {/* ── Two Login Options (Tabs) ── */}
        <div className="grid grid-cols-2 gap-2 bg-slate-50 p-1.5 rounded-xl border border-slate-100">
          <button
            type="button"
            onClick={() => handlePortalSwitch('admin')}
            className={`
              flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-bold transition-all duration-200
              ${portalRole === 'admin' 
                ? 'bg-brand-blue text-white shadow-md shadow-brand-blue/10' 
                : 'text-slate-500 hover:text-slate-700'
              }
            `}
          >
            <Shield size={14} />
            Admin Login
          </button>
          
          <button
            type="button"
            onClick={() => handlePortalSwitch('employee')}
            className={`
              flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-bold transition-all duration-200
              ${portalRole === 'employee' 
                ? 'bg-brand-orange text-white shadow-md shadow-brand-orange/10' 
                : 'text-slate-500 hover:text-slate-700'
              }
            `}
          >
            <Users size={14} />
            Employee Login
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          
          {/* Email Input */}
          <Input
            label="Email Address"
            type="email"
            placeholder={portalRole === 'admin' ? 'admin@ready2gooverseas.com' : 'counselor@ready2gooverseas.com'}
            error={errors.email}
            disabled={isSubmitting}
            {...register('email')}
          />

          {/* Password Input */}
          <div className="relative">
            <Input
              label="Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              error={errors.password}
              disabled={isSubmitting}
              {...register('password')}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3.5 top-[38px] p-1 text-slate-400 hover:text-slate-600 transition-colors"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            isLoading={isSubmitting}
            variant={portalRole === 'admin' ? 'primary' : 'secondary'}
            className="w-full mt-3"
          >
            Authenticate {portalRole === 'admin' ? 'Admin' : 'Counselor'}
          </Button>
        </form>
      </div>
    </AuthLayout>
  );
};

export default Login;
