import { apiClient } from './client';
import type {
  KanbanProject,
  KanbanColumn,
  KanbanCard,
  KanbanCardInteraction,
  KanbanAttachment,
  KanbanNotification,
} from '../types/kanban';

export const kanbanApi = {
  listProjects: async (includeArchived = false): Promise<KanbanProject[]> => {
    const response = await apiClient.get<KanbanProject[]>('/kanban/projetos', {
      params: includeArchived ? { incluir_arquivados: 'true' } : undefined,
    });
    return response.data;
  },
  getBoard: async (id: number): Promise<{ project: KanbanProject; board_progress: number; total_cards: number }> => {
    const response = await apiClient.get(`/kanban/projetos/${id}`);
    return response.data;
  },
  createProject: async (data: { titulo: string; descricao?: string; board_background_color?: string; board_pattern?: string; related_to_maintenance?: boolean; related_to_preventive?: boolean; preventive_plan_id?: number; participante_ids?: number[] }): Promise<KanbanProject> => {
    const response = await apiClient.post<KanbanProject>('/kanban/projetos', data);
    return response.data;
  },
  updateProject: async (id: number, data: Partial<KanbanProject> & { participante_ids?: number[] }): Promise<KanbanProject> => {
    const response = await apiClient.put(`/kanban/projetos/${id}`, data);
    return response.data;
  },
  deleteProject: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/kanban/projetos/${id}`);
    return response.data;
  },
  duplicateProject: async (id: number, incluir_cartoes = false): Promise<KanbanProject> => {
    const response = await apiClient.post<KanbanProject>(`/kanban/projetos/${id}/duplicar`, { incluir_cartoes });
    return response.data;
  },
  toggleProject: async (id: number, acao: string): Promise<KanbanProject> => {
    const response = await apiClient.post(`/kanban/projetos/${id}/status`, { acao });
    return response.data;
  },
  toggleFavorite: async (id: number): Promise<{ favoritado: boolean }> => {
    const response = await apiClient.post(`/kanban/projetos/${id}/favorito`);
    return response.data;
  },
  addColumn: async (projectId: number, nome: string, cor?: string): Promise<KanbanColumn> => {
    const response = await apiClient.post(`/kanban/projetos/${projectId}/colunas`, { nome, cor });
    return response.data;
  },
  updateColumn: async (columnId: number, data: Partial<KanbanColumn>): Promise<KanbanColumn> => {
    const response = await apiClient.put(`/kanban/colunas/${columnId}`, data);
    return response.data;
  },
  createCard: async (data: Partial<KanbanCard> & { participante_ids?: number[]; ativo_ids?: number[] }): Promise<KanbanCard> => {
    const response = await apiClient.post<KanbanCard>('/kanban/cards', data);
    return response.data;
  },
  getCard: async (id: number): Promise<KanbanCard> => {
    const response = await apiClient.get<KanbanCard>(`/kanban/cards/${id}`);
    return response.data;
  },
  updateCard: async (id: number, data: Partial<KanbanCard> & { participante_ids?: number[]; ativo_ids?: number[] }): Promise<KanbanCard> => {
    const response = await apiClient.put<KanbanCard>(`/kanban/cards/${id}`, data);
    return response.data;
  },
  moveCard: async (id: number, column_id: number, ordem: number, motivo?: string): Promise<void> => {
    await apiClient.post(`/kanban/cards/${id}/mover`, { column_id, ordem, motivo });
  },
  deleteCard: async (id: number): Promise<{ message: string; project_id: number }> => {
    const response = await apiClient.delete(`/kanban/cards/${id}`);
    return response.data;
  },
  uploadAttachment: async (cardId: number, arquivo?: File, link?: string, nome?: string): Promise<KanbanAttachment> => {
    const formData = new FormData();
    if (arquivo) formData.append('arquivo', arquivo);
    if (link) formData.append('link', link);
    if (nome) formData.append('nome', nome);
    const response = await apiClient.post(`/kanban/cards/${cardId}/anexo`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  deleteAttachment: async (attachmentId: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/kanban/anexos/${attachmentId}`);
    return response.data;
  },
  addComment: async (cardId: number, mensagem: string): Promise<KanbanCardInteraction> => {
    const response = await apiClient.post(`/kanban/cards/${cardId}/comentar`, { mensagem });
    return response.data;
  },
  unreadCount: async (): Promise<number> => {
    const response = await apiClient.get<{ unread_count: number }>('/kanban/notificacoes/unread-count');
    return response.data.unread_count;
  },
  listNotifications: async (): Promise<KanbanNotification[]> => {
    const response = await apiClient.get<KanbanNotification[]>('/kanban/notificacoes');
    return response.data;
  },
  markNotificationRead: async (notifId: number): Promise<void> => {
    await apiClient.post(`/kanban/notificacoes/${notifId}/lida`);
  },
  markAllNotificationsRead: async (): Promise<void> => {
    await apiClient.post('/kanban/notificacoes/lidas');
  },
};
