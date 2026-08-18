import { apiClient as api } from './client';
import type { SystemSettings, UpdateSettingsPayload } from '../types/settings';

export const getSettings = async (): Promise<SystemSettings> => {
  const response = await api.get('/admin/settings');
  return response.data;
};

export const updateSettings = async (data: UpdateSettingsPayload): Promise<void> => {
  await api.put('/admin/settings', data);
};
