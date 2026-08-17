export interface Fornecedor {
  id: number;
  nome: string;
  razao_social?: string;
  cnpj?: string;
  email?: string;
  telefone?: string;
  endereco?: string;
  cidade?: string;
  estado?: string;
  tipo_fornecedor?: string;
}

export interface NotaFiscalItem {
  codigo?: string;
  descricao?: string;
  ncm?: string;
  quantidade?: number | null;
  valor_unitario?: number | null;
  valor_total?: number | null;
}

export interface NotaFiscal {
  id: number;
  fornecedor_id: number;
  numero_nota: string;
  data_emissao?: string | null;
  natureza_operacao?: string;
  valor_total?: number | null;
  emitente_nome?: string;
  destinatario_nome?: string;
  itens: NotaFiscalItem[];
}

export interface XMLParsedSupplier {
  nome?: string;
  cnpj?: string;
  endereco?: string;
  cidade?: string;
  estado?: string;
  telefone?: string;
  razao_social?: string;
}
