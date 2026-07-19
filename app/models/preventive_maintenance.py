
from sqlalchemy import String, DateTime, Enum as SAEnum, ForeignKey, Text, Numeric, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from datetime import datetime
from typing import List, Optional
from app.database import Base
from app.core.datetime_utils import now_sp
from app.models.procurement import PurchaseProduct


class MaintenanceType(str, Enum):
    PREVENTIVA = "Preventiva"
    PREDITIVA = "Preditiva"
    INSPECAO = "Inspeção"
    CALIBRACAO = "Calibração"
    LUBRIFICACAO = "Lubrificação"
    LIMPEZA = "Limpeza"
    ATUALIZACAO = "Atualização"
    CORRETIVA = "Corretiva"
    PERSONALIZADA = "Personalizada"


class MaintenancePeriodicity(str, Enum):
    DIARIA = "Diária"
    SEMANAL = "Semanal"
    QUINZENAL = "Quinzenal"
    MENSAL = "Mensal"
    BIMESTRAL = "Bimestral"
    TRIMESTRAL = "Trimestral"
    SEMESTRAL = "Semestral"
    ANUAL = "Anual"
    PERSONALIZADA = "Personalizada"


class MaintenancePriority(str, Enum):
    BAIXA = "Baixa"
    MEDIA = "Média"
    ALTA = "Alta"
    URGENTE = "Urgente"


class MaintenanceCriticality(str, Enum):
    BAIXA = "Baixa"
    MEDIA = "Média"
    ALTA = "Alta"
    CRITICA = "Crítica"


class OrderStatus(str, Enum):
    ABERTA = "Aberta"
    AGENDADA = "Agendada"
    EM_ANDAMENTO = "Em andamento"
    AGUARDANDO_PECA = "Aguardando peça"
    PAUSADA = "Pausada"
    CONCLUIDA = "Concluída"
    CANCELADA = "Cancelada"


class PhotoType(str, Enum):
    ANTES = "Antes"
    DURANTE = "Durante"
    DEPOIS = "Depois"


class MaintenancePlan(Base):
    __tablename__ = "maintenance_plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tipo: Mapped[MaintenanceType] = mapped_column(SAEnum(MaintenanceType), default=MaintenanceType.PREVENTIVA)
    periodicidade: Mapped[MaintenancePeriodicity] = mapped_column(SAEnum(MaintenancePeriodicity), default=MaintenancePeriodicity.MENSAL)
    dias_personalizado: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tempo_estimado_horas: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    criticidade: Mapped[MaintenanceCriticality] = mapped_column(SAEnum(MaintenanceCriticality), default=MaintenanceCriticality.MEDIA)
    prioridade: Mapped[MaintenancePriority] = mapped_column(SAEnum(MaintenancePriority), default=MaintenancePriority.MEDIA)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Responsável
    responsavel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Setor
    departamento_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departamentos.id"), nullable=True)
    
    # Categoria (para aplicar a todos os ativos de uma categoria)
    categoria_id: Mapped[Optional[int]] = mapped_column(ForeignKey("asset_categories.id"), nullable=True)
    
    # Datas
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
    data_ultima_execucao: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    proxima_execucao: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Relacionamentos
    responsavel = relationship("User")
    departamento = relationship("Departamento")
    categoria = relationship("AssetCategory")
    assets = relationship("MaintenancePlanAsset", back_populates="plan", cascade="all, delete-orphan")
    checklists = relationship("MaintenanceChecklist", back_populates="plan", cascade="all, delete-orphan")
    orders = relationship("MaintenanceOrder", back_populates="plan", cascade="all, delete-orphan")
    notifications = relationship("MaintenanceNotification", back_populates="plan", cascade="all, delete-orphan")


class MaintenancePlanAsset(Base):
    __tablename__ = "maintenance_plan_assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("maintenance_plans.id"), nullable=False)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    
    # Relacionamentos
    plan = relationship("MaintenancePlan", back_populates="assets")
    asset = relationship("Asset")


