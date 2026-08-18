import { apiClient as api } from './client';
import type { EmailLogResponse } from '../types/emailLog';

export const getEmailLogs = async (limit: number = 20, offset: number = 0): Promise<EmailLogResponse> => {
  const response = await api.get(`/admin/email-logs?limit=${limit}&offset=${offset}`);
  return response.data;
};
