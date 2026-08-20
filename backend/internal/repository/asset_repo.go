package repository

import (
	"errors"

	"github.com/assettrack/backend/internal/models"
	"gorm.io/gorm"
)

type AssetRepository struct {
	db *gorm.DB
}

func (r *AssetRepository) DB() *gorm.DB {
	return r.db
}

type AssetListFilters struct {
	EPatrimonio   string
	Nome          string
	CategoriaID   uint
	LocalizacaoID uint
	FornecedorID  uint
	NotaFiscal    string
	Status        string
	DataInicio    string
	DataFim       string
}

func NewAssetRepository(db *gorm.DB) *AssetRepository {
	return &AssetRepository{db: db}
}

func (r *AssetRepository) List(skip, limit int, ePatrimonio string) ([]models.Asset, error) {
	return r.ListWithFilters(skip, limit, AssetListFilters{EPatrimonio: ePatrimonio})
}

func (r *AssetRepository) ListWithFilters(skip, limit int, filters AssetListFilters) ([]models.Asset, error) {
	var assets []models.Asset
	query := r.db.Model(&models.Asset{}).
		Preload("CurrentUser").
		Preload("CurrentDepartamento").
		Preload("CurrentLocal").
		Preload("CurrentArmazenamento").
		Preload("PrevLocal").
		Preload("PrevArmazenamento").
		Preload("Fornecedor").
		Preload("NotaFiscal").
		Preload("Categoria")

	if filters.EPatrimonio != "" {
		query = query.Where("e_patrimonio ILIKE ?", "%"+filters.EPatrimonio+"%")
	}
	if filters.Nome != "" {
		query = query.Where("nome ILIKE ?", "%"+filters.Nome+"%")
	}
	if filters.CategoriaID != 0 {
		query = query.Where("categoria_id = ?", filters.CategoriaID)
	}
	if filters.LocalizacaoID != 0 {
		query = query.Where("current_local_id = ?", filters.LocalizacaoID)
	}
	if filters.FornecedorID != 0 {
		query = query.Where("fornecedor_id = ?", filters.FornecedorID)
	}
	if filters.NotaFiscal != "" {
		query = query.Joins("LEFT JOIN notas_fiscais ON notas_fiscais.id = assets.nota_fiscal_id").
			Where("notas_fiscais.numero_nota ILIKE ?", "%"+filters.NotaFiscal+"%")
	}
	if filters.Status == "ativo_fixo" {
		query = query.Where("bloqueado = ?", true)
	} else if filters.Status != "" {
		query = query.Where("status = ?", filters.Status)
	}
	if filters.DataInicio != "" {
		query = query.Where("data_aquisicao >= ?", filters.DataInicio)
	}
	if filters.DataFim != "" {
		query = query.Where("data_aquisicao <= ?", filters.DataFim)
	}

	err := query.Offset(skip).Limit(limit).Order("id desc").Find(&assets).Error
	return assets, err
}

func (r *AssetRepository) GetByID(id uint) (*models.Asset, error) {
	var asset models.Asset
	err := r.db.Model(&models.Asset{}).
		Preload("CurrentUser").
		Preload("CurrentDepartamento").
		Preload("CurrentLocal").
		Preload("CurrentArmazenamento").
		Preload("PrevLocal").
		Preload("PrevArmazenamento").
		Preload("Fornecedor").
		Preload("NotaFiscal").
		Preload("Categoria").
		First(&asset, id).Error
	if err != nil {
		return nil, err
	}
	return &asset, nil
}

func (r *AssetRepository) GetByEPatrimonio(ePatrimonio string) (*models.Asset, error) {
	var asset models.Asset
	err := r.db.Model(&models.Asset{}).
		Preload("CurrentUser").
		Preload("CurrentDepartamento").
		Preload("CurrentLocal").
		Preload("CurrentArmazenamento").
		Preload("PrevLocal").
		Preload("PrevArmazenamento").
		Preload("Fornecedor").
		Preload("NotaFiscal").
		Preload("Categoria").
		Where("e_patrimonio = ?", ePatrimonio).First(&asset).Error
	if err != nil {
		return nil, err
	}
	return &asset, nil
}

func (r *AssetRepository) Create(asset *models.Asset) error {
	return r.db.Create(asset).Error
}

