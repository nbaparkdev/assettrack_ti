import axios from 'axios';

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
    return 'http://10.100.110.155:8080/api/v1';
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

// Response interceptor to handle token expiry
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
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
