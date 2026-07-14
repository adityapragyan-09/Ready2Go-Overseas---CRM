import React, { useState } from 'react';
import { 
  Search, Eye, FileDown, Trash2, FileText, Globe, Image, GraduationCap, 
  Sparkles, Landmark, ShieldCheck, Briefcase, Compass, HelpCircle, 
  X, Calendar, ArrowUpDown, ChevronDown, UserCheck, Trash, MailOpen
} from 'lucide-react';
import toast from 'react-hot-toast';
import documentService from '../services/documentService';
import StatusBadge from './StatusBadge';

// Config maps document_type to icons and style classes
const typeConfig = {
  passport: { label: 'Passport', icon: Globe, color: 'text-indigo-600 bg-indigo-50 border-indigo-100' },
  national_id: { label: 'National ID', icon: FileText, color: 'text-sky-600 bg-sky-50 border-sky-100' },
  photograph: { label: 'Photograph', icon: Image, color: 'text-pink-600 bg-pink-50 border-pink-100' },
  academic_certificate: { label: 'Academic Certificate', icon: GraduationCap, color: 'text-emerald-600 bg-emerald-50 border-emerald-100' },
  ielts: { label: 'IELTS Report', icon: Sparkles, color: 'text-purple-600 bg-purple-50 border-purple-100' },
  toefl: { label: 'TOEFL Report', icon: Sparkles, color: 'text-purple-600 bg-purple-50 border-purple-100' },
  offer_letter: { label: 'Offer Letter', icon: MailOpen, color: 'text-amber-600 bg-amber-50 border-amber-100' },
  bank_statement: { label: 'Bank Statement', icon: Landmark, color: 'text-cyan-600 bg-cyan-50 border-cyan-100' },
  financial_proof: { label: 'Financial Proof', icon: Landmark, color: 'text-teal-600 bg-teal-50 border-teal-100' },
  visa_application: { label: 'Visa Form', icon: FileText, color: 'text-blue-600 bg-blue-50 border-blue-100' },
  insurance: { label: 'Insurance', icon: ShieldCheck, color: 'text-rose-600 bg-rose-50 border-rose-100' },
  employment_proof: { label: 'Employment Proof', icon: Briefcase, color: 'text-slate-600 bg-slate-50 border-slate-100' },
  travel_itinerary: { label: 'Itinerary', icon: Compass, color: 'text-violet-600 bg-violet-50 border-violet-100' },
  other: { label: 'Other Document', icon: HelpCircle, color: 'text-slate-600 bg-slate-50 border-slate-100' }
};

const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