func (r *AssetRepository) Update(updated *models.Asset) error {
	// Retrieve existing record to check state transition and locking rules
	var existing models.Asset
	if err := r.db.First(&existing, updated.ID).Error; err != nil {
		return err
	}

	// Rule: If marked as Bloqueado (Ativo Fixo)
	if existing.Bloqueado {
		// 1. Entering maintenance: status changes to "Manutenção"
		if existing.Status != models.AssetStatusManutencao && updated.Status == models.AssetStatusManutencao {
			prevStatusStr := string(existing.Status)
			updated.PrevStatus = &prevStatusStr
			updated.PrevUserID = existing.CurrentUserID
			updated.PrevDepartamentoID = existing.CurrentDepartamentoID
			updated.PrevLocalID = existing.CurrentLocalID
			updated.PrevArmazenamentoID = existing.CurrentArmazenamentoID
		}

		// 2. While in maintenance, block any changes to locations/assignments
		if existing.Status == models.AssetStatusManutencao && updated.Status == models.AssetStatusManutencao {
			// Check if locations or user fields are being updated/modified
			if !uintPtrEqual(existing.CurrentUserID, updated.CurrentUserID) ||
				!uintPtrEqual(existing.CurrentDepartamentoID, updated.CurrentDepartamentoID) ||
				!uintPtrEqual(existing.CurrentLocalID, updated.CurrentLocalID) ||
				!uintPtrEqual(existing.CurrentArmazenamentoID, updated.CurrentArmazenamentoID) {
				return errors.New("não é permitido alterar a localização, departamento ou responsável de um Ativo Fixo bloqueado em manutenção")
			}
		}

		// 3. Leaving maintenance: status changes from "Manutenção" to something else
		if existing.Status == models.AssetStatusManutencao && updated.Status != models.AssetStatusManutencao {
			// Restore fields from previous state if stored
			if existing.PrevStatus != nil {
				updated.Status = models.AssetStatus(*existing.PrevStatus)
			}
			updated.CurrentUserID = existing.PrevUserID
			updated.CurrentDepartamentoID = existing.PrevDepartamentoID
			updated.CurrentLocalID = existing.PrevLocalID
			updated.CurrentArmazenamentoID = existing.PrevArmazenamentoID

			// Clear prev_* columns
			updated.PrevStatus = nil
			updated.PrevUserID = nil
			updated.PrevDepartamentoID = nil
			updated.PrevLocalID = nil
			updated.PrevArmazenamentoID = nil
		}
	}

	// Update record using db.Select("*").Save (saves all fields including nil/zeros)
	return r.db.Select("*").Save(updated).Error
}

func (r *AssetRepository) Delete(id uint) error {
	return r.db.Delete(&models.Asset{}, id).Error
}

// GetReferences returns the list of departments, locations, categories, storages, and suppliers
func (r *AssetRepository) GetReferences() (map[string]interface{}, error) {
	var cats []models.AssetCategory
	var depts []models.Departamento
	var locs []models.Localizacao
	var arms []models.Armazenamento
	var supps []models.Fornecedor

	if err := r.db.Order("nome asc").Find(&cats).Error; err != nil {
		return nil, err
	}
	if err := r.db.Order("nome asc").Find(&depts).Error; err != nil {
		return nil, err
	}
	if err := r.db.Order("nome asc").Find(&locs).Error; err != nil {
		return nil, err
	}
	if err := r.db.Order("nome asc").Find(&arms).Error; err != nil {
		return nil, err
	}
	if err := r.db.Order("nome asc").Find(&supps).Error; err != nil {
		return nil, err
	}

	refs := map[string]interface{}{
		"categorias":     cats,
		"setores":        depts,
		"localizacoes":   locs,
		"armazenamentos": arms,
		"fornecedores":   supps,
	}
	return refs, nil
}

func uintPtrEqual(a, b *uint) bool {
	if a == nil && b == nil {
		return true
	}
	if a == nil || b == nil {
		return false
	}
	return *a == *b
}

// ListByCurrentUser returns assets currently assigned to a user.
func (r *AssetRepository) ListByCurrentUser(userID uint) ([]models.Asset, error) {
	var assets []models.Asset
	err := r.db.Where("current_user_id = ? AND status = ?", userID, "EM_USO").Find(&assets).Error
	return assets, err
}
