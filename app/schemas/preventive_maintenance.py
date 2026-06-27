
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.preventive_maintenance import (
    MaintenanceType,
    MaintenancePeriodicity,
    MaintenancePriority,
    MaintenanceCriticality,
    OrderStatus,
    PhotoType
)
from app.schemas.user import UserResponse
from app.schemas.location import Departamento
from app.schemas.asset_category import AssetCategoryResponse
from app.schemas.asset import AssetResponse


# ============== Maintenance Checklist Item ==============
class MaintenanceChecklistItemBase(BaseModel):
    descricao: str
    obrigatorio: bool = True
    ordem: int = 0
    requer_foto: bool = False


class MaintenanceChecklistItemCreate(MaintenanceChecklistItemBase):
    checklist_id: int


class MaintenanceChecklistItemUpdate(BaseModel):
    descricao: Optional[str] = None
    obrigatorio: Optional[bool] = None
    ordem: Optional[int] = None
    requer_foto: Optional[bool] = None


class MaintenanceChecklistItemResponse(MaintenanceChecklistItemBase):
    id: int
    checklist_id: int

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Checklist ==============
class MaintenanceChecklistBase(BaseModel):
    nome: str
    ordem: int = 0


class MaintenanceChecklistCreate(MaintenanceChecklistBase):
    plan_id: int
    items: Optional[List[MaintenanceChecklistItemCreate]] = None


class MaintenanceChecklistUpdate(BaseModel):
    nome: Optional[str] = None
    ordem: Optional[int] = None


class MaintenanceChecklistResponse(MaintenanceChecklistBase):
    id: int
    plan_id: int
    items: Optional[List[MaintenanceChecklistItemResponse]] = None

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Plan Asset ==============
class MaintenancePlanAssetBase(BaseModel):
    plan_id: int
    asset_id: int


class MaintenancePlanAssetCreate(MaintenancePlanAssetBase):
    pass


class MaintenancePlanAssetUpdate(BaseModel):
    plan_id: Optional[int] = None
    asset_id: Optional[int] = None


class MaintenancePlanAssetResponse(MaintenancePlanAssetBase):
    id: int
    asset: Optional[AssetResponse] = None

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Plan ==============
class MaintenancePlanBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    tipo: MaintenanceType = MaintenanceType.PREVENTIVA
    periodicidade: MaintenancePeriodicity = MaintenancePeriodicity.MENSAL
    dias_personalizado: Optional[int] = None
    tempo_estimado_horas: Optional[Decimal] = None
    criticidade: MaintenanceCriticality = MaintenanceCriticality.MEDIA
    prioridade: MaintenancePriority = MaintenancePriority.MEDIA
    ativo: bool = True
    responsavel_id: Optional[int] = None
    departamento_id: Optional[int] = None
    categoria_id: Optional[int] = None
    proxima_execucao: datetime


class MaintenancePlanCreate(MaintenancePlanBase):
    asset_ids: Optional[List[int]] = None
    checklists: Optional[List[MaintenanceChecklistCreate]] = None


class MaintenancePlanUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    tipo: Optional[MaintenanceType] = None
    periodicidade: Optional[MaintenancePeriodicity] = None
    dias_personalizado: Optional[int] = None
    tempo_estimado_horas: Optional[Decimal] = None
    criticidade: Optional[MaintenanceCriticality] = None
    prioridade: Optional[MaintenancePriority] = None
    ativo: Optional[bool] = None
    responsavel_id: Optional[int] = None
    departamento_id: Optional[int] = None
    categoria_id: Optional[int] = None
    proxima_execucao: Optional[datetime] = None


class MaintenancePlanResponse(MaintenancePlanBase):
    id: int
    codigo: str
    data_criacao: datetime
    data_ultima_execucao: Optional[datetime] = None
    responsavel: Optional[UserResponse] = None
    departamento: Optional[Departamento] = None
    categoria: Optional[AssetCategoryResponse] = None
    assets: Optional[List[MaintenancePlanAssetResponse]] = None
    checklists: Optional[List[MaintenanceChecklistResponse]] = None

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Material ==============
class MaintenanceMaterialBase(BaseModel):
    produto: str
    quantidade: Decimal
    valor_unitario: Decimal
    valor_total: Decimal
    observacao: Optional[str] = None


class MaintenanceMaterialCreate(MaintenanceMaterialBase):
    order_id: int


