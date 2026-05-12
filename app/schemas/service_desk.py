# app/schemas/service_desk.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.service_desk import ServiceStatus, ServicePriority

# Categorias
class ServiceCategoryBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    setor: str

class ServiceCategoryCreate(ServiceCategoryBase):
    pass

class ServiceCategoryUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    setor: Optional[str] = None

class ServiceCategorySchema(ServiceCategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Definições de Serviço
class ServiceDefinitionBase(BaseModel):
    categoria_id: int
    nome: str
    descricao: Optional[str] = None
    prioridade_padrao: ServicePriority = ServicePriority.MEDIA
    tempo_estimado_horas: Optional[float] = None

class ServiceDefinitionCreate(ServiceDefinitionBase):
    pass

class ServiceDefinitionUpdate(BaseModel):
    categoria_id: Optional[int] = None
    nome: Optional[str] = None
    descricao: Optional[str] = None
    prioridade_padrao: Optional[ServicePriority] = None
    tempo_estimado_horas: Optional[float] = None

class ServiceDefinitionSchema(ServiceDefinitionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Chamados (Tickets)
class ServiceTicketBase(BaseModel):
    servico_id: int
    titulo: str
    descricao: str
    prioridade: ServicePriority

class ServiceTicketCreate(ServiceTicketBase):
    pass

class ServiceTicketUpdate(BaseModel):
    status: Optional[ServiceStatus] = None
    prioridade: Optional[ServicePriority] = None
    tecnico_id: Optional[int] = None
    solucao: Optional[str] = None
    feedback_usuario: Optional[str] = None
    avaliacao: Optional[int] = None

class ServiceTicketSchema(ServiceTicketBase):
    id: int
    codigo: str
    solicitante_id: int
    tecnico_id: Optional[int] = None
    status: ServiceStatus
    data_abertura: datetime
    data_atualizacao: datetime
    data_fechamento: Optional[datetime] = None
    solucao: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
