import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import Logo from '../assets/logo/Logo';
import { 
  LayoutDashboard, 
  Users, 
  GraduationCap, 
  Compass, 
  Plane, 
  Briefcase, 
  LogOut, 
  Menu, 
  X, 
  User as UserIcon,
  Shield,
  Activity,
  ChevronDown,
  PhoneCall,
  ClipboardList,
  Bell,
  Inbox
} from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../config/api';

const DashboardLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [sidebarCounts, setSidebarCounts] = useState({});
  const dropdownRef = useRef(null);

  const handleLogout = async () => {
    await logout();
    toast.success('Logout Successful!');
    navigate('/login');
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setProfileMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch sidebar badges with polling
  useEffect(() => {
    const fetchCounts = async () => {
      try {
        const [notifRes, leadRes, pendingRes] = await Promise.all([
          api.get('/notifications/unread-count'),
          api.get('/applicants').catch(() => ({ data: { success: false } })),
          api.get('/assignment-requests?status=PENDING').catch(() => ({ data: { success: false } })),
        ]);
        if (notifRes.data?.success) setUnreadCount(notifRes.data.data.unread_count || 0);
        const counts = {};
        if (leadRes.data?.success) counts.leads = leadRes.data.data.total || 0;
        if (pendingRes.data?.success) counts.pendingRequests = pendingRes.data.data.total || 0;
        setSidebarCounts(counts);
      } catch { /* silent */ }
    };
    fetchCounts();
    const interval = setInterval(fetchCounts, 30000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'All Applicants', path: '/applicants', icon: Users },
    { label: 'Student Visa', path: '/applicants?visa_type=student', icon: GraduationCap },
    { label: 'Visit Visa', path: '/applicants?visa_type=visit', icon: Compass },
    { label: 'Tourist Visa', path: '/applicants?visa_type=tourist', icon: Plane },
    { label: 'Business Visa', path: '/applicants?visa_type=business', icon: Briefcase },
    { label: 'Lead Inquiries', path: '/lead-inquiries', icon: PhoneCall },
    { label: 'Inbox', path: '/inbox', icon: Inbox },
  ];

  // Admin-only items
  if (user?.role === 'admin') {
    navItems.push(
      { label: 'Employee Management', path: '/employees', icon: Shield },
      { label: 'Activity Logs', path: '/activity-logs', icon: Activity },
      { label: 'Assignment Requests', path: '/assignment-requests', icon: ClipboardList }
    );
  }

  const isActive = (itemPath) => {
    if (itemPath.includes('?')) {
      return location.pathname + location.search === itemPath;
    }
    if (itemPath === '/applicants' && location.search !== '') {
      return false;
    }
    return location.pathname === itemPath;
  };

  // Generate dynamic breadcrumbs based on URL path
  const getBreadcrumbs = () => {
    const pathnames = location.pathname.split('/').filter((x) => x);
    const crumbs = [{ label: 'Home', path: '/dashboard' }];
    
    let currentPath = '';
    pathnames.forEach((name, index) => {
      currentPath += `/${name}`;
      if (name === 'dashboard') return;
      
      // Capitalize first letter of path segment
      const label = name.charAt(0).toUpperCase() + name.slice(1).replace('-', ' ');
      crumbs.push({
        label,
        path: index === pathnames.length - 1 ? null : currentPath,
      });
    });
    return crumbs;
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-slate-50">
      
      {/* ── Mobile Top Header ───────────────────── */}
      <header className="md:hidden bg-brand-dark px-4 py-3 flex items-center justify-between sticky top-0 z-50 shadow-md">
        <Logo variant="light" className="h-8 w-auto" />
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-expanded={mobileMenuOpen}
          aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
          className="p-1.5 rounded-lg hover:bg-white/5 text-slate-300 hover:text-white transition-colors"
        >
          {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </header>

      {/* ── Sidebar Drawer ──────────────────────── */}
      <aside className={`
        fixed inset-y-0 left-0 z-40 w-64 bg-brand-dark text-white flex flex-col transform transition-transform duration-300 ease-in-out
        md:translate-x-0 md:relative md:flex md:h-screen md:shrink-0
        ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Desktop Sidebar Logo Header */}
        <div className="hidden md:flex items-center px-6 py-6 border-b border-white/5">
          <Logo variant="light" className="h-10 w-auto" />
        </div>

        {/* Navigation links */}
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto [scrollbar-width:none] [-ms-overflow-style:none]" aria-label="Main navigation">
          {navItems.map((item, idx) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <Link
                key={idx}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                aria-current={active ? 'page' : undefined}
                className={`
                  flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 group
                  ${active
                    ? 'bg-brand-orange text-white shadow-md shadow-brand-orange/20'
                    : 'text-slate-300 hover:text-white hover:bg-white/5'
                  }
                `}
              >
                <Icon size={18} className={active ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'} />
                <span className="flex-1">{item.label}</span>
                {(() => {
                  const lbl = item.label;
                  let b = null;
                  if (lbl === 'Inbox' && unreadCount > 0) b = unreadCount;
                  else if (lbl === 'Lead Inquiries' && sidebarCounts.leads > 0) b = sidebarCounts.leads;
                  else if (lbl === 'Assignment Requests' && sidebarCounts.pendingRequests > 0) b = sidebarCounts.pendingRequests;
                  return b !== null ? <span className={`px-1.5 py-0.5 rounded-md text-[10px] font-bold ${active ? 'bg-white/20 text-white' : 'bg-brand-orange text-white'}`}>{b > 99 ? '99+' : b}</span> : null;
                })()}
              </Link>
            );
          })}
        </nav>

        {/* User Card */}
        <div className="p-4 border-t border-white/5 bg-white/[0.02]">
          <div className="flex items-center justify-between mb-2 px-2">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center text-slate-200 shrink-0">
                <UserIcon size={18} />
              </div>
              <div className="flex flex-col min-w-0 text-left">
                <span className="text-sm font-semibold truncate text-white">{user?.name || 'Employee'}</span>
                <span className="text-[10px] text-brand-orange uppercase font-bold tracking-wider leading-none mt-0.5">{user?.role}</span>
              </div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 mt-3 px-4 py-2.5 rounded-xl border border-white/10 hover:border-white/20 hover:bg-white/5 text-sm font-medium text-slate-300 hover:text-white transition-all duration-200"
          >
            <LogOut size={16} />
            Log Out
          </button>
        </div>
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div
          onClick={() => setMobileMenuOpen(false)}
          aria-label="Close menu"
          className="fixed inset-0 bg-black/40 z-30 md:hidden backdrop-blur-sm"
        ></div>
      )}

      {/* ── Main Panel ──────────────────────────── */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto h-screen">
        
        {/* Desktop Top Header & Navigation */}
        <header className="hidden md:flex items-center justify-between px-8 py-4 bg-white/70 backdrop-blur-md border-b border-slate-100 sticky top-0 z-30">
          {/* Breadcrumb Path area */}
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-400">
            {getBreadcrumbs().map((crumb, idx) => (
              <React.Fragment key={idx}>
                {idx > 0 && <span>/</span>}
                {crumb.path ? (
                  <Link to={crumb.path} className="hover:text-brand-orange transition-colors">
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-slate-800 font-bold">{crumb.label}</span>
                )}
              </React.Fragment>
            ))}
          </div>

          {/* Inbox icon + User Profile dropdown menu */}
          <div className="flex items-center gap-2">
            <Link to="/inbox" className="relative p-2 rounded-xl hover:bg-slate-50 transition-colors" title="Inbox">
              <Inbox className="h-5 w-5 text-slate-600" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-brand-orange text-white text-[8px] font-bold flex items-center justify-center">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </Link>
            <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setProfileMenuOpen(!profileMenuOpen)}
              className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl hover:bg-slate-50 transition-colors"
            >
              <div className="w-8 h-8 rounded-lg bg-brand-blue/5 border border-brand-blue/10 flex items-center justify-center text-brand-blue font-bold text-xs">
                {user?.name ? user.name.substring(0, 2).toUpperCase() : 'US'}
              </div>
              <span className="text-sm font-semibold text-slate-700 hidden sm:inline">{user?.name || 'User'}</span>
              <ChevronDown size={14} className="text-slate-400" />
            </button>

            {/* Dropdown Card */}
            {profileMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white border border-slate-100 rounded-xl shadow-xl shadow-slate-100/50 py-1.5 z-50 animate-fade-in text-left">
                <div className="px-4 py-2 border-b border-slate-100">
                  <p className="text-sm font-bold text-slate-800 truncate">{user?.name}</p>
                  <p className="text-xs text-brand-orange font-bold uppercase mt-0.5">{user?.role}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2 transition-colors text-left"
                >
                  <LogOut size={14} />
                  Sign Out
                </button>
              </div>
            )}
          </div>
          </div>
        </header>

        {/* Page Content viewport */}
        <div className="flex-1 p-6 md:p-8 animate-fade-in">
          {/* Renders nested routes here dynamically */}
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
