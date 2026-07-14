import React, { useEffect, useState } from 'react';
import { Search, X } from 'lucide-react';

export const SearchBar = ({ 
  value = '', 
  onChange, 
  placeholder = 'Search applicants by name, email, or phone...',
  className = ''
}) => {
  const [localValue, setLocalValue] = useState(value);

  // Sync state if prop changes
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  // Debounce change handler to avoid too many requests
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localValue !== value) {
        onChange(localValue);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [localValue, onChange, value]);

  const handleClear = () => {
    setLocalValue('');
    onChange('');
  };

  return (
    <div className={`relative w-full ${className}`}>
      <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-slate-400">
        <Search size={18} />
      </div>
      <input
        type="text"
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-11 pr-10 py-3 rounded-xl border border-slate-200 bg-white/70 backdrop-blur-sm focus:border-brand-blue focus:ring-4 focus:ring-brand-blue/10 outline-none transition-all duration-200 text-sm text-slate-800 placeholder-slate-400"
      />
      {localValue && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute inset-y-0 right-3 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none"
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
};

export default SearchBar;
