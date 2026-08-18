import { apiClient } from './client';
import type { Solicitacao } from '../types';

export const transactionApi = {
  // Borrowings
  listSolicitacoes: async (skip = 0, limit = 100): Promise<Solicitacao[]> => {
    const response = await apiClient.get<Solicitacao[]>(`/solicitacoes?skip=${skip}&limit=${limit}`);
    return response.data;
  },
  createSolicitacao: async (data: { asset_id: number; motivo: string; data_prevista_devolucao?: string }): Promise<Solicitacao> => {
    const response = await apiClient.post<Solicitacao>('/solicitacoes', data);
    return response.data;
  },
  approveSolicitacao: async (id: number): Promise<Solicitacao> => {
    const response = await apiClient.put<Solicitacao>(`/solicitacoes/${id}/approve`);
    return response.data;
  },
  rejectSolicitacao: async (id: number): Promise<Solicitacao> => {
    const response = await apiClient.put<Solicitacao>(`/solicitacoes/${id}/reject`);
    return response.data;
  },

  // Devolution
  devolverAsset: async (
    assetId: number,
    data: {
      condicao_equipamento: string;
      acessorios_devolvidos: string;
      observacoes_adicionais?: string;
    }
  ): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>(`/movimentacoes/devolver/${assetId}`, data);
    return response.data;
  },
};
