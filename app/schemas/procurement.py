# app/schemas/procurement.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.procurement import (
    ProductType,
    PurchaseOrderStatus,
    PurchaseRequestStatus,
)


# PurchaseCategory
class PurchaseCategoryBase(BaseModel):
    nome: str
    descricao: str | None = None
    ativo: bool = True

class PurchaseCategoryCreate(PurchaseCategoryBase):
    pass

class PurchaseCategoryUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    ativo: bool | None = None

class PurchaseCategoryResponse(PurchaseCategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# PurchaseProduct
class PurchaseProductBase(BaseModel):
    codigo: str
    nome: str
    categoria_id: int
    unidade: str = "UN"
    marca: str | None = None
    modelo: str | None = None
    fabricante: str | None = None
    descricao: str | None = None
    tipo: ProductType = ProductType.PRODUTO
    imagem_path: str | None = None
    ativo: bool = True

class PurchaseProductCreate(PurchaseProductBase):
    pass

class PurchaseProductUpdate(BaseModel):
    codigo: str | None = None
    nome: str | None = None
    categoria_id: int | None = None
    unidade: str | None = None
    marca: str | None = None
    modelo: str | None = None
    fabricante: str | None = None
    descricao: str | None = None
    tipo: ProductType | None = None
    imagem_path: str | None = None
    ativo: bool | None = None

class PurchaseProductResponse(PurchaseProductBase):
    id: int
    categoria: PurchaseCategoryResponse | None = None
    model_config = ConfigDict(from_attributes=True)


# CostCenter
class CostCenterBase(BaseModel):
    codigo: str
    nome: str
    departamento_id: int | None = None
    responsavel_id: int | None = None
    orcamento_anual: float = 0.00
    orcamento_mensal: float = 0.00
    alerta_limite: bool = True
    bloquear_limite: bool = False

class CostCenterCreate(CostCenterBase):
    pass

class CostCenterUpdate(BaseModel):
    codigo: str | None = None
    nome: str | None = None
    departamento_id: int | None = None
    responsavel_id: int | None = None
    orcamento_anual: float | None = None
    orcamento_mensal: float | None = None
    alerta_limite: bool | None = None
    bloquear_limite: bool | None = None

class CostCenterResponse(CostCenterBase):
    id: int
    orcamento_anual_usado: float
    orcamento_mensal_usado: float
    model_config = ConfigDict(from_attributes=True)


# PurchaseRequestItem
class PurchaseRequestItemBase(BaseModel):
    product_id: int
    quantidade: float
    valor_estimado: float
    fornecedor_sugerido_id: int | None = None
    observacao: str | None = None

class PurchaseRequestItemCreate(PurchaseRequestItemBase):
    pass

class PurchaseRequestItemResponse(PurchaseRequestItemBase):
    id: int
    product: PurchaseProductResponse | None = None
    model_config = ConfigDict(from_attributes=True)


# PurchaseRequest
class PurchaseRequestBase(BaseModel):
    centro_custo_id: int
    justificativa: str
    urgencia: str = "Média"
    data_necessaria: datetime | None = None
    origem_os_id: int | None = None
    origem_ticket_id: int | None = None

class PurchaseRequestCreate(PurchaseRequestBase):
    itens: list[PurchaseRequestItemCreate]

class PurchaseRequestUpdate(BaseModel):
    centro_custo_id: int | None = None
    justificativa: str | None = None
    urgencia: str | None = None
    data_necessaria: datetime | None = None
    status: PurchaseRequestStatus | None = None

class PurchaseRequestResponse(BaseModel):
    id: int
    numero: str
    solicitante_id: int
    departamento_id: int
    centro_custo_id: int
    justificativa: str
    urgencia: str
    data_necessaria: datetime | None = None
    status: PurchaseRequestStatus
    data_criacao: datetime
    origem_os_id: int | None = None
    origem_ticket_id: int | None = None
    itens: list[PurchaseRequestItemResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


# PurchaseApproval
class PurchaseApprovalBase(BaseModel):
    nivel: str
    status: str
    observacao: str | None = None

class PurchaseApprovalCreate(PurchaseApprovalBase):
    request_id: int

class PurchaseApprovalResponse(PurchaseApprovalBase):
    id: int
    request_id: int
    aprovador_id: int | None = None
    data_decisao: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


# PurchaseQuotationItem
class PurchaseQuotationItemBase(BaseModel):
    product_id: int
    quantidade: float
    valor_unitario: float

class PurchaseQuotationItemCreate(PurchaseQuotationItemBase):
    pass

class PurchaseQuotationItemResponse(PurchaseQuotationItemBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# PurchaseQuotationSupplier
class PurchaseQuotationSupplierBase(BaseModel):
    fornecedor_id: int
    frete: float = 0.00
    prazo_entrega_dias: int = 0
    garantia_meses: int = 0
    forma_pagamento: str | None = None
    observacoes: str | None = None

class PurchaseQuotationSupplierCreate(PurchaseQuotationSupplierBase):
    itens: list[PurchaseQuotationItemCreate]

class PurchaseQuotationSupplierResponse(PurchaseQuotationSupplierBase):
    id: int
    valor_total: float
    escolhido: bool
    itens: list[PurchaseQuotationItemResponse] = []
    model_config = ConfigDict(from_attributes=True)


# PurchaseQuotation
class PurchaseQuotationBase(BaseModel):
    request_id: int

class PurchaseQuotationCreate(PurchaseQuotationBase):
    suppliers: list[PurchaseQuotationSupplierCreate]

class PurchaseQuotationResponse(BaseModel):
    id: int
    numero: str
    request_id: int
    data_criacao: datetime
    status: str
    suppliers: list[PurchaseQuotationSupplierResponse] = []
    model_config = ConfigDict(from_attributes=True)


# PurchaseOrderItem
class PurchaseOrderItemBase(BaseModel):
    product_id: int
    quantidade: float
    valor_unitario: float

class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass

class PurchaseOrderItemResponse(PurchaseOrderItemBase):
    id: int
    total_item: float
    product: PurchaseProductResponse | None = None
    model_config = ConfigDict(from_attributes=True)


# PurchaseOrder
class PurchaseOrderBase(BaseModel):
    fornecedor_id: int
    centro_custo_id: int
    request_id: int | None = None
    quotation_id: int | None = None
    desconto: float = 0.00
    ipi: float = 0.00
    icms: float = 0.00
    frete: float = 0.00

class PurchaseOrderCreate(PurchaseOrderBase):
    itens: list[PurchaseOrderItemCreate]

class PurchaseOrderResponse(BaseModel):
    id: int
    numero: str
    fornecedor_id: int
    centro_custo_id: int
    request_id: int | None = None
    quotation_id: int | None = None
    valor_total: float
    desconto: float
    ipi: float
    icms: float
    frete: float
    status: PurchaseOrderStatus
    data_emissao: datetime
    itens: list[PurchaseOrderItemResponse] = []
    model_config = ConfigDict(from_attributes=True)


# PurchaseReceivingItem
class PurchaseReceivingItemBase(BaseModel):
    product_id: int
    quantidade_recebida: float
    divergencias: str | None = None
    ativo_criado_id: int | None = None

class PurchaseReceivingItemCreate(PurchaseReceivingItemBase):
    pass

class PurchaseReceivingItemResponse(PurchaseReceivingItemBase):
    id: int
    estoque_atualizado: bool
    model_config = ConfigDict(from_attributes=True)


# PurchaseReceiving
class PurchaseReceivingBase(BaseModel):
    order_id: int
    nota_fiscal_id: int | None = None
    observacoes: str | None = None

class PurchaseReceivingCreate(PurchaseReceivingBase):
    itens: list[PurchaseReceivingItemCreate]

class PurchaseReceivingResponse(PurchaseReceivingBase):
    id: int
    data_recebimento: datetime
    responsavel_id: int
    itens: list[PurchaseReceivingItemResponse] = []
    model_config = ConfigDict(from_attributes=True)


# ContractType
class ContractTypeBase(BaseModel):
    nome: str
    descricao: str | None = None
    ativo: bool = True

class ContractTypeCreate(ContractTypeBase):
    pass

class ContractTypeUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    ativo: bool | None = None

class ContractTypeResponse(ContractTypeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# PurchaseContract
class PurchaseContractBase(BaseModel):
    fornecedor_id: int
    tipo: str
    tipo_id: int | None = None
    numero: str
    data_inicio: datetime
    data_fim: datetime
    renovacao_automatica: bool = False
    valor: float
    periodicidade: str = "Mensal"
    arquivo_pdf_path: str | None = None

class PurchaseContractCreate(PurchaseContractBase):
    pass

class PurchaseContractUpdate(BaseModel):
    fornecedor_id: int | None = None
    tipo: str | None = None
    tipo_id: int | None = None
    numero: str | None = None
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    renovacao_automatica: bool | None = None
    valor: float | None = None
    periodicidade: str | None = None
    arquivo_pdf_path: str | None = None

class PurchaseContractResponse(PurchaseContractBase):
    id: int
    alertado_dias: int | None = None
    model_config = ConfigDict(from_attributes=True)


# MaterialStock
class MaterialStockResponse(BaseModel):
    id: int
    product_id: int
    quantidade_saldo: float
    localizacao_almoxarifado: str | None = None
    product: PurchaseProductResponse | None = None
    model_config = ConfigDict(from_attributes=True)


# MaterialStockTransaction
class MaterialStockTransactionResponse(BaseModel):
    id: int
    product_id: int
    quantidade: float
    tipo_movimentacao: str
    origem_tabela: str | None = None
    origem_id: int | None = None
    data_transacao: datetime
    user_id: int
    justificativa: str | None = None
    model_config = ConfigDict(from_attributes=True)


# PurchaseResearchItem
class PurchaseResearchItemBase(BaseModel):
    nome_produto: str
    link_produto: str | None = None
    imagem_path: str | None = None
    valor_estimado: float
    quantidade: float = 1.0
    tipo_produto: str = "Consumo"  # "Consumo" ou "Imobilizado"
    aprovado: bool = True

class PurchaseResearchItemCreate(PurchaseResearchItemBase):
    pass

class PurchaseResearchItemResponse(PurchaseResearchItemBase):
    id: int
    research_id: int
    model_config = ConfigDict(from_attributes=True)


# PurchaseResearch
class PurchaseResearchBase(BaseModel):
    titulo: str
    justificativa: str

class PurchaseResearchCreate(PurchaseResearchBase):
    items: list[PurchaseResearchItemCreate]

class PurchaseResearchResponse(PurchaseResearchBase):
    id: int
    numero: str
    solicitante_id: int
    status: str
    data_criacao: datetime
    items: list[PurchaseResearchItemResponse] = []
    model_config = ConfigDict(from_attributes=True)

