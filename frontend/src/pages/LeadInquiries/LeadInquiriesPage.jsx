import React, { useState, useEffect } from 'react';
import { Plus, Search, RefreshCw, Phone, Mail, Globe } from 'lucide-react';
import toast from 'react-hot-toast';
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
  const [leads, setLeads] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

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
                    <td className="py-3 px-4 text-xs text-slate-600">{lead.assigned_employee_name || '—'}</td>
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
