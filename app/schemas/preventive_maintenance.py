
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.preventive_maintenance import (
    MaintenanceCriticality,
    MaintenancePeriodicity,
    MaintenancePriority,
    MaintenanceType,
    OrderStatus,
    PhotoType,
)
from app.schemas.asset import AssetResponse
from app.schemas.asset_category import AssetCategoryResponse
from app.schemas.location import Departamento
from app.schemas.user import UserResponse


# ============== Maintenance Checklist Item ==============
class MaintenanceChecklistItemBase(BaseModel):
    descricao: str
    obrigatorio: bool = True
    ordem: int = 0
    requer_foto: bool = False


class MaintenanceChecklistItemCreate(MaintenanceChecklistItemBase):
    checklist_id: int


class MaintenanceChecklistItemUpdate(BaseModel):
    descricao: str | None = None
    obrigatorio: bool | None = None
    ordem: int | None = None
    requer_foto: bool | None = None


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
    items: list[MaintenanceChecklistItemCreate] | None = None


class MaintenanceChecklistUpdate(BaseModel):
    nome: str | None = None
    ordem: int | None = None


class MaintenanceChecklistResponse(MaintenanceChecklistBase):
    id: int
    plan_id: int
    items: list[MaintenanceChecklistItemResponse] | None = None

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Plan Asset ==============
class MaintenancePlanAssetBase(BaseModel):
    plan_id: int
    asset_id: int


class MaintenancePlanAssetCreate(MaintenancePlanAssetBase):
    pass


class MaintenancePlanAssetUpdate(BaseModel):
    plan_id: int | None = None
    asset_id: int | None = None


class MaintenancePlanAssetResponse(MaintenancePlanAssetBase):
    id: int
    asset: AssetResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Plan ==============
class MaintenancePlanBase(BaseModel):
    nome: str
    descricao: str | None = None
    tipo: MaintenanceType = MaintenanceType.PREVENTIVA
    periodicidade: MaintenancePeriodicity = MaintenancePeriodicity.MENSAL
    dias_personalizado: int | None = None
    tempo_estimado_horas: Decimal | None = None
    criticidade: MaintenanceCriticality = MaintenanceCriticality.MEDIA
    prioridade: MaintenancePriority = MaintenancePriority.MEDIA
    ativo: bool = True
    responsavel_id: int | None = None
    departamento_id: int | None = None
    categoria_id: int | None = None
    proxima_execucao: datetime


class MaintenancePlanCreate(MaintenancePlanBase):
    asset_ids: list[int] | None = None
    checklists: list[MaintenanceChecklistCreate] | None = None


class MaintenancePlanUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    tipo: MaintenanceType | None = None
    periodicidade: MaintenancePeriodicity | None = None
    dias_personalizado: int | None = None
    tempo_estimado_horas: Decimal | None = None
    criticidade: MaintenanceCriticality | None = None
    prioridade: MaintenancePriority | None = None
    ativo: bool | None = None
    responsavel_id: int | None = None
    departamento_id: int | None = None
    categoria_id: int | None = None
    proxima_execucao: datetime | None = None


class MaintenancePlanResponse(MaintenancePlanBase):
    id: int
    codigo: str
    data_criacao: datetime
    data_ultima_execucao: datetime | None = None
    responsavel: UserResponse | None = None
    departamento: Departamento | None = None
    categoria: AssetCategoryResponse | None = None
    assets: list[MaintenancePlanAssetResponse] | None = None
    checklists: list[MaintenanceChecklistResponse] | None = None

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Material ==============
class MaintenanceMaterialBase(BaseModel):
    produto: str
    quantidade: Decimal
    valor_unitario: Decimal
    valor_total: Decimal
    product_id: int | None = None
    observacao: str | None = None


class MaintenanceMaterialCreate(MaintenanceMaterialBase):
    order_id: int


class MaintenanceMaterialUpdate(BaseModel):
    produto: str | None = None
    quantidade: Decimal | None = None
    valor_unitario: Decimal | None = None
    valor_total: Decimal | None = None
    observacao: str | None = None


class MaintenanceMaterialResponse(MaintenanceMaterialBase):
    id: int
    order_id: int

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Photo ==============
class MaintenancePhotoBase(BaseModel):
    tipo: PhotoType = PhotoType.DURANTE
    caminho_arquivo: str
    descricao: str | None = None


class MaintenancePhotoCreate(MaintenancePhotoBase):
    order_id: int
    execution_id: int | None = None


class MaintenancePhotoUpdate(BaseModel):
    tipo: PhotoType | None = None
    descricao: str | None = None


class MaintenancePhotoResponse(MaintenancePhotoBase):
    id: int
    order_id: int
    execution_id: int | None = None
    data_upload: datetime
    upload_por: UserResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Execution ==============
class MaintenanceExecutionBase(BaseModel):
    checklist_item_id: int
    concluido: bool = False
    observacao: str | None = None


class MaintenanceExecutionCreate(MaintenanceExecutionBase):
    order_id: int


class MaintenanceExecutionUpdate(BaseModel):
    concluido: bool | None = None
    observacao: str | None = None


class MaintenanceExecutionResponse(MaintenanceExecutionBase):
    id: int
    order_id: int
    data_execucao: datetime | None = None
    executado_por: UserResponse | None = None
    checklist_item: MaintenanceChecklistItemResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance History ==============
class MaintenanceHistoryBase(BaseModel):
    acao: str
    descricao: str
    status_anterior: str | None = None
    status_novo: str | None = None


class MaintenanceHistoryCreate(MaintenanceHistoryBase):
    order_id: int
    usuario_id: int | None = None


