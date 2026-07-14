import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

export const ChatInput = ({ onSend, isDisabled }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  // Auto resize height depending on content rows
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [text]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!text.trim() || isDisabled) return;
    onSend(text.trim());
    setText('');
  };

  const handleKeyDown = (e) => {
    // Send on Enter, shift+enter for newline
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2.5 bg-slate-50/50 border border-slate-100 p-2.5 rounded-2xl shadow-inner">
      <textarea
        ref={textareaRef}
        rows={1}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type a counselor message to collaborate..."
        disabled={isDisabled}
        className="flex-1 bg-white border border-slate-200 focus:border-brand-orange focus:ring-1 focus:ring-brand-orange/20 rounded-xl px-4 py-2.5 text-xs font-semibold text-slate-700 placeholder:text-slate-400 outline-none resize-none max-h-32 transition-all leading-normal disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={!text.trim() || isDisabled}
        className="p-3 bg-brand-orange hover:bg-orange-600 disabled:opacity-40 text-white rounded-xl transition-all duration-200 shrink-0 flex items-center justify-center shadow-sm shadow-orange-100 disabled:shadow-none"
      >
        <Send className="w-3.5 h-3.5" />
      </button>
    </form>
  );
};

export default ChatInput;
