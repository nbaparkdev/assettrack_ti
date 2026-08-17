import { apiClient as api } from './client';
import type { User } from '../types/user';

export const profileApi = {
  updateProfile: async (data: { nome?: string; email?: string; matricula?: string }): Promise<User> => {
    const res = await api.put<User>('/profile', data);
    return res.data;
  },

  changePassword: async (data: { current_password: string; new_password: string }): Promise<{ message: string }> => {
    const res = await api.put<{ message: string }>('/profile/password', data);
    return res.data;
  },

  uploadAvatar: async (file: File): Promise<{ avatar_url: string }> => {
    const formData = new FormData();
    formData.append('avatar', file);

    const res = await api.post<{ avatar_url: string }>('/profile/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },
};
