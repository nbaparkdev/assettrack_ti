package models

import (
	"time"
)

type TipoMovimentacao string

const (
	TipoMovimentacaoEmprestimo    TipoMovimentacao = "empréstimo"
	TipoMovimentacaoDevolucao     TipoMovimentacao = "devolução"
	TipoMovimentacaoTransferencia TipoMovimentacao = "transferência"
	TipoMovimentacaoManutencao    TipoMovimentacao = "manutenção"
	TipoMovimentacaoBaixa         TipoMovimentacao = "baixa"
	TipoMovimentacaoCadastro      TipoMovimentacao = "cadastro"
)

type StatusSolicitacao string

const (
	StatusSolicitacaoPendente  StatusSolicitacao = "Pendente"
	StatusSolicitacaoAprovada  StatusSolicitacao = "Aprovada"
	StatusSolicitacaoEntregue  StatusSolicitacao = "Entregue"
	StatusSolicitacaoRejeitada StatusSolicitacao = "Rejeitada"
	StatusSolicitacaoCancelada StatusSolicitacao = "Cancelada"
)

type Movimentacao struct {
	ID                 uint             `gorm:"primaryKey" json:"id"`
	AssetID            uint             `gorm:"column:asset_id;not null" json:"asset_id"`
	Data               time.Time        `gorm:"column:data;autoCreateTime" json:"data"`
	Tipo               TipoMovimentacao `gorm:"type:varchar(30);not null" json:"tipo"`
	DeUserID           *uint            `gorm:"column:de_user_id" json:"de_user_id"`
	ParaUserID         *uint            `gorm:"column:para_user_id" json:"para_user_id"`
	DeDepartamentoID   *uint            `gorm:"column:de_departamento_id" json:"de_departamento_id"`
	ParaDepartamentoID *uint            `gorm:"column:para_departamento_id" json:"para_departamento_id"`
	Observacao         *string          `gorm:"type:text" json:"observacao"`

	Asset    *Asset `gorm:"foreignKey:AssetID" json:"asset,omitempty"`
	DeUser   *User  `gorm:"foreignKey:DeUserID" json:"de_user,omitempty"`
	ParaUser *User  `gorm:"foreignKey:ParaUserID" json:"para_user,omitempty"`
}

func (Movimentacao) TableName() string { return "movimentacoes" }

type Solicitacao struct {
	ID                    uint              `gorm:"primaryKey" json:"id"`
	SolicitanteID         *uint             `gorm:"column:solicitante_id" json:"solicitante_id"`
	AssetID               *uint             `gorm:"column:asset_id" json:"asset_id"`
	DataSolicitacao       time.Time         `gorm:"column:data_solicitacao;autoCreateTime" json:"data_solicitacao"`
	Motivo                string            `gorm:"type:text;not null" json:"motivo"`
	Status                StatusSolicitacao `gorm:"type:varchar(30);default:'Pendente'" json:"status"`
	AprovadorID           *uint             `gorm:"column:aprovador_id" json:"aprovador_id"`
	DataAprovacao         *time.Time        `gorm:"column:data_aprovacao" json:"data_aprovacao"`
	DataPrevistaDevolucao *time.Time        `gorm:"column:data_prevista_devolucao" json:"data_prevista_devolucao"`
	DataEntrega           *time.Time        `gorm:"column:data_entrega" json:"data_entrega"`
	ConfirmadoPorID       *uint             `gorm:"column:confirmado_por_id" json:"confirmado_por_id"`
	ConfirmadoViaQR       *bool             `gorm:"column:confirmado_via_qr;default:false" json:"confirmado_via_qr"`
	ObservacaoEntrega     *string           `gorm:"column:observacao_entrega;type:text" json:"observacao_entrega"`

	Solicitante *User  `gorm:"foreignKey:SolicitanteID" json:"solicitante,omitempty"`
	Aprovador   *User  `gorm:"foreignKey:AprovadorID" json:"aprovador,omitempty"`
	Confirmador *User  `gorm:"foreignKey:ConfirmadoPorID" json:"confirmador,omitempty"`
	Asset       *Asset `gorm:"foreignKey:AssetID" json:"asset,omitempty"`
}

func (Solicitacao) TableName() string { return "solicitacoes" }
