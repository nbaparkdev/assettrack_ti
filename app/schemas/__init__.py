
# app/schemas/__init__.py
from app.schemas.asset import AssetCreate, AssetResponse, AssetUpdate
from app.schemas.invoice import NotaFiscalCreate, NotaFiscalResponse, NotaFiscalUpdate
from app.schemas.location import (
    Armazenamento,
    ArmazenamentoCreate,
    ArmazenamentoUpdate,
    Departamento,
    DepartamentoCreate,
    DepartamentoUpdate,
    Localizacao,
    LocalizacaoCreate,
    LocalizacaoUpdate,
)
from app.schemas.procurement import (
    CostCenterCreate,
    CostCenterResponse,
    CostCenterUpdate,
    PurchaseApprovalCreate,
    PurchaseApprovalResponse,
    PurchaseCategoryCreate,
    PurchaseCategoryResponse,
    PurchaseCategoryUpdate,
    PurchaseContractCreate,
    PurchaseContractResponse,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseProductCreate,
    PurchaseProductResponse,
    PurchaseProductUpdate,
    PurchaseQuotationCreate,
    PurchaseQuotationResponse,
    PurchaseReceivingCreate,
    PurchaseReceivingResponse,
    PurchaseRequestCreate,
    PurchaseRequestResponse,
    PurchaseRequestUpdate,
)
from app.schemas.supplier import FornecedorCreate, FornecedorResponse, FornecedorUpdate
from app.schemas.transaction import (
    MovimentacaoCreate,
    MovimentacaoResponse,
    SolicitacaoCreate,
    SolicitacaoResponse,
    SolicitacaoUpdate,
)
from app.schemas.user import Token, TokenData, UserCreate, UserResponse, UserUpdate

