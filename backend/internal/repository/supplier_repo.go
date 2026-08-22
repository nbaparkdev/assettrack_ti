package repository

import (
	"github.com/assettrack/backend/internal/models"
	"gorm.io/gorm"
)

type SupplierRepository struct {
	db *gorm.DB
}

func NewSupplierRepository(db *gorm.DB) *SupplierRepository {
	return &SupplierRepository{db: db}
}

func (r *SupplierRepository) List(skip, limit int) ([]models.Fornecedor, error) {
	var suppliers []models.Fornecedor
	err := r.db.Preload("NotasFiscais").Offset(skip).Limit(limit).Order("nome asc").Find(&suppliers).Error
	return suppliers, err
}

func (r *SupplierRepository) GetByID(id uint) (*models.Fornecedor, error) {
	var s models.Fornecedor
	err := r.db.Preload("NotasFiscais").First(&s, id).Error
	if err != nil {
		return nil, err
	}
	return &s, nil
}

func (r *SupplierRepository) GetByCNPJ(cnpj string) (*models.Fornecedor, error) {
	var s models.Fornecedor
	err := r.db.Where("cnpj = ?", cnpj).First(&s).Error
	if err != nil {
		return nil, err
	}
	return &s, nil
}

func (r *SupplierRepository) Create(s *models.Fornecedor) error {
	return r.db.Create(s).Error
}

func (r *SupplierRepository) Update(s *models.Fornecedor) error {
	return r.db.Save(s).Error
}

func (r *SupplierRepository) Delete(id uint) error {
	return r.db.Delete(&models.Fornecedor{}, id).Error
}

type InvoiceRepository struct {
	db *gorm.DB
}

func NewInvoiceRepository(db *gorm.DB) *InvoiceRepository {
	return &InvoiceRepository{db: db}
}

func (r *InvoiceRepository) ListBySupplier(supplierID uint) ([]models.NotaFiscal, error) {
	var invoices []models.NotaFiscal
	err := r.db.Where("fornecedor_id = ?", supplierID).Order("id desc").Find(&invoices).Error
	return invoices, err
}

func (r *InvoiceRepository) GetByID(id uint) (*models.NotaFiscal, error) {
	var nf models.NotaFiscal
	err := r.db.First(&nf, id).Error
	if err != nil {
		return nil, err
	}
	return &nf, nil
}

func (r *InvoiceRepository) GetByNumeroNota(numero string) (*models.NotaFiscal, error) {
	var nf models.NotaFiscal
	err := r.db.Where("numero_nota = ?", numero).First(&nf).Error
	if err != nil {
		return nil, err
	}
	return &nf, nil
}

func (r *InvoiceRepository) Create(nf *models.NotaFiscal) error {
	return r.db.Create(nf).Error
}

func (r *InvoiceRepository) Delete(id uint) error {
	return r.db.Delete(&models.NotaFiscal{}, id).Error
}

// CountAssetsByInvoice returns how many assets are linked to the invoice.
func (r *InvoiceRepository) CountAssetsByInvoice(invoiceID uint) (int64, error) {
	var count int64
	err := r.db.Model(&models.Asset{}).Where("nota_fiscal_id = ?", invoiceID).Count(&count).Error
	return count, err
}
