export interface ServiceCategory {
  id: number;
  nome: string;
  descricao?: string;
}

export interface ServiceDefinition {
  id: number;
  nome: string;
  descricao?: string;
  categoria_id: number;
  categoria?: ServiceCategory;
}

export interface ServiceTicketInteraction {
  id: number;
  chamado_id: number;
  user_id: number;
  user?: {
    id: number;
    nome: string;
    email: string;
  };
  mensagem: string;
  data_criacao: string;
}

export interface ServiceTicket {
  id: number;
  codigo: string;
  titulo: string;
  descricao: string;
  prioridade: 'baixa' | 'media' | 'alta' | 'urgente';
  status: 'aberto' | 'em_atendimento' | 'resolvido' | 'fechado';
  solicitante_id: number;
  solicitante?: {
    id: number;
    nome: string;
    email: string;
  };
  responsavel_id?: number;
  responsavel?: {
    id: number;
    nome: string;
    email: string;
  };
  servico_id: number;
  servico?: ServiceDefinition;
  data_abertura: string;
  data_fechamento?: string;
  nota_resolucao?: string;
  nota_feedback?: number;
  comentario_feedback?: string;
  interacoes?: ServiceTicketInteraction[];
}
