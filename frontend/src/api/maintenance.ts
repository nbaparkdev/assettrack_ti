import { apiClient } from './client';
import type { SolicitacaoManutencao } from '../types';

export const maintenanceApi = {
  // Requests
  listRequests: async (skip = 0, limit = 100): Promise<SolicitacaoManutencao[]> => {
    const response = await apiClient.get<SolicitacaoManutencao[]>(`/solicitacoes-manutencao?skip=${skip}&limit=${limit}`);
    return response.data;
  },
  getRequestById: async (id: number): Promise<SolicitacaoManutencao> => {
    const response = await apiClient.get<SolicitacaoManutencao>(`/solicitacoes-manutencao/${id}`);
    return response.data;
  },
  createRequest: async (data: Partial<SolicitacaoManutencao>): Promise<SolicitacaoManutencao> => {
    const response = await apiClient.post<SolicitacaoManutencao>('/solicitacoes-manutencao', data);
    return response.data;
  },

  // Actions
  acceptRequest: async (id: number): Promise<SolicitacaoManutencao> => {
    const response = await apiClient.post<SolicitacaoManutencao>(`/solicitacoes-manutencao/${id}/aceitar`);
    return response.data;
  },
  rejectRequest: async (id: number, reason: string): Promise<SolicitacaoManutencao> => {
    const response = await apiClient.post<SolicitacaoManutencao>(`/solicitacoes-manutencao/${id}/rejeitar`, {
      observacao: reason,
    });
    return response.data;
  },
  concludeRequest: async (id: number, notes: string, cost?: number): Promise<SolicitacaoManutencao> => {
    const response = await apiClient.post<SolicitacaoManutencao>(`/solicitacoes-manutencao/${id}/concluir`, {
      observacao_conclusao: notes,
      custo: cost,
    });
    return response.data;
  },
  confirmReceipt: async (id: number): Promise<SolicitacaoManutencao> => {
    const response = await apiClient.post<SolicitacaoManutencao>(`/solicitacoes-manutencao/${id}/confirmar-recebimento`);
    return response.data;
  },
};
