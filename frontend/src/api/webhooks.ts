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

export type WebhookEventOption = {
  code: string;
  label: string;
  description: string;
};

export type WebhookEventCategory = {
  title: string;
  description: string;
  events: WebhookEventOption[];
};

export const WEBHOOK_EVENT_CATEGORIES: WebhookEventCategory[] = [
  {
    title: 'Ativos e empréstimos',
    description: 'Alterações no inventário e solicitações de equipamentos.',
    events: [
      { code: 'ASSET_CREATED', label: 'Ativo cadastrado', description: 'Um novo ativo foi incluído no inventário.' },
      { code: 'ASSET_UPDATED', label: 'Ativo atualizado', description: 'Dados, posse, localização ou status foram alterados.' },
      { code: 'ASSET_DELETED', label: 'Ativo excluído', description: 'Um ativo foi removido do inventário.' },
      { code: 'ASSET_REQUEST_CREATED', label: 'Solicitação de ativo criada', description: 'Um usuário solicitou um equipamento.' },
      { code: 'ASSET_REQUEST_APPROVED', label: 'Solicitação de ativo aprovada', description: 'A solicitação foi aprovada.' },
      { code: 'ASSET_REQUEST_REJECTED', label: 'Solicitação de ativo recusada', description: 'A solicitação foi recusada.' },
      { code: 'ASSET_REQUEST_DELIVERED', label: 'Ativo entregue', description: 'O equipamento foi entregue ao solicitante.' },
    ],
  },
  {
    title: 'Chamados e atendimento',
    description: 'Abertura, acompanhamento e encerramento de chamados.',
    events: [
      { code: 'TICKET_CREATED', label: 'Chamado aberto', description: 'Um novo chamado foi registrado.' },
      { code: 'TICKET_UPDATED', label: 'Chamado atualizado', description: 'Os dados ou status do chamado foram alterados.' },
      { code: 'TICKET_ASSIGNED', label: 'Técnico atribuído ao chamado', description: 'Um responsável foi definido para o atendimento.' },
      { code: 'TICKET_RESOLVED', label: 'Chamado resolvido', description: 'A solução foi informada pela equipe.' },
      { code: 'TICKET_CANCELLED', label: 'Chamado cancelado', description: 'O chamado foi cancelado.' },
      { code: 'TICKET_INTERACTION_ADDED', label: 'Nova interação no chamado', description: 'Foi adicionada uma mensagem ou atualização.' },
    ],
  },
  {
    title: 'Manutenção corretiva',
    description: 'Solicitações de reparo e entrega de ativos após manutenção.',
    events: [
      { code: 'MAINTENANCE_REQUESTED', label: 'Manutenção solicitada', description: 'Foi solicitado reparo para um ativo.' },
      { code: 'MAINTENANCE_ACCEPTED', label: 'Manutenção aceita', description: 'Um técnico assumiu a solicitação.' },
      { code: 'MAINTENANCE_REJECTED', label: 'Manutenção recusada', description: 'A solicitação de manutenção foi recusada.' },
      { code: 'MAINTENANCE_COMPLETED', label: 'Manutenção concluída', description: 'O reparo foi finalizado.' },
      { code: 'MAINTENANCE_DELIVERED', label: 'Ativo devolvido após manutenção', description: 'O ativo foi entregue ao solicitante.' },
    ],
  },
  {
    title: 'Manutenção preventiva',
    description: 'Planos e ordens de serviço preventivas.',
    events: [
      { code: 'PREVENTIVE_PLAN_CREATED', label: 'Plano preventivo criado', description: 'Um novo plano de manutenção foi cadastrado.' },
      { code: 'PREVENTIVE_ORDER_CREATED', label: 'Ordem preventiva criada', description: 'Uma ordem de serviço preventiva foi gerada.' },
      { code: 'PREVENTIVE_ORDER_STARTED', label: 'Ordem preventiva iniciada', description: 'O atendimento preventivo foi iniciado.' },
      { code: 'PREVENTIVE_ORDER_COMPLETED', label: 'Ordem preventiva concluída', description: 'A ordem de serviço foi concluída.' },
      { code: 'PREVENTIVE_ORDER_CANCELLED', label: 'Ordem preventiva cancelada', description: 'A ordem de serviço foi cancelada.' },
    ],
  },
  {
    title: 'Compras e suprimentos',
    description: 'Solicitações, cotações, pedidos e recebimentos.',
    events: [
      { code: 'PURCHASE_REQUEST_CREATED', label: 'Solicitação de compra criada', description: 'Uma nova solicitação de compra foi registrada.' },
      { code: 'PURCHASE_REQUEST_APPROVED', label: 'Solicitação de compra aprovada', description: 'Uma solicitação de compra foi aprovada.' },
      { code: 'PURCHASE_REQUEST_REJECTED', label: 'Solicitação de compra recusada', description: 'Uma solicitação de compra foi recusada.' },
      { code: 'PURCHASE_QUOTATION_CREATED', label: 'Cotação criada', description: 'Uma cotação foi cadastrada.' },
      { code: 'PURCHASE_ORDER_CREATED', label: 'Pedido de compra criado', description: 'Uma ordem de compra foi emitida.' },
      { code: 'PURCHASE_ORDER_RECEIVED', label: 'Pedido de compra recebido', description: 'O recebimento de um pedido foi registrado.' },
    ],
  },
  {
    title: 'Kanban e alertas',
    description: 'Movimentações de cartões e incidentes críticos.',
    events: [
      { code: 'KANBAN_CARD_MOVED', label: 'Cartão movido no Kanban', description: 'Um cartão mudou de coluna.' },
      { code: 'EMERGENCY_ALERT_TRIGGERED', label: 'Alerta emergencial acionado', description: 'Um usuário disparou um alerta de emergência.' },
    ],
  },
];

export const WEBHOOK_EVENTS_OPTIONS = WEBHOOK_EVENT_CATEGORIES.flatMap((category) => category.events.map((event) => event.code));

export const getWebhookEventLabel = (code: string) =>
  WEBHOOK_EVENT_CATEGORIES.flatMap((category) => category.events).find((event) => event.code === code)?.label || code;
