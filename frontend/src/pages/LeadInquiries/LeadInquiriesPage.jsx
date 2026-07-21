import React, { useState, useEffect, useCallback } from 'react';
import { Plus, Search, RefreshCw, Phone, Mail, Globe, ChevronDown, Check, X } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../../config/api';
import { useAuth } from '../../hooks/useAuth';
import leadInquiryService from '../../services/leadInquiryService';
import Card from '../../components/Card';
import PageHeader from '../../components/PageHeader';
import LoadingSpinner from '../../components/LoadingSpinner';
import StatusBadge from '../../components/StatusBadge';
import EmptyState from '../../components/EmptyState';

const STATUS_COLORS = {
  NEW: 'text-blue-600 bg-blue-50',
  CONTACTED: 'text-amber-600 bg-amber-50',
  FOLLOW_UP: 'text-purple-600 bg-purple-50',
  QUALIFIED: 'text-emerald-600 bg-emerald-50',
  CONVERTED: 'text-green-600 bg-green-50',
  CLOSED: 'text-slate-500 bg-slate-50',
};

export const LeadInquiriesPage = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [leads, setLeads] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Assignment state
  const [employees, setEmployees] = useState([]);
  const [assigningLead, setAssigningLead] = useState(null);
  const [assignSearch, setAssignSearch] = useState('');
  const [assignLoading, setAssignLoading] = useState({});
  const [pendingRequests, setPendingRequests] = useState({});
  const [requestLoading, setRequestLoading] = useState({});

  // Fetch employees for admin assignment dropdown
  const fetchEmployees = useCallback(async () => {
    if (!isAdmin) return;
    try {
      const res = await api.get('/employees', { params: { page_size: 100 } });
      if (res.data?.success) {
        setEmployees((res.data.data.items || []).filter(e => e.is_active && e.role !== 'admin'));
      }
    } catch {
      // Silent fail — assignment dropdown unavailable
    }
  }, [isAdmin]);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  // Fetch pending requests for the current employee
  const fetchPendingRequests = useCallback(async () => {
    try {
      const res = await api.get('/assignment-requests', { params: { page_size: 100 } });
      if (res.data?.success) {
        const reqs = {};
        (res.data.data.items || []).forEach(r => {
          if (r.status === 'PENDING') {
            reqs[r.lead_id] = r;
          }
        });
        setPendingRequests(reqs);
      }
    } catch {
      // Silent fail
    }
  }, []);

  useEffect(() => {
    if (!isAdmin) {
      fetchPendingRequests();
    }
  }, [isAdmin, fetchPendingRequests, page]);

  const handleRequestAssignment = async (leadId) => {
    if (!window.confirm('Request assignment of this lead to yourself? It requires admin approval.')) return;
    setRequestLoading(prev => ({ ...prev, [leadId]: true }));
    try {
      const res = await api.post('/assignment-requests', { lead_id: leadId });
      if (res.data?.success) {
        toast.success('Assignment request submitted for admin approval.');
        fetchPendingRequests();
      }
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to submit request.');
    } finally {
      setRequestLoading(prev => ({ ...prev, [leadId]: false }));
    }
  };

  const handleCancelRequest = async (requestId, leadId) => {
    if (!window.confirm('Cancel this assignment request?')) return;
    setRequestLoading(prev => ({ ...prev, [leadId]: true }));
    try {
      const res = await api.delete(`/assignment-requests/${requestId}`);
      if (res.data?.success) {
        toast.success('Request cancelled.');
        fetchPendingRequests();
      }
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to cancel request.');
    } finally {
      setRequestLoading(prev => ({ ...prev, [leadId]: false }));
    }
  };

  const fetchLeads = async () => {
    try {
      setIsLoading(true);
      const data = await leadInquiryService.getLeads({
        search: search || undefined,
        status: statusFilter || undefined,
        page,
        page_size: pageSize,
      });
      setLeads(data.leads || []);
      setTotal(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      toast.error(err.message || 'Failed to load leads');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, [page, statusFilter]);

  const handleDirectAssign = async (leadId, employeeId) => {
    setAssignLoading(prev => ({ ...prev, [leadId]: true }));
    try {
      const res = await api.post('/assignment-requests/direct-assign', { lead_id: leadId, employee_id: employeeId });
      if (res.data?.success) {
        toast.success('Lead assigned successfully.');
        setAssigningLead(null);
        setAssignSearch('');
        // Update the lead in local state without full reload
        setLeads(prev => prev.map(l =>
          l.id === leadId ? {
            ...l,
            assigned_employee_id: employeeId,
            assigned_employee_name: employeeId
              ? (employees.find(e => e.id === employeeId)?.full_name || 'Assigned')
              : null,
          } : l
        ));
      }
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to assign lead.');
    } finally {
      setAssignLoading(prev => ({ ...prev, [leadId]: false }));
    }
  };

  const filteredEmployees = employees
    .filter(e => !assignSearch || e.full_name?.toLowerCase().includes(assignSearch.toLowerCase()) || e.email?.toLowerCase().includes(assignSearch.toLowerCase()))
    .sort((a, b) => (a.full_name || '').localeCompare(b.full_name || ''));

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchLeads();
  };

  return (
    <div className="space-y-6 text-left animate-fade-in">
      <PageHeader
        title="Lead Inquiries"
        subtitle="Manage incoming inquiries from website, phone, WhatsApp, and social media"
        breadcrumbs={[{ label: 'Home', path: '/dashboard' }, { label: 'Lead Inquiries' }]}
      />

      <Card>
        <div className="flex flex-col md:flex-row gap-3 mb-6">
          <form onSubmit={handleSearch} className="flex-1 flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by name, email, phone, or lead number..."
                className="w-full pl-10 pr-4 py-2 border border-slate-200 bg-white rounded-xl text-xs font-semibold focus:border-brand-blue outline-none transition-all"
              />
            </div>
            <button type="submit" className="px-4 py-2 rounded-xl bg-brand-blue text-white text-xs font-bold hover:bg-brand-blue/90 transition-all">
              <Search size={14} />
            </button>
          </form>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded-xl border border-slate-200 bg-white text-xs font-semibold text-slate-600 outline-none"
          >
            <option value="">All Statuses</option>
            <option value="NEW">New</option>
            <option value="CONTACTED">Contacted</option>
            <option value="FOLLOW_UP">Follow Up</option>
            <option value="QUALIFIED">Qualified</option>
            <option value="CONVERTED">Converted</option>
            <option value="CLOSED">Closed</option>
          </select>
          <button onClick={fetchLeads} className="px-3 py-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition-all">
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>

        {isLoading ? (
          <div className="py-24 flex justify-center"><LoadingSpinner label="Loading leads..." /></div>
        ) : leads.length === 0 ? (
          <EmptyState title="No Leads Found" description="Lead inquiries from the website and other channels will appear here." />
        ) : (
          <div className="overflow-x-auto -mx-6 px-6">
            <table className="w-full text-left border-collapse min-w-[900px]">
              <thead>
                <tr className="border-b border-slate-100 text-xs font-bold text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-4">Lead #</th>
                  <th className="py-3 px-4">Student Name</th>
                  <th className="py-3 px-4">Contact</th>
                  <th className="py-3 px-4">Visa / Country</th>
                  <th className="py-3 px-4">Source</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Assigned To</th>
                  <th className="py-3 px-4">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50 text-sm">
                {leads.map((lead) => (
                  <tr key={lead.id} className="group hover:bg-slate-50/50 transition-colors">
                    <td className="py-3 px-4">
                      <span className="text-xs font-mono font-bold text-slate-500 bg-slate-100 px-2 py-1 rounded">{lead.lead_number}</span>
                    </td>
                    <td className="py-3 px-4">
                      <p className="font-bold text-slate-800">{lead.full_name}</p>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-col text-[11px]">
                        {lead.email && <span className="text-slate-600 flex items-center gap-1"><Mail size={10} /> {lead.email}</span>}
                        {lead.phone && <span className="text-slate-500 flex items-center gap-1"><Phone size={10} /> {lead.phone}</span>}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <p className="text-xs text-slate-700 capitalize">{lead.visa_type}</p>
                      {lead.preferred_country && <p className="text-[10px] text-slate-400">{lead.preferred_country}</p>}
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-[10px] font-bold text-slate-500 bg-slate-50 px-2 py-0.5 rounded">{lead.source}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold uppercase ${STATUS_COLORS[lead.status] || 'text-slate-600 bg-slate-50'}`}>
                        {lead.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs">
                      {isAdmin ? (
                        <div className="relative">
                          {assigningLead === lead.id ? (
                            <div className="flex flex-col gap-1.5 min-w-[200px]">
                              <div className="relative">
                                <Search size={12} className="absolute left-2 top-2 text-slate-400" />
                                <input
                                  type="text"
                                  value={assignSearch}
                                  onChange={(e) => setAssignSearch(e.target.value)}
                                  placeholder="Search employee..."
                                  className="w-full pl-7 pr-2 py-1.5 border border-slate-200 rounded-lg text-[10px] outline-none focus:border-brand-blue"
                                  autoFocus
                                />
                              </div>
                              <div className="max-h-32 overflow-y-auto border border-slate-100 rounded-lg bg-white shadow-sm">
                                <button
                                  onClick={() => { setAssigningLead(null); setAssignSearch(''); }}
                                  className="w-full text-left px-2.5 py-2 text-[10px] text-slate-400 hover:bg-slate-50 flex items-center gap-2"
                                >
                                  <X size={10} /> Unassign
                                </button>
                                {filteredEmployees.length === 0 ? (
                                  <p className="px-2.5 py-2 text-[10px] text-slate-400">No employees found</p>
                                ) : filteredEmployees.map(emp => (
                                  <button
                                    key={emp.id}
                                    onClick={() => handleDirectAssign(lead.id, emp.id)}
                                    disabled={assignLoading[lead.id]}
                                    className="w-full text-left px-2.5 py-2 text-[10px] hover:bg-brand-blue/5 transition-colors disabled:opacity-50 flex items-center gap-2"
                                  >
                                    <div className="w-6 h-6 rounded-full bg-brand-blue/10 flex items-center justify-center text-brand-blue font-bold text-[8px] shrink-0">
                                      {emp.full_name?.substring(0, 2).toUpperCase() || 'EM'}
                                    </div>
                                    <div className="truncate">
                                      <p className="font-semibold text-slate-700 truncate">{emp.full_name}</p>
                                      <p className="text-[8px] text-slate-400 truncate">{emp.email}</p>
                                    </div>
                                    {lead.assigned_employee_id === emp.id && <Check size={10} className="text-emerald-500 shrink-0" />}
                                  </button>
                                ))}
                              </div>
                              {assignLoading[lead.id] && <div className="w-4 h-4 border-2 border-brand-orange border-t-transparent rounded-full animate-spin mx-auto" />}
                            </div>
                          ) : (
                            <div className="flex items-center gap-2">
                              {lead.assigned_employee_name ? (
                                <>
                                  <span className="text-xs text-slate-700 font-semibold">{lead.assigned_employee_name}</span>
                                  <span className="text-[8px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-600">Assigned</span>
                                  <button
                                    onClick={() => { setAssigningLead(lead.id); setAssignSearch(''); }}
                                    className="text-[9px] text-brand-blue hover:text-brand-orange font-bold transition-colors"
                                  >
                                    Change
                                  </button>
                                </>
                              ) : (
                                <button
                                  onClick={() => { setAssigningLead(lead.id); setAssignSearch(''); }}
                                  className="flex items-center gap-1 px-2 py-1 rounded-lg border border-dashed border-slate-300 text-[10px] text-slate-500 font-semibold hover:border-brand-blue hover:text-brand-blue transition-all"
                                >
                                  <Plus size={10} /> Assign
                                </button>
                              )}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5">
                          {lead.assigned_employee_id === user?.id ? (
                            <span className="text-[10px] font-bold px-2 py-1 rounded bg-emerald-50 text-emerald-600">Assigned to you</span>
                          ) : lead.assigned_employee_name ? (
                            <span className="text-xs text-slate-600">{lead.assigned_employee_name}</span>
                          ) : pendingRequests[lead.id] ? (
                            <div className="flex items-center gap-1.5">
                              <span className="text-[10px] font-bold px-2 py-1 rounded bg-amber-50 text-amber-600">Pending Approval</span>
                              <button
                                onClick={() => handleCancelRequest(pendingRequests[lead.id].id, lead.id)}
                                disabled={requestLoading[lead.id]}
                                className="text-[9px] text-red-500 hover:text-red-700 font-bold transition-colors"
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => handleRequestAssignment(lead.id)}
                              disabled={requestLoading[lead.id]}
                              className="flex items-center gap-1 px-2 py-1 rounded-lg border border-dashed border-slate-300 text-[10px] text-slate-500 font-semibold hover:border-brand-orange hover:text-brand-orange transition-all disabled:opacity-50"
                            >
                              {requestLoading[lead.id] ? (
                                <span className="w-3 h-3 border-2 border-brand-orange border-t-transparent rounded-full animate-spin" />
                              ) : null}
                              Request Assignment
                            </button>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4 text-[10px] text-slate-400">{new Date(lead.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex justify-center gap-2 mt-6">
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
              className="px-3 py-1.5 rounded-lg border text-xs font-bold disabled:opacity-30 hover:bg-slate-50">Previous</button>
            <span className="px-3 py-1.5 text-xs text-slate-500">Page {page} of {totalPages}</span>
            <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}
              className="px-3 py-1.5 rounded-lg border text-xs font-bold disabled:opacity-30 hover:bg-slate-50">Next</button>
          </div>
        )}
      </Card>
    </div>
  );
};

export default LeadInquiriesPage;
