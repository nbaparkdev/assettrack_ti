package repository

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/assettrack/backend/internal/models"
	"gorm.io/gorm"
)

// ---------- Categories ----------

type ProcurementCategoryRepository struct {
	db *gorm.DB
}

func NewProcurementCategoryRepository(db *gorm.DB) *ProcurementCategoryRepository {
	return &ProcurementCategoryRepository{db: db}
}

func (r *ProcurementCategoryRepository) List() ([]models.PurchaseCategory, error) {
	var items []models.PurchaseCategory
	err := r.db.Order("nome asc").Find(&items).Error
	return items, err
}

func (r *ProcurementCategoryRepository) GetByID(id uint) (*models.PurchaseCategory, error) {
	var item models.PurchaseCategory
	if err := r.db.First(&item, id).Error; err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementCategoryRepository) GetByName(nome string) (*models.PurchaseCategory, error) {
	var item models.PurchaseCategory
	if err := r.db.Where("nome = ?", nome).First(&item).Error; err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementCategoryRepository) First() (*models.PurchaseCategory, error) {
	var item models.PurchaseCategory
	if err := r.db.First(&item).Error; err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementCategoryRepository) Create(item *models.PurchaseCategory) error {
	return r.db.Create(item).Error
}

// ---------- Units ----------

type ProcurementUnitRepository struct {
	db *gorm.DB
}

func NewProcurementUnitRepository(db *gorm.DB) *ProcurementUnitRepository {
	return &ProcurementUnitRepository{db: db}
}

func (r *ProcurementUnitRepository) List() ([]models.PurchaseUnit, error) {
	var items []models.PurchaseUnit
	err := r.db.Order("sigla asc").Find(&items).Error
	return items, err
}

func (r *ProcurementUnitRepository) Create(item *models.PurchaseUnit) error {
	return r.db.Create(item).Error
}

// ---------- Products ----------

type ProcurementProductRepository struct {
	db *gorm.DB
}

func NewProcurementProductRepository(db *gorm.DB) *ProcurementProductRepository {
	return &ProcurementProductRepository{db: db}
}

func (r *ProcurementProductRepository) List(skip, limit int) ([]models.PurchaseProduct, error) {
	var items []models.PurchaseProduct
	err := r.db.Preload("Categoria").Order("nome asc").Offset(skip).Limit(limit).Find(&items).Error
	return items, err
}

func (r *ProcurementProductRepository) GetByID(id uint) (*models.PurchaseProduct, error) {
	var item models.PurchaseProduct
	if err := r.db.Preload("Categoria").First(&item, id).Error; err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementProductRepository) GetByCodigo(codigo string) (*models.PurchaseProduct, error) {
	var item models.PurchaseProduct
	if err := r.db.Where("codigo = ?", codigo).First(&item).Error; err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementProductRepository) GetByName(nome string) (*models.PurchaseProduct, error) {
	var item models.PurchaseProduct
	if err := r.db.Where("LOWER(nome) = LOWER(?)", strings.TrimSpace(nome)).First(&item).Error; err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementProductRepository) Create(item *models.PurchaseProduct) error {
	return r.db.Create(item).Error
}

func (r *ProcurementProductRepository) Update(item *models.PurchaseProduct) error {
	return r.db.Save(item).Error
}

// ---------- Cost Centers ----------

type ProcurementCostCenterRepository struct {
	db *gorm.DB
}

func NewProcurementCostCenterRepository(db *gorm.DB) *ProcurementCostCenterRepository {
	return &ProcurementCostCenterRepository{db: db}
}

func (r *ProcurementCostCenterRepository) List() ([]models.CostCenter, error) {
	var items []models.CostCenter
	err := r.db.Preload("Departamento").Preload("Responsavel").Order("nome asc").Find(&items).Error
	return items, err
}

func (r *ProcurementCostCenterRepository) GetByID(id uint) (*models.CostCenter, error) {
	var item models.CostCenter
	if err := r.db.Preload("Departamento").Preload("Responsavel").First(&item, id).Error; err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementCostCenterRepository) FirstByDepartamento(deptID uint) (*models.CostCenter, error) {
	var item models.CostCenter
	if err := r.db.Where("departamento_id = ?", deptID).First(&item).Error; err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementCostCenterRepository) First() (*models.CostCenter, error) {
	var item models.CostCenter
	if err := r.db.First(&item).Error; err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementCostCenterRepository) Create(item *models.CostCenter) error {
	return r.db.Create(item).Error
}

