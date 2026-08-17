package models

import (
	"time"
)

type NotaFiscal struct {
	ID               uint       `gorm:"primaryKey" json:"id"`
	NumeroNota       string     `gorm:"not null;index" json:"numero_nota"`
	FornecedorID     uint       `gorm:"not null" json:"fornecedor_id"`
	XMLPath          *string    `json:"xml_path"`
	DataCadastro     time.Time  `gorm:"default:CURRENT_TIMESTAMP" json:"data_cadastro"`
	DataEmissao      *time.Time `json:"data_emissao"`
	ValorTotal       *float64   `json:"valor_total"`
	NaturezaOperacao *string    `json:"natureza_operacao"`
	EmitenteNome     *string    `json:"emitente_nome"`
	EmitenteCNPJ     *string    `json:"emitente_cnpj"`
	DestinatarioNome *string    `json:"destinatario_nome"`
	DestinatarioCNPJ *string    `json:"destinatario_cnpj"`
	Itens            *string    `gorm:"type:jsonb" json:"itens"` // Store as JSON string or jsonb

	Fornecedor *Fornecedor `gorm:"foreignKey:FornecedorID" json:"fornecedor,omitempty"`
}

func (NotaFiscal) TableName() string { return "notas_fiscais" }
