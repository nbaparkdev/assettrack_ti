package models

import "time"

// Card priorities
const (
	CardPriorityBaixa   = "baixa"
	CardPriorityMedia   = "media"
	CardPriorityAlta    = "alta"
	CardPriorityUrgente = "urgente"
)

// Interaction types
const (
	InteractionComentario   = "comentario"
	InteractionSistemaMove  = "sistema_movimentacao"
	InteractionSistemaResp  = "sistema_responsavel"
	InteractionSistemaAnexo = "sistema_anexo"
	InteractionSistemaSupr  = "sistema_suprimentos"
)

type KanbanProject struct {
	ID                   uint      `gorm:"primaryKey" json:"id"`
	Titulo               string    `gorm:"size:255;not null" json:"titulo"`
	Descricao            *string   `gorm:"type:text" json:"descricao"`
	BoardBackgroundColor string    `gorm:"column:board_background_color;size:20;default:'#212121'" json:"board_background_color"`
	BoardPattern         string    `gorm:"column:board_pattern;size:30;default:'glow'" json:"board_pattern"`
	RelatedToMaintenance bool      `gorm:"column:related_to_maintenance;default:false" json:"related_to_maintenance"`
	RelatedToPreventive  bool      `gorm:"column:related_to_preventive;default:false" json:"related_to_preventive"`
	PreventivePlanID     *uint     `gorm:"column:preventive_plan_id" json:"preventive_plan_id"`
	CriadorID            uint      `gorm:"column:criador_id;not null" json:"criador_id"`
	IsActive             bool      `gorm:"column:is_active;default:true" json:"is_active"`
	IsArchived           bool      `gorm:"column:is_archived;default:false" json:"is_archived"`
	CreatedAt            time.Time `gorm:"column:created_at;default:CURRENT_TIMESTAMP" json:"created_at"`
	UpdatedAt            time.Time `gorm:"column:updated_at;default:CURRENT_TIMESTAMP" json:"updated_at"`

	Criador        *User            `gorm:"foreignKey:CriadorID" json:"criador,omitempty"`
	PreventivePlan *MaintenancePlan `gorm:"foreignKey:PreventivePlanID" json:"preventive_plan,omitempty"`
	Participantes  []User           `gorm:"many2many:kanban_project_participantes;" json:"participantes,omitempty"`
	Colunas        []KanbanColumn   `gorm:"foreignKey:ProjectID" json:"colunas,omitempty"`
	Cards          []KanbanCard     `gorm:"foreignKey:ProjectID" json:"cards,omitempty"`
}

func (KanbanProject) TableName() string { return "kanban_projects" }

type KanbanColumn struct {
	ID        uint   `gorm:"primaryKey" json:"id"`
	ProjectID uint   `gorm:"column:project_id;not null" json:"project_id"`
	Nome      string `gorm:"size:100;not null" json:"nome"`
	Cor       string `gorm:"size:30;default:'#6B7280'" json:"cor"`
	Ordem     int    `gorm:"default:0" json:"ordem"`
	IsDefault bool   `gorm:"column:is_default;default:false" json:"is_default"`

	Project *KanbanProject `gorm:"foreignKey:ProjectID" json:"project,omitempty"`
	Cards   []KanbanCard   `gorm:"foreignKey:ColumnID" json:"cards,omitempty"`
}

func (KanbanColumn) TableName() string { return "kanban_columns" }

