import api from '../config/api';
import { API_ENDPOINTS } from '../constants/apiEndpoints';

const chatService = {
  /**
   * Fetch complete conversation thread history for an applicant
   */
  async getConversation(applicantId) {
    const response = await api.get(API_ENDPOINTS.CHAT.CONVERSATION(applicantId));
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to fetch conversation thread history.');
  },

  /**
   * Post a new standard chat message or file attachment
   */
  async sendMessage(applicantId, content, messageType = 'text', attachmentUrl = null) {
    const response = await api.post(API_ENDPOINTS.CHAT.CREATE(applicantId), {
      content,
      message_type: messageType,
      attachment_url: attachmentUrl,
    });
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to post message.');
  },

  /**
   * Soft delete a chat message
   */
  async deleteMessage(messageId) {
    const response = await api.delete(API_ENDPOINTS.CHAT.DELETE(messageId));
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to delete message.');
  },

  /**
   * Fetch the latest message from the thread
   */
  async getLatest(applicantId) {
    const response = await api.get(API_ENDPOINTS.CHAT.LATEST(applicantId));
    if (response.data && response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data?.message || 'Failed to fetch latest message.');
  },
};

export default chatService;
