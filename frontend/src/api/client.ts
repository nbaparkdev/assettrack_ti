import axios from 'axios';

const getApiBaseUrl = () => {
  // Always use the browser's hostname to connect to the API on port 8080
  // This allows access from other devices on the local network (e.g., 10.100.110.155)
  const { hostname, protocol } = window.location;
  return `${protocol}//${hostname}:8080/api/v1`;
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
