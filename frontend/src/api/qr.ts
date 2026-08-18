import { apiClient } from './client';
import type { BadgeInfo, UserPublicProfile, QRTokenInfo } from '../types';

export const qrApi = {
  getMyQR: async (): Promise<QRTokenInfo> => {
    const response = await apiClient.get<QRTokenInfo>('/qr/me');
    return response.data;
  },

  generateQRToken: async (): Promise<QRTokenInfo> => {
    const response = await apiClient.post<QRTokenInfo>('/qr/me/generate');
    return response.data;
  },

  getMyBadge: async (): Promise<BadgeInfo> => {
    const response = await apiClient.get<BadgeInfo>('/qr/me/badge');
    return response.data;
  },

  setPIN: async (pin: string): Promise<void> => {
    await apiClient.post('/qr/me/pin', { pin });
  },

  getUserByQR: async (token: string): Promise<UserPublicProfile> => {
    const response = await apiClient.get<UserPublicProfile>(`/qr/user/${token}`);
    return response.data;
  },

  confirmDelivery: async (data: {
    qr_token?: string;
    pin?: string;
    bypass_pin?: boolean;
    solicitacao_id?: number;
    manutencao_id?: number;
    observacao?: string;
  }): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/qr/delivery/confirm', data);
    return response.data;
  },
};
