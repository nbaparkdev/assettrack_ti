package models

import "time"

type EmailLog struct {
	ID           uint      `gorm:"primaryKey" json:"id"`
	Recipient    string    `gorm:"index;not null" json:"recipient"`
	Subject      string    `gorm:"not null" json:"subject"`
	Body         string    `gorm:"type:text;not null" json:"body"`
	SentAt       time.Time `gorm:"autoCreateTime" json:"sent_at"`
	Status       string    `gorm:"not null" json:"status"` // 'SUCCESS' or 'FAILED'
	ErrorMessage *string   `gorm:"type:text" json:"error_message"`
}

func (EmailLog) TableName() string { return "email_logs" }
