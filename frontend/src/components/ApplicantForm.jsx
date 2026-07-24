import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Save, GraduationCap, Compass, Plane, Briefcase } from 'lucide-react';
import Input from './Input';
import Button from './Button';

// Validation Schema using Zod
const schema = z.object({
  full_name: z.string().min(1, 'Full Name is required').max(150, 'Name must be less than 150 characters'),
  email: z.string().email('Invalid email address').or(z.literal('')).nullable().optional(),
  phone: z.string()
    .regex(/^\+?[1-9]\d{6,14}$/, 'Must be in international format (e.g. +919876543210)')
    .or(z.literal(''))
    .nullable()
    .optional(),
  country: z.string().max(80, 'Country name must be less than 80 characters').or(z.literal('')).nullable().optional(),
  visa_type: z.enum(['student', 'visit', 'tourist', 'business'], {
    required_error: 'Visa Type is required'
  }),
  status: z.string().min(1, 'Status is required'),
  assigned_to: z.union([z.string(), z.number()]).nullable().optional().transform(v => v ? Number(v) : null),
  notes: z.string().or(z.literal('')).nullable().optional(),
  
  // Student visa metadata
  universityName: z.string().or(z.literal('')).optional(),
  courseName: z.string().or(z.literal('')).optional(),
  intakeYear: z.string().or(z.literal('')).optional(),
  
  // Visit visa metadata
  purposeOfVisit: z.string().or(z.literal('')).optional(),
  
  // Shared metadata
  durationOfStayDays: z.string().or(z.literal('')).optional(),
  
  // Tourist visa metadata
  travelDate: z.string().or(z.literal('')).optional(),
  
  // Business visa metadata
  companyName: z.string().or(z.literal('')).optional(),
  businessPurpose: z.string().or(z.literal('')).optional()
});

