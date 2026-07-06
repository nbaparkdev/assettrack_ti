
# app/models/__init__.py
from app.models.user import User, UserRole
from app.models.location import Departamento, Localizacao, Armazenamento
from app.models.asset import Asset, AssetStatus
from app.models.asset_category import AssetCategory
from app.models.transaction import Movimentacao, Solicitacao, TipoMovimentacao, StatusSolicitacao
from app.models.maintenance import Manutencao, TipoManutencao, StatusManutencao, DestinoManutencao
from app.models.maintenance_request import SolicitacaoManutencao, PrioridadeSolicitacao, StatusSolicitacaoManutencao
from app.models.qr_log import QRLog, QRLogAction
from app.models.service_desk import ServiceCategory, ServiceDefinition, ServiceTicket, ServiceStatus, ServicePriority
from app.models.supplier import Fornecedor
from app.models.invoice import NotaFiscal
from app.models.preventive_maintenance import (
    MaintenancePlan,
    MaintenancePlanAsset,
    MaintenanceChecklist,
    MaintenanceChecklistItem,
    MaintenanceOrder,
    MaintenanceExecution,
    MaintenanceMaterial,
    MaintenancePhoto,
    MaintenanceHistory,
    MaintenanceNotification,
    MaintenanceType,
    MaintenancePeriodicity,
    MaintenancePriority,
    MaintenanceCriticality,
    OrderStatus,
    PhotoType
)
from app.models.system_settings import SystemSettings
from app.models.procurement import (
    ProductType,
    PurchaseRequestStatus,
    PurchaseOrderStatus,
    PurchaseCategory,
    PurchaseProduct,
    CostCenter,
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseApproval,
    PurchaseQuotation,
    PurchaseQuotationSupplier,
    PurchaseQuotationItem,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseReceiving,
    PurchaseReceivingItem,
    PurchaseContract,
    PurchaseAttachment,
    PurchaseHistory,
    PurchaseNotification,
    MaterialStock,
    MaterialStockTransaction
)
from app.models.email_log import EmailLog
from app.database import Base