func (r *ProcurementCostCenterRepository) Update(item *models.CostCenter) error {
	return r.db.Save(item).Error
}

func (r *ProcurementCostCenterRepository) Delete(id uint) error {
	return r.db.Delete(&models.CostCenter{}, id).Error
}

func (r *ProcurementCostCenterRepository) HasRequests(id uint) (bool, error) {
	var count int64
	err := r.db.Model(&models.PurchaseRequest{}).Where("centro_custo_id = ?", id).Count(&count).Error
	return count > 0, err
}

// ---------- Requests ----------

type ProcurementRequestRepository struct {
	db *gorm.DB
}

func NewProcurementRequestRepository(db *gorm.DB) *ProcurementRequestRepository {
	return &ProcurementRequestRepository{db: db}
}

func (r *ProcurementRequestRepository) List(status string, skip, limit int) ([]models.PurchaseRequest, error) {
	var items []models.PurchaseRequest
	q := r.db.Preload("Solicitante").Preload("Departamento").Preload("CentroCusto").Preload("Itens.Product")
	if status != "" {
		q = q.Where("status = ?", status)
	}
	err := q.Order("data_criacao desc").Offset(skip).Limit(limit).Find(&items).Error
	return items, err
}

func (r *ProcurementRequestRepository) GetByID(id uint) (*models.PurchaseRequest, error) {
	var item models.PurchaseRequest
	err := r.db.Preload("Solicitante").Preload("Departamento").Preload("CentroCusto").
		Preload("Itens.Product").Preload("Itens.FornecedorSugerido").
		Preload("Approvals.Aprovador").
		First(&item, id).Error
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementRequestRepository) Create(item *models.PurchaseRequest) error {
	return r.db.Create(item).Error
}

func (r *ProcurementRequestRepository) Update(item *models.PurchaseRequest) error {
	return r.db.Save(item).Error
}

var scNumberRegex = regexp.MustCompile(`SC-\d{4}-(\d+)`)

// GenerateRequestNumber creates SC-YYYY-NNNNNN (sequential per year, gap-aware).
func (r *ProcurementRequestRepository) GenerateRequestNumber(now time.Time) (string, error) {
	prefix := fmt.Sprintf("SC-%d-", now.Year())
	var numeros []string
	if err := r.db.Model(&models.PurchaseRequest{}).
		Where("numero LIKE ?", prefix+"%").Pluck("numero", &numeros).Error; err != nil {
		return "", err
	}
	maxSeq := 0
	for _, num := range numeros {
		m := scNumberRegex.FindStringSubmatch(num)
		if m != nil {
			if v, err := strconv.Atoi(m[1]); err == nil && v > maxSeq {
				maxSeq = v
			}
		}
	}
	return fmt.Sprintf("SC-%d-%06d", now.Year(), maxSeq+1), nil
}

// ---------- Approvals ----------

type ProcurementApprovalRepository struct {
	db *gorm.DB
}

func NewProcurementApprovalRepository(db *gorm.DB) *ProcurementApprovalRepository {
	return &ProcurementApprovalRepository{db: db}
}

func (r *ProcurementApprovalRepository) Create(item *models.PurchaseApproval) error {
	return r.db.Create(item).Error
}

// ---------- Quotations ----------

type ProcurementQuotationRepository struct {
	db *gorm.DB
}

func NewProcurementQuotationRepository(db *gorm.DB) *ProcurementQuotationRepository {
	return &ProcurementQuotationRepository{db: db}
}

func (r *ProcurementQuotationRepository) List() ([]models.PurchaseQuotation, error) {
	var items []models.PurchaseQuotation
	err := r.db.Preload("Request").Preload("Suppliers.Fornecedor").Order("data_criacao desc").Find(&items).Error
	return items, err
}

func (r *ProcurementQuotationRepository) GetByID(id uint) (*models.PurchaseQuotation, error) {
	var item models.PurchaseQuotation
	err := r.db.Preload("Request").Preload("Suppliers.Fornecedor").
		Preload("Suppliers.Itens.Product").
		First(&item, id).Error
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementQuotationRepository) Create(item *models.PurchaseQuotation) error {
	return r.db.Create(item).Error
}

