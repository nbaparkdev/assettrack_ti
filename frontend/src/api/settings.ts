import { apiClient as api } from './client';
import type { SystemSettings, UpdateSettingsPayload } from '../types/settings';

export const getSettings = async (): Promise<SystemSettings> => {
  const response = await api.get('/admin/settings');
  return response.data;
};

export const updateSettings = async (data: UpdateSettingsPayload): Promise<void> => {
  await api.put('/admin/settings', data);
};

export const sendTestEmail = async (email?: string): Promise<{ message: string; recipient: string }> => {
  const response = await api.post<{ message: string; recipient: string }>('/admin/settings/test-email', { email: email?.trim() || undefined });
  return response.data;
};
