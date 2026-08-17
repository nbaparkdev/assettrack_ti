import { create } from 'zustand';
import type { User } from '../types';
import { authApi } from '../api/auth';

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  login: (token: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  loading: false,
  error: null,

  login: async (token: string) => {
    localStorage.setItem('token', token);
    set({ token, loading: true, error: null });
    try {
      const user = await authApi.me();
      set({ user, loading: false });
    } catch (err: any) {
      localStorage.removeItem('token');
      set({ token: null, user: null, loading: false, error: err.response?.data?.detail || 'Erro ao carregar dados do usuário' });
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, token: null, error: null });
    window.location.href = '/login';
  },

  checkAuth: async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      set({ user: null, token: null, loading: false });
      return;
    }

    set({ loading: true, error: null });
    try {
      const user = await authApi.me();
      set({ user, token, loading: false });
    } catch (err: any) {
      localStorage.removeItem('token');
      set({ user: null, token: null, loading: false });
    }
  },
}));