func (r *ProcurementQuotationRepository) Update(item *models.PurchaseQuotation) error {
	return r.db.Save(item).Error
}

var cqNumberRegex = regexp.MustCompile(`CQ-\d{4}-(\d+)`)

// GenerateQuotationNumber creates CQ-YYYY-NNNNNN.
func (r *ProcurementQuotationRepository) GenerateQuotationNumber(now time.Time) (string, error) {
	prefix := fmt.Sprintf("CQ-%d-", now.Year())
	var numeros []string
	if err := r.db.Model(&models.PurchaseQuotation{}).
		Where("numero LIKE ?", prefix+"%").Pluck("numero", &numeros).Error; err != nil {
		return "", err
	}
	maxSeq := 0
	for _, num := range numeros {
		m := cqNumberRegex.FindStringSubmatch(num)
		if m != nil {
			if v, err := strconv.Atoi(m[1]); err == nil && v > maxSeq {
				maxSeq = v
			}
		}
	}
	return fmt.Sprintf("CQ-%d-%06d", now.Year(), maxSeq+1), nil
}

func (r *ProcurementQuotationRepository) GetSupplierByID(id uint) (*models.PurchaseQuotationSupplier, error) {
	var item models.PurchaseQuotationSupplier
	if err := r.db.Preload("Itens").First(&item, id).Error; err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementQuotationRepository) UpdateSupplier(item *models.PurchaseQuotationSupplier) error {
	return r.db.Save(item).Error
}

// ---------- Orders ----------

type ProcurementOrderRepository struct {
	db *gorm.DB
}

func NewProcurementOrderRepository(db *gorm.DB) *ProcurementOrderRepository {
	return &ProcurementOrderRepository{db: db}
}

func (r *ProcurementOrderRepository) List(status string, skip, limit int) ([]models.PurchaseOrder, error) {
	var items []models.PurchaseOrder
	q := r.db.Preload("Fornecedor").Preload("CentroCusto").Preload("Request").Preload("Itens.Product")
	if status != "" {
		q = q.Where("status = ?", status)
	}
	err := q.Order("data_emissao desc").Offset(skip).Limit(limit).Find(&items).Error
	return items, err
}

func (r *ProcurementOrderRepository) GetByID(id uint) (*models.PurchaseOrder, error) {
	var item models.PurchaseOrder
	err := r.db.Preload("Fornecedor").Preload("CentroCusto").Preload("Request").
		Preload("Itens.Product").Preload("Receivings.Responsavel").
		First(&item, id).Error
	if err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementOrderRepository) Create(item *models.PurchaseOrder) error {
	return r.db.Create(item).Error
}

func (r *ProcurementOrderRepository) Update(item *models.PurchaseOrder) error {
	return r.db.Save(item).Error
}

var pcNumberRegex = regexp.MustCompile(`PC-\d{4}-(\d+)`)

// GenerateOrderNumber creates PC-YYYY-NNNNNN.
func (r *ProcurementOrderRepository) GenerateOrderNumber(now time.Time) (string, error) {
	prefix := fmt.Sprintf("PC-%d-", now.Year())
	var numeros []string
	if err := r.db.Model(&models.PurchaseOrder{}).
		Where("numero LIKE ?", prefix+"%").Pluck("numero", &numeros).Error; err != nil {
		return "", err
	}
	maxSeq := 0
	for _, num := range numeros {
		m := pcNumberRegex.FindStringSubmatch(num)
		if m != nil {
			if v, err := strconv.Atoi(m[1]); err == nil && v > maxSeq {
				maxSeq = v
			}
		}
	}
	return fmt.Sprintf("PC-%d-%06d", now.Year(), maxSeq+1), nil
}

// ---------- Receivings ----------

type ProcurementReceivingRepository struct {
	db *gorm.DB
}

func NewProcurementReceivingRepository(db *gorm.DB) *ProcurementReceivingRepository {
	return &ProcurementReceivingRepository{db: db}
}

func (r *ProcurementReceivingRepository) Create(item *models.PurchaseReceiving) error {
	return r.db.Create(item).Error
}

func (r *ProcurementReceivingRepository) GetByID(id uint) (*models.PurchaseReceiving, error) {
	var item models.PurchaseReceiving
	if err := r.db.Preload("Order").Preload("Itens.Product").First(&item, id).Error; err != nil {
		return nil, err
	}
	return &item, nil
}

