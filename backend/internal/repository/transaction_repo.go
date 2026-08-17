package repository

import (
	"time"

	"github.com/assettrack/backend/internal/models"
	"gorm.io/gorm"
)

type TransactionRepository struct {
	db *gorm.DB
}

func NewTransactionRepository(db *gorm.DB) *TransactionRepository {
	return &TransactionRepository{db: db}
}

// Movimentacao methods
func (r *TransactionRepository) ListMovements(skip, limit int) ([]models.Movimentacao, error) {
	var movs []models.Movimentacao
	err := r.db.Preload("Asset").
		Preload("DeUser").
		Preload("ParaUser").
		Order("data desc").
		Offset(skip).
		Limit(limit).
		Find(&movs).Error
	return movs, err
}

func (r *TransactionRepository) CreateMovement(mov *models.Movimentacao) error {
	mov.Data = time.Now()
	return r.db.Create(mov).Error
}

// Solicitacao methods
func (r *TransactionRepository) ListSolicitacoes(skip, limit int) ([]models.Solicitacao, error) {
	var sols []models.Solicitacao
	err := r.db.Preload("Solicitante").
		Preload("Aprovador").
		Preload("Confirmador").
		Preload("Asset").
		Order("data_solicitacao desc").
		Offset(skip).
		Limit(limit).
		Find(&sols).Error
	return sols, err
}

func (r *TransactionRepository) GetSolicitacaoByID(id uint) (*models.Solicitacao, error) {
	var sol models.Solicitacao
	err := r.db.Preload("Solicitante").
		Preload("Aprovador").
		Preload("Confirmador").
		Preload("Asset").
		First(&sol, id).Error
	if err != nil {
		return nil, err
	}
	return &sol, nil
}

func (r *TransactionRepository) CreateSolicitacao(sol *models.Solicitacao) error {
	sol.DataSolicitacao = time.Now()
	return r.db.Create(sol).Error
}

func (r *TransactionRepository) UpdateSolicitacao(sol *models.Solicitacao) error {
	return r.db.Save(sol).Error
}
