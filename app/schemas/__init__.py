
# app/schemas/__init__.py
from app.schemas.user import UserCreate, UserUpdate, UserResponse, Token, TokenData
from app.schemas.asset import AssetCreate, AssetUpdate, AssetResponse
from app.schemas.location import (
    DepartamentoCreate, DepartamentoUpdate, Departamento, 
    LocalizacaoCreate, LocalizacaoUpdate, Localizacao,
    ArmazenamentoCreate, ArmazenamentoUpdate, Armazenamento
)
from app.schemas.transaction import (
    MovimentacaoCreate, MovimentacaoResponse,
    SolicitacaoCreate, SolicitacaoUpdate, SolicitacaoResponse
)