// ---------- Stock ----------

type ProcurementStockRepository struct {
	db *gorm.DB
}

func NewProcurementStockRepository(db *gorm.DB) *ProcurementStockRepository {
	return &ProcurementStockRepository{db: db}
}

func (r *ProcurementStockRepository) List() ([]models.MaterialStock, error) {
	var items []models.MaterialStock
	err := r.db.Preload("Product.Categoria").Order("id asc").Find(&items).Error
	return items, err
}

func (r *ProcurementStockRepository) GetByID(id uint) (*models.MaterialStock, error) {
	var item models.MaterialStock
	if err := r.db.Preload("Product").First(&item, id).Error; err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementStockRepository) GetByProductID(productID uint) (*models.MaterialStock, error) {
	var item models.MaterialStock
	if err := r.db.Where("product_id = ?", productID).First(&item).Error; err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementStockRepository) Create(item *models.MaterialStock) error {
	return r.db.Create(item).Error
}

func (r *ProcurementStockRepository) Update(item *models.MaterialStock) error {
	return r.db.Save(item).Error
}

// CreateOrUpdate adjusts stock balance and records a transaction (mirrors create_or_update_stock).
func (r *ProcurementStockRepository) CreateOrUpdate(
	productID uint, quantidade float64, tipo string, userID uint, justificativa string, origemTabela string, origemID *uint,
) (*models.MaterialStock, error) {
	stock, err := r.GetByProductID(productID)
	if err != nil {
		stock = &models.MaterialStock{ProductID: productID, QuantidadeSaldo: 0}
		if err := r.db.Create(stock).Error; err != nil {
			return nil, err
		}
	}
	if tipo == models.StockEntrada {
		stock.QuantidadeSaldo += quantidade
	} else {
		stock.QuantidadeSaldo -= quantidade
	}
	if err := r.db.Save(stock).Error; err != nil {
		return nil, err
	}
	var just *string
	if justificativa != "" {
		just = &justificativa
	}
	var origem *string
	if origemTabela != "" {
		origem = &origemTabela
	}
	tx := &models.MaterialStockTransaction{
		ProductID:        productID,
		Quantidade:       quantidade,
		TipoMovimentacao: tipo,
		OrigemTabela:     origem,
		OrigemID:         origemID,
		UserID:           userID,
		Justificativa:    just,
	}
	if err := r.db.Create(tx).Error; err != nil {
		return nil, err
	}
	return stock, nil
}

func (r *ProcurementStockRepository) ListTransactions(productID uint, limit int) ([]models.MaterialStockTransaction, error) {
	var items []models.MaterialStockTransaction
	q := r.db.Preload("User")
	if productID != 0 {
		q = q.Where("product_id = ?", productID)
	}
	err := q.Order("data_transacao desc").Limit(limit).Find(&items).Error
	return items, err
}

// ---------- Contracts ----------

type ProcurementContractRepository struct {
	db *gorm.DB
}

func NewProcurementContractRepository(db *gorm.DB) *ProcurementContractRepository {
	return &ProcurementContractRepository{db: db}
}

func (r *ProcurementContractRepository) List() ([]models.PurchaseContract, error) {
	var items []models.PurchaseContract
	err := r.db.Preload("Fornecedor").Preload("TipoContrato").Order("data_fim asc").Find(&items).Error
	return items, err
}

func (r *ProcurementContractRepository) GetByID(id uint) (*models.PurchaseContract, error) {
	var item models.PurchaseContract
	if err := r.db.Preload("Fornecedor").Preload("TipoContrato").First(&item, id).Error; err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementContractRepository) Create(item *models.PurchaseContract) error {
	return r.db.Create(item).Error
}

func (r *ProcurementContractRepository) Update(item *models.PurchaseContract) error {
	return r.db.Save(item).Error
}

func (r *ProcurementContractRepository) Delete(id uint) error {
	return r.db.Delete(&models.PurchaseContract{}, id).Error
}

// ---------- Contract Types ----------

type ProcurementContractTypeRepository struct {
	db *gorm.DB
}

func NewProcurementContractTypeRepository(db *gorm.DB) *ProcurementContractTypeRepository {
	return &ProcurementContractTypeRepository{db: db}
}

