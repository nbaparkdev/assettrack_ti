import { apiClient } from './client';
import type { User, QRTokenInfo, BadgeInfo, UserPublicProfile } from '../types';

export const usersApi = {
  list: async (skip = 0, limit = 100): Promise<User[]> => {
    const response = await apiClient.get<User[]>(`/users?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  getById: async (id: number): Promise<User> => {
    const response = await apiClient.get<User>(`/users/${id}`);
    return response.data;
  },

  create: async (data: Omit<User, 'id' | 'departamento'> & { password?: string }): Promise<User> => {
    const response = await apiClient.post<User>('/users', data);
    return response.data;
  },

  update: async (id: number, data: Partial<User> & { password?: string }): Promise<User> => {
    const response = await apiClient.put<User>(`/users/${id}`, data);
    return response.data;
  },

  getMyQR: async (): Promise<QRTokenInfo> => {
    const response = await apiClient.get<QRTokenInfo>('/qr/me');
    return response.data;
  },

  regenerateQR: async (): Promise<QRTokenInfo> => {
    const response = await apiClient.post<QRTokenInfo>('/qr/me/generate');
    return response.data;
  },

  getMyBadge: async (): Promise<BadgeInfo> => {
    const response = await apiClient.get<BadgeInfo>('/qr/me/badge');
    return response.data;
  },

  setPIN: async (pin: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/qr/me/pin', { pin });
    return response.data;
  },

  getUserByQRToken: async (token: string): Promise<UserPublicProfile> => {
    const response = await apiClient.get<UserPublicProfile>(`/qr/user/${token}`);
    return response.data;
  },
};
