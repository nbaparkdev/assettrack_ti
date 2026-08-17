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
  matricula: string | null;
  cargo: string | null;
  departamento_id: number | null;
  departamento: Departamento | null;
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
