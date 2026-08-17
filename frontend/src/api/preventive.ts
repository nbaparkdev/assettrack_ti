import { apiClient } from './client';
import type {
  MaintenancePlan,
  MaintenanceChecklist,
  MaintenanceChecklistItem,
  MaintenanceOrder,
  MaintenanceHistory,
  MaintenanceMaterial,
  MaintenancePhoto,
  CustomMaintenanceType,
  PMNotification,
  PMDashboard,
} from '../types/preventive';

export const preventiveApi = {
  // Dashboard
  dashboard: async (): Promise<PMDashboard> => {
    const response = await apiClient.get<PMDashboard>('/preventiva/dashboard');
    return response.data;
  },

  // Plans
  listPlans: async (): Promise<MaintenancePlan[]> => {
    const response = await apiClient.get<MaintenancePlan[]>('/preventiva/planos');
    return response.data;
  },
  getPlan: async (id: number): Promise<{ plan: MaintenancePlan; orders: MaintenanceOrder[] }> => {
    const response = await apiClient.get(`/preventiva/planos/${id}`);
    return response.data;
  },
  createPlan: async (data: Partial<MaintenancePlan>): Promise<MaintenancePlan> => {
    const response = await apiClient.post<MaintenancePlan>('/preventiva/planos', data);
    return response.data;
  },
  updatePlan: async (id: number, data: Partial<MaintenancePlan>): Promise<MaintenancePlan> => {
    const response = await apiClient.put<MaintenancePlan>(`/preventiva/planos/${id}`, data);
    return response.data;
  },
  deletePlan: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/preventiva/planos/${id}`);
    return response.data;
  },
  addChecklist: async (planId: number, nome: string): Promise<MaintenanceChecklist> => {
    const response = await apiClient.post(`/preventiva/planos/${planId}/checklists`, { nome });
    return response.data;
  },
  deleteChecklist: async (planId: number, checklistId: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/preventiva/planos/${planId}/checklists/${checklistId}`);
    return response.data;
  },
  addChecklistItem: async (
    planId: number,
    checklistId: number,
    data: Partial<MaintenanceChecklistItem>
  ): Promise<MaintenanceChecklistItem> => {
    const response = await apiClient.post(
      `/preventiva/planos/${planId}/checklists/${checklistId}/items`,
      data
    );
    return response.data;
  },
  deleteChecklistItem: async (
    planId: number,
    checklistId: number,
    itemId: number
  ): Promise<{ message: string }> => {
    const response = await apiClient.delete(
      `/preventiva/planos/${planId}/checklists/${checklistId}/items/${itemId}`
    );
    return response.data;
  },

  // Orders
  listOrders: async (status = '', skip = 0, limit = 100): Promise<MaintenanceOrder[]> => {
    const response = await apiClient.get<MaintenanceOrder[]>(
      `/preventiva/ordens?status=${encodeURIComponent(status)}&skip=${skip}&limit=${limit}`
    );
    return response.data;
  },
  getOrder: async (id: number): Promise<{ order: MaintenanceOrder; checklists: MaintenanceChecklist[] }> => {
    const response = await apiClient.get(`/preventiva/ordens/${id}`);
    return response.data;
  },
  createOrder: async (
    data: Partial<MaintenanceOrder> & { descricao?: string }
  ): Promise<MaintenanceOrder> => {
    const response = await apiClient.post<MaintenanceOrder>('/preventiva/ordens', data);
    return response.data;
  },
  updateOrder: async (id: number, data: Partial<MaintenanceOrder>): Promise<MaintenanceOrder> => {
    const response = await apiClient.put<MaintenanceOrder>(`/preventiva/ordens/${id}`, data);
    return response.data;
  },
  deleteOrder: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/preventiva/ordens/${id}`);
    return response.data;
  },
  startOrder: async (id: number): Promise<MaintenanceOrder> => {
    const response = await apiClient.post(`/preventiva/ordens/${id}/iniciar`);
    return response.data;
  },
  pauseOrder: async (id: number, motivo?: string): Promise<MaintenanceOrder> => {
    const response = await apiClient.post(`/preventiva/ordens/${id}/pausar`, { motivo });
    return response.data;
  },
  completeOrder: async (id: number, solucao?: string, custo_total?: string): Promise<MaintenanceOrder> => {
    const response = await apiClient.post(`/preventiva/ordens/${id}/concluir`, { solucao, custo_total });
    return response.data;
  },
  cancelOrder: async (id: number, motivo?: string): Promise<MaintenanceOrder> => {
    const response = await apiClient.post(`/preventiva/ordens/${id}/cancelar`, { motivo });
    return response.data;
  },
  executeChecklistItem: async (
    orderId: number,
    checklistItemId: number,
    concluido: boolean,
    observacao?: string,
    foto?: File
  ): Promise<void> => {
    const formData = new FormData();
    formData.append('checklist_item_id', String(checklistItemId));
    formData.append('concluido', concluido ? 'true' : 'false');
    if (observacao) formData.append('observacao', observacao);
    if (foto) formData.append('foto', foto);
    await apiClient.post(`/preventiva/ordens/${orderId}/executar-checklist`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getOrderHistory: async (id: number): Promise<MaintenanceHistory[]> => {
    const response = await apiClient.get(`/preventiva/ordens/${id}/historico`);
    return response.data;
  },
  addMaterial: async (orderId: number, data: Partial<MaintenanceMaterial>): Promise<MaintenanceMaterial> => {
    const response = await apiClient.post(`/preventiva/ordens/${orderId}/materiais`, data);
    return response.data;
  },
  removeMaterial: async (orderId: number, materialId: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/preventiva/ordens/${orderId}/materiais/${materialId}`);
    return response.data;
  },
  uploadPhoto: async (orderId: number, foto: File, tipo?: string, descricao?: string): Promise<MaintenancePhoto> => {
    const formData = new FormData();
    formData.append('foto', foto);
    if (tipo) formData.append('tipo', tipo);
    if (descricao) formData.append('descricao', descricao);
    const response = await apiClient.post(`/preventiva/ordens/${orderId}/fotos`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  deletePhoto: async (orderId: number, photoId: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/preventiva/ordens/${orderId}/fotos/${photoId}`);
    return response.data;
  },

  // Custom types
  listCustomTypes: async (): Promise<CustomMaintenanceType[]> => {
    const response = await apiClient.get('/preventiva/tipos');
    return response.data;
  },

  // Notifications
  myNotifications: async (): Promise<PMNotification[]> => {
    const response = await apiClient.get('/preventiva/notificacoes');
    return response.data;
  },
  markNotificationsRead: async (): Promise<{ message: string }> => {
    const response = await apiClient.post('/preventiva/notificacoes/lidas');
    return response.data;
  },
};
