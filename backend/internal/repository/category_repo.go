package repository

import (
	"github.com/assettrack/backend/internal/models"
	"gorm.io/gorm"
)

type AssetCategoryRepository struct {
	db *gorm.DB
}

func NewAssetCategoryRepository(db *gorm.DB) *AssetCategoryRepository {
	return &AssetCategoryRepository{db: db}
}

func (r *AssetCategoryRepository) List(skip, limit int) ([]models.AssetCategory, error) {
	var cats []models.AssetCategory
	err := r.db.Offset(skip).Limit(limit).Order("nome asc").Find(&cats).Error
	return cats, err
}

func (r *AssetCategoryRepository) GetByID(id uint) (*models.AssetCategory, error) {
	var cat models.AssetCategory
	err := r.db.First(&cat, id).Error
	if err != nil {
		return nil, err
	}
	return &cat, nil
}

func (r *AssetCategoryRepository) GetByName(name string) (*models.AssetCategory, error) {
	var cat models.AssetCategory
	err := r.db.Where("nome = ?", name).First(&cat).Error
	if err != nil {
		return nil, err
	}
	return &cat, nil
}

func (r *AssetCategoryRepository) Create(cat *models.AssetCategory) error {
	return r.db.Create(cat).Error
}

func (r *AssetCategoryRepository) Update(cat *models.AssetCategory) error {
	return r.db.Save(cat).Error
}

func (r *AssetCategoryRepository) Delete(id uint) error {
	return r.db.Delete(&models.AssetCategory{}, id).Error
}
