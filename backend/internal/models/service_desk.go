package models

import (
	"time"
)

type ServiceStatus string

const (
	ServiceStatusAberto             ServiceStatus = "Aberto"
	ServiceStatusEmAtendimento      ServiceStatus = "Em Atendimento"
	ServiceStatusAguardandoTerceiro ServiceStatus = "Aguardando Terceiro"
	ServiceStatusEsperandoCompra    ServiceStatus = "Esperando Compra"
	ServiceStatusResolvido          ServiceStatus = "Resolvido"
	ServiceStatusFechado            ServiceStatus = "Fechado"
	ServiceStatusCancelado          ServiceStatus = "Cancelado"
)

type ServicePriority string

const (
	ServicePriorityBaixa   ServicePriority = "Baixa"
	ServicePriorityMedia   ServicePriority = "Média"
	ServicePriorityAlta    ServicePriority = "Alta"
	ServicePriorityUrgente ServicePriority = "Urgente"
)

type ServiceCategory struct {
	ID        uint                `gorm:"primaryKey" json:"id"`
	Nome      string              `gorm:"uniqueIndex;not null;type:varchar(100)" json:"nome"`
	Descricao *string             `gorm:"type:text" json:"descricao"`
	Setor     string              `gorm:"type:varchar(50);not null" json:"setor"`
	Servicos  []ServiceDefinition `gorm:"foreignKey:CategoriaID;constraint:OnDelete:CASCADE" json:"servicos,omitempty"`
}

func (ServiceCategory) TableName() string { return "service_categories" }

type ServiceDefinition struct {
	ID                 uint            `gorm:"primaryKey" json:"id"`
	CategoriaID        uint            `gorm:"not null" json:"categoria_id"`
	Nome               string          `gorm:"not null;type:varchar(100)" json:"nome"`
	Descricao          *string         `gorm:"type:text" json:"descricao"`
	PrioridadePadrao   ServicePriority `gorm:"type:varchar(20);default:'Média'" json:"prioridade_padrao"`
	TempoEstimadoHoras *float64        `json:"tempo_estimado_horas"`

	Categoria *ServiceCategory `gorm:"foreignKey:CategoriaID" json:"categoria,omitempty"`
}

func (ServiceDefinition) TableName() string { return "service_definitions" }

type ServiceTicket struct {
	ID              uint            `gorm:"primaryKey" json:"id"`
	Codigo          string          `gorm:"uniqueIndex;not null;type:varchar(20)" json:"codigo"`
	ServicoID       uint            `gorm:"not null" json:"servico_id"`
	SolicitanteID   uint            `gorm:"not null" json:"solicitante_id"`
	TecnicoID       *uint           `json:"tecnico_id"`
	Descricao       string          `gorm:"not null;type:text" json:"descricao"`
	Status          ServiceStatus   `gorm:"type:varchar(30);default:'Aberto'" json:"status"`
	Prioridade      ServicePriority `gorm:"type:varchar(20);not null" json:"prioridade"`
	Foto            *string         `gorm:"type:varchar(255)" json:"foto"`
	DataAbertura    time.Time       `gorm:"not null;autoCreateTime" json:"data_abertura"`
	DataAtualizacao time.Time       `gorm:"not null;autoUpdateTime" json:"data_atualizacao"`
	DataFechamento  *time.Time      `json:"data_fechamento"`
	Solucao         *string         `gorm:"type:text" json:"solucao"`
	FeedbackUsuario *string         `gorm:"type:text" json:"feedback_usuario"`
	Avaliacao       *int            `json:"avaliacao"`

	Servico     *ServiceDefinition         `gorm:"foreignKey:ServicoID" json:"servico,omitempty"`
	Solicitante *User                      `gorm:"foreignKey:SolicitanteID" json:"solicitante,omitempty"`
	Tecnico     *User                      `gorm:"foreignKey:TecnicoID" json:"tecnico,omitempty"`
	Interacoes  []ServiceTicketInteraction `gorm:"foreignKey:TicketID;constraint:OnDelete:CASCADE" json:"interacoes,omitempty"`
}

func (ServiceTicket) TableName() string { return "service_tickets" }

type ServiceTicketInteraction struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	TicketID    uint      `gorm:"not null" json:"ticket_id"`
	UsuarioID   uint      `gorm:"not null" json:"usuario_id"`
	Mensagem    string    `gorm:"not null;type:text" json:"mensagem"`
	Foto        *string   `gorm:"type:varchar(255)" json:"foto"`
	DataCriacao time.Time `gorm:"not null;autoCreateTime" json:"data_criacao"`
	Tipo        string    `gorm:"type:varchar(50);default:'Comentário'" json:"tipo"`

	Ticket  *ServiceTicket `gorm:"foreignKey:TicketID" json:"ticket,omitempty"`
	Usuario *User          `gorm:"foreignKey:UsuarioID" json:"usuario,omitempty"`
}

func (ServiceTicketInteraction) TableName() string { return "service_ticket_interactions" }