class MaintenanceMaterialUpdate(BaseModel):
    produto: Optional[str] = None
    quantidade: Optional[Decimal] = None
    valor_unitario: Optional[Decimal] = None
    valor_total: Optional[Decimal] = None
    observacao: Optional[str] = None


class MaintenanceMaterialResponse(MaintenanceMaterialBase):
    id: int
    order_id: int

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Photo ==============
class MaintenancePhotoBase(BaseModel):
    tipo: PhotoType = PhotoType.DURANTE
    caminho_arquivo: str
    descricao: Optional[str] = None


class MaintenancePhotoCreate(MaintenancePhotoBase):
    order_id: int
    execution_id: Optional[int] = None


class MaintenancePhotoUpdate(BaseModel):
    tipo: Optional[PhotoType] = None
    descricao: Optional[str] = None


class MaintenancePhotoResponse(MaintenancePhotoBase):
    id: int
    order_id: int
    execution_id: Optional[int] = None
    data_upload: datetime
    upload_por: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Execution ==============
class MaintenanceExecutionBase(BaseModel):
    checklist_item_id: int
    concluido: bool = False
    observacao: Optional[str] = None


class MaintenanceExecutionCreate(MaintenanceExecutionBase):
    order_id: int


class MaintenanceExecutionUpdate(BaseModel):
    concluido: Optional[bool] = None
    observacao: Optional[str] = None


class MaintenanceExecutionResponse(MaintenanceExecutionBase):
    id: int
    order_id: int
    data_execucao: Optional[datetime] = None
    executado_por: Optional[UserResponse] = None
    checklist_item: Optional[MaintenanceChecklistItemResponse] = None

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance History ==============
class MaintenanceHistoryBase(BaseModel):
    acao: str
    descricao: str
    status_anterior: Optional[str] = None
    status_novo: Optional[str] = None


class MaintenanceHistoryCreate(MaintenanceHistoryBase):
    order_id: int
    usuario_id: Optional[int] = None


class MaintenanceHistoryResponse(MaintenanceHistoryBase):
    id: int
    order_id: int
    usuario: Optional[UserResponse] = None
    data_hora: datetime

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Notification ==============
class MaintenanceNotificationBase(BaseModel):
    tipo: str
    mensagem: str
    lida: bool = False


class MaintenanceNotificationCreate(MaintenanceNotificationBase):
    order_id: Optional[int] = None
    plan_id: Optional[int] = None
    usuario_id: int


class MaintenanceNotificationUpdate(BaseModel):
    lida: Optional[bool] = None


class MaintenanceNotificationResponse(MaintenanceNotificationBase):
    id: int
    order_id: Optional[int] = None
    plan_id: Optional[int] = None
    usuario_id: int
    data_criacao: datetime

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Order ==============
class MaintenanceOrderBase(BaseModel):
    plan_id: Optional[int] = None
    asset_id: int
    tecnico_id: Optional[int] = None
    solicitante_id: Optional[int] = None
    status: OrderStatus = OrderStatus.ABERTA
    prioridade: MaintenancePriority = MaintenancePriority.MEDIA
    criticidade: MaintenanceCriticality = MaintenanceCriticality.MEDIA
    tipo: MaintenanceType = MaintenanceType.PREVENTIVA
    data_agendada: Optional[datetime] = None
    observacoes: Optional[str] = None
    service_ticket_id: Optional[int] = None


class MaintenanceOrderCreate(MaintenanceOrderBase):
    pass


class MaintenanceOrderUpdate(BaseModel):
    plan_id: Optional[int] = None
    tecnico_id: Optional[int] = None
    solicitante_id: Optional[int] = None
    status: Optional[OrderStatus] = None
    prioridade: Optional[MaintenancePriority] = None
    criticidade: Optional[MaintenanceCriticality] = None
    tipo: Optional[MaintenanceType] = None
    data_agendada: Optional[datetime] = None
    observacoes: Optional[str] = None
    solucao: Optional[str] = None
    service_ticket_id: Optional[int] = None


