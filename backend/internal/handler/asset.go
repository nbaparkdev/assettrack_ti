package handler

import (
	"bytes"
	"encoding/csv"
	"fmt"
	_ "image/gif"
	_ "image/jpeg"
	_ "image/png"
	"io"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/repository"
	"github.com/gin-gonic/gin"
	qrcode "github.com/skip2/go-qrcode"
	qrdecoder "github.com/tuotoo/qrcode"
)

type AssetHandler struct {
	repo         *repository.AssetRepository
	categoryRepo *repository.AssetCategoryRepository
}

func NewAssetHandler(repo *repository.AssetRepository, categoryRepo *repository.AssetCategoryRepository) *AssetHandler {
	return &AssetHandler{
		repo:         repo,
		categoryRepo: categoryRepo,
	}
}

func (h *AssetHandler) List(c *gin.Context) {
	skip, _ := strconv.Atoi(c.DefaultQuery("skip", "0"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))

	assets, err := h.repo.ListWithFilters(skip, limit, buildAssetFilters(c))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, assets)
}

func (h *AssetHandler) ExportCSV(c *gin.Context) {
	assets, err := h.repo.ListWithFilters(0, 10000, buildAssetFilters(c))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	var buf bytes.Buffer
	buf.WriteString("\xEF\xBB\xBF")

	writer := csv.NewWriter(&buf)
	writer.Comma = ';'

	if err := writer.Write([]string{
		"ID",
		"E-Patrimonio",
		"Nome",
		"Modelo",
		"Numero de Serie",
		"Status",
		"Categoria",
		"Localizacao",
		"Armazenamento",
		"Fornecedor",
		"Nota Fiscal",
		"Data Aquisicao",
		"Valor",
		"Ativo Fixo",
		"Em Posse De",
	}); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Falha ao gerar CSV"})
		return
	}

	for _, asset := range assets {
		row := []string{
			strconv.FormatUint(uint64(asset.ID), 10),
			safeCSV(asset.EPatrimonio),
			safeCSV(asset.Nome),
			safeCSV(stringValue(asset.Modelo)),
			safeCSV(stringValue(asset.NumeroSerie)),
			string(asset.Status),
			safeCSV(assetCategoryName(asset)),
			safeCSV(assetLocationName(asset)),
			safeCSV(assetStorageName(asset)),
			safeCSV(assetSupplierName(asset)),
			safeCSV(assetInvoiceNumber(asset)),
			formatDate(asset.DataAquisicao),
			formatFloat(asset.Valor),
			formatBool(asset.Bloqueado),
			safeCSV(stringValue(asset.EmPosseDe)),
		}
		if err := writer.Write(row); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Falha ao gerar CSV"})
			return
		}
	}

	writer.Flush()
	if err := writer.Error(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Falha ao finalizar CSV"})
		return
	}

	filename := fmt.Sprintf("ativos_%s.csv", time.Now().Format("20060102_150405"))
	c.Header("Content-Disposition", fmt.Sprintf(`attachment; filename="%s"`, filename))
	c.Data(http.StatusOK, "text/csv; charset=utf-8", buf.Bytes())
}

func buildAssetFilters(c *gin.Context) repository.AssetListFilters {
	return repository.AssetListFilters{
		EPatrimonio:   c.Query("e_patrimonio"),
		Nome:          c.Query("nome"),
		CategoriaID:   parseUintQuery(c, "categoria_id"),
		LocalizacaoID: parseUintQuery(c, "localizacao_id"),
		FornecedorID:  parseUintQuery(c, "fornecedor_id"),
		NotaFiscal:    c.Query("nfe"),
		Status:        c.Query("status"),
		DataInicio:    c.Query("data_inicio"),
		DataFim:       c.Query("data_fim"),
	}
}

func parseUintQuery(c *gin.Context, name string) uint {
	value := c.Query(name)
	if value == "" {
		return 0
	}
	parsed, err := strconv.ParseUint(value, 10, 32)
	if err != nil {
		return 0
	}
	return uint(parsed)
}

