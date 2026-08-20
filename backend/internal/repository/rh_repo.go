package repository

import (
	"github.com/assettrack/backend/internal/models"
	"gorm.io/gorm"
)

type RHRepository struct {
	db *gorm.DB
}

func NewRHRepository(db *gorm.DB) *RHRepository {
	return &RHRepository{db: db}
}

func (r *RHRepository) ListTermos() ([]models.TermoResponsabilidade, error) {
	var termos []models.TermoResponsabilidade
	err := r.db.Preload("Usuario").Preload("Asset").Preload("Solicitacao").Find(&termos).Error
	return termos, err
}

func (r *RHRepository) GetTermoByID(id uint) (*models.TermoResponsabilidade, error) {
	var termo models.TermoResponsabilidade
	err := r.db.Preload("Usuario").Preload("Asset").Preload("Solicitacao").First(&termo, id).Error
	return &termo, err
}

func (r *RHRepository) CreateTermo(termo *models.TermoResponsabilidade) error {
	return r.db.Create(termo).Error
}

func (r *RHRepository) UpdateTermo(termo *models.TermoResponsabilidade) error {
	return r.db.Save(termo).Error
}

func (r *RHRepository) GetPendingSolicitacoesRH() ([]models.Solicitacao, error) {
	var solicitacoes []models.Solicitacao
	// Solicitacoes Entregues that do not have a termo yet
	subQuery := r.db.Model(&models.TermoResponsabilidade{}).Select("solicitacao_id").Where("solicitacao_id IS NOT NULL")
	err := r.db.Preload("Solicitante").Preload("Asset").
		Joins("JOIN assets ON assets.id = solicitacoes.asset_id").
		Where("solicitacoes.status = ?", "Entregue").
		Where("assets.requer_termo_rh = ?", true).
		Where("solicitacoes.id NOT IN (?)", subQuery).
		Find(&solicitacoes).Error
	return solicitacoes, err
}

func (r *RHRepository) GetSolicitacaoWithDetails(id uint) (*models.Solicitacao, error) {
	var sol models.Solicitacao
	err := r.db.Preload("Solicitante").Preload("Asset").First(&sol, id).Error
	return &sol, err
}
