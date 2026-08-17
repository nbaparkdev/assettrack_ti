import { apiClient } from './client';
import type { Fornecedor, NotaFiscal, XMLParsedSupplier } from '../types/supplier';

export const suppliersApi = {
  list: async (skip = 0, limit = 100): Promise<Fornecedor[]> => {
    const response = await apiClient.get<Fornecedor[]>(`/fornecedores?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  getById: async (id: number): Promise<Fornecedor> => {
    const response = await apiClient.get<Fornecedor>(`/fornecedores/${id}`);
    return response.data;
  },

  create: async (data: Partial<Fornecedor>): Promise<Fornecedor> => {
    const response = await apiClient.post<Fornecedor>('/fornecedores', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Fornecedor>): Promise<Fornecedor> => {
    const response = await apiClient.put<Fornecedor>(`/fornecedores/${id}`, data);
    return response.data;
  },

  remove: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/fornecedores/${id}`);
    return response.data;
  },

  listInvoices: async (supplierId: number): Promise<{ id: number; numero_nota: string }[]> => {
    const response = await apiClient.get<{ id: number; numero_nota: string }[]>(
      `/fornecedores/${supplierId}/notas-fiscais`
    );
    return response.data;
  },

  getInvoice: async (invoiceId: number): Promise<NotaFiscal> => {
    const response = await apiClient.get<NotaFiscal>(`/notas-fiscais/${invoiceId}`);
    return response.data;
  },

  deleteInvoice: async (invoiceId: number): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/notas-fiscais/${invoiceId}`);
    return response.data;
  },

  uploadInvoice: async (supplierId: number, file: File): Promise<NotaFiscal> => {
    const formData = new FormData();
    formData.append('xml_file', file);
    const response = await apiClient.post<NotaFiscal>(
      `/fornecedores/${supplierId}/notas-fiscais/upload`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  parseXML: async (file: File): Promise<XMLParsedSupplier> => {
    const formData = new FormData();
    formData.append('xml_file', file);
    const response = await apiClient.post<XMLParsedSupplier>('/notas-fiscais/parse-xml', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};
