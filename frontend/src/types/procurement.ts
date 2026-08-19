export interface PurchaseCategory {
  id: number;
  nome: string;
  descricao?: string;
  ativo: boolean;
}

export interface PurchaseProduct {
  id: number;
  codigo: string;
  nome: string;
  categoria_id: number;
  unidade: string;
  marca?: string;
  modelo?: string;
  fabricante?: string;
  descricao?: string;
  tipo: string;
  imagem_path?: string;
  ativo: boolean;
  categoria?: PurchaseCategory;
}

export interface CostCenter {
  id: number;
  codigo: string;
  nome: string;
  departamento_id?: number;
  responsavel_id?: number;
  orcamento_anual: number;
  orcamento_mensal: number;
  orcamento_anual_usado: number;
  orcamento_mensal_usado: number;
  alerta_limite: boolean;
  bloquear_limite: boolean;
  departamento?: { id: number; nome: string };
  responsavel?: { id: number; nome: string };
}

export interface PurchaseRequestItem {
  id: number;
  request_id: number;
  product_id: number;
  quantidade: number;
  valor_estimado: number;
  fornecedor_sugerido_id?: number;
  observacao?: string;
  product?: PurchaseProduct;
  fornecedor_sugerido?: { id: number; nome: string };
}

export interface PurchaseApproval {
  id: number;
  request_id: number;
  nivel: string;
  aprovador_id?: number;
  status: string;
  observacao?: string;
  data_decisao?: string;
  aprovador?: { id: number; nome: string };
}

export interface PurchaseRequest {
  id: number;
  numero: string;
  solicitante_id: number;
  departamento_id: number;
  centro_custo_id: number;
  justificativa: string;
  urgencia: string;
  data_necessaria?: string;
  status: string;
  data_criacao: string;
  solicitante?: { id: number; nome: string };
  departamento?: { id: number; nome: string };
  centro_custo?: CostCenter;
  itens: PurchaseRequestItem[];
  approvals: PurchaseApproval[];
  valor_estimado_total: number;
  nivel_aprovacao_sugerido: string;
  situacao_orcamento_centro: string;
}

export interface PurchaseQuotationItem {
  id: number;
  quotation_supplier_id: number;
  product_id: number;
  quantidade: number;
  valor_unitario: number;
  product?: PurchaseProduct;
}

export interface PurchaseQuotationSupplier {
  id: number;
  quotation_id: number;
  fornecedor_id: number;
  valor_total: number;
  frete: number;
  prazo_entrega_dias: number;
  garantia_meses: number;
  forma_pagamento?: string;
  observacoes?: string;
  escolhido: boolean;
  fornecedor?: { id: number; nome: string };
  itens: PurchaseQuotationItem[];
}

export interface PurchaseQuotation {
  id: number;
  numero: string;
  request_id: number;
  data_criacao: string;
  status: string;
  request?: PurchaseRequest;
  suppliers: PurchaseQuotationSupplier[];
}

export interface PurchaseOrderItem {
  id: number;
  order_id: number;
  product_id: number;
  quantidade: number;
  valor_unitario: number;
  total_item: number;
  product?: PurchaseProduct;
}

export interface PurchaseOrder {
  id: number;
  numero: string;
  fornecedor_id: number;
  centro_custo_id: number;
  request_id?: number;
  quotation_id?: number;
  valor_total: number;
  desconto: number;
  ipi: number;
  icms: number;
  frete: number;
  status: string;
  data_emissao: string;
  fornecedor?: { id: number; nome: string };
  centro_custo?: CostCenter;
  itens: PurchaseOrderItem[];
  request_valor_estimado_total: number;
  economia_estimada: number;
  prazo_entrega_dias: number;
  sla_status: string;
  data_prevista_entrega?: string;
  ultima_data_recebimento?: string;
}

export interface PurchaseReceivingItem {
  id: number;
  receiving_id: number;
  product_id: number;
  quantidade_recebida: number;
  divergencias?: string;
  estoque_atualizado: boolean;
  ativo_criado_id?: number;
  product?: PurchaseProduct;
}

export interface PurchaseReceiving {
  id: number;
  order_id: number;
  data_recebimento: string;
  responsavel_id: number;
  nota_fiscal_id?: number;
  observacoes?: string;
  responsavel?: { id: number; nome: string };
  itens: PurchaseReceivingItem[];
}

export interface MaterialStock {
  id: number;
  product_id: number;
  quantidade_saldo: number;
  localizacao_almoxarifado?: string;
  product?: PurchaseProduct;
}

export interface MaterialStockTransaction {
  id: number;
  product_id: number;
  quantidade: number;
  tipo_movimentacao: string;
  origem_tabela?: string;
  origem_id?: number;
  data_transacao: string;
  user_id: number;
  justificativa?: string;
  product?: PurchaseProduct;
  user?: { id: number; nome: string };
}