func stringValue(value *string) string {
	if value == nil {
		return ""
	}
	return *value
}

func formatDate(value *time.Time) string {
	if value == nil {
		return ""
	}
	return value.Format("02/01/2006")
}

func formatFloat(value *float64) string {
	if value == nil {
		return ""
	}
	return fmt.Sprintf("%.2f", *value)
}

func formatBool(value bool) string {
	if value {
		return "Sim"
	}
	return "Nao"
}

func safeCSV(value string) string {
	if value == "" {
		return ""
	}
	if strings.ContainsAny(value[:1], "=+-@") {
		return "'" + value
	}
	return value
}

func assetCategoryName(asset models.Asset) string {
	if asset.Categoria == nil {
		return ""
	}
	return asset.Categoria.Nome
}

func assetLocationName(asset models.Asset) string {
	if asset.CurrentLocal == nil {
		return ""
	}
	return asset.CurrentLocal.Nome
}

func assetStorageName(asset models.Asset) string {
	if asset.CurrentArmazenamento == nil {
		return ""
	}
	return asset.CurrentArmazenamento.Nome
}

func assetSupplierName(asset models.Asset) string {
	if asset.Fornecedor == nil {
		return ""
	}
	return asset.Fornecedor.Nome
}

func assetInvoiceNumber(asset models.Asset) string {
	if asset.NotaFiscal == nil {
		return ""
	}
	return asset.NotaFiscal.NumeroNota
}

func (h *AssetHandler) GetByID(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	asset, err := h.repo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ativo não encontrado"})
		return
	}
	c.JSON(http.StatusOK, asset)
}

func (h *AssetHandler) Create(c *gin.Context) {
	var asset models.Asset
	if err := c.ShouldBindJSON(&asset); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Verify EPatrimonio uniqueness
	existing, _ := h.repo.GetByEPatrimonio(asset.EPatrimonio)
	if existing != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Ativo com este E-Patrimônio já existe"})
		return
	}

	// Set CreatedByID if auth user context is available
	if val, exists := c.Get("user_id"); exists {
		userID := val.(uint)
		asset.CreatedByID = &userID
	}

	if err := h.repo.Create(&asset); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, asset)
}

func (h *AssetHandler) Update(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	// Find existing
	asset, err := h.repo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ativo não encontrado"})
		return
	}

	oldStatus := asset.Status

	// Bind update payload into existing struct
	if err := c.ShouldBindJSON(asset); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Ensure ID stays the same
	asset.ID = uint(id)

	if err := h.repo.Update(asset); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Sync maintenance records if status changed to/from Manutenção
	newStatusLower := strings.ToLower(string(asset.Status))
	oldStatusLower := strings.ToLower(string(oldStatus))

	if (strings.Contains(newStatusLower, "manuten") || asset.Status == models.AssetStatusManutencao) && !strings.Contains(oldStatusLower, "manuten") {
		// Ensure active record exists in table manutencoes
		var count int64
		h.repo.DB().Model(&models.Manutencao{}).
			Where("asset_id = ? AND status = ?", asset.ID, models.StatusManutencaoEmAndamento).
			Count(&count)

		if count == 0 {
			var userIDPtr *uint
			if val, exists := c.Get("user_id"); exists {
				uid := val.(uint)
				userIDPtr = &uid
			}
			maint := models.Manutencao{
				AssetID:       asset.ID,
				ResponsavelID: userIDPtr,
				Motivo:        "Ativo alterado para Manutenção via cadastro de ativos",
				Tipo:          models.TipoManutencaoCorretiva,
				DataEntrada:   time.Now(),
				Status:        models.StatusManutencaoEmAndamento,
			}
			_ = h.repo.DB().Create(&maint).Error
		}
	} else if strings.Contains(oldStatusLower, "manuten") && !strings.Contains(newStatusLower, "manuten") {
		// Conclude active maintenance
		now := time.Now()
		h.repo.DB().Model(&models.Manutencao{}).
			Where("asset_id = ? AND status = ?", asset.ID, models.StatusManutencaoEmAndamento).
			Updates(map[string]interface{}{
				"status":         models.StatusManutencaoConcluida,
				"data_conclusao": &now,
			})
	}

	c.JSON(http.StatusOK, asset)
}

