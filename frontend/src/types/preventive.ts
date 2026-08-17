export interface MaintenancePlan {
  id: number;
  nome: string;
  codigo: string;
  descricao?: string;
  tipo: string;
  periodicidade: string;
  dias_personalizado?: number;
  tempo_estimado_horas?: number;
  criticidade: string;
  prioridade: string;
  ativo: boolean;
  responsavel_id?: number;
  departamento_id?: number;
  categoria_id?: number;
  data_criacao: string;
  data_ultima_execucao?: string;
  proxima_execucao: string;
  responsavel?: { id: number; nome: string };
  categoria?: { id: number; nome: string };
  assets?: MaintenancePlanAsset[];
  checklists?: MaintenanceChecklist[];
}

export interface MaintenancePlanAsset {
  id: number;
  plan_id: number;
  asset_id: number;
  asset?: { id: number; nome: string; e_patrimonio: string };
}

export interface MaintenanceChecklist {
  id: number;
  plan_id: number;
  nome: string;
  ordem: number;
  items: MaintenanceChecklistItem[];
}

export interface MaintenanceChecklistItem {
  id: number;
  checklist_id: number;
  descricao: string;
  obrigatorio: boolean;
  ordem: number;
  requer_foto: boolean;
}

export interface MaintenanceOrder {
  id: number;
  numero: string;
  plan_id?: number;
  asset_id?: number;
  infra_predial_servico?: string;
  tecnico_id?: number;
  solicitante_id?: number;
  status: string;
  prioridade: string;
  criticidade: string;
  tipo: string;
  data_abertura: string;
  data_agendada?: string;
  data_inicio?: string;
  data_pausa?: string;
  data_conclusao?: string;
  tempo_total_minutos?: number;
  observacoes?: string;
  solucao?: string;
  custo_total?: number;
  asset?: { id: number; nome: string; e_patrimonio: string };
  tecnico?: { id: number; nome: string };
  plan?: { id: number; nome: string; codigo: string };
  executions: MaintenanceExecution[];
  materials: MaintenanceMaterial[];
  photos: MaintenancePhoto[];
  history: MaintenanceHistory[];
}

export interface MaintenanceExecution {
  id: number;
  order_id: number;
  checklist_item_id: number;
  concluido: boolean;
  observacao?: string;
  data_execucao?: string;
  executado_por_id?: number;
  checklist_item?: MaintenanceChecklistItem;
  executado_por?: { id: number; nome: string };
}

export interface MaintenanceMaterial {
  id: number;
  order_id: number;
  produto: string;
  quantidade: number;
  valor_unitario: number;
  valor_total: number;
  observacao?: string;
}

export interface MaintenancePhoto {
  id: number;
  order_id: number;
  execution_id?: number;
  tipo: string;
  caminho_arquivo: string;
  descricao?: string;
  data_upload: string;
  upload_por_id?: number;
}

export interface MaintenanceHistory {
  id: number;
  order_id: number;
  acao: string;
  descricao: string;
  usuario_id?: number;
  data_hora: string;
  status_anterior?: string;
  status_novo?: string;
  usuario?: { id: number; nome: string };
}

export interface CustomMaintenanceType {
  id: number;
  nome: string;
  descricao?: string;
  criado_em: string;
}

export interface PMNotification {
  id: number;
  order_id?: number;
  plan_id?: number;
  usuario_id: number;
  tipo: string;
  mensagem: string;
  lida: boolean;
  data_criacao: string;
}

export interface PMDashboard {
  total_plans: number;
  active_plans: number;
  plans_due: number;
  total_orders: number;
  open_orders: number;
  due_soon: number;
  orders_by_status: Record<string, number>;
}

export const PM_STATUSES = ['Aberta', 'Agendada', 'Em andamento', 'Aguardando peça', 'Pausada', 'Concluída', 'Cancelada'];
export const PM_TYPES = ['Preventiva', 'Preditiva', 'Inspeção', 'Calibração', 'Lubrificação', 'Limpeza', 'Atualização', 'Corretiva', 'Personalizada'];
export const PM_PERIODICITIES = ['Diária', 'Semanal', 'Quinzenal', 'Mensal', 'Bimestral', 'Trimestral', 'Semestral', 'Anual', 'Personalizada'];
export const PM_PRIORITIES = ['Baixa', 'Média', 'Alta', 'Urgente'];
export const PM_CRITICALITIES = ['Baixa', 'Média', 'Alta', 'Crítica'];
