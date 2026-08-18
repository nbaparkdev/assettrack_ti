package repository

import (
	"context"

	"github.com/assettrack/backend/internal/models"
	"gorm.io/gorm"
)

type EmailLogRepository interface {
	Create(ctx context.Context, log *models.EmailLog) error
	List(ctx context.Context, limit int, offset int) ([]models.EmailLog, int64, error)
}

type emailLogRepository struct {
	db *gorm.DB
}

func NewEmailLogRepository(db *gorm.DB) EmailLogRepository {
	return &emailLogRepository{db: db}
}

func (r *emailLogRepository) Create(ctx context.Context, log *models.EmailLog) error {
	return r.db.WithContext(ctx).Create(log).Error
}

func (r *emailLogRepository) List(ctx context.Context, limit int, offset int) ([]models.EmailLog, int64, error) {
	var logs []models.EmailLog
	var total int64

	err := r.db.WithContext(ctx).Model(&models.EmailLog{}).Count(&total).Error
	if err != nil {
		return nil, 0, err
	}

	err = r.db.WithContext(ctx).Order("sent_at desc").Limit(limit).Offset(offset).Find(&logs).Error
	if err != nil {
		return nil, 0, err
	}

	return logs, total, nil
}
