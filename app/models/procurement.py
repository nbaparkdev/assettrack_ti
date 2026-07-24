# app/models/procurement.py
from sqlalchemy import String, DateTime, Enum as SAEnum, ForeignKey, Numeric, Boolean, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from datetime import datetime
from typing import List, Optional
from app.database import Base
from app.core.datetime_utils import now_sp

class ProductType(str, Enum):
    PRODUTO = "Produto"
    SERVICO = "Serviço"
    LICENCA = "Licença"
    ASSINATURA = "Assinatura"
    EQUIPAMENTO = "Equipamento"
    MATERIAL_CONSUMO = "Material de Consumo"

class PurchaseRequestStatus(str, Enum):
    RASCUNHO = "Rascunho"
    PENDENTE = "Pendente"
    EM_APROVACAO = "Em aprovação"
    APROVADA = "Aprovada"
    REPROVADA = "Reprovada"
    CANCELADA = "Cancelada"
    CONVERTIDA_COTACAO = "Convertida em cotação"
    AGUARDANDO_ORCAMENTO = "Aguardando Liberação de Orçamento"

class PurchaseOrderStatus(str, Enum):
    ABERTO = "Aberto"
    ENVIADO = "Enviado"
    ACEITO = "Aceito"
    EM_TRANSPORTE = "Em transporte"
    RECEBIDO_PARCIAL = "Recebido parcialmente"
    RECEBIDO_TOTAL = "Recebido totalmente"
    CANCELADO = "Cancelado"

class PurchaseCategory(Base):
    __tablename__ = "purchase_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    products = relationship("PurchaseProduct", back_populates="categoria")

class PurchaseUnit(Base):
    __tablename__ = "purchase_units"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sigla: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

class PurchaseProduct(Base):
    __tablename__ = "purchase_products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("purchase_categories.id"), nullable=False)
    unidade: Mapped[str] = mapped_column(String(20), default="UN")
    marca: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    modelo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fabricante: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tipo: Mapped[ProductType] = mapped_column(SAEnum(ProductType), default=ProductType.PRODUTO)
    imagem_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    categoria = relationship("PurchaseCategory", back_populates="products")
    stock = relationship("MaterialStock", back_populates="product", uselist=False)

class CostCenter(Base):
    __tablename__ = "cost_centers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    departamento_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departamentos.id"), nullable=True)
    responsavel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    orcamento_anual: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00)
    orcamento_mensal: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00)
    orcamento_anual_usado: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00)
    orcamento_mensal_usado: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00)
    
    alerta_limite: Mapped[bool] = mapped_column(Boolean, default=True)
    bloquear_limite: Mapped[bool] = mapped_column(Boolean, default=False)

    departamento = relationship("Departamento")
    responsavel = relationship("User")

class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    numero: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    solicitante_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    departamento_id: Mapped[int] = mapped_column(ForeignKey("departamentos.id"), nullable=False)
    centro_custo_id: Mapped[int] = mapped_column(ForeignKey("cost_centers.id"), nullable=False)
    
    justificativa: Mapped[str] = mapped_column(Text, nullable=False)
    urgencia: Mapped[str] = mapped_column(String(20), default="Média") # Baixa, Média, Alta, Urgente
    data_necessaria: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[PurchaseRequestStatus] = mapped_column(SAEnum(PurchaseRequestStatus), default=PurchaseRequestStatus.RASCUNHO, index=True)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
    
    # Integrações
    origem_os_id: Mapped[Optional[int]] = mapped_column(ForeignKey("maintenance_orders.id"), nullable=True)
    origem_ticket_id: Mapped[Optional[int]] = mapped_column(ForeignKey("service_tickets.id"), nullable=True)

    solicitante = relationship("User", foreign_keys=[solicitante_id])
    departamento = relationship("Departamento")
    centro_custo = relationship("CostCenter")
    origem_os = relationship("MaintenanceOrder")
    origem_ticket = relationship("ServiceTicket")
    
    itens = relationship("PurchaseRequestItem", back_populates="request", cascade="all, delete-orphan")
    approvals = relationship("PurchaseApproval", back_populates="request", cascade="all, delete-orphan")

