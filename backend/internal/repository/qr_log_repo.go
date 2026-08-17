package repository

import (
	"github.com/assettrack/backend/internal/models"
	"gorm.io/gorm"
)

type QRLogRepository struct {
	db *gorm.DB
}

func NewQRLogRepository(db *gorm.DB) *QRLogRepository {
	return &QRLogRepository{db: db}
}

func (r *QRLogRepository) Create(log *models.QRLog) error {
	return r.db.Create(log).Error
}
