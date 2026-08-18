import { apiClient as api } from './client';
import type { ChatMessage, ChatResponse } from '../types/ai';

export const sendChatMessage = async (messages: ChatMessage[]): Promise<ChatResponse> => {
  const response = await api.post('/chat', { messages });
  return response.data;
};
