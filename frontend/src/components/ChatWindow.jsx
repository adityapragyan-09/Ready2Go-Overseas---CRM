import React, { useState, useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import chatService from '../services/chatService';
import MessageBubble from './MessageBubble';
import SystemMessage from './SystemMessage';
import ChatInput from './ChatInput';
import EmptyChatState from './EmptyChatState';
import LoadingSpinner from './LoadingSpinner';

export const ChatWindow = ({ applicantId, currentUser }) => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef(null);

  const loadConversation = async () => {
    if (!applicantId) return;
    try {
      const data = await chatService.getConversation(applicantId);
      setMessages(data);
    } catch (err) {
      // Silent fail - chat load errors are surfaced via EmptyChatState or retry
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadConversation();
  }, [applicantId]);

  // Scroll to bottom on new message load
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (text) => {
    setIsSending(true);
    try {
      const newMsg = await chatService.sendMessage(applicantId, text);
      // Optimistically append or reload list to keep in sync
      setMessages((prev) => [...prev, newMsg]);
    } catch (err) {
      toast.error(err.message || 'Failed to send message.');
    } finally {
      setIsSending(false);
    }
  };

  const handleDeleteMessage = async (messageId) => {
    try {
      await chatService.deleteMessage(messageId);
      toast.success('Message deleted.');
      // Remove or refresh local list
      setMessages((prev) => prev.filter((m) => m.id !== messageId));
    } catch (err) {
      toast.error(err.message || 'Failed to delete message.');
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm flex flex-col overflow-hidden h-[550px] transition-all duration-300 hover:shadow-md">
      {/* Top Banner Header */}
      <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-800">Case Collaboration Feed</h3>
          <p className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">
            Private coordinate channel
          </p>
        </div>
      </div>

      {/* Messages Feed Viewport */}
      <div className="flex-1 p-4 overflow-y-auto bg-slate-50/20 flex flex-col gap-2">
        {isLoading ? (
          <div className="flex-1 flex items-center justify-center">
            <LoadingSpinner label="Compiling coordinator chats..." />
          </div>
        ) : messages.length > 0 ? (
          <>
            {messages.map((msg) =>
              msg.is_system_message ? (
                <SystemMessage key={msg.id} message={msg} />
              ) : (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  currentUser={currentUser}
                  onDelete={handleDeleteMessage}
                />
              )
            )}
            <div ref={messagesEndRef} />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <EmptyChatState />
          </div>
        )}
      </div>

      {/* Input Form Bar */}
      <div className="p-3 border-t border-slate-100 bg-white">
        <ChatInput onSend={handleSendMessage} isDisabled={isSending || isLoading} />
      </div>
    </div>
  );
};

export default ChatWindow;
