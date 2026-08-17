package models

type Fornecedor struct {
	ID             uint    `gorm:"primaryKey" json:"id"`
	Nome           string  `gorm:"not null;index" json:"nome"`
	RazaoSocial    *string `json:"razao_social"`
	CNPJ           *string `gorm:"uniqueIndex" json:"cnpj"`
	Email          *string `json:"email"`
	Telefone       *string `json:"telefone"`
	Endereco       *string `json:"endereco"`
	Cidade         *string `json:"cidade"`
	Estado         *string `json:"estado"`
	TipoFornecedor *string `json:"tipo_fornecedor"`
}

func (Fornecedor) TableName() string { return "fornecedores" }
