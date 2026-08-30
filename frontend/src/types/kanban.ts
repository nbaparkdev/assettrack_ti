export interface KanbanProject {
  id: number;
  titulo: string;
  descricao?: string;
  board_background_color?: string;
  board_pattern?: 'glow' | 'grid' | 'dots' | 'clean';
  related_to_maintenance?: boolean;
  related_to_preventive?: boolean;
  preventive_plan_id?: number;
  preventive_automation_enabled?: boolean;
  preventive_automation_horizon_days?: number;
  preventive_automation_started_at?: string | null;
  preventive_automation_last_run_at?: string | null;
  preventive_automation_next_run_at?: string | null;
  preventive_card_title_template?: string;
  preventive_card_description_template?: string;
  preventive_card_checklist_template?: string;
  preventive_card_priority?: string;
  preventive_card_color?: string;
  criador_id: number;
  is_active: boolean;
  is_archived: boolean;
  favoritado?: boolean;
  created_at: string;
  updated_at: string;
  criador?: { id: number; nome: string };
  preventive_plan?: { id: number; nome: string; codigo: string };
  participantes?: { id: number; nome: string; avatar_url?: string | null }[];
  colunas?: KanbanColumn[];
  cards?: KanbanCard[];
}

export interface KanbanColumn {
  id: number;
  project_id: number;
  nome: string;
  cor: string;
  ordem: number;
  is_default: boolean;
  cards?: KanbanCard[];
}

export interface KanbanChecklistItem {
  id: string;
  titulo: string;
  concluido: boolean;
}

export interface KanbanCard {
  id: number;
  project_id: number;
  column_id: number;
  titulo: string;
  cor?: string;
  descricao?: string;
  checklist_json?: string;
  checklist_items?: KanbanChecklistItem[];
  preventive_order_id?: number;
  criador_id: number;
  responsavel_id?: number;
  prioridade: string;
  data_entrega?: string;
  ordem: number;
  created_at: string;
  updated_at: string;
  purchase_request_id?: number;
  material_stock_id?: number;
  tipo_item_necessario?: string;
  column?: KanbanColumn;
  criador?: { id: number; nome: string; avatar_url?: string | null };
  responsavel?: { id: number; nome: string; avatar_url?: string | null };
  preventive_order?: {
    id: number;
    numero: string;
    status: string;
    prioridade: string;
    tipo: string;
    data_agendada?: string;
    asset?: { id: number; nome: string; e_patrimonio: string };
    tecnico?: { id: number; nome: string };
    plan?: { id: number; nome: string; codigo: string };
  };
  participantes?: { id: number; nome: string; avatar_url?: string | null }[];
  ativos?: { id: number; nome: string }[];
  anexos?: KanbanAttachment[];
  interacoes?: KanbanCardInteraction[];
}

export interface KanbanCardInteraction {
  id: number;
  card_id: number;
  usuario_id: number;
  mensagem: string;
  tipo: string;
  created_at: string;
  usuario?: { id: number; nome: string };
}

export interface KanbanAttachment {
  id: number;
  card_id: number;
  nome: string;
  tipo: string; // imagem, link, arquivo
  url: string;
  criado_em: string;
}

export interface KanbanNotification {
  id: number;
  user_id: number;
  project_id?: number;
  card_id?: number;
  autor_id?: number;
  tipo: string;
  titulo: string;
  mensagem: string;
  link?: string;
  lida: boolean;
  created_at: string;
  autor?: { id: number; nome: string };
}

export const CARD_PRIORITIES = ['baixa', 'media', 'alta', 'urgente'];

export const priorityColor: Record<string, string> = {
  baixa: 'text-brand-muted border-brand-border',
  media: 'text-blue-400 border-blue-500/30',
  alta: 'text-yellow-400 border-yellow-500/30',
  urgente: 'text-red-400 border-red-500/30',
};