export const DocumentGrid = ({ documents = [], employees = [], onDeleteSuccess }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [uploaderFilter, setUploaderFilter] = useState('');
  const [sortOrder, setSortOrder] = useState('newest'); // 'newest', 'oldest', 'alphabetical'
  
  // Preview State
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewName, setPreviewName] = useState('');
  const [previewType, setPreviewType] = useState('image'); // 'image' or 'pdf'

  const getEmployeeName = (id) => {
    const emp = employees.find(e => e.id === Number(id));
    return emp ? emp.name : `Advisor #${id}`;
  };

  // Find list of unique uploaders actually present in local list
  const activeUploaders = Array.from(new Set(documents.map(d => d.uploaded_by)));

  // Actions
  const handleDownload = async (doc) => {
    try {
      const loader = toast.loading(`Resolving signed link for "${doc.original_file_name}"...`);
      const res = await documentService.download(doc.id);
      toast.dismiss(loader);
      
      // Trigger download
      const link = document.createElement('a');
      link.href = res.download_url;
      link.target = '_blank';
      link.setAttribute('download', doc.original_file_name);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      toast.error('Failed to download file. Please check permissions.');
    }
  };

  const handlePreview = async (doc) => {
    const ext = doc.file_extension?.toLowerCase();
    const isImage = ['jpg', 'jpeg', 'png'].includes(ext);
    const isPdf = ext === 'pdf';
    const isWord = ['doc', 'docx'].includes(ext);

    if (!isImage && !isPdf && !isWord) {
      // Just download for unsupported preview extensions
      handleDownload(doc);
      return;
    }

    try {
      const loader = toast.loading(`Preparing preview for "${doc.original_file_name}"...`);
      const res = await documentService.getPreviewUrl(doc.id);
      toast.dismiss(loader);

      if (isWord) {
        // Open securely in new tab
        window.open(res.view_url, '_blank');
      } else {
        // Image or PDF preview modal
        setPreviewType(isPdf ? 'pdf' : 'image');
        setPreviewUrl(res.view_url);
        setPreviewName(doc.original_file_name);
      }
    } catch (err) {
      toast.dismiss();
      toast.error(err.message || 'Failed to generate preview URL.');
    }
  };

  const handleDelete = async (doc) => {
    if (!window.confirm(`Are you sure you want to delete "${doc.original_file_name}"? This will archive the file.`)) {
      return;
    }

    try {
      await documentService.delete(doc.id);
      toast.success('Document archived successfully!');
      if (onDeleteSuccess) {
        onDeleteSuccess();
      }
    } catch (err) {
      toast.error(err.message || 'Failed to archive document');
    }
  };

  // Filter & Sort Logic
  const filteredDocuments = documents
    .filter(doc => {
      const nameMatch = doc.original_file_name.toLowerCase().includes(searchTerm.toLowerCase());
      const codeMatch = doc.document_code?.toLowerCase().includes(searchTerm.toLowerCase());
      const typeMatch = typeFilter ? doc.document_type === typeFilter : true;
      const uploaderMatch = uploaderFilter ? doc.uploaded_by === Number(uploaderFilter) : true;
      return (nameMatch || codeMatch) && typeMatch && uploaderMatch;
    })
    .sort((a, b) => {
      if (sortOrder === 'newest') {
        return new Date(b.uploaded_at) - new Date(a.uploaded_at);
      }
      if (sortOrder === 'oldest') {
        return new Date(a.uploaded_at) - new Date(b.uploaded_at);
      }
      if (sortOrder === 'alphabetical') {
        return a.original_file_name.localeCompare(b.original_file_name);
      }
      return 0;
    });

  return (
    <div className="space-y-5 text-left">
      
      {/* Inline Toolbar */}
      <div className="bg-slate-50/50 p-4 rounded-2xl border border-slate-100 flex flex-col md:flex-row gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search size={14} className="absolute inset-y-0 my-auto left-3.5 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by name or code..."
            className="w-full pl-9 pr-4 py-2 border border-slate-200 bg-white rounded-xl text-xs font-semibold focus:border-brand-blue outline-none transition-all"
          />
        </div>
        
        {/* Filters */}
        <div className="grid grid-cols-2 md:flex gap-3 text-xs">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-2 rounded-xl border border-slate-200 bg-white font-semibold text-slate-600 focus:outline-none"
          >
            <option value="">All Types</option>
            {Object.keys(typeConfig).map(type => (
              <option key={type} value={type}>
                {typeConfig[type].label}
              </option>
            ))}
          </select>

          <select
            value={uploaderFilter}
            onChange={(e) => setUploaderFilter(e.target.value)}
            className="px-3 py-2 rounded-xl border border-slate-200 bg-white font-semibold text-slate-600 focus:outline-none"
          >
            <option value="">All Uploaders</option>
            {activeUploaders.map(uid => (
              <option key={uid} value={uid}>
                {getEmployeeName(uid)}
              </option>
            ))}
          </select>

          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
            className="px-3 py-2 rounded-xl border border-slate-200 bg-white font-semibold text-slate-600 focus:outline-none col-span-2 md:col-span-1"
          >
            <option value="newest">Sort: Newest</option>
            <option value="oldest">Sort: Oldest</option>
            <option value="alphabetical">Sort: A-Z</option>
          </select>
        </div>
      </div>

      {/* Grid of Documents */}
      {filteredDocuments.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 border border-dashed border-slate-200 rounded-2xl bg-white/40 backdrop-blur-sm">
          <HelpCircle size={32} className="text-slate-300 mb-3" />
          <h4 className="text-xs font-bold text-slate-700">No documents found</h4>
          <p className="text-[10px] text-slate-400 mt-1">Upload validation files or update filters above.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredDocuments.map(doc => {
            const config = typeConfig[doc.document_type] || {
              label: doc.document_type,
              icon: HelpCircle,
              color: 'text-slate-600 bg-slate-50 border-slate-100'
            };
            const Icon = config.icon;
            
            return (
              <div 
                key={doc.id}
                className="bg-white border border-slate-100 shadow-sm shadow-brand-blue/5 rounded-2xl p-4 flex flex-col justify-between hover:shadow-md hover:border-slate-200/80 transition-all group"
              >
                <div>
                  {/* Card Header: Type Badge + Document Code */}
                  <div className="flex justify-between items-center mb-3">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-[10px] font-bold border ${config.color}`}>
                      <Icon size={10} className="shrink-0" />
                      {config.label}
                    </span>
                    <span className="text-[9px] font-mono font-bold text-slate-400 bg-slate-50 border border-slate-100 px-1.5 py-0.5 rounded">
                      {doc.document_code}
                    </span>
                  </div>

                  {/* Title & extension */}
                  <h4 
                    title={doc.original_file_name}
                    className="text-xs font-bold text-slate-700 truncate max-w-full mb-1 leading-snug"
                  >
                    {doc.original_file_name}
                  </h4>
                  
                  {/* Meta stats */}
                  <div className="space-y-1.5 mt-3 text-[10px] text-slate-400 font-semibold">
                    <div className="flex justify-between">
                      <span>Size:</span>
                      <span className="text-slate-600">{formatFileSize(doc.file_size)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Uploaded By:</span>
                      <span className="text-slate-600">{getEmployeeName(doc.uploaded_by)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Upload Date:</span>
                      <span className="text-slate-600">{new Date(doc.uploaded_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Status:</span>
                      <span className="inline-flex items-center gap-1 text-[9px] bg-emerald-50 text-emerald-600 px-1.5 py-0.2 rounded font-extrabold uppercase">
                        Verified
                      </span>
                    </div>
                  </div>
                </div>

                {/* Actions Footer */}
                <div className="flex items-center justify-between border-t border-slate-50 pt-3 mt-4">
                  <span className="text-[9px] font-bold text-slate-300 font-mono uppercase">
                    .{doc.file_extension}
                  </span>
                  
                  <div className="flex gap-1">
                    <button
                      onClick={() => handlePreview(doc)}
                      className="p-1.5 text-slate-400 hover:text-brand-blue hover:bg-brand-blue/5 rounded-lg transition-all"
                      title="Preview File"
                    >
                      <Eye size={13} />
                    </button>
                    <button
                      onClick={() => handleDownload(doc)}
                      className="p-1.5 text-slate-400 hover:text-brand-orange hover:bg-brand-orange/5 rounded-lg transition-all"
                      title="Download File"
                    >
                      <FileDown size={13} />
                    </button>
                    <button
                      onClick={() => handleDelete(doc)}
                      className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                      title="Archive Record"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Document Preview Overlay Modal */}
      {previewUrl && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-scale-up">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-800 truncate pr-4">{previewName}</h3>
              <button 
                onClick={() => { setPreviewUrl(null); setPreviewName(''); }}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-all"
              >
                <X size={16} />
              </button>
            </div>
            
            <div className="flex-1 bg-slate-50 flex items-center justify-center overflow-auto p-4 max-h-[70vh]">
              {previewType === 'pdf' ? (
                <iframe 
                  src={previewUrl} 
                  title="PDF Preview"
                  className="w-full h-[65vh] rounded-lg border border-slate-200 bg-white"
                />
              ) : (
                <img 
                  src={previewUrl} 
                  alt="File Preview" 
                  className="max-w-full max-h-full object-contain rounded-lg border border-slate-200/50 shadow-md"
                />
              )}
            </div>

            <div className="px-6 py-3.5 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => { setPreviewUrl(null); setPreviewName(''); }}
                className="px-4 py-2 border border-slate-200 hover:bg-slate-50 rounded-xl text-xs font-bold text-slate-600 transition-all"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
      
    </div>
  );
};

export default DocumentGrid;
