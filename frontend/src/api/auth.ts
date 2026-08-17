import { apiClient } from './client';
import type { LoginCredentials, TokenResponse, User, QRLoginCredentials } from '../types';

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/auth/login', credentials);
    return response.data;
  },

  qrLogin: async (credentials: QRLoginCredentials): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/qr/login', credentials);
    return response.data;
  },

  me: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },
};