class MaintenanceOrderResponse(MaintenanceOrderBase):
    id: int
    numero: str
    data_abertura: datetime
    data_inicio: Optional[datetime] = None
    data_pausa: Optional[datetime] = None
    data_conclusao: Optional[datetime] = None
    tempo_total_minutos: Optional[int] = None
    solucao: Optional[str] = None
    custo_total: Optional[Decimal] = None
    plan: Optional[MaintenancePlanResponse] = None
    asset: Optional[AssetResponse] = None
    tecnico: Optional[UserResponse] = None
    solicitante: Optional[UserResponse] = None
    executions: Optional[List[MaintenanceExecutionResponse]] = None
    materials: Optional[List[MaintenanceMaterialResponse]] = None
    photos: Optional[List[MaintenancePhotoResponse]] = None
    history: Optional[List[MaintenanceHistoryResponse]] = None

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Material ==============
class MaintenanceMaterialBase(BaseModel):
    produto: str
    quantidade: float
    valor_unitario: float
    valor_total: float
    observacao: Optional[str] = None


class MaintenanceMaterialCreate(MaintenanceMaterialBase):
    order_id: int


class MaintenanceMaterialUpdate(BaseModel):
    produto: Optional[str] = None
    quantidade: Optional[float] = None
    valor_unitario: Optional[float] = None
    valor_total: Optional[float] = None
    observacao: Optional[str] = None


class MaintenanceMaterialResponse(MaintenanceMaterialBase):
    id: int
    order_id: int

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Photo ==============
class MaintenancePhotoBase(BaseModel):
    tipo: str
    caminho_arquivo: str
    descricao: Optional[str] = None


class MaintenancePhotoCreate(MaintenancePhotoBase):
    order_id: int
    execution_id: Optional[int] = None


class MaintenancePhotoUpdate(BaseModel):
    tipo: Optional[str] = None
    descricao: Optional[str] = None


class MaintenancePhotoResponse(MaintenancePhotoBase):
    id: int
    order_id: int
    execution_id: Optional[int] = None
    data_upload: datetime
    upload_por: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Execution ==============
class MaintenanceExecutionBase(BaseModel):
    checklist_item_id: int
    concluido: bool = False
    observacao: Optional[str] = None


class MaintenanceExecutionCreate(MaintenanceExecutionBase):
    order_id: int


class MaintenanceExecutionUpdate(BaseModel):
    concluido: Optional[bool] = None
    observacao: Optional[str] = None


class MaintenanceExecutionResponse(MaintenanceExecutionBase):
    id: int
    order_id: int
    data_execucao: Optional[datetime] = None
    executado_por: Optional[UserResponse] = None
    checklist_item: Optional[MaintenanceChecklistItemResponse] = None

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance History ==============
class MaintenanceHistoryBase(BaseModel):
    acao: str
    descricao: str
    status_anterior: Optional[str] = None
    status_novo: Optional[str] = None


class MaintenanceHistoryCreate(MaintenanceHistoryBase):
    order_id: int
    usuario_id: Optional[int] = None


class MaintenanceHistoryResponse(MaintenanceHistoryBase):
    id: int
    order_id: int
    usuario: Optional[UserResponse] = None
    data_hora: datetime

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Notification ==============
class MaintenanceNotificationBase(BaseModel):
    tipo: str
    mensagem: str
    lida: bool = False


class MaintenanceNotificationCreate(MaintenanceNotificationBase):
    order_id: Optional[int] = None
    plan_id: Optional[int] = None
    usuario_id: int


class MaintenanceNotificationUpdate(BaseModel):
    lida: Optional[bool] = None


class MaintenanceNotificationResponse(MaintenanceNotificationBase):
    id: int
    order_id: Optional[int] = None
    plan_id: Optional[int] = None
    usuario_id: int
    data_criacao: datetime

    model_config = ConfigDict(from_attributes=True)


# ============== Dashboard Statistics ==============
class DashboardStats(BaseModel):
    manutencoes_vencidas: int = 0
    manutencoes_hoje: int = 0
    manutencoes_semana: int = 0
    manutencoes_concluidas: int = 0
    ordens_em_andamento: int = 0
    equipamentos_indisponiveis: int = 0


class DashboardChartData(BaseModel):
    preventiva_vs_corretiva: dict
    status_ordens: dict
    ordens_por_tecnico: dict
    ordens_por_setor: dict
    custos_mensais: dict
    equipamentos_mais_manutencoes: dict


class MaintenanceDashboardResponse(BaseModel):
    stats: DashboardStats
    charts: DashboardChartData
    proximas_manutencoes: List[MaintenanceOrderResponse]

