import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { 
  Plus, 
  ArrowLeft, 
  Edit2, 
  Trash2, 
  Mail, 
  Phone, 
  Globe, 
  User, 
  Calendar,
  Clock,
  FileText,
  MessageSquare,
  FileDown,
  UploadCloud,
  Send
} from 'lucide-react';

import api from '../../config/api';
import applicantService from '../../services/applicantService';
import { useAuth } from '../../hooks/useAuth';
import useDocumentTitle from '../../hooks/useDocumentTitle';

// UI Components
import Card from '../../components/Card';
import Button from '../../components/Button';
import PageHeader from '../../components/PageHeader';
import LoadingSpinner from '../../components/LoadingSpinner';
import EmptyState from '../../components/EmptyState';
import SearchBar from '../../components/SearchBar';
import FilterPanel from '../../components/FilterPanel';
import StatusBadge from '../../components/StatusBadge';
import StatusTimeline from '../../components/StatusTimeline';
import ApplicantTable from '../../components/ApplicantTable';
import ApplicantForm from '../../components/ApplicantForm';
import DocumentUploader from '../../components/DocumentUploader';
import DocumentGrid from '../../components/DocumentGrid';
import documentService from '../../services/documentService';
import progressService from '../../services/progressService';
import ProgressSummaryCard from '../../components/ProgressSummaryCard';
import ProgressTimeline from '../../components/ProgressTimeline';
import ProgressHistory from '../../components/ProgressHistory';
import StatusUpdateModal from '../../components/StatusUpdateModal';
import ChatWindow from '../../components/ChatWindow';
import { appConfig } from '../../config/appConfig';