class PurchaseRequestItem(Base):
    __tablename__ = "purchase_request_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("purchase_requests.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("purchase_products.id"), nullable=False)
    quantidade: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    valor_estimado: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    fornecedor_sugerido_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fornecedores.id"), nullable=True)
    observacao: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    request = relationship("PurchaseRequest", back_populates="itens")
    product = relationship("PurchaseProduct")
    fornecedor_sugerido = relationship("Fornecedor")

class PurchaseApproval(Base):
    __tablename__ = "purchase_approvals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("purchase_requests.id"), nullable=False)
    nivel: Mapped[str] = mapped_column(String(50), nullable=False) # Gestor, Gerente, Financeiro, Diretoria, Compras
    aprovador_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Pendente") # Pendente, Aprovado, Reprovado, Ajuste Solicitado
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_decisao: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    request = relationship("PurchaseRequest", back_populates="approvals")
    aprovador = relationship("User")

class PurchaseQuotation(Base):
    __tablename__ = "purchase_quotations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    numero: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    request_id: Mapped[int] = mapped_column(ForeignKey("purchase_requests.id"), nullable=False)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
    status: Mapped[str] = mapped_column(String(20), default="Em cotação") # Em cotação, Finalizada, Cancelada

    request = relationship("PurchaseRequest")
    suppliers = relationship("PurchaseQuotationSupplier", back_populates="quotation", cascade="all, delete-orphan")

class PurchaseQuotationSupplier(Base):
    __tablename__ = "purchase_quotation_suppliers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    quotation_id: Mapped[int] = mapped_column(ForeignKey("purchase_quotations.id"), nullable=False)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedores.id"), nullable=False)
    
    valor_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00)
    frete: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    prazo_entrega_dias: Mapped[int] = mapped_column(Integer, default=0)
    garantia_meses: Mapped[int] = mapped_column(Integer, default=0)
    forma_pagamento: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    escolhido: Mapped[bool] = mapped_column(Boolean, default=False)

    quotation = relationship("PurchaseQuotation", back_populates="suppliers")
    fornecedor = relationship("Fornecedor")
    itens = relationship("PurchaseQuotationItem", back_populates="quotation_supplier", cascade="all, delete-orphan")

class PurchaseQuotationItem(Base):
    __tablename__ = "purchase_quotation_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    quotation_supplier_id: Mapped[int] = mapped_column(ForeignKey("purchase_quotation_suppliers.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("purchase_products.id"), nullable=False)
    quantidade: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    valor_unitario: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    quotation_supplier = relationship("PurchaseQuotationSupplier", back_populates="itens")
    product = relationship("PurchaseProduct")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    numero: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedores.id"), nullable=False)
    centro_custo_id: Mapped[int] = mapped_column(ForeignKey("cost_centers.id"), nullable=False)
    request_id: Mapped[Optional[int]] = mapped_column(ForeignKey("purchase_requests.id"), nullable=True)
    quotation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("purchase_quotations.id"), nullable=True)
    
    valor_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    desconto: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    ipi: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    icms: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    frete: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    
    status: Mapped[PurchaseOrderStatus] = mapped_column(SAEnum(PurchaseOrderStatus), default=PurchaseOrderStatus.ABERTO, index=True)
    data_emissao: Mapped[datetime] = mapped_column(DateTime, default=now_sp)

    fornecedor = relationship("Fornecedor")
    centro_custo = relationship("CostCenter")
    request = relationship("PurchaseRequest")
    quotation = relationship("PurchaseQuotation")
    
    itens = relationship("PurchaseOrderItem", back_populates="order", cascade="all, delete-orphan")
    receivings = relationship("PurchaseReceiving", back_populates="order")

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("purchase_products.id"), nullable=False)
    quantidade: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    valor_unitario: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_item: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    order = relationship("PurchaseOrder", back_populates="itens")
    product = relationship("PurchaseProduct")

