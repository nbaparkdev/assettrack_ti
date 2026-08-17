package models

import "time"

// QRLogAction constants matching PostgreSQL enum values
const (
	QRActionLogin           = "login"
	QRActionLoginFailed     = "login_failed"
	QRActionRegenerate      = "regenerate"
	QRActionPINSet          = "pin_set"
	QRActionPINChanged      = "pin_changed"
	QRActionProfileView     = "profile_view"
	QRActionDeliveryConfirm = "delivery_confirm"
)

// QRLog maps to the existing "qr_logs" table
type QRLog struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	UserID    *uint     `gorm:"column:user_id" json:"user_id"`
	ActorID   *uint     `gorm:"column:actor_id" json:"actor_id"`
	Action    string    `gorm:"type:varchar(30);not null" json:"action"`
	IPAddress *string   `gorm:"column:ip_address" json:"ip_address"`
	Details   *string   `json:"details"`
	Success   bool      `gorm:"default:true" json:"success"`
	Timestamp time.Time `gorm:"autoCreateTime" json:"timestamp"`

	User  *User `gorm:"foreignKey:UserID" json:"user,omitempty"`
	Actor *User `gorm:"foreignKey:ActorID" json:"actor,omitempty"`
}

func (QRLog) TableName() string { return "qr_logs" }