const visaTypes = [
  { value: 'student', label: 'Student Visa', icon: GraduationCap },
  { value: 'visit', label: 'Visit Visa', icon: Compass },
  { value: 'tourist', label: 'Tourist Visa', icon: Plane },
  { value: 'business', label: 'Business Visa', icon: Briefcase }
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

export const ApplicantForm = ({
  initialData = null,
  employees = [],
  onSubmit: onSave,
  onCancel,
  isLoading = false,
  forcedVisaType = null
}) => {
  // Pre-fill metadata fields if editing
  const getDefaults = () => {
    if (!initialData) {
      return {
        full_name: '',
        email: '',
        phone: '',
        country: '',
        visa_type: forcedVisaType || 'student',
        status: 'inquiry',
        assigned_to: '',
        notes: '',
        universityName: '',
        courseName: '',
        intakeYear: '',
        purposeOfVisit: '',
        durationOfStayDays: '',
        travelDate: '',
        companyName: '',
        businessPurpose: ''
      };
    }

    const meta = initialData.metadata || {};
    return {
      full_name: initialData.full_name || '',
      email: initialData.email || '',
      phone: initialData.phone || '',
      country: initialData.country || '',
      visa_type: initialData.visa_type || 'student',
      status: initialData.status || 'inquiry',
      assigned_to: initialData.assigned_to || '',
      notes: initialData.notes || '',
      universityName: meta.universityName || '',
      courseName: meta.courseName || '',
      intakeYear: meta.intakeYear || '',
      purposeOfVisit: meta.purposeOfVisit || '',
      durationOfStayDays: meta.durationOfStayDays || '',
      travelDate: meta.travelDate || '',
      companyName: meta.companyName || '',
      businessPurpose: meta.businessPurpose || ''
    };
  };

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors }
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: getDefaults()
  });

  const selectedVisaType = watch('visa_type');

  // Watch for forcedVisaType prop changes to dynamically update form value
  useEffect(() => {
    if (forcedVisaType) {
      setValue('visa_type', forcedVisaType);
    }
  }, [forcedVisaType, setValue]);

  const handleFormSubmit = (data) => {
    // Map visa-specific metadata fields into unified metadata dictionary
    const meta = {};
    if (data.visa_type === 'student') {
      if (data.universityName) meta.universityName = data.universityName;
      if (data.courseName) meta.courseName = data.courseName;
      if (data.intakeYear) meta.intakeYear = data.intakeYear;
    } else if (data.visa_type === 'visit') {
      if (data.purposeOfVisit) meta.purposeOfVisit = data.purposeOfVisit;
      if (data.durationOfStayDays) meta.durationOfStayDays = data.durationOfStayDays;
    } else if (data.visa_type === 'tourist') {
      if (data.travelDate) meta.travelDate = data.travelDate;
      if (data.durationOfStayDays) meta.durationOfStayDays = data.durationOfStayDays;
    } else if (data.visa_type === 'business') {
      if (data.companyName) meta.companyName = data.companyName;
      if (data.businessPurpose) meta.businessPurpose = data.businessPurpose;
      if (data.durationOfStayDays) meta.durationOfStayDays = data.durationOfStayDays;
    }

    const payload = {
      full_name: data.full_name,
      email: data.email || null,
      phone: data.phone || null,
      country: data.country || null,
      visa_type: data.visa_type,
      status: data.status,
      assigned_to: data.assigned_to || null,
      notes: data.notes || null,
      metadata: meta
    };

    onSave(payload);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6 text-left">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Full Name */}
        <Input
          label="Full Name"
          placeholder="e.g. Rajesh Kumar"
          error={errors.full_name}
          {...register('full_name')}
          disabled={isLoading}
        />

        {/* Email */}
        <Input
          label="Email Address"
          type="email"
          placeholder="e.g. rajesh@example.com"
          error={errors.email}
          {...register('email')}
          disabled={isLoading}
        />

        {/* Phone */}
        <Input
          label="Phone Number"
          placeholder="e.g. +919876543210"
          error={errors.phone}
          {...register('phone')}
          disabled={isLoading}
        />

        {/* Country */}
        <Input
          label="Destination Country"
          placeholder="e.g. Canada, United Kingdom"
          error={errors.country}
          {...register('country')}
          disabled={isLoading}
        />

        {/* Visa Type Selector */}
        <div className="flex flex-col gap-1.5 w-full">
          <label className="text-xs font-bold text-slate-600 uppercase tracking-wider">
            Visa Type
          </label>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {visaTypes.map((type) => {
              const Icon = type.icon;
              const isSelected = selectedVisaType === type.value;
              return (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => setValue('visa_type', type.value)}
                  disabled={isLoading || (forcedVisaType && forcedVisaType !== type.value)}
                  className={`
                    px-3 py-3 rounded-xl border text-xs font-bold text-center flex flex-col items-center justify-center gap-1.5 transition-all duration-200
                    ${isSelected 
                      ? 'border-brand-orange bg-brand-orange/5 text-brand-orange font-bold' 
                      : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }
                    disabled:opacity-50
                  `}
                >
                  <Icon size={16} />
                  {type.label}
                </button>
              );
            })}
          </div>
          {errors.visa_type && (
            <span className="text-xs font-semibold text-red-500">{errors.visa_type.message}</span>
          )}
        </div>

        {/* Status Dropdown */}
        <div className="flex flex-col gap-1.5 w-full">
          <label className="text-xs font-bold text-slate-600 uppercase tracking-wider">
            Application Status
          </label>
          <select
            {...register('status')}
            disabled={isLoading}
            className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white/70 backdrop-blur-sm focus:border-brand-blue focus:ring-4 focus:ring-brand-blue/10 outline-none transition-all duration-200 text-sm text-slate-800"
          >
            {statuses.map((status) => (
              <option key={status.value} value={status.value}>
                {status.label}
              </option>
            ))}
          </select>
          {errors.status && (
            <span className="text-xs font-semibold text-red-500">{errors.status.message}</span>
          )}
        </div>

        {/* Employee Handling */}
        <div className="flex flex-col gap-1.5 w-full">
          <label className="text-xs font-bold text-slate-600 uppercase tracking-wider">
            Employee Handling
          </label>
          <select
            {...register('assigned_to')}
            disabled={isLoading}
            className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white/70 backdrop-blur-sm focus:border-brand-blue focus:ring-4 focus:ring-brand-blue/10 outline-none transition-all duration-200 text-sm text-slate-800"
          >
            <option value="">Unassigned</option>
            {employees
              .filter(emp => emp.role !== 'admin' && emp.is_active !== false)
              .sort((a, b) => (a.full_name || '').localeCompare(b.full_name || ''))
              .map((emp) => (
              <option key={emp.id} value={emp.id}>
                {emp.full_name}
              </option>
            ))}
            {employees.filter(emp => emp.role !== 'admin' && emp.is_active !== false).length === 0 && (
              <option value="" disabled>No active employees available</option>
            )}
          </select>
          {errors.assigned_to && (
            <span className="text-xs font-semibold text-red-500">{errors.assigned_to.message}</span>
          )}
        </div>

        {/* Notes (Full width) */}
        <div className="flex flex-col gap-1.5 w-full md:col-span-2">
          <label className="text-xs font-bold text-slate-600 uppercase tracking-wider">
            Application Notes
          </label>
          <textarea
            {...register('notes')}
            disabled={isLoading}
            rows={3}
            placeholder="Add case logs, advisor instructions, or updates..."
            className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white/70 backdrop-blur-sm focus:border-brand-blue focus:ring-4 focus:ring-brand-blue/10 outline-none transition-all duration-200 text-sm text-slate-800 placeholder-slate-400"
          />
          {errors.notes && (
            <span className="text-xs font-semibold text-red-500">{errors.notes.message}</span>
          )}
        </div>

      </div>

      {/* ── Visa Specific Fields Section ── */}
      <div className="border-t border-slate-100 pt-5 mt-4">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">
          Visa-Specific Details ({selectedVisaType ? `${selectedVisaType} details` : 'choose visa type'})
        </h4>
        
        {selectedVisaType === 'student' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-in">
            <Input
              label="University / Institution Name"
              placeholder="e.g. University of Toronto"
              error={errors.universityName}
              {...register('universityName')}
              disabled={isLoading}
            />
            <Input
              label="Course / Program Name"
              placeholder="e.g. Master of Computer Science"
              error={errors.courseName}
              {...register('courseName')}
              disabled={isLoading}
            />
            <Input
              label="Intake Year / Session"
              placeholder="e.g. Fall 2026"
              error={errors.intakeYear}
              {...register('intakeYear')}
              disabled={isLoading}
            />
          </div>
        )}

        {selectedVisaType === 'visit' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fade-in">
            <Input
              label="Purpose of Visit"
              placeholder="e.g. Family meetup, Medical treatment"
              error={errors.purposeOfVisit}
              {...register('purposeOfVisit')}
              disabled={isLoading}
            />
            <Input
              label="Duration of Stay (Days)"
              type="number"
              placeholder="e.g. 30"
              error={errors.durationOfStayDays}
              {...register('durationOfStayDays')}
              disabled={isLoading}
            />
          </div>
        )}

        {selectedVisaType === 'tourist' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-in">
            <Input
              label="Expected Travel Date"
              type="date"
              error={errors.travelDate}
              {...register('travelDate')}
              disabled={isLoading}
            />
            <Input
              label="Duration of Stay (Days)"
              type="number"
              placeholder="e.g. 15"
              error={errors.durationOfStayDays}
              {...register('durationOfStayDays')}
              disabled={isLoading}
            />
          </div>
        )}

        {selectedVisaType === 'business' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-in">
            <Input
              label="Company Name"
              placeholder="e.g. Acme Corporation"
              error={errors.companyName}
              {...register('companyName')}
              disabled={isLoading}
            />
            <Input
              label="Business Purpose"
              placeholder="e.g. Tech Conference, Trade Deal"
              error={errors.businessPurpose}
              {...register('businessPurpose')}
              disabled={isLoading}
            />
            <Input
              label="Expected Duration (Days)"
              type="number"
              placeholder="e.g. 10"
              error={errors.durationOfStayDays}
              {...register('durationOfStayDays')}
              disabled={isLoading}
            />
          </div>
        )}
      </div>

      {/* Form Action Buttons */}
      <div className="flex justify-end gap-3 border-t border-slate-100 pt-6 mt-6">
        <Button
          onClick={onCancel}
          variant="outline"
          disabled={isLoading}
          className="w-full sm:w-auto"
        >
          Cancel
        </Button>
        <Button
          type="submit"
          variant="primary"
          isLoading={isLoading}
          className="w-full sm:w-auto flex items-center gap-2"
        >
          <Save size={16} />
          Save Record
        </Button>
      </div>

    </form>
  );
};

export default ApplicantForm;
