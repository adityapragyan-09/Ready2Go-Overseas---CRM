import React from 'react';
import { Trash2, FileText, Download } from 'lucide-react';

const ROLE_BADGES = {
  admin: { label: 'Admin', bg: 'bg-rose-100 text-rose-800' },
  employee: { label: 'Counselor', bg: 'bg-orange-100 text-orange-800' },
};

export const MessageBubble = ({ message, currentUser, onDelete }) => {
  const isMe = message.sender_id === currentUser?.id;
  const senderRole = message.sender_role || 'employee'; // fallback
  const badgeConfig = ROLE_BADGES[senderRole] || ROLE_BADGES.employee;

  const formattedDate = new Date(message.created_at).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  });

  const formattedTime = new Date(message.created_at).toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  });

  // Calculate sender initials for avatar fallback
  const getInitials = (name) => {
    if (!name) return '?';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
  };

  const showDelete = isMe || currentUser?.role === 'admin';

  return (
    <div className={`flex gap-3 my-4 group animate-fade-in ${isMe ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className="shrink-0">
        <div className={`w-8 h-8 rounded-full border flex items-center justify-center text-xs font-bold shadow-sm ${
          isMe 
            ? 'bg-brand-orange text-white border-brand-orange ring-2 ring-orange-50' 
            : 'bg-slate-100 text-slate-700 border-slate-200'
        }`}>
          {getInitials(message.sender_name)}
        </div>
      </div>

      {/* Bubble Container */}
      <div className={`max-w-[75%] flex flex-col ${isMe ? 'items-end' : 'items-start'}`}>
        {/* Metadata Header */}
        <div className="flex items-center gap-1.5 mb-1 text-[10px] text-slate-400 font-bold uppercase tracking-wider">
          <span>{message.sender_name}</span>
          <span className={`px-1.5 py-0.5 rounded text-[8px] font-extrabold ${badgeConfig.bg}`}>
            {badgeConfig.label}
          </span>
          <span>&bull;</span>
          <span>{formattedDate} {formattedTime}</span>
        </div>

        {/* Message bubble itself */}
        <div className={`relative px-4 py-3 rounded-2xl text-xs font-medium leading-relaxed shadow-sm ${
          isMe 
            ? 'bg-brand-orange/10 border border-brand-orange/20 text-slate-800 rounded-tr-none' 
            : 'bg-white border border-slate-100 text-slate-700 rounded-tl-none'
        }`}>
          {/* Attachment render if applicable */}
          {message.message_type === 'attachment' && message.attachment_url && (
            <div className="mb-2.5 p-2 bg-slate-50 border border-slate-100 rounded-xl flex items-center justify-between gap-3 text-slate-600 font-bold">
              <div className="flex items-center gap-2 max-w-[80%]">
                <FileText className="w-4 h-4 text-brand-orange shrink-0" />
                <span className="truncate text-[10px] uppercase tracking-wider">Attachment file link</span>
              </div>
              <a
                href={message.attachment_url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-1 bg-white border border-slate-200 hover:border-slate-300 rounded-lg text-slate-500 hover:text-slate-700 transition-all shadow-sm"
              >
                <Download className="w-3.5 h-3.5" />
              </a>
            </div>
          )}
          
          <p className="whitespace-pre-wrap">{message.message}</p>

          {/* Delete Option hover trigger */}
          {showDelete && (
            <button
              onClick={() => onDelete(message.id)}
              className={`absolute top-1/2 -translate-y-1/2 p-1.5 bg-white border border-slate-150 hover:border-rose-200 text-slate-400 hover:text-rose-600 rounded-lg transition-all duration-200 opacity-0 group-hover:opacity-100 shadow-sm ${
                isMe ? 'right-full mr-2' : 'left-full ml-2'
              }`}
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
