import axios from 'axios';
import { offlineStorage } from '../utils/offlineStorage';

const getApiBaseUrl = () => {
  // Check if there is a custom API URL configured (useful for mobile local testing)
  const customUrl = typeof window !== 'undefined' ? localStorage.getItem('custom_api_url') : null;
  if (customUrl) {
    return customUrl;
  }

  const { hostname, protocol } = window.location;
  
  // Check if running inside a Capacitor app
  const isCapacitor = typeof window !== 'undefined' && !!(window as any).Capacitor;

  // If running inside Capacitor (localhost), fall back to the development server IP on the Wi-Fi network
  if (isCapacitor && (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '')) {
    // IP da interface Wi-Fi do servidor no ambiente local atual.
    // O portal web continua usando o hostname acessado pelo dispositivo;
    // o APK precisa de um endereço explícito para alcançar a API.
    return 'http://172.30.6.127:8080/api/v1';
  }
  
  // Ensure we use http/https protocol for requests (Capacitor uses custom protocols like capacitor://)
  const apiProtocol = protocol.startsWith('http') ? protocol : 'http:';
  return `${apiProtocol}//${hostname}:8080/api/v1`;
};

export const API_BASE_URL = getApiBaseUrl();
export const API_ORIGIN = API_BASE_URL.replace(/\/api\/v1$/, '');

export const toApiFileUrl = (path?: string | null) => {
  if (!path) return '';
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_ORIGIN}${path.startsWith('/') ? path : `/${path}`}`;
};

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add access token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle caching, offline queueing and token expiry
apiClient.interceptors.response.use(
  (response) => {
    // Automatically cache GET responses for offline read-access
    if (response.config.method?.toLowerCase() === 'get' && response.config.url) {
      offlineStorage.setCache(response.config.url, response.data);
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    const isNetworkError = !error.response || error.code === 'ERR_NETWORK' || !navigator.onLine;

    // Handle offline scenario
    if (isNetworkError && originalRequest) {
      const method = (originalRequest.method || 'get').toLowerCase();
      const url = originalRequest.url || '';

      // Emergency alerts are strictly blocked offline
      if (url.includes('/alertas/alertar') || url.includes('/emergencia/alertar')) {
        return Promise.reject(new Error('Os alertas de emergência são em tempo real e exigem conexão ativa com a internet.'));
      }

      // 1. If GET, serve from offline cache if available
      if (method === 'get') {
        const cached = offlineStorage.getCache(url);
        if (cached !== null) {
          return Promise.resolve({
            data: cached,
            status: 200,
            statusText: 'OK (Offline Cache)',
            headers: {},
            config: originalRequest,
          });
        }
      }

      // 2. If mutating request (POST, PUT, DELETE, PATCH), enqueue for auto-sync
      if (['post', 'put', 'delete', 'patch'].includes(method)) {
        let payload = originalRequest.data;
        try {
          if (typeof payload === 'string') {
            payload = JSON.parse(payload);
          }
        } catch {
          // keep as is
        }

        // Determine friendly description
        let description = 'Operação em lote';
        let category: 'chamado' | 'interacao' | 'ativo' | 'movimentacao' | 'geral' = 'geral';
        if (url.includes('/servicos/chamados')) {
          description = 'Abertura/atualização de chamado';
          category = 'chamado';
        } else if (url.includes('/servicos/interacoes')) {
          description = 'Comentário em chamado';
          category = 'interacao';
        } else if (url.includes('/assets')) {
          description = 'Atualização de ativo';
          category = 'ativo';
        } else if (url.includes('/transacoes') || url.includes('/movimentacoes')) {
          description = 'Movimentação / Empréstimo';
          category = 'movimentacao';
        }

        const queueItem = offlineStorage.enqueue({
          endpoint: url,
          method: method.toUpperCase() as any,
          payload,
          description,
          category,
        });

        // Return simulated accepted response so UI continues seamlessly
        return Promise.resolve({
          data: {
            id: `temp_${Date.now()}`,
            ...payload,
            _offline_queued: true,
            _queue_id: queueItem.id,
            message: 'Ação salva localmente no dispositivo. Será sincronizada automaticamente ao restabelecer a conexão.',
          },
          status: 202,
          statusText: 'Accepted (Enqueued Offline)',
          headers: {},
          config: originalRequest,
        });
      }
    }

    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      // Redirect to login if on protected page
      if (window.location.pathname !== '/login' && window.location.pathname !== '/qr-login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
