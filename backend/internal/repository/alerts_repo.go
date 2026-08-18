package repository

import (
	"time"

	"github.com/assettrack/backend/internal/models"
	"gorm.io/gorm"
)

type EmergencyAlertRepository struct {
	db *gorm.DB
}

func NewEmergencyAlertRepository(db *gorm.DB) *EmergencyAlertRepository {
	return &EmergencyAlertRepository{db: db}
}

func (r *EmergencyAlertRepository) Create(alert *models.EmergencyAlert) error {
	return r.db.Create(alert).Error
}

func (r *EmergencyAlertRepository) History(limit int) ([]models.EmergencyAlert, error) {
	var alerts []models.EmergencyAlert
	err := r.db.Preload("Usuario").Preload("CientePor").Preload("AtendidoPor").
		Order("created_at desc").Limit(limit).Find(&alerts).Error
	return alerts, err
}

func (r *EmergencyAlertRepository) GetByID(id uint) (*models.EmergencyAlert, error) {
	var alert models.EmergencyAlert
	err := r.db.First(&alert, id).Error
	if err != nil {
		return nil, err
	}
	return &alert, nil
}

func (r *EmergencyAlertRepository) MarkAtendido(id, userID uint) error {
	return r.db.Model(&models.EmergencyAlert{}).Where("id = ?", id).
		Updates(map[string]interface{}{"atendido": true, "atendido_por_id": userID}).Error
}

func (r *EmergencyAlertRepository) MarkCiente(id, userID uint) error {
	now := time.Now()
	return r.db.Model(&models.EmergencyAlert{}).Where("id = ?", id).
		Updates(map[string]interface{}{
			"ciente":        true,
			"ciente_por_id": userID,
			"ciente_em":     &now,
		}).Error
}

type AvisoRepository struct {
	db *gorm.DB
}

func NewAvisoRepository(db *gorm.DB) *AvisoRepository {
	return &AvisoRepository{db: db}
}

func (r *AvisoRepository) List() ([]models.Aviso, error) {
	var avisos []models.Aviso
	err := r.db.Order("data_cadastro desc").Find(&avisos).Error
	return avisos, err
}

// ListActive returns avisos currently active and within their scheduling window.
func (r *AvisoRepository) ListActive(now time.Time) ([]models.Aviso, error) {
	var avisos []models.Aviso
	err := r.db.Where("ativo = true").
		Where("(programado_inicio IS NULL OR programado_inicio <= ?)", now).
		Where("(programado_fim IS NULL OR programado_fim >= ?)", now).
		Order("data_cadastro desc").Find(&avisos).Error
	return avisos, err
}

func (r *AvisoRepository) Create(aviso *models.Aviso) error {
	return r.db.Create(aviso).Error
}

func (r *AvisoRepository) Update(aviso *models.Aviso) error {
	return r.db.Save(aviso).Error
}

func (r *AvisoRepository) Delete(id uint) error {
	return r.db.Delete(&models.Aviso{}, id).Error
}

func (r *AvisoRepository) GetByID(id uint) (*models.Aviso, error) {
	var aviso models.Aviso
	err := r.db.First(&aviso, id).Error
	if err != nil {
		return nil, err
	}
	return &aviso, nil
}