func (h *AssetHandler) Delete(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	if err := h.repo.Delete(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "deleted"})
}

func (h *AssetHandler) GetReferences(c *gin.Context) {
	refs, err := h.repo.GetReferences()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, refs)
}

func (h *AssetHandler) CreateCategoria(c *gin.Context) {
	var item models.AssetCategory
	if err := c.ShouldBindJSON(&item); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := h.repo.DB().Create(&item).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao criar categoria"})
		return
	}
	c.JSON(http.StatusCreated, item)
}

func (h *AssetHandler) CreateLocalizacao(c *gin.Context) {
	var item models.Localizacao
	if err := c.ShouldBindJSON(&item); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := h.repo.DB().Create(&item).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao criar localização"})
		return
	}
	c.JSON(http.StatusCreated, item)
}

func (h *AssetHandler) CreateArmazenamento(c *gin.Context) {
	var item models.Armazenamento
	if err := c.ShouldBindJSON(&item); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := h.repo.DB().Create(&item).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao criar armazenamento"})
		return
	}
	c.JSON(http.StatusCreated, item)
}

func (h *AssetHandler) CreateDepartamento(c *gin.Context) {
	var item models.Departamento
	if err := c.ShouldBindJSON(&item); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if err := h.repo.DB().Create(&item).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao criar departamento"})
		return
	}
	c.JSON(http.StatusCreated, item)
}

func (h *AssetHandler) DeleteDepartamento(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	if err := h.repo.DB().Delete(&models.Departamento{}, id).Error; err != nil {
		if strings.Contains(err.Error(), "foreign key constraint") || strings.Contains(err.Error(), "violates foreign key") || strings.Contains(err.Error(), "a foreign key constraint fails") || strings.Contains(err.Error(), "SQLSTATE 23503") {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Não é possível excluir este setor pois existem usuários ou ativos vinculados a ele."})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao excluir departamento"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"detail": "Setor excluído com sucesso"})
}
func (h *AssetHandler) GetQRCode(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	asset, err := h.repo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ativo não encontrado"})
		return
	}

	qrContent := fmt.Sprintf("assettrack://assets/ep/%s", asset.EPatrimonio)
	pngBytes, err := qrcode.Encode(qrContent, qrcode.Medium, 256)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao gerar QR Code"})
		return
	}

	c.Data(http.StatusOK, "image/png", pngBytes)
}

func (h *AssetHandler) ScanQRCode(c *gin.Context) {
	fileHeader, err := c.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Arquivo não enviado"})
		return
	}

	file, err := fileHeader.Open()
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Falha ao abrir arquivo"})
		return
	}
	defer file.Close()

	fileBytes, err := io.ReadAll(file)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Falha ao ler arquivo"})
		return
	}

	// Decode QR image bytes using pure Go qr decoder
	matrix, err := qrdecoder.Decode(bytes.NewReader(fileBytes))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Não foi possível decodificar o QR Code"})
		return
	}

	decoded := matrix.Content
	var asset *models.Asset

	if strings.Contains(decoded, "assets/ep/") {
		patrimonio := strings.Split(decoded, "assets/ep/")[1]
		asset, err = h.repo.GetByEPatrimonio(patrimonio)
	} else if strings.Contains(decoded, "assets/sn/") {
		serial := strings.Split(decoded, "assets/sn/")[1]
		asset, err = h.repo.GetByEPatrimonio(serial)
	} else if strings.Contains(decoded, "assets/") {
		assetIDStr := strings.Split(decoded, "assets/")[1]
		assetID, _ := strconv.ParseUint(assetIDStr, 10, 32)
		asset, err = h.repo.GetByID(uint(assetID))
	} else {
		// Try parsing direct ID
		assetID, errParse := strconv.ParseUint(decoded, 10, 32)
		if errParse == nil {
			asset, err = h.repo.GetByID(uint(assetID))
		}
	}

	if err != nil || asset == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ativo não encontrado com base no QR Code"})
		return
	}

	c.JSON(http.StatusOK, asset)
}