func (r *ProcurementContractTypeRepository) List(onlyActive bool) ([]models.ContractType, error) {
	var items []models.ContractType
	q := r.db.Order("nome asc")
	if onlyActive {
		q = q.Where("ativo = true")
	}
	err := q.Find(&items).Error
	return items, err
}

func (r *ProcurementContractTypeRepository) GetByID(id uint) (*models.ContractType, error) {
	var item models.ContractType
	if err := r.db.First(&item, id).Error; err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementContractTypeRepository) Create(item *models.ContractType) error {
	return r.db.Create(item).Error
}

func (r *ProcurementContractTypeRepository) Update(item *models.ContractType) error {
	return r.db.Save(item).Error
}

func (r *ProcurementContractTypeRepository) Delete(id uint) error {
	return r.db.Delete(&models.ContractType{}, id).Error
}

func (r *ProcurementContractTypeRepository) HasContracts(id uint) (bool, error) {
	var count int64
	err := r.db.Model(&models.PurchaseContract{}).Where("tipo_id = ?", id).Count(&count).Error
	return count > 0, err
}

// ---------- History ----------

type ProcurementHistoryRepository struct {
	db *gorm.DB
}

func NewProcurementHistoryRepository(db *gorm.DB) *ProcurementHistoryRepository {
	return &ProcurementHistoryRepository{db: db}
}

func (r *ProcurementHistoryRepository) Create(item *models.PurchaseHistory) error {
	return r.db.Create(item).Error
}

// ---------- Notifications ----------

type ProcurementNotificationRepository struct {
	db *gorm.DB
}

func NewProcurementNotificationRepository(db *gorm.DB) *ProcurementNotificationRepository {
	return &ProcurementNotificationRepository{db: db}
}

func (r *ProcurementNotificationRepository) Create(item *models.PurchaseNotification) error {
	return r.db.Create(item).Error
}

func (r *ProcurementNotificationRepository) ListByUser(userID uint) ([]models.PurchaseNotification, error) {
	var items []models.PurchaseNotification
	err := r.db.Where("user_id = ?", userID).Order("data_criacao desc").Limit(50).Find(&items).Error
	return items, err
}

func (r *ProcurementNotificationRepository) MarkAllRead(userID uint) error {
	return r.db.Model(&models.PurchaseNotification{}).
		Where("user_id = ? AND lido = false", userID).
		Update("lido", true).Error
}

// ---------- Researches ----------

type ProcurementResearchRepository struct {
	db *gorm.DB
}

func NewProcurementResearchRepository(db *gorm.DB) *ProcurementResearchRepository {
	return &ProcurementResearchRepository{db: db}
}

func (r *ProcurementResearchRepository) List() ([]models.PurchaseResearch, error) {
	var items []models.PurchaseResearch
	err := r.db.Preload("Solicitante").Preload("Items").Order("data_criacao desc").Find(&items).Error
	return items, err
}

func (r *ProcurementResearchRepository) GetByID(id uint) (*models.PurchaseResearch, error) {
	var item models.PurchaseResearch
	if err := r.db.Preload("Solicitante").Preload("Items").First(&item, id).Error; err != nil {
		return nil, err
	}
	return &item, nil
}

func (r *ProcurementResearchRepository) Create(item *models.PurchaseResearch) error {
	return r.db.Create(item).Error
}

func (r *ProcurementResearchRepository) Update(item *models.PurchaseResearch) error {
	return r.db.Save(item).Error
}

var pqNumberRegex = regexp.MustCompile(`PQ-\d{4}-(\d+)`)

// GenerateResearchNumber creates PQ-YYYY-NNNNNN.
func (r *ProcurementResearchRepository) GenerateResearchNumber(now time.Time) (string, error) {
	prefix := fmt.Sprintf("PQ-%d-", now.Year())
	var numeros []string
	if err := r.db.Model(&models.PurchaseResearch{}).
		Where("numero LIKE ?", prefix+"%").Pluck("numero", &numeros).Error; err != nil {
		return "", err
	}
	maxSeq := 0
	for _, num := range numeros {
		m := pqNumberRegex.FindStringSubmatch(num)
		if m != nil {
			if v, err := strconv.Atoi(m[1]); err == nil && v > maxSeq {
				maxSeq = v
			}
		}
	}
	return fmt.Sprintf("PQ-%d-%06d", now.Year(), maxSeq+1), nil
}
