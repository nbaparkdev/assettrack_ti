package handler

import (
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"time"

	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/repository"
	"github.com/assettrack/backend/internal/service"
	"github.com/gin-gonic/gin"
)

const xmlUploadDir = "uploads/xml"

type SupplierHandler struct {
	repo        *repository.SupplierRepository
	invoiceRepo *repository.InvoiceRepository
}

func NewSupplierHandler(repo *repository.SupplierRepository, invoiceRepo *repository.InvoiceRepository) *SupplierHandler {
	return &SupplierHandler{repo: repo, invoiceRepo: invoiceRepo}
}

func (h *SupplierHandler) List(c *gin.Context) {
	skip, _ := strconv.Atoi(c.DefaultQuery("skip", "0"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))

	suppliers, err := h.repo.List(skip, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, suppliers)
}

func (h *SupplierHandler) GetByID(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	supplier, err := h.repo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Fornecedor não encontrado"})
		return
	}
	c.JSON(http.StatusOK, supplier)
}

func (h *SupplierHandler) Create(c *gin.Context) {
	var supplier models.Fornecedor
	if err := c.ShouldBindJSON(&supplier); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if supplier.Nome == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Nome é obrigatório"})
		return
	}

	if supplier.CNPJ != nil && *supplier.CNPJ != "" {
		existing, err := h.repo.GetByCNPJ(*supplier.CNPJ)
		if err == nil && existing != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Já existe fornecedor com este CNPJ"})
			return
		}
	}

	if err := h.repo.Create(&supplier); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, supplier)
}

func (h *SupplierHandler) Update(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	supplier, err := h.repo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Fornecedor não encontrado"})
		return
	}

	if err := c.ShouldBindJSON(supplier); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	supplier.ID = uint(id)

	if err := h.repo.Update(supplier); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, supplier)
}

func (h *SupplierHandler) Delete(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	if _, err := h.repo.GetByID(uint(id)); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Fornecedor não encontrado"})
		return
	}

	if err := h.repo.Delete(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Fornecedor excluído"})
}

// ListInvoices returns the invoices of a supplier (id + numero_nota, like Python).
func (h *SupplierHandler) ListInvoices(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	invoices, err := h.invoiceRepo.ListBySupplier(uint(id))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	result := make([]gin.H, 0, len(invoices))
	for _, nf := range invoices {
		result = append(result, gin.H{"id": nf.ID, "numero_nota": nf.NumeroNota})
	}
	c.JSON(http.StatusOK, result)
}

type invoiceDetailResponse struct {
	ID               uint                 `json:"id"`
	FornecedorID     uint                 `json:"fornecedor_id"`
	NumeroNota       string               `json:"numero_nota"`
	DataEmissao      *time.Time           `json:"data_emissao"`
	NaturezaOperacao string               `json:"natureza_operacao"`
	ValorTotal       *float64             `json:"valor_total"`
	EmitenteNome     string               `json:"emitente_nome"`
	DestinatarioNome string               `json:"destinatario_nome"`
	Itens            []service.NFEXMLItem `json:"itens"`
}

func (h *SupplierHandler) GetInvoice(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	invoice, err := h.invoiceRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Nota fiscal não encontrada"})
		return
	}

	resp := invoiceDetailResponse{
		ID:           invoice.ID,
		FornecedorID: invoice.FornecedorID,
		NumeroNota:   invoice.NumeroNota,
		DataEmissao:  invoice.DataEmissao,
		ValorTotal:   invoice.ValorTotal,
		Itens:        []service.NFEXMLItem{},
	}
	if invoice.NaturezaOperacao != nil {
		resp.NaturezaOperacao = *invoice.NaturezaOperacao
	}
	if invoice.EmitenteNome != nil {
		resp.EmitenteNome = *invoice.EmitenteNome
	}
	if invoice.DestinatarioNome != nil {
		resp.DestinatarioNome = *invoice.DestinatarioNome
	}
	if invoice.Itens != nil && *invoice.Itens != "" {
		var itens []service.NFEXMLItem
		if err := json.Unmarshal([]byte(*invoice.Itens), &itens); err == nil {
			resp.Itens = itens
		}
	}
	c.JSON(http.StatusOK, resp)
}

