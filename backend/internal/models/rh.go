package models

import "time"

type TermoResponsabilidade struct {
	ID             uint       `gorm:"primaryKey" json:"id"`
	SolicitacaoID  *uint      `gorm:"column:solicitacao_id" json:"solicitacao_id"`
	AssetID        uint       `gorm:"column:asset_id;not null" json:"asset_id"`
	UsuarioID      uint       `gorm:"column:usuario_id;not null" json:"usuario_id"`
	Status         string     `gorm:"type:varchar(30);default:'Pendente'" json:"status"`
	ConteudoTermo  string     `gorm:"type:text;not null" json:"conteudo_termo"`
	DataGeracao    time.Time  `gorm:"column:data_geracao;autoCreateTime" json:"data_geracao"`
	DataAssinatura *time.Time `gorm:"column:data_assinatura" json:"data_assinatura"`

	Solicitacao *Solicitacao `gorm:"foreignKey:SolicitacaoID" json:"solicitacao,omitempty"`
	Asset       *Asset       `gorm:"foreignKey:AssetID" json:"asset,omitempty"`
	Usuario     *User        `gorm:"foreignKey:UsuarioID" json:"usuario,omitempty"`
}

func (TermoResponsabilidade) TableName() string { return "termos_responsabilidade" }
