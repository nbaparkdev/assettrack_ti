import { API_BASE_URL, apiClient } from './client';
import type { Asset, AssetReferences, BulkDuplicateRequest, BulkDuplicateResponse } from '../types';

export interface AssetListFilters {
  e_patrimonio?: string;
  nome?: string;
  categoria_id?: number | '';
  localizacao_id?: number | '';
  fornecedor_id?: number | '';
  nfe?: string;
  status?: string;
  data_inicio?: string;
  data_fim?: string;
}

const buildAssetQuery = (skip = 0, limit = 100, filters: AssetListFilters = {}) => {
  const params = new URLSearchParams({
    skip: String(skip),
    limit: String(limit),
  });

  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, String(value));
    }
  });

  return params;
};

export const assetsApi = {
  list: async (skip = 0, limit = 100, filters: AssetListFilters = {}): Promise<Asset[]> => {
    const query = buildAssetQuery(skip, limit, filters);
    const url = `/assets?${query.toString()}`;
    const response = await apiClient.get<Asset[]>(url);
    return response.data;
  },

  listUrl: (skip = 0, limit = 100, filters: AssetListFilters = {}): string => {
    const query = buildAssetQuery(skip, limit, filters);
    const token = localStorage.getItem('token');
    if (token) {
      query.append('token', token);
    }
    return `${API_BASE_URL}/assets?${query.toString()}`;
  },

  exportCsv: async (filters: AssetListFilters = {}): Promise<void> => {
    const query = buildAssetQuery(0, 10000, filters);
    const response = await apiClient.get<Blob>(`/assets/export.csv?${query.toString()}`, {
      responseType: 'blob',
    });

    const blobUrl = URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = `ativos_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(blobUrl);
  },

  getById: async (id: number): Promise<Asset> => {
    const response = await apiClient.get<Asset>(`/assets/${id}`);
    return response.data;
  },

  create: async (data: Partial<Asset>): Promise<Asset> => {
    const response = await apiClient.post<Asset>('/assets', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Asset>): Promise<Asset> => {
    const response = await apiClient.put<Asset>(`/assets/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/assets/${id}`);
  },

  getReferences: async (): Promise<AssetReferences> => {
    const response = await apiClient.get<AssetReferences>('/assets/referencias');
    return response.data;
  },

  bulkDuplicate: async (data: BulkDuplicateRequest): Promise<BulkDuplicateResponse> => {
    const response = await apiClient.post<BulkDuplicateResponse>('/assets/bulk', data);
    return response.data;
  },

  scanQRCode: async (file: File): Promise<Asset> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<Asset>('/assets/scan-qr', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getQRCodeUrl: (id: number): string => {
    const token = localStorage.getItem('token');
    return `${API_BASE_URL}/assets/${id}/qrcode?token=${token || ''}`;
  },
};