type BulkCopySpec struct {
	EPatrimonio            string  `json:"e_patrimonio" binding:"required"`
	NumeroSerie            *string `json:"numero_serie"`
	CurrentLocalID         *uint   `json:"current_local_id"`
	CurrentArmazenamentoID *uint   `json:"current_armazenamento_id"`
}

type BulkDuplicateRequest struct {
	TemplateID uint           `json:"template_id" binding:"required"`
	Copies     []BulkCopySpec `json:"copies" binding:"required"`
}

type BulkCopyResult struct {
	EPatrimonio string `json:"e_patrimonio"`
	Success     bool   `json:"success"`
	Error       string `json:"error,omitempty"`
	AssetID     uint   `json:"asset_id,omitempty"`
}

func (h *AssetHandler) BulkDuplicate(c *gin.Context) {
	var req BulkDuplicateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	template, err := h.repo.GetByID(req.TemplateID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ativo template não encontrado"})
		return
	}

	results := make([]BulkCopyResult, 0, len(req.Copies))
	successCount := 0
	failedCount := 0

	for _, copySpec := range req.Copies {
		// Check EPatrimonio uniqueness
		existing, _ := h.repo.GetByEPatrimonio(copySpec.EPatrimonio)
		if existing != nil {
			results = append(results, BulkCopyResult{
				EPatrimonio: copySpec.EPatrimonio,
				Success:     false,
				Error:       "Ativo com este E-Patrimônio já existe",
			})
			failedCount++
			continue
		}

		// Prepare duplicate object from template
		newAsset := models.Asset{
			Nome:                   template.Nome,
			Modelo:                 template.Modelo,
			Descricao:              template.Descricao,
			Valor:                  template.Valor,
			Status:                 models.AssetStatusDisponivel,
			Bloqueado:              template.Bloqueado,
			RequerTermoRH:          template.RequerTermoRH,
			CategoriaID:            template.CategoriaID,
			FornecedorID:           template.FornecedorID,
			NotaFiscalID:           template.NotaFiscalID,
			CurrentUserID:          nil, // Disassociated on copy
			CurrentDepartamentoID:  template.CurrentDepartamentoID,
			CurrentLocalID:         copySpec.CurrentLocalID,
			CurrentArmazenamentoID: copySpec.CurrentArmazenamentoID,
			EPatrimonio:            copySpec.EPatrimonio,
			NumeroSerie:            copySpec.NumeroSerie,
		}

		// Inherit location from template if not customized in the spec
		if newAsset.CurrentLocalID == nil {
			newAsset.CurrentLocalID = template.CurrentLocalID
		}
		if newAsset.CurrentArmazenamentoID == nil {
			newAsset.CurrentArmazenamentoID = template.CurrentArmazenamentoID
		}

		// Auth context user id as creator
		if val, exists := c.Get("user_id"); exists {
			userID := val.(uint)
			newAsset.CreatedByID = &userID
		}

		// Create copy spec
		if err := h.repo.Create(&newAsset); err != nil {
			results = append(results, BulkCopyResult{
				EPatrimonio: copySpec.EPatrimonio,
				Success:     false,
				Error:       err.Error(),
			})
			failedCount++
		} else {
			results = append(results, BulkCopyResult{
				EPatrimonio: copySpec.EPatrimonio,
				Success:     true,
				AssetID:     newAsset.ID,
			})
			successCount++
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"success_count": successCount,
		"failed_count":  failedCount,
		"results":       results,
	})
}
