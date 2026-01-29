
# app/crud/location.py
from app.crud.base import CRUDBase
from app.models.location import Departamento, Localizacao, Armazenamento
from app.schemas.location import (
    DepartamentoCreate, DepartamentoUpdate,
    LocalizacaoCreate, LocalizacaoUpdate,
    ArmazenamentoCreate, ArmazenamentoUpdate
)

class CRUDDepartamento(CRUDBase[Departamento, DepartamentoCreate, DepartamentoUpdate]):
    pass

class CRUDLocalizacao(CRUDBase[Localizacao, LocalizacaoCreate, LocalizacaoUpdate]):
    pass

class CRUDArmazenamento(CRUDBase[Armazenamento, ArmazenamentoCreate, ArmazenamentoUpdate]):
    pass

departamento = CRUDDepartamento(Departamento)
localizacao = CRUDLocalizacao(Localizacao)
armazenamento = CRUDArmazenamento(Armazenamento)