// ParseXML receives an NFe XML upload and returns the extracted data
// for auto-filling the supplier form (like Python's /suppliers/parse-xml).
func (h *SupplierHandler) ParseXML(c *gin.Context) {
	file, err := c.FormFile("xml_file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Arquivo XML não enviado"})
		return
	}

	f, err := file.Open()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer f.Close()

	data, err := io.ReadAll(f)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	parsed, err := service.ParseNFEXML(data)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"nome":         parsed.EmitenteNome,
		"cnpj":         parsed.EmitenteCNPJ,
		"endereco":     parsed.EmitenteEndereco,
		"cidade":       parsed.EmitenteCidade,
		"estado":       parsed.EmitenteEstado,
		"telefone":     parsed.EmitenteTelefone,
		"razao_social": parsed.EmitenteNome,
	})
}

// UploadInvoice receives an NFe XML for a supplier, parses it and creates
// a NotaFiscal (like the XML handling in Python's create/update supplier).
func (h *SupplierHandler) UploadInvoice(c *gin.Context) {
	supplierID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	if _, err := h.repo.GetByID(uint(supplierID)); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Fornecedor não encontrado"})
		return
	}

	file, err := c.FormFile("xml_file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Arquivo XML não enviado"})
		return
	}

	parsed, xmlPath, err := h.saveAndParseXML(file, fmt.Sprintf("%d_", supplierID))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if parsed.NumeroNota == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Não foi possível extrair o Número da Nota (nNF) do XML fornecido."})
		return
	}

	// Check duplicate invoice number
	existing, err := h.invoiceRepo.GetByNumeroNota(parsed.NumeroNota)
	if err == nil && existing != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": fmt.Sprintf("Nota fiscal %s já cadastrada", parsed.NumeroNota)})
		return
	}

	itensJSON, _ := json.Marshal(parsed.Itens)
	itensStr := string(itensJSON)

	invoice := &models.NotaFiscal{
		NumeroNota:   parsed.NumeroNota,
		FornecedorID: uint(supplierID),
		XMLPath:      &xmlPath,
		DataEmissao:  parsed.DataEmissao,
		ValorTotal:   parsed.ValorTotal,
		Itens:        &itensStr,
	}
	if parsed.NaturezaOperacao != "" {
		invoice.NaturezaOperacao = &parsed.NaturezaOperacao
	}
	if parsed.EmitenteNome != "" {
		invoice.EmitenteNome = &parsed.EmitenteNome
	}
	if parsed.EmitenteCNPJ != "" {
		invoice.EmitenteCNPJ = &parsed.EmitenteCNPJ
	}
	if parsed.DestinatarioNome != "" {
		invoice.DestinatarioNome = &parsed.DestinatarioNome
	}
	if parsed.DestinatarioCNPJ != "" {
		invoice.DestinatarioCNPJ = &parsed.DestinatarioCNPJ
	}

	if err := h.invoiceRepo.Create(invoice); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, invoice)
}

// saveAndParseXML saves the uploaded file under uploads/xml and parses it.
// Returns the parsed data and the public path "/uploads/xml/<file>".
func (h *SupplierHandler) saveAndParseXML(fileHeader *multipart.FileHeader, prefix string) (*service.NFEData, string, error) {
	f, err := fileHeader.Open()
	if err != nil {
		return nil, "", err
	}
	defer f.Close()

	data, err := io.ReadAll(f)
	if err != nil {
		return nil, "", err
	}

	parsed, err := service.ParseNFEXML(data)
	if err != nil {
		return nil, "", err
	}

	// Save physical file (same layout as Python: static/uploads/xml/<supplierId>_<filename>)
	if err := os.MkdirAll(xmlUploadDir, 0o755); err != nil {
		return nil, "", err
	}
	safeName := filepath.Base(fileHeader.Filename)
	filePath := filepath.Join(xmlUploadDir, prefix+safeName)
	if err := os.WriteFile(filePath, data, 0o644); err != nil {
		return nil, "", err
	}

	return parsed, "/" + filepath.ToSlash(filePath), nil
}

func (h *SupplierHandler) DeleteInvoice(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	invoice, err := h.invoiceRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Nota fiscal não encontrada"})
		return
	}

	count, err := h.invoiceRepo.CountAssetsByInvoice(uint(id))
	if err == nil && count > 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Não é possível excluir nota com ativos vinculados"})
		return
	}

	// Delete physical XML file
	if invoice.XMLPath != nil && *invoice.XMLPath != "" {
		fullPath := filepath.Clean(*invoice.XMLPath)
		fullPath = filepath.FromSlash(fullPath)
		if err := os.Remove(fullPath); err != nil {
			// Non-fatal: just log
			c.Error(err)
		}
	}

	if err := h.invoiceRepo.Delete(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Nota fiscal excluída"})
}