class MaintenanceHistoryResponse(MaintenanceHistoryBase):
    id: int
    order_id: int
    usuario: UserResponse | None = None
    data_hora: datetime

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Notification ==============
class MaintenanceNotificationBase(BaseModel):
    tipo: str
    mensagem: str
    lida: bool = False


class MaintenanceNotificationCreate(MaintenanceNotificationBase):
    order_id: int | None = None
    plan_id: int | None = None
    usuario_id: int


class MaintenanceNotificationUpdate(BaseModel):
    lida: bool | None = None


class MaintenanceNotificationResponse(MaintenanceNotificationBase):
    id: int
    order_id: int | None = None
    plan_id: int | None = None
    usuario_id: int
    data_criacao: datetime

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Order ==============
class MaintenanceOrderBase(BaseModel):
    plan_id: int | None = None
    asset_id: int | None = None
    infra_predial_servico: str | None = None
    tecnico_id: int | None = None
    solicitante_id: int | None = None
    status: OrderStatus = OrderStatus.ABERTA
    prioridade: MaintenancePriority = MaintenancePriority.MEDIA
    criticidade: MaintenanceCriticality = MaintenanceCriticality.MEDIA
    tipo: MaintenanceType = MaintenanceType.PREVENTIVA
    data_agendada: datetime | None = None
    observacoes: str | None = None
    service_ticket_id: int | None = None


class MaintenanceOrderCreate(MaintenanceOrderBase):
    pass


class MaintenanceOrderUpdate(BaseModel):
    plan_id: int | None = None
    tecnico_id: int | None = None
    solicitante_id: int | None = None
    status: OrderStatus | None = None
    prioridade: MaintenancePriority | None = None
    criticidade: MaintenanceCriticality | None = None
    tipo: MaintenanceType | None = None
    data_agendada: datetime | None = None
    observacoes: str | None = None
    solucao: str | None = None
    service_ticket_id: int | None = None


class MaintenanceOrderResponse(MaintenanceOrderBase):
    id: int
    numero: str
    data_abertura: datetime
    data_inicio: datetime | None = None
    data_pausa: datetime | None = None
    data_conclusao: datetime | None = None
    tempo_total_minutos: int | None = None
    solucao: str | None = None
    custo_total: Decimal | None = None
    plan: MaintenancePlanResponse | None = None
    asset: AssetResponse | None = None
    tecnico: UserResponse | None = None
    solicitante: UserResponse | None = None
    executions: list[MaintenanceExecutionResponse] | None = None
    materials: list[MaintenanceMaterialResponse] | None = None
    photos: list[MaintenancePhotoResponse] | None = None
    history: list[MaintenanceHistoryResponse] | None = None

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Material ==============
class MaintenanceMaterialBase(BaseModel):
    produto: str
    quantidade: float
    valor_unitario: float
    valor_total: float
    product_id: int | None = None
    observacao: str | None = None


class MaintenanceMaterialCreate(MaintenanceMaterialBase):
    order_id: int


class MaintenanceMaterialUpdate(BaseModel):
    produto: str | None = None
    quantidade: float | None = None
    valor_unitario: float | None = None
    valor_total: float | None = None
    observacao: str | None = None


class MaintenanceMaterialResponse(MaintenanceMaterialBase):
    id: int
    order_id: int

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Photo ==============
class MaintenancePhotoBase(BaseModel):
    tipo: str
    caminho_arquivo: str
    descricao: str | None = None


class MaintenancePhotoCreate(MaintenancePhotoBase):
    order_id: int
    execution_id: int | None = None


class MaintenancePhotoUpdate(BaseModel):
    tipo: str | None = None
    descricao: str | None = None


class MaintenancePhotoResponse(MaintenancePhotoBase):
    id: int
    order_id: int
    execution_id: int | None = None
    data_upload: datetime
    upload_por: UserResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Execution ==============
class MaintenanceExecutionBase(BaseModel):
    checklist_item_id: int
    concluido: bool = False
    observacao: str | None = None


class MaintenanceExecutionCreate(MaintenanceExecutionBase):
    order_id: int


class MaintenanceExecutionUpdate(BaseModel):
    concluido: bool | None = None
    observacao: str | None = None


class MaintenanceExecutionResponse(MaintenanceExecutionBase):
    id: int
    order_id: int
    data_execucao: datetime | None = None
    executado_por: UserResponse | None = None
    checklist_item: MaintenanceChecklistItemResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance History ==============
class MaintenanceHistoryBase(BaseModel):
    acao: str
    descricao: str
    status_anterior: str | None = None
    status_novo: str | None = None


class MaintenanceHistoryCreate(MaintenanceHistoryBase):
    order_id: int
    usuario_id: int | None = None


class MaintenanceHistoryResponse(MaintenanceHistoryBase):
    id: int
    order_id: int
    usuario: UserResponse | None = None
    data_hora: datetime

    model_config = ConfigDict(from_attributes=True)


# ============== Maintenance Notification ==============
class MaintenanceNotificationBase(BaseModel):
    tipo: str
    mensagem: str
    lida: bool = False


class MaintenanceNotificationCreate(MaintenanceNotificationBase):
    order_id: int | None = None
    plan_id: int | None = None
    usuario_id: int


class MaintenanceNotificationUpdate(BaseModel):
    lida: bool | None = None


class MaintenanceNotificationResponse(MaintenanceNotificationBase):
    id: int
    order_id: int | None = None
    plan_id: int | None = None
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
    proximas_manutencoes: list[MaintenanceOrderResponse]