class PurchaseReceiving(Base):
    __tablename__ = "purchase_receivings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    data_recebimento: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
    responsavel_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    nota_fiscal_id: Mapped[Optional[int]] = mapped_column(ForeignKey("notas_fiscais.id"), nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    order = relationship("PurchaseOrder", back_populates="receivings")
    responsavel = relationship("User")
    nota_fiscal = relationship("NotaFiscal")
    itens = relationship("PurchaseReceivingItem", back_populates="receiving", cascade="all, delete-orphan")

class PurchaseReceivingItem(Base):
    __tablename__ = "purchase_receiving_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    receiving_id: Mapped[int] = mapped_column(ForeignKey("purchase_receivings.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("purchase_products.id"), nullable=False)
    quantidade_recebida: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    divergencias: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    estoque_atualizado: Mapped[bool] = mapped_column(Boolean, default=False)
    ativo_criado_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assets.id"), nullable=True)

    receiving = relationship("PurchaseReceiving", back_populates="itens")
    product = relationship("PurchaseProduct")
    ativo_criado = relationship("Asset")

class PurchaseContract(Base):
    __tablename__ = "purchase_contracts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedores.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False) # Hardware, Software, cloud, etc.
    numero: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    data_inicio: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_fim: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    renovacao_automatica: Mapped[bool] = mapped_column(Boolean, default=False)
    valor: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    periodicidade: Mapped[str] = mapped_column(String(50), default="Mensal") # Mensal, Anual, etc.
    arquivo_pdf_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    alertado_dias: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    fornecedor = relationship("Fornecedor")

class PurchaseAttachment(Base):
    __tablename__ = "purchase_attachments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tabela_origem: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # purchase_requests, purchase_orders, etc.
    registro_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    arquivo_path: Mapped[str] = mapped_column(String(255), nullable=False)
    nome_original: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo_arquivo: Mapped[str] = mapped_column(String(50), nullable=False) # pdf, xml, png, etc.
    data_envio: Mapped[datetime] = mapped_column(DateTime, default=now_sp)

class PurchaseHistory(Base):
    __tablename__ = "purchase_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tabela_origem: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    registro_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    acao: Mapped[str] = mapped_column(String(100), nullable=False) # Criou, Aprovou, Recebeu, etc.
    data_acao: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user = relationship("User")

class PurchaseNotification(Base):
    __tablename__ = "purchase_notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    lido: Mapped[bool] = mapped_column(Boolean, default=False)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
    link_redirecionamento: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user = relationship("User")

class MaterialStock(Base):
    __tablename__ = "material_stocks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("purchase_products.id"), unique=True, nullable=False)
    quantidade_saldo: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    localizacao_almoxarifado: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    product = relationship("PurchaseProduct", back_populates="stock")

class MaterialStockTransaction(Base):
    __tablename__ = "material_stock_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("purchase_products.id"), nullable=False)
    quantidade: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tipo_movimentacao: Mapped[str] = mapped_column(String(20), nullable=False) # Entrada, Saída
    origem_tabela: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # purchase_receivings, maintenance_execution, etc.
    origem_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    data_transacao: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    justificativa: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    product = relationship("PurchaseProduct")
    user = relationship("User")


class PurchaseResearchStatus(str, Enum):
    RASCUNHO = "Rascunho"
    PENDENTE = "Pendente"
    APROVADA = "Aprovada"
    REPROVADA = "Reprovada"


class PurchaseResearch(Base):
    __tablename__ = "purchase_researches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    numero: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    solicitante_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(100), nullable=False)
    justificativa: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[PurchaseResearchStatus] = mapped_column(SAEnum(PurchaseResearchStatus), default=PurchaseResearchStatus.RASCUNHO, index=True)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=now_sp)

    solicitante = relationship("User")
    items = relationship("PurchaseResearchItem", back_populates="research", cascade="all, delete-orphan")


class PurchaseResearchItem(Base):
    __tablename__ = "purchase_research_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    research_id: Mapped[int] = mapped_column(ForeignKey("purchase_researches.id"), nullable=False)
    nome_produto: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    link_produto: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    imagem_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    valor_estimado: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantidade: Mapped[float] = mapped_column(Numeric(10, 2), default=1.0)
    tipo_produto: Mapped[str] = mapped_column(String(20), default="Consumo") # "Consumo" ou "Imobilizado"
    aprovado: Mapped[bool] = mapped_column(Boolean, default=True)

    research = relationship("PurchaseResearch", back_populates="items")

