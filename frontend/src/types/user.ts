export type UserRole =
  | 'admin'
  | 'gerente_ti'
  | 'tecnico'
  | 'gerente_infra'
  | 'comprador'
  | 'usuario_comum'
  | 'rh';

export interface Departamento {
  id: number;
  nome: string;
}

export interface User {
  id: number;
  email: string;
  nome: string;
  role: UserRole;
  is_active: boolean;
  has_rh_management?: boolean;
  show_on_monitoring?: boolean;
  matricula: string | null;
  cargo: string | null;
  departamento_id: number | null;
  gestor_id?: number | null;
  gestor?: { id: number; nome: string } | null;
  departamento: Departamento | null;
  localizacao_id: number | null;
  localizacao: { id: number; nome: string } | null;
  avatar_url?: string | null;
}

export interface QRTokenInfo {
  qr_code_base64: string;
  qr_token: string;
  created_at: string | null;
  has_pin: boolean;
}

export interface BadgeInfo {
  id: number;
  nome: string;
  email: string;
  matricula: string | null;
  cargo: string | null;
  departamento_nome: string | null;
  avatar_url: string | null;
  qr_code_base64: string;
}

export interface PendingDeliveryItem {
  id: number;
  tipo: string;
  asset_tag: string;
  asset_nome: string;
  data_solicitacao: string;
  status: string;
}

export interface UserPublicProfile {
  id: number;
  nome: string;
  email: string;
  matricula: string | null;
  cargo: string | null;
  departamento_nome: string | null;
  avatar_url: string | null;
  pending_deliveries: PendingDeliveryItem[];
}

export interface UserHistoryEvent {
  categoria: string;
  tipo: string;
  titulo: string;
  status?: string;
  data: string;
  referencia?: string;
  ativo?: string;
  detalhes?: string;
}

export interface UserHistoryReport {
  usuario: User;
  qr_code_base64: string;
  ativos: Array<{
    id: number;
    nome: string;
    e_patrimonio: string;
    status: string;
    numero_serie: string | null;
  }>;
  eventos: UserHistoryEvent[];
  resumo: Record<string, number>;
}
