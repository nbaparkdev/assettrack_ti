package repository

import (
	"github.com/assettrack/backend/internal/models"
	"gorm.io/gorm"
)

type WebhookRepository struct {
	db *gorm.DB
}

func NewWebhookRepository(db *gorm.DB) *WebhookRepository {
	return &WebhookRepository{db: db}
}

func (r *WebhookRepository) List() ([]models.Webhook, error) {
	var webhooks []models.Webhook
	err := r.db.Order("id desc").Find(&webhooks).Error
	return webhooks, err
}

func (r *WebhookRepository) ListActive() ([]models.Webhook, error) {
	var webhooks []models.Webhook
	err := r.db.Where("is_active = ?", true).Find(&webhooks).Error
	return webhooks, err
}

func (r *WebhookRepository) GetByID(id uint) (*models.Webhook, error) {
	var webhook models.Webhook
	err := r.db.First(&webhook, id).Error
	if err != nil {
		return nil, err
	}
	return &webhook, nil
}

func (r *WebhookRepository) Create(webhook *models.Webhook) error {
	return r.db.Create(webhook).Error
}

func (r *WebhookRepository) Update(webhook *models.Webhook) error {
	return r.db.Save(webhook).Error
}

func (r *WebhookRepository) Delete(id uint) error {
	return r.db.Delete(&models.Webhook{}, id).Error
}

func (r *WebhookRepository) CreateLog(log *models.WebhookLog) error {
	return r.db.Create(log).Error
}

func (r *WebhookRepository) GetLogs(webhookID uint, limit int) ([]models.WebhookLog, error) {
	var logs []models.WebhookLog
	err := r.db.Where("webhook_id = ?", webhookID).Order("id desc").Limit(limit).Find(&logs).Error
	return logs, err
}
