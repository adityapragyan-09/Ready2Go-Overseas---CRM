import React, { useState, useEffect, useCallback } from 'react';
import { Search, RefreshCw, CheckCircle, XCircle, Clock, Eye, X, UserCheck } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../../config/api';
import { useAuth } from '../../hooks/useAuth';
import Card from '../../components/Card';
import PageHeader from '../../components/PageHeader';
import LoadingSpinner from '../../components/LoadingSpinner';
import EmptyState from '../../components/EmptyState';
import ConfirmationModal from '../../components/ConfirmationModal';

const STATUS_STYLES = {
  PENDING: 'text-amber-600 bg-amber-50 border-amber-200',
  APPROVED: 'text-emerald-600 bg-emerald-50 border-emerald-200',
  REJECTED: 'text-red-600 bg-red-50 border-red-200',
  CANCELLED: 'text-slate-500 bg-slate-50 border-slate-200',
};

const RejectReasons = ['Already assigned', 'Capacity exceeded', 'Duplicate request', 'Other'];

export const AssignmentRequestsPage = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [requests, setRequests] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Detail drawer
  const [selectedReq, setSelectedReq] = useState(null);

  // Confirm modals
  const [approveTarget, setApproveTarget] = useState(null);
  const [rejectTarget, setRejectTarget] = useState(null);
  const [rejectReason, setRejectReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Stats
  const [stats, setStats] = useState({ pending: 0, approvedToday: 0, rejectedToday: 0 });

  const fetchRequests = useCallback(async () => {
    try {
      setIsLoading(true);
      const res = await api.get('/assignment-requests', {
        params: { status: statusFilter || undefined, page, page_size: pageSize, q: search || undefined },
      });
      if (res.data?.success) {
        setRequests(res.data.data.items || []);
        setTotal(res.data.data.total || 0);
        const all = res.data.data.items || [];
        setStats({
          pending: all.filter(r => r.status === 'PENDING').length,
          approvedToday: all.filter(r => r.status === 'APPROVED').length,
          rejectedToday: all.filter(r => r.status === 'REJECTED').length,
        });
      }
    } catch {
      toast.error('Failed to load requests.');
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter, page, pageSize, search]);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  const handleApprove = async () => {
    if (!approveTarget) return;
    setActionLoading(true);
    try {
      const res = await api.patch(`/assignment-requests/${approveTarget.id}/approve`);
      if (res.data?.success) {
        toast.success('Assignment approved.');
        setApproveTarget(null);
        fetchRequests();
      }
    } catch (err) {
      toast.error(err.response?.data?.message || 'Approval failed.');
      setApproveTarget(null);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!rejectTarget) return;
    setActionLoading(true);
    try {
      const res = await api.patch(`/assignment-requests/${rejectTarget.id}/reject`, { remarks: rejectReason });
      if (res.data?.success) {
        toast.success('Request rejected.');
        setRejectTarget(null);
        setRejectReason('');
        fetchRequests();
      }
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to reject.');
      setRejectTarget(null);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchRequests();
  };

  return (
    <div className="space-y-6 text-left animate-fade-in">
      <PageHeader
        title="Assignment Requests"
        subtitle="Manage employee requests for lead ownership"
        breadcrumbs={[{ label: 'Home', path: '/dashboard' }, { label: 'Assignment Requests' }]}
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-100 text-center">
          <p className="text-[10px] font-bold text-amber-600 uppercase tracking-wider">Pending</p>
          <p className="text-2xl font-extrabold text-amber-700 mt-1">{stats.pending}</p>
        </div>
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-100 text-center">
          <p className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider">Approved Today</p>
          <p className="text-2xl font-extrabold text-emerald-700 mt-1">{stats.approvedToday}</p>
        </div>
        <div className="p-4 rounded-2xl bg-red-50 border border-red-100 text-center">
          <p className="text-[10px] font-bold text-red-600 uppercase tracking-wider">Rejected Today</p>
          <p className="text-2xl font-extrabold text-red-700 mt-1">{stats.rejectedToday}</p>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-col md:flex-row gap-3 mb-6">
          <form onSubmit={handleSearch} className="flex-1 flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by lead number, name, email..."
                className="w-full pl-10 pr-4 py-2 border border-slate-200 bg-white rounded-xl text-xs font-semibold focus:border-brand-blue outline-none" />
            </div>
            <button type="submit" className="px-4 py-2 rounded-xl bg-brand-blue text-white text-xs font-bold hover:bg-brand-blue/90"><Search size={14} /></button>
          </form>
          <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded-xl border border-slate-200 bg-white text-xs font-semibold outline-none">
            <option value="">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
          <button onClick={fetchRequests} className="px-3 py-2 rounded-xl border border-slate-200 hover:bg-slate-50">
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>

        {isLoading ? (
          <div className="py-24 flex justify-center"><LoadingSpinner label="Loading requests..." /></div>
        ) : requests.length === 0 ? (
          <EmptyState title="No Requests" description="Employee assignment requests will appear here." />
        ) : (
          <div className="overflow-x-auto -mx-6 px-6">
            <table className="w-full text-left border-collapse min-w-[900px]">
              <thead>
                <tr className="border-b border-slate-100 text-xs font-bold text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-4">Lead</th>
                  <th className="py-3 px-4">Employee</th>
                  <th className="py-3 px-4">Requested At</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50 text-sm">
                {requests.map((req) => (
                  <tr key={req.id} className="group hover:bg-slate-50/50 transition-colors">
                    <td className="py-3 px-4">
                      <p className="font-bold text-slate-800">{req.lead_name || `Lead #${req.lead_id}`}</p>
                      <p className="text-[10px] text-slate-400 font-mono">{req.lead_number || ''}</p>
                    </td>
                    <td className="py-3 px-4">
                      <p className="font-semibold text-slate-700">{req.employee_name || 'Unknown'}</p>
                      <p className="text-[10px] text-slate-400">{req.employee_email || ''}</p>
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-500">{new Date(req.requested_at).toLocaleString()}</td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${STATUS_STYLES[req.status] || 'text-slate-600 bg-slate-50'}`}>
                        {req.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button onClick={() => setSelectedReq(req)} className="px-2.5 py-1.5 text-[10px] font-bold rounded-lg border border-blue-200 text-blue-600 bg-blue-50 hover:bg-blue-100 transition-all">
                          <Eye size={12} /> View
                        </button>
                        {req.status === 'PENDING' && (
                          <>
                            <button onClick={() => setApproveTarget(req)}
                              className="px-2.5 py-1.5 text-[10px] font-bold rounded-lg bg-emerald-500 text-white hover:bg-emerald-600 transition-all">
                              <CheckCircle size={12} /> Approve
                            </button>
                            <button onClick={() => { setRejectTarget(req); setRejectReason(''); }}
                              className="px-2.5 py-1.5 text-[10px] font-bold rounded-lg bg-red-500 text-white hover:bg-red-600 transition-all">
                              <XCircle size={12} /> Reject
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {total > pageSize && (
          <div className="flex justify-center gap-2 mt-6">
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
              className="px-3 py-1.5 rounded-lg border text-xs font-bold disabled:opacity-30 hover:bg-slate-50">Previous</button>
            <span className="px-3 py-1.5 text-xs text-slate-500">Page {page} of {Math.ceil(total / pageSize)}</span>
            <button disabled={page >= Math.ceil(total / pageSize)} onClick={() => setPage(p => p + 1)}
              className="px-3 py-1.5 rounded-lg border text-xs font-bold disabled:opacity-30 hover:bg-slate-50">Next</button>
          </div>
        )}
      </Card>

      {/* Approve Confirmation */}
      <ConfirmationModal
        visible={!!approveTarget}
        title="Approve Assignment?"
        message={approveTarget ? `Assign lead "${approveTarget.lead_name || '#' + approveTarget.lead_id}" to ${approveTarget.employee_name}?` : ''}
        warning="This will transfer ownership immediately."
        confirmText="Approve"
        confirmVariant="primary"
        loading={actionLoading}
        onConfirm={handleApprove}
        onCancel={() => setApproveTarget(null)}
      />

      {/* Reject Modal */}
      {rejectTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div onClick={() => setRejectTarget(null)} className="absolute inset-0 bg-black/40 backdrop-blur-sm"></div>
          <div className="relative bg-white rounded-2xl shadow-2xl p-6 max-w-md w-full mx-4 text-left z-10">
            <h3 className="text-sm font-bold text-slate-800">Reject Assignment</h3>
            <p className="text-xs text-slate-500 mt-2 mb-4">Reject request from {rejectTarget.employee_name} for lead {rejectTarget.lead_name || '#' + rejectTarget.lead_id}.</p>
            <label className="text-xs font-bold text-slate-600 block mb-1">Reason</label>
            <select value={rejectReason} onChange={(e) => setRejectReason(e.target.value)}
              className="w-full px-3 py-2.5 border border-slate-200 rounded-xl text-xs font-semibold outline-none focus:border-brand-orange mb-4">
              <option value="">Select a reason...</option>
              {RejectReasons.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
            <div className="flex gap-3">
              <button onClick={() => setRejectTarget(null)} className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50">Cancel</button>
              <button onClick={handleReject} disabled={!rejectReason || actionLoading}
                className="flex-1 px-4 py-2.5 rounded-xl bg-red-500 text-white text-xs font-bold hover:bg-red-600 disabled:opacity-50">
                {actionLoading ? 'Processing...' : 'Reject'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Detail Drawer */}
      {selectedReq && (
        <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
          <div onClick={() => setSelectedReq(null)} className="absolute inset-0 bg-black/40 backdrop-blur-sm"></div>
          <div className="relative w-full max-w-md bg-white h-full shadow-2xl p-6 overflow-y-auto text-left z-10">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Request Details</h3>
                <h2 className="text-lg font-black text-slate-800 mt-1">#{selectedReq.id}</h2>
              </div>
              <button onClick={() => setSelectedReq(null)} className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-50"><X size={18} /></button>
            </div>
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-50 space-y-2">
                <p className="text-xs font-bold text-slate-400 uppercase">Lead</p>
                <p className="text-sm font-bold text-slate-800">{selectedReq.lead_name || `Lead #${selectedReq.lead_id}`}</p>
                <p className="text-xs text-slate-500">{selectedReq.lead_number || ''}</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 space-y-2">
                <p className="text-xs font-bold text-slate-400 uppercase">Employee</p>
                <p className="text-sm font-bold text-slate-800">{selectedReq.employee_name || 'Unknown'}</p>
                <p className="text-xs text-slate-500">{selectedReq.employee_email || ''}</p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-slate-50">
                  <p className="font-bold text-slate-400 uppercase">Status</p>
                  <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold uppercase mt-1 border ${STATUS_STYLES[selectedReq.status] || 'text-slate-600 bg-slate-50'}`}>
                    {selectedReq.status}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50">
                  <p className="font-bold text-slate-400 uppercase">Requested</p>
                  <p className="font-semibold text-slate-700 mt-1">{new Date(selectedReq.requested_at).toLocaleString()}</p>
                </div>
              </div>
              {selectedReq.remarks && (
                <div className="p-3 rounded-xl bg-slate-50">
                  <p className="text-[10px] font-bold text-slate-400 uppercase">Remarks</p>
                  <p className="text-xs text-slate-600 mt-1">{selectedReq.remarks}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssignmentRequestsPage;
