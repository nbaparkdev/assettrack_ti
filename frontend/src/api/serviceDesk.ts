import { apiClient } from './client';
import type { ServiceCategory, ServiceDefinition, ServiceTicket, ServiceTicketInteraction } from '../types';

export const serviceDeskApi = {
  // Categories
  listCategories: async (): Promise<ServiceCategory[]> => {
    const response = await apiClient.get<ServiceCategory[]>('/servicos/categorias');
    return response.data;
  },
  createCategory: async (data: Partial<ServiceCategory>): Promise<ServiceCategory> => {
    const response = await apiClient.post<ServiceCategory>('/servicos/categorias', data);
    return response.data;
  },

  // Definitions
  listDefinitions: async (): Promise<ServiceDefinition[]> => {
    const response = await apiClient.get<ServiceDefinition[]>('/servicos/definicoes');
    return response.data;
  },
  createDefinition: async (data: Partial<ServiceDefinition>): Promise<ServiceDefinition> => {
    const response = await apiClient.post<ServiceDefinition>('/servicos/definicoes', data);
    return response.data;
  },

  // Tickets
  listTickets: async (skip = 0, limit = 100): Promise<ServiceTicket[]> => {
    const response = await apiClient.get<ServiceTicket[]>(`/servicos/chamados?skip=${skip}&limit=${limit}`);
    return response.data;
  },
  getTicketById: async (id: number): Promise<ServiceTicket> => {
    const response = await apiClient.get<ServiceTicket>(`/servicos/chamados/${id}`);
    return response.data;
  },
  createTicket: async (data: Partial<ServiceTicket>): Promise<ServiceTicket> => {
    const response = await apiClient.post<ServiceTicket>('/servicos/chamados', data);
    return response.data;
  },
  updateTicket: async (id: number, data: Partial<ServiceTicket>): Promise<ServiceTicket> => {
    const response = await apiClient.put<ServiceTicket>(`/servicos/chamados/${id}`, data);
    return response.data;
  },

  // Interactions / Comments
  createInteraction: async (ticketId: number, message: string): Promise<ServiceTicketInteraction> => {
    const response = await apiClient.post<ServiceTicketInteraction>(`/servicos/chamados/${ticketId}/interacoes`, {
      mensagem: message,
    });
    return response.data;
  },
};