export const ApplicantsPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();

  // Route Params
  const view = searchParams.get('view') || 'list'; // 'list', 'add', 'edit', 'details'
  const applicantId = searchParams.get('id');
  const visaTypeQuery = searchParams.get('visa_type');

  useDocumentTitle(
    view === 'add' 
      ? 'Add Applicant' 
      : view === 'edit' 
      ? 'Edit Applicant' 
      : view === 'details' 
      ? 'Applicant Details' 
      : 'Applicants Queue'
  );

  // States
  const [applicants, setApplicants] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(appConfig.DEFAULT_PAGE_SIZE);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Active applicant for Detail or Edit view
  const [selectedApplicant, setSelectedApplicant] = useState(null);

  // Filter States
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({
    visaType: visaTypeQuery || '',
    status: '',
    country: '',
    assignedEmployee: ''
  });

  // Mock states for detail view (interactive documents and messages)
  const [mockDocs, setMockDocs] = useState([
    { id: 1, name: 'Passport_Copy.pdf', type: 'application/pdf', size: '2.4 MB', date: '2 days ago', status: 'Approved' },
    { id: 2, name: 'IELTS_Report_Card.pdf', type: 'application/pdf', size: '1.1 MB', date: '2 days ago', status: 'Under Review' },
    { id: 3, name: 'Letter_of_Acceptance.pdf', type: 'application/pdf', size: '3.8 MB', date: 'Yesterday', status: 'Approved' }
  ]);
  const [mockMessages, setMockMessages] = useState([
    { id: 1, sender: 'System', text: 'Applicant created and pipeline initiated.', time: '2 days ago', isSystem: true },
    { id: 2, sender: 'Counselor Team', text: 'Checked passport details, valid for next 2 years.', time: 'Yesterday', isSystem: false },
    { id: 3, sender: 'Advisor', text: 'Sent email requesting additional financial proof documentation.', time: '5 hours ago', isSystem: false }
  ]);
  const [newMessageText, setNewMessageText] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [applicantDocs, setApplicantDocs] = useState([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [timeline, setTimeline] = useState([]);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('status');

  const loadApplicantDocs = async () => {
    if (!applicantId) return;
    try {
      setDocsLoading(true);
      const data = await documentService.list(applicantId);
      setApplicantDocs(data);
    } catch (err) {
      console.error("Failed to load applicant documents", err);
    } finally {
      setDocsLoading(false);
    }
  };

  // Fetch employees lookup
  useEffect(() => {
    const fetchEmployees = async () => {
      try {
        const res = await api.get('/employees');
        if (res.data && res.data.success) {
          setEmployees(res.data.data);
        }
      } catch (err) {
        console.error('Failed to load employee list', err);
      }
    };
    fetchEmployees();
  }, []);

  // Sync visa_type from URL sidebar tabs into filter state
  useEffect(() => {
    setFilters(prev => ({
      ...prev,
      visaType: visaTypeQuery || ''
    }));
    setPage(1);
  }, [visaTypeQuery]);

  // Load applicants list
  const loadApplicants = async () => {
    if (view !== 'list') return;
    try {
      setIsLoading(true);
      const data = await applicantService.list({
        page,
        page_size: pageSize,
        search: search || undefined,
        visa_type: filters.visaType || undefined,
        status: filters.status || undefined,
        country: filters.country || undefined,
        assigned_to: filters.assignedEmployee || undefined
      });
      setApplicants(data.applicants);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      toast.error('Failed to retrieve applicant queue.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadApplicants();
  }, [view, page, pageSize, search, filters]);

  const loadSingleApplicant = async () => {
    if ((view === 'edit' || view === 'details') && applicantId) {
      try {
        setIsLoading(true);
        const data = await applicantService.get(applicantId);
        setSelectedApplicant(data);
      } catch (err) {
        toast.error('Failed to load applicant file.');
        navigate('/applicants');
      } finally {
        setIsLoading(false);
      }
    }
  };

  // Load single applicant for edit/details
  useEffect(() => {
    loadSingleApplicant();
  }, [view, applicantId]);

  const loadApplicantTimeline = async () => {
    if (!applicantId) return;
    try {
      setTimelineLoading(true);
      const data = await progressService.getTimeline(applicantId);
      setTimeline(data);
    } catch (err) {
      console.error("Failed to load applicant timeline", err);
    } finally {
      setTimelineLoading(false);
    }
  };

  useEffect(() => {
    if (view === 'details' && applicantId && activeTab === 'progress') {
      loadApplicantTimeline();
    }
  }, [view, applicantId, activeTab]);

  const handleSaveSuccess = async () => {
    await loadSingleApplicant();
    await loadApplicantTimeline();
  };

  // Load documents when details view documents tab is active
  useEffect(() => {
    if (view === 'details' && applicantId && activeTab === 'documents') {
      loadApplicantDocs();
    }
  }, [view, applicantId, activeTab]);

  // Action Handlers
  const handleCreate = async (payload) => {
    try {
      setIsSubmitting(true);
      await applicantService.create(payload);
      toast.success('Applicant record registered successfully!');
      navigate('/applicants');
    } catch (err) {
      const msg = err.message || 'Failed to create applicant.';
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdate = async (payload) => {
    try {
      setIsSubmitting(true);
      await applicantService.update(applicantId, payload);
      toast.success('Applicant record updated successfully!');
      
      // Redirect back to details or list depending on user journey
      navigate(`/applicants?view=details&id=${applicantId}`);
    } catch (err) {
      const msg = err.message || 'Failed to update applicant.';
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete applicant "${name}"? This will archive their file record in the database.`)) {
      return;
    }
    try {
      await applicantService.delete(id);
      toast.success(`Applicant "${name}" deleted successfully.`);
      if (view === 'details') {
        navigate('/applicants');
      } else {
        loadApplicants();
      }
    } catch (err) {
      toast.error(err.message || 'Failed to delete applicant.');
    }
  };

  const resetFilters = () => {
    setFilters({
      visaType: '',
      status: '',
      country: '',
      assignedEmployee: ''
    });
    setSearch('');
    setPage(1);
    // Clear sidebar query param selection
    if (location.search.includes('visa_type')) {
      navigate('/applicants');
    }
  };

  // Mock message send handler
  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!newMessageText.trim()) return;
    const msg = {
      id: Date.now(),
      sender: user?.name || 'Counselor',
      text: newMessageText,
      time: 'Just now',
      isSystem: false
    };
    setMockMessages(prev => [...prev, msg]);
    setNewMessageText('');
    toast.success('Message posted to advisor notes thread.');
  };

  // Mock document upload handler
  const handleMockUpload = () => {
    const fileName = prompt('Enter mock file name to upload:', 'Financial_Statement.pdf');
    if (!fileName) return;
    const newDoc = {
      id: Date.now(),
      name: fileName,
      type: 'application/pdf',
      size: '1.8 MB',
      date: 'Just now',
      status: 'Under Review'
    };
    setMockDocs(prev => [...prev, newDoc]);
    toast.success(`File "${fileName}" uploaded successfully.`);
  };

  // Helpers
  const getAdvisorName = (id) => {
    const emp = employees.find(e => e.id === Number(id));
    return emp ? emp.name : 'Unassigned';
  };

  const formatKeyName = (key) => {
    return key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
  };

  // ── RENDER SUB-VIEWS ─────────────────────────────

  // Add / Edit View
  if (view === 'add' || view === 'edit') {
    return (
      <div className="space-y-6 text-left">
        <PageHeader
          title={view === 'add' ? 'Add New Applicant' : 'Edit Applicant Record'}
          subtitle={view === 'add' ? 'Fill details to submit a new client file' : `Updating files for applicant ID: #${applicantId}`}
          breadcrumbs={[
            { label: 'Home', path: '/dashboard' },
            { label: 'Applicants', path: '/applicants' },
            { label: view === 'add' ? 'Add File' : 'Modify File' }
          ]}
        />
        <Card>
          {view === 'edit' && isLoading ? (
            <div className="py-12 flex justify-center">
              <LoadingSpinner label="Retrieving record detail..." />
            </div>
          ) : (
            <ApplicantForm
              initialData={view === 'edit' ? selectedApplicant : null}
              employees={employees}
              onSubmit={view === 'add' ? handleCreate : handleUpdate}
              onCancel={() => navigate(view === 'edit' ? `/applicants?view=details&id=${applicantId}` : '/applicants')}
              isLoading={isSubmitting}
              forcedVisaType={view === 'add' ? visaTypeQuery : null}
            />
          )}
        </Card>
      </div>
    );
  }

  // Details View
  if (view === 'details') {
    return (
      <div className="space-y-6 text-left animate-fade-in">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 pb-5">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate(-1)}
              className="p-2 border border-slate-200 rounded-xl bg-white hover:bg-slate-50 transition-colors text-slate-500"
              title="Go Back"
            >
              <ArrowLeft size={16} />
            </button>
            <div>
              <h2 className="text-xl font-extrabold text-slate-800 font-display flex items-center gap-2.5">
                {selectedApplicant?.full_name || 'Applicant Detail File'}
                {selectedApplicant?.applicant_code && (
                  <span className="text-xs font-mono font-bold bg-slate-100 border border-slate-200 text-slate-700 px-2.5 py-1 rounded-lg shrink-0">
                    {selectedApplicant.applicant_code}
                  </span>
                )}
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Consolidated File ID: #{selectedApplicant?.id}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => navigate(`/applicants?view=edit&id=${applicantId}`)}
              variant="outline"
              size="sm"
              className="flex items-center gap-1.5"
            >
              <Edit2 size={14} />
              Edit File
            </Button>
            <Button
              onClick={() => handleDelete(selectedApplicant.id, selectedApplicant.full_name)}
              variant="danger"
              size="sm"
              className="flex items-center gap-1.5"
            >
              <Trash2 size={14} />
              Delete File
            </Button>
          </div>
        </div>

        {isLoading ? (
          <div className="py-24 flex justify-center">
            <LoadingSpinner label="Loading file records..." />
          </div>
        ) : !selectedApplicant ? (
          <EmptyState description="Applicant file not found." />
        ) : (
          <div className="space-y-6">
            {/* Tabs Navigation */}
            <div className="flex border-b border-slate-200 gap-6 overflow-x-auto pb-px">
              {[
                { id: 'overview', label: 'Overview' },
                { id: 'documents', label: 'Documents' },
                { id: 'progress', label: 'Progress' },
                { id: 'chat', label: 'Internal Chat' },
                { id: 'activity', label: 'Activity History' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`pb-3 text-sm font-bold border-b-2 transition-all focus:outline-none whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-brand-orange text-brand-blue'
                      : 'border-transparent text-slate-400 hover:text-slate-600'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Contents */}
            {activeTab === 'overview' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Core Personal Details & Notes */}
                <div className="lg:col-span-2 space-y-6">
                  <Card title="Personal & Contact Details">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-sm">
                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-400">
                          <User size={16} />
                        </div>
                        <div>
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Full Name</p>
                          <p className="font-bold text-slate-700 mt-0.5">{selectedApplicant.full_name}</p>
                        </div>
                      </div>

                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-400">
                          <Mail size={16} />
                        </div>
                        <div>
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Email Address</p>
                          <p className="font-bold text-slate-700 mt-0.5 break-all">{selectedApplicant.email || 'None'}</p>
                        </div>
                      </div>

                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-400">
                          <Phone size={16} />
                        </div>
                        <div>
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Phone Number</p>
                          <p className="font-bold text-slate-700 mt-0.5">{selectedApplicant.phone || 'None'}</p>
                        </div>
                      </div>

                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-400">
                          <Globe size={16} />
                        </div>
                        <div>
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Destination Country</p>
                          <p className="font-bold text-slate-700 mt-0.5">{selectedApplicant.country || '--'}</p>
                        </div>
                      </div>

                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-400">
                          <Calendar size={16} />
                        </div>
                        <div>
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Assigned Counselor</p>
                          <p className="font-bold text-slate-700 mt-0.5">{getAdvisorName(selectedApplicant.assigned_to)}</p>
                        </div>
                      </div>

                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-400">
                          <Clock size={16} />
                        </div>
                        <div>
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Created On</p>
                          <p className="font-bold text-slate-700 mt-0.5">
                            {new Date(selectedApplicant.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-400">
                          <User size={16} />
                        </div>
                        <div>
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Created By</p>
                          <p className="font-bold text-slate-700 mt-0.5">
                            {selectedApplicant.created_by_name || 'System'}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-400">
                          <User size={16} />
                        </div>
                        <div>
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Applicant Code</p>
                          <p className="font-bold text-slate-700 mt-0.5 font-mono">
                            {selectedApplicant.applicant_code || 'N/A'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </Card>

                  <Card title="Advisor Notes" subtitle="Internal dossier remarks">
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-sm text-slate-600 leading-relaxed font-medium">
                      {selectedApplicant.notes || 'No counselor notes submitted for this file.'}
                    </div>
                  </Card>
                </div>

                {/* Visa Specific details */}
                <div>
                  <Card title="Visa Profile Data">
                    <div className="space-y-3.5">
                      <div className="flex justify-between items-center border-b border-slate-50 pb-2">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Visa Type</span>
                        <span className="text-xs font-bold text-brand-orange uppercase">{selectedApplicant.visa_type}</span>
                      </div>

                      {selectedApplicant.metadata && Object.keys(selectedApplicant.metadata).length > 0 ? (
                        Object.entries(selectedApplicant.metadata).map(([key, val]) => (
                          <div key={key} className="flex justify-between items-center py-1.5 border-b border-slate-50">
                            <span className="text-xs font-semibold text-slate-500">{formatKeyName(key)}</span>
                            <span className="text-xs font-bold text-slate-800">{val}</span>
                          </div>
                        ))
                      ) : (
                        <div className="py-2 text-center text-xs text-slate-400 italic">
                          No additional visa metadata registered.
                        </div>
                      )}
                    </div>
                  </Card>
                </div>
              </div>
            )}

            {activeTab === 'documents' && (
              <div className="space-y-6">
                <DocumentUploader 
                  applicantId={selectedApplicant.id} 
                  onUploadSuccess={loadApplicantDocs} 
                />

                {docsLoading ? (
                  <div className="py-12 flex justify-center">
                    <LoadingSpinner label="Refreshing documents folder..." />
                  </div>
                ) : (
                  <DocumentGrid 
                    documents={applicantDocs} 
                    employees={employees} 
                    onDeleteSuccess={loadApplicantDocs}
                  />
                )}
              </div>
            )}

            {activeTab === 'progress' && (
              <div className="space-y-6">
                <ProgressSummaryCard 
                  applicant={selectedApplicant} 
                  latestHistory={timeline[timeline.length - 1]} 
                />
                
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-1">
                    <ProgressTimeline currentStatus={selectedApplicant.status} />
                  </div>
                  <div className="lg:col-span-2">
                    {timelineLoading ? (
                      <div className="py-12 flex justify-center bg-white border border-slate-100 rounded-2xl shadow-sm">
                        <LoadingSpinner label="Loading progress history..." />
                      </div>
                    ) : (
                      <ProgressHistory
                        timeline={timeline}
                        onOpenUpdateModal={() => {
                          setModalMode('status');
                          setIsUpdateModalOpen(true);
                        }}
                        onOpenNoteModal={() => {
                          setModalMode('note');
                          setIsUpdateModalOpen(true);
                        }}
                      />
                    )}
                  </div>
                </div>

                <StatusUpdateModal
                  isOpen={isUpdateModalOpen}
                  onClose={() => setIsUpdateModalOpen(false)}
                  applicant={selectedApplicant}
                  mode={modalMode}
                  onSaveSuccess={handleSaveSuccess}
                />
              </div>
            )}

            {activeTab === 'chat' && (
              <div className="max-w-3xl">
                <ChatWindow 
                  applicantId={selectedApplicant.id} 
                  currentUser={user} 
                />
              </div>
            )}

            {activeTab === 'activity' && (
              <div className="max-w-3xl">
                <Card title="Activity History" subtitle="System audit trail of modifications on this file">
                  <div className="relative border-l-2 border-slate-100 pl-6 ml-3 space-y-6 text-left py-2">
                    <div className="relative">
                      <div className="absolute -left-[31px] top-1.5 w-2 h-2 rounded-full bg-brand-orange ring-4 ring-orange-50"></div>
                      <p className="text-xs font-bold text-slate-700">Counselor Assigned</p>
                      <p className="text-[10px] text-slate-400 font-medium mt-0.5">Yesterday &bull; by System</p>
                      <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                        File status set to Documents Pending and counselor assigned to employee.
                      </p>
                    </div>
                    <div className="relative">
                      <div className="absolute -left-[31px] top-1.5 w-2 h-2 rounded-full bg-emerald-500 ring-4 ring-emerald-50"></div>
                      <p className="text-xs font-bold text-slate-700">Applicant Registered</p>
                      <p className="text-[10px] text-slate-400 font-medium mt-0.5">2 days ago &bull; by {selectedApplicant.created_by_name || 'System'}</p>
                      <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                        Applicant profile created under code <span className="font-mono font-bold text-slate-600">{selectedApplicant.applicant_code}</span>.
                      </p>
                    </div>
                  </div>
                </Card>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // List View (Default)
  const showFiltersBadgeCount = Object.values(filters).filter(Boolean).length;

  return (
    <div className="space-y-6 text-left">
      <PageHeader
        title={visaTypeQuery ? `${visaTypeQuery.charAt(0).toUpperCase() + visaTypeQuery.slice(1)} Visa Queue` : 'Applicant Pipeline'}
        subtitle={visaTypeQuery ? `Consolidated logs for all active ${visaTypeQuery} visa cases` : 'Browse, track, and manage all active applicant visa folders'}
        breadcrumbs={[
          { label: 'Home', path: '/dashboard' },
          { label: visaTypeQuery ? `${visaTypeQuery.charAt(0).toUpperCase() + visaTypeQuery.slice(1)} Applicants` : 'Applicants' }
        ]}
        action={
          <Button
            onClick={() => navigate(`/applicants?view=add${visaTypeQuery ? `&visa_type=${visaTypeQuery}` : ''}`)}
            variant="secondary"
            className="flex items-center gap-2"
          >
            <Plus size={16} />
            Register Applicant
          </Button>
        }
      />

      {/* Search & Filter Container */}
      <div className="space-y-4">
        <SearchBar 
          value={search} 
          onChange={setSearch} 
          placeholder="Search applicants by name, email, phone, or applicant code..." 
        />
        
        <FilterPanel 
          filters={filters} 
          onChange={setFilters} 
          onReset={resetFilters} 
          employees={employees}
          hideVisaType={!!visaTypeQuery}
        />
      </div>

      {/* Main Table Card */}
      <Card>
        {isLoading ? (
          <div className="py-24 flex justify-center">
            <LoadingSpinner label="Loading applicant files..." />
          </div>
        ) : applicants.length === 0 ? (
          <EmptyState 
            title={showFiltersBadgeCount || search ? 'No Matching Records' : 'Dossier Queue Empty'}
            description={showFiltersBadgeCount || search 
              ? 'Try widening your filters or correcting the query parameter spelling.' 
              : 'Add an applicant to trigger active visa workflows.'
            } 
            actionButton={
              (showFiltersBadgeCount || search) && (
                <Button onClick={resetFilters} variant="outline" size="sm">
                  Clear Filters
                </Button>
              )
            }
          />
        ) : (
          <ApplicantTable
            applicants={applicants}
            employees={employees}
            onView={(id) => navigate(`/applicants?view=details&id=${id}`)}
            onEdit={(id) => navigate(`/applicants?view=edit&id=${id}`)}
            onDelete={handleDelete}
            pagination={{
              page,
              pageSize,
              totalPages,
              total
            }}
            onPageChange={setPage}
          />
        )}
      </Card>
    </div>
  );
};

export default ApplicantsPage;
