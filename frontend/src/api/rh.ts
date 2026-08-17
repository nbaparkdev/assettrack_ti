import { apiClient } from './client';
import type { TermoResponsabilidade, RHListResponse } from '../types/rh';
import type { Solicitacao } from '../types/transaction';

export const rhApi = {
  list: async (): Promise<RHListResponse> => {
    const response = await apiClient.get<RHListResponse>('/rh/termos');
    return response.data;
  },
  generateTemplate: async (solicitacaoId: number): Promise<{ conteudo_termo: string; solicitacao: Solicitacao }> => {
    const response = await apiClient.get(`/rh/solicitacoes/${solicitacaoId}/modelo`);
    return response.data;
  },
  create: async (data: { solicitacao_id?: number; conteudo_termo: string }): Promise<TermoResponsabilidade> => {
    const response = await apiClient.post<TermoResponsabilidade>('/rh/termos', data);
    return response.data;
  },
  update: async (id: number, conteudo_termo: string): Promise<TermoResponsabilidade> => {
    const response = await apiClient.put<TermoResponsabilidade>(`/rh/termos/${id}`, { conteudo_termo });
    return response.data;
  },
  sign: async (id: number): Promise<TermoResponsabilidade> => {
    const response = await apiClient.post<TermoResponsabilidade>(`/rh/termos/${id}/assinar`);
    return response.data;
  },
  cancel: async (id: number): Promise<TermoResponsabilidade> => {
    const response = await apiClient.post<TermoResponsabilidade>(`/rh/termos/${id}/cancelar`);
    return response.data;
  },
  pdf: async (id: number): Promise<Blob> => {
    const response = await apiClient.get(`/rh/termos/${id}/pdf`, { responseType: 'blob' });
    return response.data;
  },
  offboardUser: async (userId: number): Promise<{ message: string; assets_affected: number }> => {
    const response = await apiClient.post<{ message: string; assets_affected: number }>(`/rh/colaboradores/${userId}/desligamento`);
    return response.data;
  },
};