export interface PurchaseContract {
  id: number;
  fornecedor_id: number;
  tipo: string;
  tipo_id?: number;
  numero: string;
  data_inicio: string;
  data_fim: string;
  renovacao_automatica: boolean;
  valor: number;
  periodicidade: string;
  arquivo_pdf_path?: string;
  fornecedor?: { id: number; nome: string };
}

export interface ContractType {
  id: number;
  nome: string;
  descricao?: string;
  ativo: boolean;
}

export interface PurchaseResearchItem {
  id: number;
  research_id: number;
  nome_produto: string;
  link_produto?: string;
  imagem_path?: string;
  valor_estimado: number;
  quantidade: number;
  tipo_produto: string;
  aprovado: boolean;
}

export interface PurchaseResearch {
  id: number;
  numero: string;
  solicitante_id: number;
  titulo: string;
  justificativa: string;
  status: string;
  data_criacao: string;
  solicitante?: { id: number; nome: string };
  items: PurchaseResearchItem[];
}

export interface PurchaseNotification {
  id: number;
  user_id: number;
  mensagem: string;
  lido: boolean;
  data_criacao: string;
  link_redirecionamento?: string;
}

export interface ProcurementDashboard {
  req_pending_count: number;
  orders_active_count: number;
  low_stock_count: number;
  requests_recent: PurchaseRequest[];
  orders_recent: PurchaseOrder[];
  requested_total: number;
  quoted_total: number;
  ordered_total: number;
  estimated_savings_total: number;
  top_suppliers: Array<{
    id: number;
    nome: string;
    total_pedidos: number;
    valor_total: number;
  }>;
  cost_center_reports: Array<{
    id: number;
    codigo: string;
    nome: string;
    orcamento_mensal: number;
    orcamento_usado: number;
    solicitado_pendente: number;
    solicitado_aprovado: number;
    comprado_total: number;
    economia_total: number;
  }>;
  supplier_performance: Array<{
    id: number;
    nome: string;
    total_pedidos: number;
    valor_total: number;
    pedidos_recebidos: number;
    pedidos_ativos: number;
    pedidos_no_prazo: number;
    pedidos_em_atraso: number;
    ticket_medio: number;
    sla_percentual: number;
  }>;
  monthly_budget_total: number;
  monthly_budget_used: number;
  cost_centers_alert: number;
  cost_centers_over_limit: number;
  cost_centers_summary: Array<{
    id: number;
    codigo: string;
    nome: string;
    orcamento_mensal: number;
    orcamento_mensal_usado: number;
    uso_percentual: number;
    status: 'ok' | 'alert' | 'over_limit' | 'no_budget';
  }>;
}

export const PRODUCT_TYPES = ['Produto', 'Serviço', 'Licença', 'Assinatura', 'Equipamento', 'Material de Consumo'];

export const REQUEST_STATUSES = [
  'Rascunho',
  'Pendente',
  'Em aprovação',
  'Aprovada',
  'Reprovada',
  'Cancelada',
  'Convertida em cotação',
  'Aguardando Liberação de Orçamento',
];

export const ORDER_STATUSES = [
  'Aberto',
  'Enviado',
  'Aceito',
  'Em transporte',
  'Recebido parcialmente',
  'Recebido totalmente',
  'Cancelado',
];

export const URGENCIES = ['Baixa', 'Média', 'Alta', 'Urgente'];

export const requestStatusColor: Record<string, string> = {
  'Rascunho': 'text-brand-muted border-brand-border',
  'Pendente': 'text-blue-400 border-blue-500/30',
  'Em aprovação': 'text-yellow-400 border-yellow-500/30',
  'Aprovada': 'text-green-400 border-green-500/30',
  'Reprovada': 'text-red-400 border-red-500/30',
  'Cancelada': 'text-gray-400 border-gray-500/30',
  'Convertida em cotação': 'text-cyan-400 border-cyan-500/30',
  'Aguardando Liberação de Orçamento': 'text-orange-400 border-orange-500/30',
};

export const orderStatusColor: Record<string, string> = {
  'Aberto': 'text-blue-400 border-blue-500/30',
  'Enviado': 'text-cyan-400 border-cyan-500/30',
  'Aceito': 'text-yellow-400 border-yellow-500/30',
  'Em transporte': 'text-purple-400 border-purple-500/30',
  'Recebido parcialmente': 'text-orange-400 border-orange-500/30',
  'Recebido totalmente': 'text-green-400 border-green-500/30',
  'Cancelado': 'text-red-400 border-red-500/30',
};