type KanbanCard struct {
	ID                uint       `gorm:"primaryKey" json:"id"`
	ProjectID         uint       `gorm:"column:project_id;not null" json:"project_id"`
	ColumnID          uint       `gorm:"column:column_id;not null" json:"column_id"`
	Titulo            string     `gorm:"size:255;not null" json:"titulo"`
	Cor               string     `gorm:"column:cor;size:20;default:'#0079BF'" json:"cor"`
	Descricao         *string    `gorm:"type:text" json:"descricao"`
	ChecklistJSON     *string    `gorm:"column:checklist_json;type:text" json:"checklist_json"`
	PreventiveOrderID *uint      `gorm:"column:preventive_order_id" json:"preventive_order_id"`
	CriadorID         uint       `gorm:"column:criador_id;not null" json:"criador_id"`
	ResponsavelID     *uint      `gorm:"column:responsavel_id" json:"responsavel_id"`
	Prioridade        string     `gorm:"size:20;default:'media'" json:"prioridade"`
	DataEntrega       *time.Time `gorm:"column:data_entrega" json:"data_entrega"`
	Ordem             int        `gorm:"default:0" json:"ordem"`
	CreatedAt         time.Time  `gorm:"column:created_at;default:CURRENT_TIMESTAMP" json:"created_at"`
	UpdatedAt         time.Time  `gorm:"column:updated_at;default:CURRENT_TIMESTAMP" json:"updated_at"`

	// Procurement links (plain columns; FK constraints are managed by the procurement module)
	PurchaseRequestID  *uint   `gorm:"column:purchase_request_id" json:"purchase_request_id"`
	MaterialStockID    *uint   `gorm:"column:material_stock_id" json:"material_stock_id"`
	TipoItemNecessario *string `gorm:"column:tipo_item_necessario;size:50" json:"tipo_item_necessario"`

	Project         *KanbanProject          `gorm:"foreignKey:ProjectID" json:"project,omitempty"`
	Column          *KanbanColumn           `gorm:"foreignKey:ColumnID" json:"column,omitempty"`
	PreventiveOrder *MaintenanceOrder       `gorm:"foreignKey:PreventiveOrderID" json:"preventive_order,omitempty"`
	Criador         *User                   `gorm:"foreignKey:CriadorID" json:"criador,omitempty"`
	Responsavel     *User                   `gorm:"foreignKey:ResponsavelID" json:"responsavel,omitempty"`
	Participantes   []User                  `gorm:"many2many:kanban_card_participantes;" json:"participantes,omitempty"`
	Ativos          []Asset                 `gorm:"many2many:kanban_card_assets;" json:"ativos,omitempty"`
	Anexos          []KanbanAttachment      `gorm:"foreignKey:CardID" json:"anexos,omitempty"`
	Interacoes      []KanbanCardInteraction `gorm:"foreignKey:CardID" json:"interacoes,omitempty"`
}

func (KanbanCard) TableName() string { return "kanban_cards" }

type KanbanCardInteraction struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	CardID    uint      `gorm:"column:card_id;not null;index" json:"card_id"`
	UsuarioID uint      `gorm:"column:usuario_id;not null" json:"usuario_id"`
	Mensagem  string    `gorm:"type:text;not null" json:"mensagem"`
	Tipo      string    `gorm:"size:50;default:'comentario'" json:"tipo"`
	CreatedAt time.Time `gorm:"column:created_at;default:CURRENT_TIMESTAMP" json:"created_at"`

	Card    *KanbanCard `gorm:"foreignKey:CardID" json:"card,omitempty"`
	Usuario *User       `gorm:"foreignKey:UsuarioID" json:"usuario,omitempty"`
}

func (KanbanCardInteraction) TableName() string { return "kanban_card_interactions" }

type KanbanAttachment struct {
	ID       uint      `gorm:"primaryKey" json:"id"`
	CardID   uint      `gorm:"column:card_id;not null" json:"card_id"`
	Nome     string    `gorm:"size:255;not null" json:"nome"`
	Tipo     string    `gorm:"size:50;not null" json:"tipo"` // imagem, link, arquivo
	URL      string    `gorm:"type:text;not null" json:"url"`
	CriadoEm time.Time `gorm:"column:criado_em;default:CURRENT_TIMESTAMP" json:"criado_em"`

	Card *KanbanCard `gorm:"foreignKey:CardID" json:"card,omitempty"`
}

func (KanbanAttachment) TableName() string { return "kanban_attachments" }

// Notification types
const (
	NotifProjetoAdicionado = "PROJETO_ADICIONADO"
	NotifCartaoAtribuido   = "CARTAO_ATRIBUIDO"
	NotifCartaoMovimentado = "CARTAO_MOVIMENTADO"
	NotifAnexoAdicionado   = "ANEXO_ADICIONADO"
)

type KanbanNotification struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	UserID    uint      `gorm:"column:user_id;not null;index" json:"user_id"`
	ProjectID *uint     `gorm:"column:project_id" json:"project_id"`
	CardID    *uint     `gorm:"column:card_id" json:"card_id"`
	AutorID   *uint     `gorm:"column:autor_id" json:"autor_id"`
	Tipo      string    `gorm:"size:50;not null" json:"tipo"`
	Titulo    string    `gorm:"size:255;not null" json:"titulo"`
	Mensagem  string    `gorm:"type:text;not null" json:"mensagem"`
	Link      *string   `gorm:"size:255" json:"link"`
	Lida      bool      `gorm:"default:false" json:"lida"`
	CreatedAt time.Time `gorm:"column:created_at;default:CURRENT_TIMESTAMP" json:"created_at"`

	User  *User `gorm:"foreignKey:UserID" json:"user,omitempty"`
	Autor *User `gorm:"foreignKey:AutorID" json:"autor,omitempty"`
}

func (KanbanNotification) TableName() string { return "kanban_notifications" }
