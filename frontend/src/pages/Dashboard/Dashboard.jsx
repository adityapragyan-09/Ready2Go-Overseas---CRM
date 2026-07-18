import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  FileText,
  Bell,
  Search,
  Plus,
  UserPlus,
  RefreshCw,
  Activity,
  Database,
  Cloud,
  Server,
  Clock,
  CheckCircle2,
  Eye,
  X,
  MessageSquare,
  FileDown
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useNotifications } from '../../context/NotificationContext';
import dashboardService from '../../services/dashboardService';
import Card from '../../components/Card';
import LoadingSpinner from '../../components/LoadingSpinner';
import toast from 'react-hot-toast';

export const Dashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { notifications, fetchNotifications, markAsRead } = useNotifications();
  
  // Dashboard states
  const [summary, setSummary] = useState(null);
  const [charts, setCharts] = useState(null);
  const [recent, setRecent] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [system, setSystem] = useState(null);
  
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  const isAdmin = user?.role === 'admin';

  // Workload detail drawer
  const [selectedAdvisor, setSelectedAdvisor] = useState(null);
  const [advisorApplicants, setAdvisorApplicants] = useState([]);
  const [isLoadingAdvisor, setIsLoadingAdvisor] = useState(false);
  const [selectedDeleteDate, setSelectedDeleteDate] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const loadAdvisorApplicants = async (employeeId, name) => {
    if (!employeeId) return;
    setIsLoadingAdvisor(true);
    setSelectedAdvisor({ id: employeeId, name });
    try {
      const res = await api.get(`/applicants?assigned_to=${employeeId}&page_size=100`);
      if (res.data?.success) {
        setAdvisorApplicants(res.data.data.applicants || []);
      } else {
        setAdvisorApplicants([]);
      }
    } catch (err) {
      setAdvisorApplicants([]);
    } finally {
      setIsLoadingAdvisor(false);
    }
  };

  // Load dashboard dataset
  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      const [summaryData, chartsData, recentData] = await Promise.all([
        dashboardService.getSummary(),
        dashboardService.getCharts(),
        dashboardService.getRecent()
      ]);

      setSummary(summaryData);
      setCharts(chartsData);
      setRecent(recentData);

      if (isAdmin) {
        const [empData, sysData] = await Promise.all([
          dashboardService.getEmployees(),
          dashboardService.getSystem()
        ]);
        setEmployees(empData);
        setSystem(sysData);
      } else {
        // Counselors see their own employee item in workload
        const selfData = await dashboardService.getEmployees();
        setEmployees(selfData);
      }

      await fetchNotifications(1);
    } catch (err) {
      toast.error('Failed to load dashboard statistics.');
    } finally {
      setIsLoading(false);
    }
  };

  // BUG FIX: Depend on the full `user` object (not the derived `isAdmin` boolean).
  // When AuthContext resolves asynchronously, `isAdmin` flips from false→true causing
  // a double fetch. Guarding on `user` (null → object) triggers only once after auth,
  // and checking `user` is non-null prevents a premature load with wrong role context.
  useEffect(() => {
    if (!user) return; // wait for auth to resolve before fetching
    loadDashboardData();
  }, [user?.id]); // use user.id as stable dependency — won't change on re-renders

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  // Filter logic for global search across dashboard lists
  const getFilteredApplicants = () => {
    if (!recent?.recent_applicants) return [];
    if (!searchQuery) return recent.recent_applicants;
    return recent.recent_applicants.filter(a => 
      a.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.visa_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.status.toLowerCase().includes(searchQuery.toLowerCase())
    );
  };

  const getFilteredDocuments = () => {
    if (!recent?.recent_documents) return [];
    if (!searchQuery) return recent.recent_documents;
    return recent.recent_documents.filter(d => 
      d.original_file_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.document_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.applicant_name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  };

  const getFilteredEmployees = () => {
    if (!employees) return [];
    if (!searchQuery) return employees;
    return employees.filter(e => 
      e.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (e.role && e.role.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  };

  // Helper: percentage calculation
  const getPercent = (value, total) => {
    if (!total || total === 0) return 0;
    return Math.round((value / total) * 100);
  };

  // Date representation
  const formattedDate = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* ── HEADER & GLOBAL SEARCH ── */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        <div>
          <span className="text-xs font-bold text-brand-orange uppercase tracking-widest">{formattedDate}</span>
          <h1 className="text-3xl font-extrabold text-slate-800 font-display leading-tight mt-1">
            Welcome back, {user?.name || 'Advisor'}
          </h1>
          <p className="text-sm text-slate-500">
            {user?.designation ? `${user.designation} • ` : ''} {user?.department || 'CRM Operations'} Panel
          </p>
        </div>

        {/* Global Search Bar */}
        <div className="relative w-full lg:w-96">
          <Search className="absolute left-4 top-3.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search applicants, employees, documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-11 pr-4 py-3 rounded-2xl border border-slate-100 bg-white/70 backdrop-blur-md focus:border-brand-orange focus:ring-4 focus:ring-brand-orange/10 outline-none transition-brand placeholder-slate-400 text-slate-800 text-sm shadow-sm shadow-brand-blue/5"
          />
        </div>
      </div>

      {/* ── QUICK ACTIONS ── */}
      <div className={`grid grid-cols-1 sm:grid-cols-2 ${isAdmin ? 'md:grid-cols-3' : 'md:grid-cols-2'} gap-4`}>
        <button
          onClick={() => navigate('/applicants?view=add')}
          className="flex items-center gap-3 p-4 rounded-2xl bg-gradient-to-r from-brand-blue to-brand-blue/90 text-white font-semibold text-sm hover:shadow-lg hover:shadow-brand-blue/20 transition-brand group"
        >
          <div className="p-2 rounded-xl bg-white/10 group-hover:scale-110 transition-transform">
            <Plus className="h-4 w-4" />
          </div>
          <span>Add Applicant</span>
        </button>

        {isAdmin && (
          <button
            onClick={() => navigate('/employees?action=add')}
            className="flex items-center gap-3 p-4 rounded-2xl bg-white border border-slate-100/80 shadow-md shadow-brand-blue/5 text-slate-700 font-semibold text-sm hover:bg-slate-50 transition-brand group"
          >
            <div className="p-2 rounded-xl bg-slate-100 group-hover:scale-110 transition-transform text-slate-600">
              <UserPlus className="h-4 w-4" />
            </div>
            <span>Add Employee</span>
          </button>
        )}

        <button
          onClick={() => navigate('/applicants')}
          className="flex items-center gap-3 p-4 rounded-2xl bg-white border border-slate-100/80 shadow-md shadow-brand-blue/5 text-slate-700 font-semibold text-sm hover:bg-slate-50 transition-brand group"
        >
          <div className="p-2 rounded-xl bg-slate-100 group-hover:scale-110 transition-transform text-slate-600">
            <RefreshCw className="h-4 w-4" />
          </div>
          <span>Update Progress</span>
        </button>
      </div>

      {/* ── TOP KPI CARDS GRID ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Card className="hover:scale-[1.02] transition-transform duration-300">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-xs font-bold text-slate-400 uppercase">Total Applicants</span>
              <h3 className="text-3xl font-extrabold text-slate-800 font-display mt-1">{summary?.total_applicants || 0}</h3>
            </div>
            <div className="p-3 rounded-2xl bg-brand-blue/10 text-brand-blue">
              <Users className="h-5 w-5" />
            </div>
          </div>
          <div className="flex items-center gap-2 mt-4 text-[11px] text-slate-500">
            <span className="font-semibold text-emerald-600">{summary?.completed_applications || 0} Completed</span>
            <span>•</span>
            <span>{summary?.applications_processing || 0} Processing</span>
          </div>
        </Card>

        <Card className="hover:scale-[1.02] transition-transform duration-300">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-xs font-bold text-slate-400 uppercase">Visa Approvals</span>
              <h3 className="text-3xl font-extrabold text-slate-800 font-display mt-1">{summary?.visa_approved || 0}</h3>
            </div>
            <div className="p-3 rounded-2xl bg-emerald-50 text-emerald-600">
              <CheckCircle2 className="h-5 w-5" />
            </div>
          </div>
          <div className="flex items-center gap-2 mt-4 text-[11px] text-slate-500">
            <span className="font-semibold text-rose-600">{summary?.visa_rejected || 0} Rejected</span>
            <span>•</span>
            <span>Approval Rate: {getPercent(summary?.visa_approved, (summary?.visa_approved + summary?.visa_rejected))}%</span>
          </div>
        </Card>

        <Card className="hover:scale-[1.02] transition-transform duration-300">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-xs font-bold text-slate-400 uppercase">Documents Stored</span>
              <h3 className="text-3xl font-extrabold text-slate-800 font-display mt-1">{summary?.documents_uploaded || 0}</h3>
            </div>
            <div className="p-3 rounded-2xl bg-indigo-50 text-indigo-600">
              <FileText className="h-5 w-5" />
            </div>
          </div>
          <div className="flex items-center gap-2 mt-4 text-[11px] text-slate-500">
            <span className="font-semibold text-amber-600">{summary?.documents_pending || 0} Pending upload</span>
          </div>
        </Card>

        <Card className="hover:scale-[1.02] transition-transform duration-300">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-xs font-bold text-slate-400 uppercase">Alert Badges</span>
              <h3 className="text-3xl font-extrabold text-slate-800 font-display mt-1">{summary?.unread_notifications || 0}</h3>
            </div>
            <div className="p-3 rounded-2xl bg-brand-orange/10 text-brand-orange">
              <Bell className="h-5 w-5" />
            </div>
          </div>
          <div className="flex items-center gap-2 mt-4 text-[11px] text-slate-500">
            <span>Advisor Action Queue</span>
          </div>
        </Card>
      </div>

      {/* Mini visa breakdown grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-white/40 border border-slate-100 p-4 rounded-3xl backdrop-blur-md">
        <div className="text-center p-3 border-r border-slate-100 last:border-0">
          <span className="text-[10px] font-bold text-slate-400 uppercase">Student Visa</span>
          <h4 className="text-xl font-bold text-brand-blue mt-0.5">{summary?.student_visa || 0}</h4>
        </div>
        <div className="text-center p-3 border-r border-slate-100 last:border-0">
          <span className="text-[10px] font-bold text-slate-400 uppercase">Visit Visa</span>
          <h4 className="text-xl font-bold text-brand-blue mt-0.5">{summary?.visit_visa || 0}</h4>
        </div>
        <div className="text-center p-3 border-r border-slate-100 last:border-0">
          <span className="text-[10px] font-bold text-slate-400 uppercase">Tourist Visa</span>
          <h4 className="text-xl font-bold text-brand-blue mt-0.5">{summary?.tourist_visa || 0}</h4>
        </div>
        <div className="text-center p-3 last:border-0">
          <span className="text-[10px] font-bold text-slate-400 uppercase">Business Visa</span>
          <h4 className="text-xl font-bold text-brand-blue mt-0.5">{summary?.business_visa || 0}</h4>
        </div>
      </div>

      {/* ── CHARTS & ANALYTICS SECTION ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* SVG Area Chart: Monthly Registrations */}
        <Card className="lg:col-span-2" title="Applicant Growth Trends" subtitle="Timeline of registrations in the current year">
          <div className="h-64 flex flex-col justify-between mt-2">
            {charts?.applicant_analytics?.monthly_registrations ? (
              <div className="relative w-full h-full flex items-end">
                {/* SVG Area Grid */}
                <svg className="absolute w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                  {/* Grid Lines */}
                  <line x1="0" y1="25" x2="100" y2="25" stroke="#f1f5f9" strokeWidth="0.5" />
                  <line x1="0" y1="50" x2="100" y2="50" stroke="#f1f5f9" strokeWidth="0.5" />
                  <line x1="0" y1="75" x2="100" y2="75" stroke="#f1f5f9" strokeWidth="0.5" />
                  
                  {/* Generate Path dynamically based on registrations */}
                  {(() => {
                    const data = charts.applicant_analytics.monthly_registrations;
                    const maxVal = Math.max(...data.map(d => d.value), 5);
                    const points = data.map((d, i) => {
                      const x = (i / (data.length - 1)) * 100;
                      const y = 100 - (d.value / maxVal) * 80; // keep margins
                      return `${x},${y}`;
                    });

                    return (
                      <>
                        {/* Shaded Area */}
                        <path
                          d={`M 0,100 L ${points.join(' L ')} L 100,100 Z`}
                          fill="url(#gradient-blue)"
                          opacity="0.15"
                        />
                        {/* Line Path */}
                        <path
                          d={`M ${points.join(' L ')}`}
                          fill="none"
                          stroke="#0b2e5e"
                          strokeWidth="2.5"
                          strokeLinecap="round"
                        />
                        {/* Gradients */}
                        <defs>
                          <linearGradient id="gradient-blue" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#0b2e5e" />
                            <stop offset="100%" stopColor="#fff" stopOpacity="0" />
                          </linearGradient>
                        </defs>
                      </>
                    );
                  })()}
                </svg>

                {/* Monthly count indicators overlay */}
                <div className="absolute w-full flex justify-between px-1 text-[10px] text-slate-500 font-bold">
                  {charts.applicant_analytics.monthly_registrations.map((d, i) => (
                    <div key={i} className="flex flex-col items-center">
                      <span className="mb-1 text-slate-800 bg-slate-50 px-1 rounded">{d.value}</span>
                      <span>{d.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center text-slate-400 text-sm py-20">No monthly metrics available.</div>
            )}
          </div>
        </Card>

        {/* Status Distribution Funnel */}
        <Card title="Pipeline Status Funnel" subtitle="Distribution of active application folders">
          <div className="space-y-4 mt-2">
            {charts?.applicant_analytics?.by_status && charts.applicant_analytics.by_status.length > 0 ? (
              charts.applicant_analytics.by_status.map((item, idx) => {
                const total = summary?.total_applicants || 1;
                const pct = getPercent(item.value, total);
                return (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-slate-600 capitalize">{item.label.replace('_', ' ')}</span>
                      <span className="text-slate-800">{item.value} ({pct}%)</span>
                    </div>
                    <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-brand-orange transition-all duration-500"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="text-center text-slate-400 text-sm py-16">No funnel status data.</div>
            )}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Visa mix & country breakdown */}
        <Card title="Country Demographics" subtitle="Active applicants grouped by destination">
          <div className="space-y-4">
            {charts?.applicant_analytics?.by_country && charts.applicant_analytics.by_country.length > 0 ? (
              charts.applicant_analytics.by_country.map((item, idx) => {
                const maxVal = Math.max(...charts.applicant_analytics.by_country.map(c => c.value), 1);
                const widthPct = (item.value / maxVal) * 100;
                return (
                  <div key={idx} className="flex items-center gap-4">
                    <span className="w-24 text-xs font-bold text-slate-600 truncate">{item.label}</span>
                    <div className="flex-1 h-3 rounded-full bg-slate-100 overflow-hidden">
                      <div 
                        className="h-full rounded-full bg-brand-blue/80" 
                        style={{ width: `${widthPct}%` }}
                      />
                    </div>
                    <span className="text-xs font-bold text-slate-800">{item.value} files</span>
                  </div>
                );
              })
            ) : (
              <div className="text-center text-slate-400 text-sm py-12">No country filters recorded.</div>
            )}
          </div>
        </Card>

      </div>

      {/* ── EMPLOYEE PERFORMANCE & WORKLOAD TABLE ── */}
      <Card title="Advisor Workload & Productivity" subtitle="Active, completed, and pending cases by advisor">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-xs">
            <thead>
              <tr className="border-b border-slate-100 text-slate-400 font-bold uppercase">
                <th className="py-3 px-4">Advisor Name</th>
                <th className="py-3 px-4 text-center">Active Cases</th>
                <th className="py-3 px-4 text-center">Completed Cases</th>
                <th className="py-3 px-4 text-center">Pending Cases</th>
                <th className="py-3 px-4 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {getFilteredEmployees().length > 0 ? (
                getFilteredEmployees().map((emp, idx) => (
                  <tr key={idx} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                    <td className="py-3 px-4 text-left">
                      <p className="font-bold text-slate-800">{emp.name}</p>
                      <p className="text-[10px] text-slate-400 capitalize">{emp.role}</p>
                    </td>
                    <td className="py-3 px-4 text-center font-bold text-slate-700">{emp.active_cases || 0}</td>
                    <td className="py-3 px-4 text-center text-emerald-600 font-semibold">{emp.completed_cases || 0}</td>
                    <td className="py-3 px-4 text-center text-brand-orange font-semibold">{emp.pending_cases || 0}</td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => loadAdvisorApplicants(emp.employee_id, emp.name)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-brand-blue/5 text-brand-blue text-[10px] font-bold hover:bg-brand-blue/10 transition-all"
                      >
                        <Eye size={12} />
                        View Workload
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400">No advisor workload metrics matching filter.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* ── ADVISOR WORKLOAD DETAIL DRAWER ── */}
      {selectedAdvisor && (
        <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
          <div onClick={() => setSelectedAdvisor(null)} className="absolute inset-0 bg-black/40 backdrop-blur-sm"></div>
          <div className="relative w-full max-w-lg bg-white h-full shadow-2xl flex flex-col p-6 animate-slide-left z-10 border-l border-slate-100 text-left overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Advisor Workload</h3>
                <h2 className="text-lg font-black text-slate-800 mt-1">{selectedAdvisor.name}</h2>
              </div>
              <button onClick={() => setSelectedAdvisor(null)} className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-50">
                <X size={18} />
              </button>
            </div>

            {isLoadingAdvisor ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-brand-orange border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : advisorApplicants.length === 0 ? (
              <div className="flex-1 flex items-center justify-center">
                <p className="text-sm text-slate-400">No applicants are currently assigned to this advisor.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {advisorApplicants.map((app) => (
                  <div key={app.id} className="p-4 bg-white border border-slate-100 rounded-xl hover:border-brand-orange/30 transition-all shadow-sm">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <p className="text-sm font-bold text-slate-800">{app.full_name}</p>
                        <p className="text-[10px] text-slate-400">{app.country || '—'} &bull; {app.visa_type}</p>
                      </div>
                      <span className="text-[9px] font-bold uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                        {app.status?.replace('_', ' ') || '—'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-3 pt-2 border-t border-slate-50">
                      <button onClick={() => navigate(`/applicants?view=details&id=${app.id}`)}
                        className="flex items-center gap-1 text-[10px] font-bold text-brand-blue hover:text-brand-orange transition-colors">
                        <Eye size={12} /> Profile
                      </button>
                      <button onClick={() => navigate(`/applicants?view=details&id=${app.id}`)}
                        className="flex items-center gap-1 text-[10px] font-bold text-brand-blue hover:text-brand-orange transition-colors">
                        <FileText size={12} /> Documents
                      </button>
                      <button onClick={() => navigate(`/applicants?view=details&id=${app.id}`)}
                        className="flex items-center gap-1 text-[10px] font-bold text-brand-blue hover:text-brand-orange transition-colors">
                        <MessageSquare size={12} /> Chat
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── RECENT ACTIVITY FEED & NOTIFICATION PANEL ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Recent Activity Log */}
        <Card className="lg:col-span-2" title="System Event Activities Feed" subtitle="Chronological applicant lifecycle changes">
          <div className="space-y-4 max-h-96 overflow-y-auto pr-2 mt-2">
            {getFilteredApplicants().length > 0 || getFilteredDocuments().length > 0 ? (
              <div className="relative border-l-2 border-slate-100 pl-6 ml-3 space-y-6 text-left">
                {/* Applicants registered */}
                {getFilteredApplicants().slice(0, 3).map((a, idx) => (
                  <div key={`app-${idx}`} className="relative">
                    <div className="absolute -left-[31px] top-0.5 p-1 rounded-full bg-blue-50 border border-blue-200 text-brand-blue">
                      <Users className="h-3.5 w-3.5" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-slate-800">New Applicant Registered</p>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Applicant <span className="font-semibold text-slate-700">{a.full_name}</span> has been entered under the <span className="uppercase text-slate-600 font-semibold">{a.visa_type}</span> visa pipeline.
                      </p>
                      <span className="text-[10px] text-slate-400 flex items-center gap-1 mt-1">
                        <Clock className="h-3 w-3" />
                        {new Date(a.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}

                {/* Documents uploaded */}
                {getFilteredDocuments().slice(0, 3).map((d, idx) => (
                  <div key={`doc-${idx}`} className="relative">
                    <div className="absolute -left-[31px] top-0.5 p-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-600">
                      <FileText className="h-3.5 w-3.5" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-slate-800">Document Upload Completed</p>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        File <span className="font-semibold text-slate-700">{d.original_file_name}</span> ({d.document_type}) uploaded for applicant {d.applicant_name}.
                      </p>
                      <span className="text-[10px] text-slate-400 flex items-center gap-1 mt-1">
                        <Clock className="h-3 w-3" />
                        {new Date(d.uploaded_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-slate-400 text-sm py-20">No matching activities found.</div>
            )}
          </div>
        </Card>

        {/* Notifications list Widget */}
        <Card title="Latest Notifications" subtitle="Real-time alerts & action items">
          <div className="space-y-3 max-h-96 overflow-y-auto pr-2 mt-2">
            {notifications && notifications.length > 0 ? (
              notifications.slice(0, 5).map((notif, idx) => (
                <div 
                  key={idx}
                  onClick={() => !notif.is_read && markAsRead(notif.id)}
                  className={`p-3 rounded-xl border text-left cursor-pointer transition-all duration-200 
                    ${notif.is_read ? 'bg-white border-slate-50 hover:bg-slate-50' : 'bg-brand-orange/[0.02] border-brand-orange/10 hover:bg-brand-orange/[0.04]'}
                  `}
                >
                  <div className="flex justify-between items-start gap-2">
                    <h6 className={`text-xs font-bold ${notif.is_read ? 'text-slate-700' : 'text-slate-800'}`}>
                      {notif.title}
                    </h6>
                    {!notif.is_read && <span className="h-2 w-2 rounded-full bg-brand-orange shrink-0 mt-1" />}
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1 leading-relaxed">{notif.message}</p>
                  <span className="text-[9px] text-slate-400 block mt-1.5">{new Date(notif.created_at).toLocaleTimeString()}</span>
                </div>
              ))
            ) : (
              <div className="text-center text-slate-400 text-xs py-16">No notifications found.</div>
            )}
          </div>
        </Card>
      </div>

      {/* ── SYSTEM HEALTH & INFRASTRUCTURE ── */}
      {isAdmin && system && (
        <Card title="System Performance & Infrastructure" subtitle="Admin panel metrics mapping SQLite & Supabase Storage">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mt-2">
            <div className="flex items-center gap-4 bg-slate-50/50 border border-slate-100 p-4 rounded-2xl text-left">
              <div className="p-3 rounded-xl bg-brand-blue/5 text-brand-blue">
                <Database className="h-5 w-5" />
              </div>
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase">Database Engine</p>
                <p className="text-sm font-extrabold text-slate-800 mt-0.5 capitalize">{system.db_backend}</p>
                <p className="text-[10px] text-slate-400">Database backend provider</p>
              </div>
            </div>

            <div className="flex items-center gap-4 bg-slate-50/50 border border-slate-100 p-4 rounded-2xl text-left">
              <div className="p-3 rounded-xl bg-emerald-50 text-emerald-600">
                <Cloud className="h-5 w-5" />
              </div>
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase">Supabase Storage</p>
                <p className="text-sm font-extrabold text-slate-800 mt-0.5">Operational</p>
                <p className="text-[10px] text-slate-400">Bucket: ready2go-documents</p>
              </div>
            </div>

            <div className="flex items-center gap-4 bg-slate-50/50 border border-slate-100 p-4 rounded-2xl text-left">
              <div className="p-3 rounded-xl bg-indigo-50 text-indigo-600">
                <Server className="h-5 w-5" />
              </div>
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase">Active Sessions</p>
                <p className="text-sm font-extrabold text-slate-800 mt-0.5">{system.active_user_sessions} sessions</p>
                <p className="text-[10px] text-slate-400">Last 24 hours</p>
              </div>
            </div>

            <div className="flex items-center gap-4 bg-slate-50/50 border border-slate-100 p-4 rounded-2xl text-left">
              <div className="p-3 rounded-xl bg-brand-orange/10 text-brand-orange">
                <Activity className="h-5 w-5" />
              </div>
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase">System Uptime</p>
                <p className="text-sm font-extrabold text-slate-800 mt-0.5">{(system.system_uptime_seconds / 60).toFixed(0)} mins</p>
                <p className="text-[10px] text-slate-400">Total record entries: {system.total_records}</p>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default Dashboard;
