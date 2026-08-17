import { apiClient as api } from './client';
import type { Webhook, WebhookInput, WebhookLog } from '../types/webhook';

export const webhooksApi = {
  list: async (): Promise<Webhook[]> => {
    const res = await api.get<Webhook[]>('/webhooks');
    return res.data;
  },

  getById: async (id: number): Promise<Webhook> => {
    const res = await api.get<Webhook>(`/webhooks/${id}`);
    return res.data;
  },

  create: async (data: WebhookInput): Promise<Webhook> => {
    const res = await api.post<Webhook>('/webhooks', data);
    return res.data;
  },

  update: async (id: number, data: WebhookInput): Promise<Webhook> => {
    const res = await api.put<Webhook>(`/webhooks/${id}`, data);
    return res.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/webhooks/${id}`);
  },

  test: async (id: number): Promise<{ sucesso: boolean; message: string }> => {
    const res = await api.post<{ sucesso: boolean; message: string }>(`/webhooks/${id}/test`);
    return res.data;
  },

  getLogs: async (id: number): Promise<WebhookLog[]> => {
    const res = await api.get<WebhookLog[]>(`/webhooks/${id}/logs`);
    return res.data;
  },
};

export const WEBHOOK_EVENTS_OPTIONS = [
  "ASSET_CREATED",
  "ASSET_UPDATED",
  "ASSET_DELETED",
  "ASSET_REQUEST_CREATED",
  "ASSET_REQUEST_APPROVED",
  "ASSET_REQUEST_REJECTED",
  "ASSET_REQUEST_DELIVERED",
  "MAINTENANCE_REQUESTED",
  "MAINTENANCE_ACCEPTED",
  "MAINTENANCE_REJECTED",
  "MAINTENANCE_COMPLETED",
  "MAINTENANCE_DELIVERED",
  "PREVENTIVE_PLAN_CREATED",
  "PREVENTIVE_ORDER_CREATED",
  "PREVENTIVE_ORDER_STARTED",
  "PREVENTIVE_ORDER_COMPLETED",
  "PREVENTIVE_ORDER_CANCELLED",
  "TICKET_CREATED",
  "TICKET_UPDATED",
  "TICKET_ASSIGNED",
  "TICKET_RESOLVED",
  "TICKET_CANCELLED",
  "TICKET_INTERACTION_ADDED",
  "EMERGENCY_ALERT_TRIGGERED",
  "KANBAN_CARD_MOVED",
  "PURCHASE_REQUEST_CREATED",
  "PURCHASE_REQUEST_APPROVED",
  "PURCHASE_REQUEST_REJECTED",
  "PURCHASE_QUOTATION_CREATED",
  "PURCHASE_ORDER_CREATED",
  "PURCHASE_ORDER_RECEIVED"
];
