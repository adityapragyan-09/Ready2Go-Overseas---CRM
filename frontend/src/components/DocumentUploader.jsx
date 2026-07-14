import React, { useState, useRef } from 'react';
import { UploadCloud, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import documentService from '../services/documentService';
import { appConfig } from '../config/appConfig';

const documentTypes = [
  { value: 'passport', label: 'Passport' },
  { value: 'national_id', label: 'National ID' },
  { value: 'photograph', label: 'Photograph' },
  { value: 'academic_certificate', label: 'Academic Certificate' },
  { value: 'ielts', label: 'IELTS Report' },
  { value: 'toefl', label: 'TOEFL Report' },
  { value: 'offer_letter', label: 'Offer Letter' },
  { value: 'bank_statement', label: 'Bank Statement' },
  { value: 'financial_proof', label: 'Financial Proof' },
  { value: 'visa_application', label: 'Visa Application Form' },
  { value: 'insurance', label: 'Travel/Health Insurance' },
  { value: 'employment_proof', label: 'Employment Proof' },
  { value: 'travel_itinerary', label: 'Travel Itinerary' },
  { value: 'other', label: 'Other Document' }
];

export const DocumentUploader = ({ applicantId, onUploadSuccess }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedType, setSelectedType] = useState('passport');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentFileName, setCurrentFileName] = useState('');
  const fileInputRef = useRef(null);

  const allowedExtensions = appConfig.ALLOWED_DOCUMENT_TYPES.map(ext => `.${ext}`);
  const maxFileSize = appConfig.MAX_UPLOAD_SIZE_MB * 1024 * 1024;

  const validateFile = (file) => {
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!allowedExtensions.includes(ext)) {
      toast.error(`File extension "${ext}" is not supported. Allowed: ${appConfig.ALLOWED_DOCUMENT_TYPES.join(', ').toUpperCase()}.`);
      return false;
    }
    if (file.size > maxFileSize) {
      toast.error(`File "${file.name}" exceeds the ${appConfig.MAX_UPLOAD_SIZE_MB} MB size limit.`);
      return false;
    }
    return true;
  };

  const handleFiles = async (files) => {
    if (!files || files.length === 0) return;
    setIsUploading(true);
    
    // Process files sequentially
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (!validateFile(file)) continue;

      setCurrentFileName(file.name);
      setUploadProgress(0);

      try {
        await documentService.upload(
          file, 
          applicantId, 
          selectedType, 
          (progress) => setUploadProgress(progress)
        );
        toast.success(`Successfully uploaded "${file.name}" as ${selectedType.replace('_', ' ')}!`);
      } catch (err) {
        toast.error(err.message || `Failed to upload "${file.name}"`);
      }
    }

    setIsUploading(false);
    setUploadProgress(0);
    setCurrentFileName('');
    if (onUploadSuccess) {
      onUploadSuccess();
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const onButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="bg-white/80 backdrop-blur-md border border-slate-100/80 shadow-xl shadow-brand-blue/5 rounded-2xl p-5 space-y-4 text-left">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-3">
        <div>
          <h3 className="text-sm font-bold text-slate-800 font-display">Upload Documents</h3>
          <p className="text-[10px] text-slate-400 mt-0.5 font-medium">Verify credentials via official folders</p>
        </div>
        
        {/* Document Type Dropdown */}
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Type:</span>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            disabled={isUploading}
            className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs font-bold text-slate-700 focus:outline-none focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/5 outline-none transition-all duration-200"
          >
            {documentTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Drag & Drop Area */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`
          relative py-8 px-4 rounded-xl border-2 border-dashed flex flex-col items-center justify-center text-center transition-all duration-200
          ${dragActive 
            ? 'border-brand-orange bg-brand-orange/5 text-brand-orange' 
            : 'border-slate-200 hover:border-brand-orange hover:bg-brand-orange/5/30 text-slate-500 hover:text-brand-orange'
          }
          ${isUploading ? 'opacity-65 pointer-events-none' : 'cursor-pointer'}
        `}
        onClick={isUploading ? undefined : onButtonClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileInputChange}
          className="hidden"
          accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
        />

        <div className="w-10 h-10 rounded-lg bg-brand-blue/5 border border-brand-blue/10 flex items-center justify-center text-brand-blue mb-3">
          <UploadCloud size={20} className={isUploading ? 'animate-bounce' : ''} />
        </div>
        
        <p className="text-xs font-bold text-slate-800">
          Drag & drop your files here, or <span className="text-brand-orange hover:underline">browse</span>
        </p>
        <p className="text-[10px] text-slate-400 mt-1 font-semibold uppercase tracking-wider">
          {appConfig.ALLOWED_DOCUMENT_TYPES.join(', ').toUpperCase()} (Max {appConfig.MAX_UPLOAD_SIZE_MB}MB)
        </p>
      </div>

      {/* Upload Progress Indicator */}
      {isUploading && (
        <div className="p-3 border border-slate-100 rounded-xl bg-slate-50/50 space-y-2.5 animate-fade-in">
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-slate-700 truncate max-w-[70%] flex items-center gap-1.5">
              <Loader2 size={12} className="animate-spin text-brand-orange shrink-0" />
              Uploading: {currentFileName}
            </span>
            <span className="font-bold text-brand-orange">{uploadProgress}%</span>
          </div>
          
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div 
              className="bg-brand-orange h-full rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentUploader;
