import { apiClient } from './client';
import type { EmergencyAlert, Aviso } from '../types/alerts';

export const alertsApi = {
  sendAlert: async (motivo: string): Promise<{ status: string; message: string; alert: any }> => {
    const response = await apiClient.post('/alertas/alertar', { motivo });
    return response.data;
  },
  history: async (): Promise<EmergencyAlert[]> => {
    const response = await apiClient.get<EmergencyAlert[]>('/alertas/historico');
    return response.data;
  },
  markAtendido: async (alertId: number): Promise<void> => {
    await apiClient.post(`/alertas/${alertId}/atender`);
  },
  listAvisos: async (): Promise<Aviso[]> => {
    const response = await apiClient.get<Aviso[]>('/avisos');
    return response.data;
  },
  listActiveAvisos: async (): Promise<Aviso[]> => {
    const response = await apiClient.get<Aviso[]>('/avisos/ativos');
    return response.data;
  },
  createAviso: async (data: Partial<Aviso>): Promise<Aviso> => {
    const response = await apiClient.post<Aviso>('/avisos', data);
    return response.data;
  },
  updateAviso: async (id: number, data: Partial<Aviso>): Promise<Aviso> => {
    const response = await apiClient.put<Aviso>(`/avisos/${id}`, data);
    return response.data;
  },
  toggleAviso: async (id: number): Promise<Aviso> => {
    const response = await apiClient.post<Aviso>(`/avisos/${id}/toggle`);
    return response.data;
  },
  deleteAviso: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/avisos/${id}`);
    return response.data;
  },
};
