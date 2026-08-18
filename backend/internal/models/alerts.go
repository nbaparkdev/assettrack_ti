package models

import "time"

type EmergencyAlert struct {
	ID            uint       `gorm:"primaryKey" json:"id"`
	UsuarioID     uint       `gorm:"column:usuario_id;not null" json:"usuario_id"`
	UsuarioNome   string     `gorm:"column:usuario_nome;not null" json:"usuario_nome"`
	SetorNome     *string    `gorm:"column:setor_nome" json:"setor_nome"`
	AtivoNome     *string    `gorm:"column:ativo_nome" json:"ativo_nome"`
	Motivo        string     `gorm:"type:text;not null" json:"motivo"`
	Ciente        bool       `gorm:"default:false" json:"ciente"`
	CientePorID   *uint      `gorm:"column:ciente_por_id" json:"ciente_por_id"`
	CienteEm      *time.Time `gorm:"column:ciente_em" json:"ciente_em"`
	Atendido      bool       `gorm:"default:false" json:"atendido"`
	AtendidoPorID *uint      `gorm:"column:atendido_por_id" json:"atendido_por_id"`
	CreatedAt     time.Time  `gorm:"column:created_at;default:CURRENT_TIMESTAMP" json:"created_at"`

	Usuario     *User `gorm:"foreignKey:UsuarioID" json:"usuario,omitempty"`
	CientePor   *User `gorm:"foreignKey:CientePorID" json:"ciente_por,omitempty"`
	AtendidoPor *User `gorm:"foreignKey:AtendidoPorID" json:"atendido_por,omitempty"`
}

func (EmergencyAlert) TableName() string { return "emergency_alerts" }

type Aviso struct {
	ID               uint       `gorm:"primaryKey" json:"id"`
	Titulo           string     `gorm:"not null" json:"titulo"`
	Texto            *string    `json:"texto"`
	MidiaURL         *string    `gorm:"column:midia_url" json:"midia_url"`
	MidiaTipo        *string    `gorm:"column:midia_tipo" json:"midia_tipo"` // imagem, video
	LinkURL          *string    `gorm:"column:link_url" json:"link_url"`
	LinkTexto        *string    `gorm:"column:link_texto" json:"link_texto"`
	Ativo            bool       `gorm:"default:true" json:"ativo"`
	ProgramadoInicio *time.Time `gorm:"column:programado_inicio" json:"programado_inicio"`
	ProgramadoFim    *time.Time `gorm:"column:programado_fim" json:"programado_fim"`
	DataCadastro     time.Time  `gorm:"column:data_cadastro;default:CURRENT_TIMESTAMP" json:"data_cadastro"`
}

func (Aviso) TableName() string { return "avisos" }
