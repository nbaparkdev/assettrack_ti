package models

import "time"

type Webhook struct {
	ID                 uint         `gorm:"primaryKey" json:"id"`
	Nome               string       `gorm:"not null" json:"nome"`
	URL                string       `gorm:"not null" json:"url"`
	IsActive           bool         `gorm:"default:true" json:"is_active"`
	SecretKey          *string      `gorm:"column:secret_key" json:"secret_key"` // For HMAC SHA-256 signature
	EventosPermitidos  string       `gorm:"type:text;column:eventos_permitidos" json:"eventos_permitidos"` // JSON array of allowed events
	CreatedAt          time.Time    `gorm:"autoCreateTime" json:"created_at"`
	UpdatedAt          time.Time    `gorm:"autoUpdateTime" json:"updated_at"`
	Logs               []WebhookLog `gorm:"foreignKey:WebhookID;constraint:OnDelete:CASCADE" json:"logs,omitempty"`
}

func (Webhook) TableName() string { return "webhooks" }

type WebhookLog struct {
	ID             uint      `gorm:"primaryKey" json:"id"`
	WebhookID      uint      `gorm:"index;not null" json:"webhook_id"`
	Evento         string    `gorm:"not null" json:"evento"`
	PayloadEnviado string    `gorm:"type:text" json:"payload_enviado"`
	ResponseCode   int       `json:"response_code"`
	ResponseBody   string    `gorm:"type:text" json:"response_body"`
	Sucesso        bool      `gorm:"default:false" json:"sucesso"`
	CreatedAt      time.Time `gorm:"autoCreateTime" json:"created_at"`
}

func (WebhookLog) TableName() string { return "webhook_logs" }
