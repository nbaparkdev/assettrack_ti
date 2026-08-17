# app/schemas/service_desk.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.service_desk import ServicePriority, ServiceStatus


# Categorias
class ServiceCategoryBase(BaseModel):
    nome: str
    descricao: str | None = None
    setor: str

class ServiceCategoryCreate(ServiceCategoryBase):
    pass

class ServiceCategoryUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    setor: str | None = None

class ServiceCategorySchema(ServiceCategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Definições de Serviço
class ServiceDefinitionBase(BaseModel):
    categoria_id: int
    nome: str
    descricao: str | None = None
    prioridade_padrao: ServicePriority = ServicePriority.MEDIA
    tempo_estimado_horas: float | None = None

class ServiceDefinitionCreate(ServiceDefinitionBase):
    pass

class ServiceDefinitionUpdate(BaseModel):
    categoria_id: int | None = None
    nome: str | None = None
    descricao: str | None = None
    prioridade_padrao: ServicePriority | None = None
    tempo_estimado_horas: float | None = None

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
    foto: str | None = None

class ServiceTicketUpdate(BaseModel):
    status: ServiceStatus | None = None
    prioridade: ServicePriority | None = None
    tecnico_id: int | None = None
    solucao: str | None = None
    feedback_usuario: str | None = None
    avaliacao: int | None = None

class ServiceTicketSchema(ServiceTicketBase):
    id: int
    codigo: str
    solicitante_id: int
    tecnico_id: int | None = None
    status: ServiceStatus
    foto: str | None = None
    data_abertura: datetime
    data_atualizacao: datetime
    data_fechamento: datetime | None = None
    solucao: str | None = None
    
    model_config = ConfigDict(from_attributes=True)

# Interações (Timeline)
class ServiceTicketInteractionBase(BaseModel):
    mensagem: str
    tipo: str = "Comentário"

class ServiceTicketInteractionCreate(ServiceTicketInteractionBase):
    ticket_id: int
    foto: str | None = None

class ServiceTicketInteractionSchema(ServiceTicketInteractionBase):
    id: int
    ticket_id: int
    usuario_id: int
    foto: str | None = None
    data_criacao: datetime
    
    model_config = ConfigDict(from_attributes=True)
