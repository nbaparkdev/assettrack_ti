package dto

import "time"

// QRLoginRequest - login via QR Code + PIN
type QRLoginRequest struct {
	QRToken string `json:"qr_token" binding:"required"`
	PIN     string `json:"pin" binding:"required"`
}

// PINSetupRequest - configure PIN (4-6 digits)
type PINSetupRequest struct {
	PIN string `json:"pin" binding:"required,min=4,max=6,numeric"`
}

// UserQRResponse - QR code data
type UserQRResponse struct {
	QRCodeBase64 string     `json:"qr_code_base64"`
	QRToken      string     `json:"qr_token"`
	CreatedAt    *time.Time `json:"created_at"`
	HasPIN       bool       `json:"has_pin"`
}

// UserBadgeResponse - digital badge
type UserBadgeResponse struct {
	ID               uint    `json:"id"`
	Nome             string  `json:"nome"`
	Email            string  `json:"email"`
	Matricula        *string `json:"matricula"`
	Cargo            *string `json:"cargo"`
	DepartamentoNome *string `json:"departamento_nome"`
	AvatarURL        *string `json:"avatar_url"`
	QRCodeBase64     string  `json:"qr_code_base64"`
}

// PendingDeliveryItem - item awaiting delivery
type PendingDeliveryItem struct {
	ID              uint      `json:"id"`
	Tipo            string    `json:"tipo"`
	AssetTag        string    `json:"asset_tag"`
	AssetNome       string    `json:"asset_nome"`
	DataSolicitacao time.Time `json:"data_solicitacao"`
	Status          string    `json:"status"`
}

// UserPublicProfile - public profile via QR scan
type UserPublicProfile struct {
	ID                uint                  `json:"id"`
	Nome              string                `json:"nome"`
	Email             string                `json:"email"`
	Matricula         *string               `json:"matricula"`
	Cargo             *string               `json:"cargo"`
	DepartamentoNome  *string               `json:"departamento_nome"`
	AvatarURL         *string               `json:"avatar_url"`
	PendingDeliveries []PendingDeliveryItem `json:"pending_deliveries"`
}

// DeliveryConfirmRequest - confirm equipment delivery
type DeliveryConfirmRequest struct {
	QRToken       *string `json:"qr_token,omitempty"`
	PIN           *string `json:"pin,omitempty"`
	BypassPIN     bool    `json:"bypass_pin,omitempty"`
	SolicitacaoID *uint   `json:"solicitacao_id,omitempty"`
	ManutencaoID  *uint   `json:"manutencao_id,omitempty"`
	Observacao    *string `json:"observacao,omitempty"`
}
