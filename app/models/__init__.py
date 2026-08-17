
# app/models/__init__.py
from app.database import Base
from app.models.asset import Asset, AssetStatus
from app.models.asset_category import AssetCategory
from app.models.aviso import Aviso
from app.models.email_log import EmailLog
from app.models.emergency_alert import EmergencyAlert
from app.models.invoice import NotaFiscal
from app.models.kanban import (
    KanbanAttachment,
    KanbanCard,
    KanbanColumn,
    KanbanNotification,
    KanbanProject,
    kanban_card_assets,
    kanban_card_assignees,
    kanban_project_participants,
)
from app.models.location import Armazenamento, Departamento, Localizacao
from app.models.maintenance import (
    DestinoManutencao,
    Manutencao,
    StatusManutencao,
    TipoManutencao,
)
from app.models.maintenance_request import (
    PrioridadeSolicitacao,
    SolicitacaoManutencao,
    StatusSolicitacaoManutencao,
)
from app.models.preventive_maintenance import (
    CustomMaintenanceType,
    MaintenanceChecklist,
    MaintenanceChecklistItem,
    MaintenanceCriticality,
    MaintenanceExecution,
    MaintenanceHistory,
    MaintenanceMaterial,
    MaintenanceNotification,
    MaintenanceOrder,
    MaintenancePeriodicity,
    MaintenancePhoto,
    MaintenancePlan,
    MaintenancePlanAsset,
    MaintenancePriority,
    MaintenanceType,
    OrderStatus,
    PhotoType,
)
from app.models.procurement import (
    CostCenter,
    MaterialStock,
    MaterialStockTransaction,
    ProductType,
    PurchaseApproval,
    PurchaseAttachment,
    PurchaseCategory,
    PurchaseContract,
    PurchaseHistory,
    PurchaseNotification,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderStatus,
    PurchaseProduct,
    PurchaseQuotation,
    PurchaseQuotationItem,
    PurchaseQuotationSupplier,
    PurchaseReceiving,
    PurchaseReceivingItem,
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestStatus,
    PurchaseResearch,
    PurchaseResearchItem,
    PurchaseResearchStatus,
)
from app.models.qr_log import QRLog, QRLogAction
from app.models.service_desk import (
    ServiceCategory,
    ServiceDefinition,
    ServicePriority,
    ServiceStatus,
    ServiceTicket,
)
from app.models.supplier import Fornecedor
from app.models.system_settings import SystemSettings
from app.models.termo_responsabilidade import TermoResponsabilidade
from app.models.transaction import (
    Movimentacao,
    Solicitacao,
    StatusSolicitacao,
    TipoMovimentacao,
)
from app.models.user import User, UserRole
from app.models.webhook import Webhook, WebhookLog