class MaintenanceChecklist(Base):
    __tablename__ = "maintenance_checklists"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("maintenance_plans.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relacionamentos
    plan = relationship("MaintenancePlan", back_populates="checklists")
    items = relationship("MaintenanceChecklistItem", back_populates="checklist", cascade="all, delete-orphan")


class MaintenanceChecklistItem(Base):
    __tablename__ = "maintenance_checklist_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    checklist_id: Mapped[int] = mapped_column(ForeignKey("maintenance_checklists.id"), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    obrigatorio: Mapped[bool] = mapped_column(Boolean, default=True)
    ordem: Mapped[int] = mapped_column(Integer, default=0)
    requer_foto: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relacionamentos
    checklist = relationship("MaintenanceChecklist", back_populates="items")


class MaintenanceOrder(Base):
    __tablename__ = "maintenance_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    numero: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    plan_id: Mapped[Optional[int]] = mapped_column(ForeignKey("maintenance_plans.id"), nullable=True)
    asset_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assets.id"), nullable=True)
    infra_predial_servico: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Responsáveis
    tecnico_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    solicitante_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Dados da ordem
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus), default=OrderStatus.ABERTA)
    prioridade: Mapped[MaintenancePriority] = mapped_column(SAEnum(MaintenancePriority), default=MaintenancePriority.MEDIA)
    criticidade: Mapped[MaintenanceCriticality] = mapped_column(SAEnum(MaintenanceCriticality), default=MaintenanceCriticality.MEDIA)
    tipo: Mapped[MaintenanceType] = mapped_column(SAEnum(MaintenanceType), default=MaintenanceType.PREVENTIVA)
    
    # Datas e horários
    data_abertura: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
    data_agendada: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    data_inicio: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    data_pausa: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    data_conclusao: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    tempo_total_minutos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Observações
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    solucao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Custos
    custo_total: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True, default=0.0)
    
    # Relacionamentos com Service Desk
    service_ticket_id: Mapped[Optional[int]] = mapped_column(ForeignKey("service_tickets.id"), nullable=True)
    
    # Relacionamentos
    plan = relationship("MaintenancePlan", back_populates="orders")
    asset = relationship("Asset")
    tecnico = relationship("User", foreign_keys=[tecnico_id])
    solicitante = relationship("User", foreign_keys=[solicitante_id])
    service_ticket = relationship("ServiceTicket")
    executions = relationship("MaintenanceExecution", back_populates="order", cascade="all, delete-orphan")
    materials = relationship("MaintenanceMaterial", back_populates="order", cascade="all, delete-orphan")
    photos = relationship("MaintenancePhoto", back_populates="order", cascade="all, delete-orphan")
    history = relationship("MaintenanceHistory", back_populates="order", cascade="all, delete-orphan")
    notifications = relationship("MaintenanceNotification", back_populates="order", cascade="all, delete-orphan")

    @property
    def display_tipo(self) -> str:
        if self.tipo.value == "personalizada" and self.observacoes and self.observacoes.startswith("[TIPO: "):
            import re
            match = re.match(r'^\[TIPO: ([^\]]+)\]', self.observacoes)
            if match:
                return match.group(1)
        return self.tipo.value


class MaintenanceExecution(Base):
    __tablename__ = "maintenance_executions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("maintenance_orders.id"), nullable=False)
    checklist_item_id: Mapped[int] = mapped_column(ForeignKey("maintenance_checklist_items.id"), nullable=False)
    concluido: Mapped[bool] = mapped_column(Boolean, default=False)
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_execucao: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    executado_por_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Relacionamentos
    order = relationship("MaintenanceOrder", back_populates="executions")
    checklist_item = relationship("MaintenanceChecklistItem")
    executado_por = relationship("User")


class MaintenanceMaterial(Base):
    __tablename__ = "maintenance_materials"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("maintenance_orders.id"), nullable=False)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("purchase_products.id"), nullable=True)
    produto: Mapped[str] = mapped_column(String(200), nullable=False)
    quantidade: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    valor_unitario: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    valor_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relacionamentos
    order = relationship("MaintenanceOrder", back_populates="materials")
    product = relationship("PurchaseProduct")


class MaintenancePhoto(Base):
    __tablename__ = "maintenance_photos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("maintenance_orders.id"), nullable=False)
    execution_id: Mapped[Optional[int]] = mapped_column(ForeignKey("maintenance_executions.id"), nullable=True)
    tipo: Mapped[PhotoType] = mapped_column(SAEnum(PhotoType), default=PhotoType.DURANTE)
    caminho_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_upload: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
    upload_por_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Relacionamentos
    order = relationship("MaintenanceOrder", back_populates="photos")
    execution = relationship("MaintenanceExecution")
    upload_por = relationship("User")


class MaintenanceHistory(Base):
    __tablename__ = "maintenance_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("maintenance_orders.id"), nullable=False)
    acao: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    usuario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    data_hora: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
    status_anterior: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status_novo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Relacionamentos
    order = relationship("MaintenanceOrder", back_populates="history")
    usuario = relationship("User")


class MaintenanceNotification(Base):
    __tablename__ = "maintenance_notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("maintenance_orders.id", ondelete="CASCADE"), nullable=True)
    plan_id: Mapped[Optional[int]] = mapped_column(ForeignKey("maintenance_plans.id", ondelete="CASCADE"), nullable=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    lida: Mapped[bool] = mapped_column(Boolean, default=False)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
    
    # Relacionamentos
    order = relationship("MaintenanceOrder", back_populates="notifications")
    plan = relationship("MaintenancePlan", back_populates="notifications")
    usuario = relationship("User")


class CustomMaintenanceType(Base):
    """Tipos de manutenção customizados (além dos tipos fixos do Enum MaintenanceType)."""
    __tablename__ = "custom_maintenance_types"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
