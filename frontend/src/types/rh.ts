import type { Asset } from './asset';
import type { Solicitacao } from './transaction';

export interface TermoResponsabilidade {
  id: number;
  solicitacao_id?: number;
  solicitacao?: Solicitacao;
  asset_id: number;
  asset?: Asset;
  usuario_id: number;
  usuario?: {
    id: number;
    nome: string;
    email: string;
  };
  status: 'Pendente' | 'Assinado' | 'Cancelado' | string;
  conteudo_termo: string;
  data_criacao: string;
  data_assinatura?: string;
}

export interface RHListResponse {
  termos: TermoResponsabilidade[];
  pendentes: Solicitacao[];
}
