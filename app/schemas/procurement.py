# app/schemas/procurement.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from app.models.procurement import ProductType, PurchaseRequestStatus, PurchaseOrderStatus

# PurchaseCategory
class PurchaseCategoryBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True

class PurchaseCategoryCreate(PurchaseCategoryBase):
    pass

class PurchaseCategoryUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    ativo: Optional[bool] = None

class PurchaseCategoryResponse(PurchaseCategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# PurchaseProduct
class PurchaseProductBase(BaseModel):
    codigo: str
    nome: str
    categoria_id: int
    unidade: str = "UN"
    marca: Optional[str] = None
    modelo: Optional[str] = None
    fabricante: Optional[str] = None
    descricao: Optional[str] = None
    tipo: ProductType = ProductType.PRODUTO
    imagem_path: Optional[str] = None
    ativo: bool = True

class PurchaseProductCreate(PurchaseProductBase):
    pass

class PurchaseProductUpdate(BaseModel):
    codigo: Optional[str] = None
    nome: Optional[str] = None
    categoria_id: Optional[int] = None
    unidade: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    fabricante: Optional[str] = None
    descricao: Optional[str] = None
    tipo: Optional[ProductType] = None
    imagem_path: Optional[str] = None
    ativo: Optional[bool] = None

class PurchaseProductResponse(PurchaseProductBase):
    id: int
    categoria: Optional[PurchaseCategoryResponse] = None
    model_config = ConfigDict(from_attributes=True)


# CostCenter
class CostCenterBase(BaseModel):
    codigo: str
    nome: str
    departamento_id: Optional[int] = None
    responsavel_id: Optional[int] = None
    orcamento_anual: float = 0.00
    orcamento_mensal: float = 0.00
    alerta_limite: bool = True
    bloquear_limite: bool = False

class CostCenterCreate(CostCenterBase):
    pass

class CostCenterUpdate(BaseModel):
    codigo: Optional[str] = None
    nome: Optional[str] = None
    departamento_id: Optional[int] = None
    responsavel_id: Optional[int] = None
    orcamento_anual: Optional[float] = None
    orcamento_mensal: Optional[float] = None
    alerta_limite: Optional[bool] = None
    bloquear_limite: Optional[bool] = None

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
    fornecedor_sugerido_id: Optional[int] = None
    observacao: Optional[str] = None

class PurchaseRequestItemCreate(PurchaseRequestItemBase):
    pass

class PurchaseRequestItemResponse(PurchaseRequestItemBase):
    id: int
    product: Optional[PurchaseProductResponse] = None
    model_config = ConfigDict(from_attributes=True)


# PurchaseRequest
class PurchaseRequestBase(BaseModel):
    centro_custo_id: int
    justificativa: str
    urgencia: str = "Média"
    data_necessaria: Optional[datetime] = None
    origem_os_id: Optional[int] = None
    origem_ticket_id: Optional[int] = None

class PurchaseRequestCreate(PurchaseRequestBase):
    itens: List[PurchaseRequestItemCreate]

class PurchaseRequestUpdate(BaseModel):
    centro_custo_id: Optional[int] = None
    justificativa: Optional[str] = None
    urgencia: Optional[str] = None
    data_necessaria: Optional[datetime] = None
    status: Optional[PurchaseRequestStatus] = None

class PurchaseRequestResponse(BaseModel):
    id: int
    numero: str
    solicitante_id: int
    departamento_id: int
    centro_custo_id: int
    justificativa: str
    urgencia: str
    data_necessaria: Optional[datetime] = None
    status: PurchaseRequestStatus
    data_criacao: datetime
    origem_os_id: Optional[int] = None
    origem_ticket_id: Optional[int] = None
    itens: List[PurchaseRequestItemResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


# PurchaseApproval
class PurchaseApprovalBase(BaseModel):
    nivel: str
    status: str
    observacao: Optional[str] = None

class PurchaseApprovalCreate(PurchaseApprovalBase):
    request_id: int

class PurchaseApprovalResponse(PurchaseApprovalBase):
    id: int
    request_id: int
    aprovador_id: Optional[int] = None
    data_decisao: Optional[datetime] = None
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
    forma_pagamento: Optional[str] = None
    observacoes: Optional[str] = None

class PurchaseQuotationSupplierCreate(PurchaseQuotationSupplierBase):
    itens: List[PurchaseQuotationItemCreate]

class PurchaseQuotationSupplierResponse(PurchaseQuotationSupplierBase):
    id: int
    valor_total: float
    escolhido: bool
    itens: List[PurchaseQuotationItemResponse] = []
    model_config = ConfigDict(from_attributes=True)


# PurchaseQuotation
class PurchaseQuotationBase(BaseModel):
    request_id: int

class PurchaseQuotationCreate(PurchaseQuotationBase):
    suppliers: List[PurchaseQuotationSupplierCreate]

class PurchaseQuotationResponse(BaseModel):
    id: int
    numero: str
    request_id: int
    data_criacao: datetime
    status: str
    suppliers: List[PurchaseQuotationSupplierResponse] = []
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
    product: Optional[PurchaseProductResponse] = None
    model_config = ConfigDict(from_attributes=True)


# PurchaseOrder
class PurchaseOrderBase(BaseModel):
    fornecedor_id: int
    centro_custo_id: int
    request_id: Optional[int] = None
    quotation_id: Optional[int] = None
    desconto: float = 0.00
    ipi: float = 0.00
    icms: float = 0.00
    frete: float = 0.00

class PurchaseOrderCreate(PurchaseOrderBase):
    itens: List[PurchaseOrderItemCreate]

class PurchaseOrderResponse(BaseModel):
    id: int
    numero: str
    fornecedor_id: int
    centro_custo_id: int
    request_id: Optional[int] = None
    quotation_id: Optional[int] = None
    valor_total: float
    desconto: float
    ipi: float
    icms: float
    frete: float
    status: PurchaseOrderStatus
    data_emissao: datetime
    itens: List[PurchaseOrderItemResponse] = []
    model_config = ConfigDict(from_attributes=True)


# PurchaseReceivingItem
class PurchaseReceivingItemBase(BaseModel):
    product_id: int
    quantidade_recebida: float
    divergencias: Optional[str] = None
    ativo_criado_id: Optional[int] = None

class PurchaseReceivingItemCreate(PurchaseReceivingItemBase):
    pass

class PurchaseReceivingItemResponse(PurchaseReceivingItemBase):
    id: int
    estoque_atualizado: bool
    model_config = ConfigDict(from_attributes=True)


# PurchaseReceiving
class PurchaseReceivingBase(BaseModel):
    order_id: int
    nota_fiscal_id: Optional[int] = None
    observacoes: Optional[str] = None

class PurchaseReceivingCreate(PurchaseReceivingBase):
    itens: List[PurchaseReceivingItemCreate]

class PurchaseReceivingResponse(PurchaseReceivingBase):
    id: int
    data_recebimento: datetime
    responsavel_id: int
    itens: List[PurchaseReceivingItemResponse] = []
    model_config = ConfigDict(from_attributes=True)


# PurchaseContract
class PurchaseContractBase(BaseModel):
    fornecedor_id: int
    tipo: str
    numero: str
    data_inicio: datetime
    data_fim: datetime
    renovacao_automatica: bool = False
    valor: float
    periodicidade: str = "Mensal"
    arquivo_pdf_path: Optional[str] = None

class PurchaseContractCreate(PurchaseContractBase):
    pass

class PurchaseContractUpdate(BaseModel):
    fornecedor_id: Optional[int] = None
    tipo: Optional[str] = None
    numero: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    renovacao_automatica: Optional[bool] = None
    valor: Optional[float] = None
    periodicidade: Optional[str] = None
    arquivo_pdf_path: Optional[str] = None

class PurchaseContractResponse(PurchaseContractBase):
    id: int
    alertado_dias: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


# MaterialStock
class MaterialStockResponse(BaseModel):
    id: int
    product_id: int
    quantidade_saldo: float
    localizacao_almoxarifado: Optional[str] = None
    product: Optional[PurchaseProductResponse] = None
    model_config = ConfigDict(from_attributes=True)


# MaterialStockTransaction
class MaterialStockTransactionResponse(BaseModel):
    id: int
    product_id: int
    quantidade: float
    tipo_movimentacao: str
    origem_tabela: Optional[str] = None
    origem_id: Optional[int] = None
    data_transacao: datetime
    user_id: int
    justificativa: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# PurchaseResearchItem
class PurchaseResearchItemBase(BaseModel):
    nome_produto: str
    link_produto: Optional[str] = None
    imagem_path: Optional[str] = None
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
    items: List[PurchaseResearchItemCreate]

class PurchaseResearchResponse(PurchaseResearchBase):
    id: int
    numero: str
    solicitante_id: int
    status: str
    data_criacao: datetime
    items: List[PurchaseResearchItemResponse] = []
    model_config = ConfigDict(from_attributes=True)

