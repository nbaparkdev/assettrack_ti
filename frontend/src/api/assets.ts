import { apiClient } from './client';
import type { Asset, AssetReferences, BulkDuplicateRequest, BulkDuplicateResponse } from '../types';

export const assetsApi = {
  list: async (skip = 0, limit = 100, ePatrimonio = ''): Promise<Asset[]> => {
    let url = `/assets?skip=${skip}&limit=${limit}`;
    if (ePatrimonio) {
      url += `&e_patrimonio=${encodeURIComponent(ePatrimonio)}`;
    }
    const response = await apiClient.get<Asset[]>(url);
    return response.data;
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
    return `http://localhost:8080/api/v1/assets/${id}/qrcode?token=${token || ''}`;
  },
};
