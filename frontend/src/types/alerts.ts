export interface EmergencyAlert {
  id: number;
  usuario_id: number;
  usuario_nome: string;
  setor_nome?: string;
  ativo_nome?: string;
  motivo: string;
  atendido: boolean;
  atendido_por_id?: number;
  created_at: string;
  atendido_por?: { id: number; nome: string };
}

export interface Aviso {
  id: number;
  titulo: string;
  texto?: string;
  midia_url?: string;
  midia_tipo?: string; // imagem | video
  link_url?: string;
  link_texto?: string;
  ativo: boolean;
  programado_inicio?: string;
  programado_fim?: string;
  data_cadastro: string;
}
