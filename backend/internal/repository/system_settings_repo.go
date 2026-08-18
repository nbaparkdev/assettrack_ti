package repository

import (
	"context"

	"github.com/assettrack/backend/internal/models"
	"gorm.io/gorm"
)

type SystemSettingsRepository interface {
	GetSetting(ctx context.Context, key string) (*models.SystemSetting, error)
	GetAllSettings(ctx context.Context) ([]models.SystemSetting, error)
	SetSetting(ctx context.Context, key string, value string, descricao *string) error
}

type systemSettingsRepository struct {
	db *gorm.DB
}

func NewSystemSettingsRepository(db *gorm.DB) SystemSettingsRepository {
	return &systemSettingsRepository{db: db}
}

func (r *systemSettingsRepository) GetSetting(ctx context.Context, key string) (*models.SystemSetting, error) {
	var setting models.SystemSetting
	err := r.db.WithContext(ctx).Where("setting_key = ?", key).First(&setting).Error
	if err != nil {
		return nil, err
	}
	return &setting, nil
}

func (r *systemSettingsRepository) GetAllSettings(ctx context.Context) ([]models.SystemSetting, error) {
	var settings []models.SystemSetting
	err := r.db.WithContext(ctx).Find(&settings).Error
	if err != nil {
		return nil, err
	}
	return settings, nil
}

func (r *systemSettingsRepository) SetSetting(ctx context.Context, key string, value string, descricao *string) error {
	var setting models.SystemSetting
	err := r.db.WithContext(ctx).Where("setting_key = ?", key).First(&setting).Error

	if err == gorm.ErrRecordNotFound {
		// Create
		newSetting := models.SystemSetting{
			SettingKey:   key,
			SettingValue: value,
			Descricao:    descricao,
		}
		return r.db.WithContext(ctx).Create(&newSetting).Error
	} else if err != nil {
		return err
	}

	// Update
	setting.SettingValue = value
	if descricao != nil {
		setting.Descricao = descricao
	}
	return r.db.WithContext(ctx).Save(&setting).Error
}
