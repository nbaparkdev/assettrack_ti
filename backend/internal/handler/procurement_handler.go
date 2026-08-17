package handler

import (
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/assettrack/backend/internal/middleware"
	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/repository"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// procurementManager roles allowed to manage procurement records (admin, gerente_ti, gerente_infra, comprador).
func procurementManager(user *models.User) bool {
	if user == nil {
		return false
	}
	return user.Role == models.RoleAdmin || user.Role == models.RoleGerente ||
		user.Role == models.RoleGerenteInfra || user.Role == models.RoleComprador
}

// procurementAdmin roles allowed for budget release / deletions (admin, gerente_ti, gerente_infra).
func procurementAdmin(user *models.User) bool {
	if user == nil {
		return false
	}
	return user.Role == models.RoleAdmin || user.Role == models.RoleGerente || user.Role == models.RoleGerenteInfra
}

// canApproveLevel mirrors the Python decide_request authorization matrix.
func canApproveLevel(role, nivel string) bool {
	switch nivel {
	case "Gestor", "Gerente":
		return role == models.RoleAdmin || role == models.RoleGerente ||
			role == models.RoleGerenteInfra || role == models.RoleComprador
	case "Financeiro", "Diretoria", "Compras":
		return role == models.RoleAdmin || role == models.RoleComprador
	}
	return false
}

type ProcurementHandler struct {
	categoryRepo     *repository.ProcurementCategoryRepository
	productRepo      *repository.ProcurementProductRepository
	ccRepo           *repository.ProcurementCostCenterRepository
	requestRepo      *repository.ProcurementRequestRepository
	approvalRepo     *repository.ProcurementApprovalRepository
	quotationRepo    *repository.ProcurementQuotationRepository
	orderRepo        *repository.ProcurementOrderRepository
	receivingRepo    *repository.ProcurementReceivingRepository
	stockRepo        *repository.ProcurementStockRepository
	contractRepo     *repository.ProcurementContractRepository
	contractTypeRepo *repository.ProcurementContractTypeRepository
	historyRepo      *repository.ProcurementHistoryRepository
	notifRepo        *repository.ProcurementNotificationRepository
	researchRepo     *repository.ProcurementResearchRepository
	assetRepo        *repository.AssetRepository
	userRepo         *repository.UserRepository
	cardRepo         *repository.KanbanCardRepository
	interactionRepo  *repository.KanbanInteractionRepository
}

func NewProcurementHandler(
	categoryRepo *repository.ProcurementCategoryRepository,
	productRepo *repository.ProcurementProductRepository,
	ccRepo *repository.ProcurementCostCenterRepository,
	requestRepo *repository.ProcurementRequestRepository,
	approvalRepo *repository.ProcurementApprovalRepository,
	quotationRepo *repository.ProcurementQuotationRepository,
	orderRepo *repository.ProcurementOrderRepository,
	receivingRepo *repository.ProcurementReceivingRepository,
	stockRepo *repository.ProcurementStockRepository,
	contractRepo *repository.ProcurementContractRepository,
	contractTypeRepo *repository.ProcurementContractTypeRepository,
	historyRepo *repository.ProcurementHistoryRepository,
	notifRepo *repository.ProcurementNotificationRepository,
	researchRepo *repository.ProcurementResearchRepository,
	assetRepo *repository.AssetRepository,
	userRepo *repository.UserRepository,
	cardRepo *repository.KanbanCardRepository,
	interactionRepo *repository.KanbanInteractionRepository,
) *ProcurementHandler {
	return &ProcurementHandler{
		categoryRepo:     categoryRepo,
		productRepo:      productRepo,
		ccRepo:           ccRepo,
		requestRepo:      requestRepo,
		approvalRepo:     approvalRepo,
		quotationRepo:    quotationRepo,
		orderRepo:        orderRepo,
		receivingRepo:    receivingRepo,
		stockRepo:        stockRepo,
		contractRepo:     contractRepo,
		contractTypeRepo: contractTypeRepo,
		historyRepo:      historyRepo,
		notifRepo:        notifRepo,
		researchRepo:     researchRepo,
		assetRepo:        assetRepo,
		userRepo:         userRepo,
		cardRepo:         cardRepo,
		interactionRepo:  interactionRepo,
	}
}

func (h *ProcurementHandler) logHistory(tabela string, registroID, userID uint, acao string) {
	_ = h.historyRepo.Create(&models.PurchaseHistory{
		TabelaOrigem: tabela,
		RegistroID:   registroID,
		UserID:       userID,
		Acao:         acao,
	})
}

// notifyStaff creates in-DB notifications for manager/comprador roles.
func (h *ProcurementHandler) notifyStaff(mensagem string) {
	staff, err := h.userRepo.ListByRoles([]string{models.RoleAdmin, models.RoleGerente, models.RoleGerenteInfra, models.RoleComprador})
	if err != nil {
		return
	}
	for _, u := range staff {
		_ = h.notifRepo.Create(&models.PurchaseNotification{
			UserID:               u.ID,
			Mensagem:             mensagem,
			LinkRedirecionamento: strPtr("/compras"),
		})
	}
}

func strPtr(s string) *string { return &s }

func parseProcDate(s string) *time.Time {
	if s == "" {
		return nil
	}
	for _, layout := range []string{time.RFC3339, "2006-01-02", "2006-01-02T15:04"} {
		if t, err := time.Parse(layout, s); err == nil {
			return &t
		}
	}
	return nil
}

// ---------- Dashboard ----------

func (h *ProcurementHandler) Dashboard(c *gin.Context) {
	var reqPending, ordersActive, lowStock int64
	reqs, _ := h.requestRepo.List("", 0, 1000)
	for _, r := range reqs {
		if r.Status == models.PRStatusPendente {
			reqPending++
		}
	}
	orders, _ := h.orderRepo.List("", 0, 1000)
	for _, o := range orders {
		if o.Status == models.POStatusAberto {
			ordersActive++
		}
	}
	stocks, _ := h.stockRepo.List()
	for _, s := range stocks {
		if s.QuantidadeSaldo < 5 {
			lowStock++
		}
	}
	recentReq := reqs
	if len(recentReq) > 5 {
		recentReq = recentReq[:5]
	}
	recentOrders := orders
	if len(recentOrders) > 5 {
		recentOrders = recentOrders[:5]
	}
	c.JSON(http.StatusOK, gin.H{
		"req_pending_count":   reqPending,
		"orders_active_count": ordersActive,
		"low_stock_count":     lowStock,
		"requests_recent":     recentReq,
		"orders_recent":       recentOrders,
	})
}

// ---------- Categories ----------

func (h *ProcurementHandler) ListCategories(c *gin.Context) {
	items, err := h.categoryRepo.List()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, items)
}

func (h *ProcurementHandler) CreateCategory(c *gin.Context) {
	var in struct {
		Nome      string `json:"nome"`
		Descricao string `json:"descricao"`
		Ativo     *bool  `json:"ativo"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if in.Nome == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Nome é obrigatório"})
		return
	}
	cat := &models.PurchaseCategory{Nome: in.Nome, Ativo: true}
	if in.Descricao != "" {
		cat.Descricao = &in.Descricao
	}
	if in.Ativo != nil {
		cat.Ativo = *in.Ativo
	}
	if err := h.categoryRepo.Create(cat); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Já existe uma categoria com este nome"})
		return
	}
	c.JSON(http.StatusCreated, cat)
}

// ---------- Products ----------

func (h *ProcurementHandler) ListProducts(c *gin.Context) {
	skip, _ := strconv.Atoi(c.DefaultQuery("skip", "0"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))
	items, err := h.productRepo.List(skip, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, items)
}

type productInput struct {
	Codigo      string `json:"codigo"`
	Nome        string `json:"nome"`
	CategoriaID uint   `json:"categoria_id"`
	Unidade     string `json:"unidade"`
	Tipo        string `json:"tipo"`
	Marca       string `json:"marca"`
	Modelo      string `json:"modelo"`
	Fabricante  string `json:"fabricante"`
	Descricao   string `json:"descricao"`
	Ativo       *bool  `json:"ativo"`
}

func (h *ProcurementHandler) CreateProduct(c *gin.Context) {
	var in productInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if in.Codigo == "" || in.Nome == "" || in.CategoriaID == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Código, nome e categoria são obrigatórios"})
		return
	}
	if _, err := h.productRepo.GetByCodigo(in.Codigo); err == nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Código de produto já cadastrado"})
		return
	}
	prod := &models.PurchaseProduct{
		Codigo:      in.Codigo,
		Nome:        in.Nome,
		CategoriaID: in.CategoriaID,
		Unidade:     "UN",
		Tipo:        normalizeEnumValue(in.Tipo, []string{models.ProductTypeProduto, models.ProductTypeServico, models.ProductTypeLicenca, models.ProductTypeAssinatura, models.ProductTypeEquipamento, models.ProductTypeMaterialConsumo}, models.ProductTypeProduto),
		Ativo:       true,
	}
	if in.Unidade != "" {
		prod.Unidade = in.Unidade
	}
	if in.Marca != "" {
		prod.Marca = &in.Marca
	}
	if in.Modelo != "" {
		prod.Modelo = &in.Modelo
	}
	if in.Fabricante != "" {
		prod.Fabricante = &in.Fabricante
	}
	if in.Descricao != "" {
		prod.Descricao = &in.Descricao
	}
	if in.Ativo != nil {
		prod.Ativo = *in.Ativo
	}
	if err := h.productRepo.Create(prod); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, prod)
}

// ---------- Cost Centers ----------

func (h *ProcurementHandler) ListCostCenters(c *gin.Context) {
	items, err := h.ccRepo.List()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, items)
}

type costCenterInput struct {
	Codigo          string  `json:"codigo"`
	Nome            string  `json:"nome"`
	DepartamentoID  *uint   `json:"departamento_id"`
	ResponsavelID   *uint   `json:"responsavel_id"`
	OrcamentoMensal float64 `json:"orcamento_mensal"`
	OrcamentoAnual  float64 `json:"orcamento_anual"`
	AlertaLimite    *bool   `json:"alerta_limite"`
	BloquearLimite  *bool   `json:"bloquear_limite"`
}

func (h *ProcurementHandler) CreateCostCenter(c *gin.Context) {
	var in costCenterInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if in.Codigo == "" || in.Nome == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Código e nome são obrigatórios"})
		return
	}
	cc := &models.CostCenter{
		Codigo:               in.Codigo,
		Nome:                 in.Nome,
		DepartamentoID:       in.DepartamentoID,
		ResponsavelID:        in.ResponsavelID,
		OrcamentoMensal:      in.OrcamentoMensal,
		OrcamentoAnual:       in.OrcamentoAnual,
		AlertaLimite:         true,
		BloquearLimite:       false,
		OrcamentoMensalUsado: 0,
		OrcamentoAnualUsado:  0,
	}
	if in.AlertaLimite != nil {
		cc.AlertaLimite = *in.AlertaLimite
	}
	if in.BloquearLimite != nil {
		cc.BloquearLimite = *in.BloquearLimite
	}
	if err := h.ccRepo.Create(cc); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Já existe um centro de custo com este código"})
		return
	}
	c.JSON(http.StatusCreated, cc)
}

func (h *ProcurementHandler) UpdateCostCenter(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	cc, err := h.ccRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Centro de custo não encontrado"})
		return
	}
	var in costCenterInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if in.Nome != "" {
		cc.Nome = in.Nome
	}
	cc.DepartamentoID = in.DepartamentoID
	cc.ResponsavelID = in.ResponsavelID
	cc.OrcamentoMensal = in.OrcamentoMensal
	cc.OrcamentoAnual = in.OrcamentoAnual
	if in.AlertaLimite != nil {
		cc.AlertaLimite = *in.AlertaLimite
	}
	if in.BloquearLimite != nil {
		cc.BloquearLimite = *in.BloquearLimite
	}
	if err := h.ccRepo.Update(cc); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, cc)
}

func (h *ProcurementHandler) DeleteCostCenter(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	if _, err := h.ccRepo.GetByID(uint(id)); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Centro de custo não encontrado"})
		return
	}
	has, _ := h.ccRepo.HasRequests(uint(id))
	if has {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Não é possível excluir este Centro de Custo pois existem solicitações de compra vinculadas a ele."})
		return
	}
	if err := h.ccRepo.Delete(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Centro de custo excluído"})
}

// ---------- Purchase Requests ----------

func (h *ProcurementHandler) ListRequests(c *gin.Context) {
	status := c.Query("status")
	skip, _ := strconv.Atoi(c.DefaultQuery("skip", "0"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))
	items, err := h.requestRepo.List(status, skip, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, items)
}

type requestItemInput struct {
	ProductID            uint    `json:"product_id"`
	Quantidade           float64 `json:"quantidade"`
	ValorEstimado        float64 `json:"valor_estimado"`
	FornecedorSugeridoID *uint   `json:"fornecedor_sugerido_id"`
	Observacao           string  `json:"observacao"`
}

type requestInput struct {
	CentroCustoID  uint               `json:"centro_custo_id"`
	Justificativa  string             `json:"justificativa"`
	Urgencia       string             `json:"urgencia"`
	DataNecessaria string             `json:"data_necessaria"`
	Itens          []requestItemInput `json:"itens"`
}

func (h *ProcurementHandler) CreateRequest(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	var in requestInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if in.CentroCustoID == 0 || in.Justificativa == "" || len(in.Itens) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Centro de custo, justificativa e ao menos um item são obrigatórios"})
		return
	}
	cc, err := h.ccRepo.GetByID(in.CentroCustoID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Centro de Custo não encontrado"})
		return
	}

	var estimatedTotal float64
	for _, it := range in.Itens {
		estimatedTotal += it.Quantidade * it.ValorEstimado
	}

	status := models.PRStatusPendente
	if cc.BloquearLimite && (cc.OrcamentoMensalUsado+estimatedTotal > cc.OrcamentoMensal) {
		status = models.PRStatusAguardandoOrcamento
	}

	num, err := h.requestRepo.GenerateRequestNumber(time.Now())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	deptID := uint(1)
	if user.DepartamentoID != nil {
		deptID = *user.DepartamentoID
	}

	req := &models.PurchaseRequest{
		Numero:         num,
		SolicitanteID:  user.ID,
		DepartamentoID: deptID,
		CentroCustoID:  in.CentroCustoID,
		Justificativa:  in.Justificativa,
		Urgencia:       normalizeEnumValue(in.Urgencia, []string{models.UrgencyBaixa, models.UrgencyMedia, models.UrgencyAlta, models.UrgencyUrgente}, models.UrgencyMedia),
		Status:         status,
		DataCriacao:    time.Now(),
	}
	if in.DataNecessaria != "" {
		req.DataNecessaria = parseProcDate(in.DataNecessaria)
	}
	for _, it := range in.Itens {
		item := models.PurchaseRequestItem{
			ProductID:            it.ProductID,
			Quantidade:           it.Quantidade,
			ValorEstimado:        it.ValorEstimado,
			FornecedorSugeridoID: it.FornecedorSugeridoID,
		}
		if it.Observacao != "" {
			item.Observacao = &it.Observacao
		}
		req.Itens = append(req.Itens, item)
	}
	if err := h.requestRepo.Create(req); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	h.logHistory("purchase_requests", req.ID, user.ID, "Solicitação de Compra Criada")
	h.notifyStaff(fmt.Sprintf("Nova Solicitação de Compra %s criada por %s. Valor estimado: R$ %.2f.", req.Numero, user.Nome, estimatedTotal))
	c.JSON(http.StatusCreated, req)
}

func (h *ProcurementHandler) GetRequest(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	req, err := h.requestRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Solicitação não encontrada"})
		return
	}
	c.JSON(http.StatusOK, req)
}

func (h *ProcurementHandler) DecideRequest(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	req, err := h.requestRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Solicitação não encontrada"})
		return
	}
	var in struct {
		Nivel      string `json:"nivel"`
		Decisao    string `json:"decisao"` // Aprovado / Reprovado
		Observacao string `json:"observacao"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if !canApproveLevel(user.Role, in.Nivel) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Não autorizado a decidir este nível de solicitação"})
		return
	}

	now := time.Now()
	approval := &models.PurchaseApproval{
		RequestID:   req.ID,
		Nivel:       in.Nivel,
		AprovadorID: &user.ID,
		Status:      in.Decisao,
		DataDecisao: &now,
	}
	if in.Observacao != "" {
		approval.Observacao = &in.Observacao
	}
	_ = h.approvalRepo.Create(approval)

	if in.Decisao == models.ApprovalReprovado {
		req.Status = models.PRStatusReprovada
	} else if in.Nivel == "Compras" {
		req.Status = models.PRStatusAprovada
		// Auto update cost center budget used
		if cc, err := h.ccRepo.GetByID(req.CentroCustoID); err == nil && cc != nil {
			var total float64
			for _, it := range req.Itens {
				total += it.Quantidade * it.ValorEstimado
			}
			cc.OrcamentoMensalUsado += total
			cc.OrcamentoAnualUsado += total
			_ = h.ccRepo.Update(cc)
		}
	} else {
		req.Status = models.PRStatusEmAprovacao
	}
	if err := h.requestRepo.Update(req); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	h.logHistory("purchase_requests", req.ID, user.ID, fmt.Sprintf("Decisão de %s: %s", in.Nivel, in.Decisao))
	c.JSON(http.StatusOK, req)
}

func (h *ProcurementHandler) ReleaseBudget(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	req, err := h.requestRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Solicitação não encontrada"})
		return
	}
	if !procurementAdmin(user) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Não autorizado a liberar orçamento"})
		return
	}
	if len(req.Approvals) > 0 {
		req.Status = models.PRStatusEmAprovacao
	} else {
		req.Status = models.PRStatusPendente
	}
	if err := h.requestRepo.Update(req); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	h.logHistory("purchase_requests", req.ID, user.ID, "Orçamento Liberado pelo Administrador")
	c.JSON(http.StatusOK, req)
}

// ---------- Quotations ----------

func (h *ProcurementHandler) ListQuotations(c *gin.Context) {
	items, err := h.quotationRepo.List()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, items)
}

type quotationItemInput struct {
	ProductID     uint    `json:"product_id"`
	Quantidade    float64 `json:"quantidade"`
	ValorUnitario float64 `json:"valor_unitario"`
}

type quotationSupplierInput struct {
	FornecedorID     uint                 `json:"fornecedor_id"`
	Frete            float64              `json:"frete"`
	PrazoEntregaDias int                  `json:"prazo_entrega_dias"`
	GarantiaMeses    int                  `json:"garantia_meses"`
	FormaPagamento   string               `json:"forma_pagamento"`
	Observacoes      string               `json:"observacoes"`
	Itens            []quotationItemInput `json:"itens"`
}

type quotationInput struct {
	RequestID uint                     `json:"request_id"`
	Suppliers []quotationSupplierInput `json:"suppliers"`
}

func (h *ProcurementHandler) CreateQuotation(c *gin.Context) {
	var in quotationInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	req, err := h.requestRepo.GetByID(in.RequestID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Solicitação não encontrada"})
		return
	}
	num, err := h.quotationRepo.GenerateQuotationNumber(time.Now())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	quotation := &models.PurchaseQuotation{
		Numero:      num,
		RequestID:   in.RequestID,
		Status:      models.QuotationEmCotacao,
		DataCriacao: time.Now(),
	}
	for _, s := range in.Suppliers {
		var total float64
		supplier := models.PurchaseQuotationSupplier{
			FornecedorID:     s.FornecedorID,
			Frete:            s.Frete,
			PrazoEntregaDias: s.PrazoEntregaDias,
			GarantiaMeses:    s.GarantiaMeses,
		}
		if s.FormaPagamento != "" {
			supplier.FormaPagamento = &s.FormaPagamento
		}
		if s.Observacoes != "" {
			supplier.Observacoes = &s.Observacoes
		}
		for _, it := range s.Itens {
			supplier.Itens = append(supplier.Itens, models.PurchaseQuotationItem{
				ProductID:     it.ProductID,
				Quantidade:    it.Quantidade,
				ValorUnitario: it.ValorUnitario,
			})
			total += it.ValorUnitario * it.Quantidade
		}
		total += s.Frete
		supplier.ValorTotal = total
		quotation.Suppliers = append(quotation.Suppliers, supplier)
	}
	if err := h.quotationRepo.Create(quotation); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	// Update request status to "Convertida em cotação"
	req.Status = models.PRStatusConvertidaCotacao
	_ = h.requestRepo.Update(req)

	c.JSON(http.StatusCreated, quotation)
}

func (h *ProcurementHandler) GetQuotation(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	quotation, err := h.quotationRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Cotação não encontrada"})
		return
	}
	// Comparison winners (cheapest / fastest / best value)
	var cheapestID, fastestID, bestValueID *uint
	if len(quotation.Suppliers) > 0 {
		cheapest := quotation.Suppliers[0]
		fastest := quotation.Suppliers[0]
		bestValue := quotation.Suppliers[0]
		bestScore := 0.0
		for i := range quotation.Suppliers {
			s := &quotation.Suppliers[i]
			if s.ValorTotal < cheapest.ValorTotal {
				cheapest = *s
			}
			if s.PrazoEntregaDias < fastest.PrazoEntregaDias {
				fastest = *s
			}
			score := s.ValorTotal*0.7 + float64(s.PrazoEntregaDias)*50*0.3
			if i == 0 || score < bestScore {
				bestScore = score
				bestValue = *s
			}
		}
		cheapestID = &cheapest.ID
		fastestID = &fastest.ID
		bestValueID = &bestValue.ID
	}
	c.JSON(http.StatusOK, gin.H{
		"quotation":     quotation,
		"cheapest_id":   cheapestID,
		"fastest_id":    fastestID,
		"best_value_id": bestValueID,
	})
}

func (h *ProcurementHandler) SelectWinner(c *gin.Context) {
	quotationID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	var in struct {
		WinnerSupplierID uint `json:"winner_supplier_id"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	winner, err := h.quotationRepo.GetSupplierByID(in.WinnerSupplierID)
	if err != nil || winner.QuotationID != uint(quotationID) {
		c.JSON(http.StatusNotFound, gin.H{"error": "Fornecedor cotado não encontrado"})
		return
	}
	winner.Escolhido = true
	_ = h.quotationRepo.UpdateSupplier(winner)

	quotation, err := h.quotationRepo.GetByID(uint(quotationID))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Cotação não encontrada"})
		return
	}
	quotation.Status = models.QuotationFinalizada
	_ = h.quotationRepo.Update(quotation)

	centroCustoID := uint(1)
	if req, err := h.requestRepo.GetByID(quotation.RequestID); err == nil && req != nil {
		centroCustoID = req.CentroCustoID
	}

	num, err := h.orderRepo.GenerateOrderNumber(time.Now())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	order := &models.PurchaseOrder{
		Numero:        num,
		FornecedorID:  winner.FornecedorID,
		CentroCustoID: centroCustoID,
		RequestID:     &quotation.RequestID,
		QuotationID:   &quotation.ID,
		ValorTotal:    winner.ValorTotal,
		Frete:         winner.Frete,
		Status:        models.POStatusAberto,
		DataEmissao:   time.Now(),
	}
	for _, it := range winner.Itens {
		order.Itens = append(order.Itens, models.PurchaseOrderItem{
			ProductID:     it.ProductID,
			Quantidade:    it.Quantidade,
			ValorUnitario: it.ValorUnitario,
			TotalItem:     it.Quantidade * it.ValorUnitario,
		})
	}
	if err := h.orderRepo.Create(order); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	h.notifyStaff(fmt.Sprintf("Pedido de Compra %s emitido (fornecedor #%d). Valor total: R$ %.2f.", order.Numero, winner.FornecedorID, winner.ValorTotal))
	c.JSON(http.StatusCreated, order)
}

// ---------- Purchase Orders ----------

func (h *ProcurementHandler) ListOrders(c *gin.Context) {
	status := c.Query("status")
	skip, _ := strconv.Atoi(c.DefaultQuery("skip", "0"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))
	items, err := h.orderRepo.List(status, skip, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, items)
}

type orderItemInput struct {
	ProductID     uint    `json:"product_id"`
	Quantidade    float64 `json:"quantidade"`
	ValorUnitario float64 `json:"valor_unitario"`
}

type purchaseOrderInput struct {
	FornecedorID  uint             `json:"fornecedor_id"`
	CentroCustoID uint             `json:"centro_custo_id"`
	RequestID     *uint            `json:"request_id"`
	QuotationID   *uint            `json:"quotation_id"`
	Desconto      float64          `json:"desconto"`
	IPI           float64          `json:"ipi"`
	ICMS          float64          `json:"icms"`
	Frete         float64          `json:"frete"`
	Itens         []orderItemInput `json:"itens"`
}

func (h *ProcurementHandler) CreateOrder(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	var in purchaseOrderInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if in.FornecedorID == 0 || in.CentroCustoID == 0 || len(in.Itens) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Fornecedor, centro de custo e ao menos um item são obrigatórios"})
		return
	}
	var total float64
	for _, it := range in.Itens {
		total += it.Quantidade * it.ValorUnitario
	}
	total = total + in.Frete + in.IPI + in.ICMS - in.Desconto

	num, err := h.orderRepo.GenerateOrderNumber(time.Now())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	order := &models.PurchaseOrder{
		Numero:        num,
		FornecedorID:  in.FornecedorID,
		CentroCustoID: in.CentroCustoID,
		RequestID:     in.RequestID,
		QuotationID:   in.QuotationID,
		ValorTotal:    total,
		Desconto:      in.Desconto,
		IPI:           in.IPI,
		ICMS:          in.ICMS,
		Frete:         in.Frete,
		Status:        models.POStatusAberto,
		DataEmissao:   time.Now(),
	}
	for _, it := range in.Itens {
		order.Itens = append(order.Itens, models.PurchaseOrderItem{
			ProductID:     it.ProductID,
			Quantidade:    it.Quantidade,
			ValorUnitario: it.ValorUnitario,
			TotalItem:     it.Quantidade * it.ValorUnitario,
		})
	}
	if err := h.orderRepo.Create(order); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	h.logHistory("purchase_orders", order.ID, user.ID, "Pedido Emitido")
	c.JSON(http.StatusCreated, order)
}

func (h *ProcurementHandler) GetOrder(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	order, err := h.orderRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Pedido não encontrado"})
		return
	}
	c.JSON(http.StatusOK, order)
}

// ---------- Receiving ----------

type receivingItemInput struct {
	ProductID          uint    `json:"product_id"`
	QuantidadeRecebida float64 `json:"quantidade_recebida"`
	Divergencias       string  `json:"divergencias"`
}

type receivingInput struct {
	NotaFiscalID           *uint                `json:"nota_fiscal_id"`
	Observacoes            string               `json:"observacoes"`
	CurrentLocalID         *uint                `json:"current_local_id"`
	CurrentArmazenamentoID *uint                `json:"current_armazenamento_id"`
	Itens                  []receivingItemInput `json:"itens"`
}

func (h *ProcurementHandler) ReceiveOrder(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	orderID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	order, err := h.orderRepo.GetByID(uint(orderID))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Pedido não encontrado"})
		return
	}
	var in receivingInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if len(in.Itens) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Informe ao menos um item recebido"})
		return
	}

	receiving := &models.PurchaseReceiving{
		OrderID:         order.ID,
		ResponsavelID:   user.ID,
		NotaFiscalID:    in.NotaFiscalID,
		DataRecebimento: time.Now(),
	}
	if in.Observacoes != "" {
		receiving.Observacoes = &in.Observacoes
	}
	for _, it := range in.Itens {
		item := models.PurchaseReceivingItem{
			ProductID:          it.ProductID,
			QuantidadeRecebida: it.QuantidadeRecebida,
		}
		if it.Divergencias != "" {
			item.Divergencias = &it.Divergencias
		}
		receiving.Itens = append(receiving.Itens, item)
	}
	if err := h.receivingRepo.Create(receiving); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Trigger asset creation & stock addition
	createdAssets := h.convertReceivingToAssets(receiving, order, user.ID, in.CurrentLocalID, in.CurrentArmazenamentoID)

	// Update order status to fully received
	order.Status = models.POStatusRecebidoTotal
	_ = h.orderRepo.Update(order)
	h.logHistory("purchase_receivings", receiving.ID, user.ID, "Recebimento Registrado")

	c.JSON(http.StatusCreated, gin.H{"receiving": receiving, "created_assets": createdAssets})
}

// convertReceivingToAssets creates assets for equipment items and adds stock for consumable items.
func (h *ProcurementHandler) convertReceivingToAssets(
	receiving *models.PurchaseReceiving, order *models.PurchaseOrder, userID uint, localID, armazenamentoID *uint,
) []models.Asset {
	var created []models.Asset
	// Sequential patrimonio tag based on existing asset count.
	allAssets, err := h.assetRepo.List(0, 100000, "")
	currentCount := 0
	if err == nil {
		currentCount = len(allAssets)
	}
	year := time.Now().Year()
	for i := range receiving.Itens {
		item := &receiving.Itens[i]
		if item.ProductID == 0 {
			continue
		}
		product, err := h.productRepo.GetByID(item.ProductID)
		if err != nil {
			continue
		}
		if product.Tipo == models.ProductTypeEquipamento {
			currentCount++
			patrimonio := fmt.Sprintf("PAT-%d-%04d", year, currentCount)
			valor := 0.0
			if len(order.Itens) > 0 {
				valor = order.ValorTotal / float64(len(order.Itens))
			}
			asset := models.Asset{
				Nome:                   product.Nome,
				EPatrimonio:            patrimonio,
				Modelo:                 product.Modelo,
				DataAquisicao:          timePtr(time.Now()),
				Valor:                  &valor,
				Status:                 models.AssetStatusArmazenado,
				NumeroSerie:            &product.Codigo,
				FornecedorID:           &order.FornecedorID,
				NotaFiscalID:           receiving.NotaFiscalID,
				CreatedByID:            &userID,
				CurrentLocalID:         localID,
				CurrentArmazenamentoID: armazenamentoID,
			}
			desc := fmt.Sprintf("Criado automaticamente pelo recebimento do Pedido %s", order.Numero)
			asset.Descricao = &desc
			if cc, err := h.ccRepo.GetByID(order.CentroCustoID); err == nil && cc != nil {
				asset.CurrentDepartamentoID = cc.DepartamentoID
			}
			if err := h.assetRepo.Create(&asset); err == nil {
				item.AtivoCriadoID = &asset.ID
				created = append(created, asset)
			}
		} else if product.Tipo == models.ProductTypeMaterialConsumo {
			_, _ = h.stockRepo.CreateOrUpdate(
				item.ProductID, item.QuantidadeRecebida, models.StockEntrada, userID,
				fmt.Sprintf("Entrada por Recebimento %d do Pedido %s", receiving.ID, order.Numero),
				"purchase_receivings", &receiving.ID,
			)
			item.EstoqueAtualizado = true
		}
	}
	return created
}

func timePtr(t time.Time) *time.Time { return &t }

// ---------- Stock ----------

func (h *ProcurementHandler) ListStock(c *gin.Context) {
	items, err := h.stockRepo.List()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, items)
}

// ---------- Contracts ----------

func (h *ProcurementHandler) ListContracts(c *gin.Context) {
	items, err := h.contractRepo.List()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, items)
}

type contractInput struct {
	FornecedorID        uint    `json:"fornecedor_id"`
	Tipo                string  `json:"tipo"`
	TipoID              *uint   `json:"tipo_id"`
	Numero              string  `json:"numero"`
	DataInicio          string  `json:"data_inicio"`
	DataFim             string  `json:"data_fim"`
	RenovacaoAutomatica bool    `json:"renovacao_automatica"`
	Valor               float64 `json:"valor"`
	Periodicidade       string  `json:"periodicidade"`
}

func (h *ProcurementHandler) CreateContract(c *gin.Context) {
	var in contractInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if in.FornecedorID == 0 || in.Numero == "" || in.DataInicio == "" || in.DataFim == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Fornecedor, número e datas são obrigatórios"})
		return
	}
	dtIni := parseProcDate(in.DataInicio)
	dtFim := parseProcDate(in.DataFim)
	if dtIni == nil || dtFim == nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Datas inválidas"})
		return
	}
	contract := &models.PurchaseContract{
		FornecedorID:        in.FornecedorID,
		Tipo:                in.Tipo,
		TipoID:              in.TipoID,
		Numero:              in.Numero,
		DataInicio:          *dtIni,
		DataFim:             *dtFim,
		RenovacaoAutomatica: in.RenovacaoAutomatica,
		Valor:               in.Valor,
		Periodicidade:       "Mensal",
	}
	if in.Periodicidade != "" {
		contract.Periodicidade = in.Periodicidade
	}
	if err := h.contractRepo.Create(contract); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Já existe um contrato com este número"})
		return
	}
	c.JSON(http.StatusCreated, contract)
}

func (h *ProcurementHandler) UpdateContract(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	contract, err := h.contractRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Contrato não encontrado"})
		return
	}
	var in contractInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if in.FornecedorID != 0 {
		contract.FornecedorID = in.FornecedorID
	}
	if in.Tipo != "" {
		contract.Tipo = in.Tipo
	}
	contract.TipoID = in.TipoID
	if in.Numero != "" {
		contract.Numero = in.Numero
	}
	if dt := parseProcDate(in.DataInicio); dt != nil {
		contract.DataInicio = *dt
	}
	if dt := parseProcDate(in.DataFim); dt != nil {
		contract.DataFim = *dt
	}
	contract.RenovacaoAutomatica = in.RenovacaoAutomatica
	contract.Valor = in.Valor
	if in.Periodicidade != "" {
		contract.Periodicidade = in.Periodicidade
	}
	if err := h.contractRepo.Update(contract); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, contract)
}

func (h *ProcurementHandler) DeleteContract(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	if _, err := h.contractRepo.GetByID(uint(id)); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Contrato não encontrado"})
		return
	}
	if err := h.contractRepo.Delete(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Contrato excluído"})
}

// ---------- Contract Types ----------

func (h *ProcurementHandler) ListContractTypes(c *gin.Context) {
	items, err := h.contractTypeRepo.List(false)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, items)
}

type contractTypeInput struct {
	Nome      string `json:"nome"`
	Descricao string `json:"descricao"`
	Ativo     *bool  `json:"ativo"`
}

func (h *ProcurementHandler) CreateContractType(c *gin.Context) {
	var in contractTypeInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if in.Nome == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Nome é obrigatório"})
		return
	}
	ct := &models.ContractType{Nome: in.Nome, Ativo: true}
	if in.Descricao != "" {
		ct.Descricao = &in.Descricao
	}
	if in.Ativo != nil {
		ct.Ativo = *in.Ativo
	}
	if err := h.contractTypeRepo.Create(ct); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Já existe um tipo de contrato com este nome"})
		return
	}
	c.JSON(http.StatusCreated, ct)
}

func (h *ProcurementHandler) UpdateContractType(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	ct, err := h.contractTypeRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Tipo de contrato não encontrado"})
		return
	}
	var in contractTypeInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if in.Nome != "" {
		ct.Nome = in.Nome
	}
	if in.Descricao != "" {
		ct.Descricao = &in.Descricao
	}
	if in.Ativo != nil {
		ct.Ativo = *in.Ativo
	}
	if err := h.contractTypeRepo.Update(ct); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, ct)
}

func (h *ProcurementHandler) DeleteContractType(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	if _, err := h.contractTypeRepo.GetByID(uint(id)); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Tipo de contrato não encontrado"})
		return
	}
	has, _ := h.contractTypeRepo.HasContracts(uint(id))
	if has {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Não é possível excluir este tipo pois existem contratos vinculados a ele."})
		return
	}
	if err := h.contractTypeRepo.Delete(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Tipo de contrato excluído"})
}

// ---------- Notifications ----------

func (h *ProcurementHandler) MyNotifications(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	items, err := h.notifRepo.ListByUser(user.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, items)
}

func (h *ProcurementHandler) MarkNotificationsRead(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	if err := h.notifRepo.MarkAllRead(user.ID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Notificações marcadas como lidas"})
}

// ---------- Purchase Researches ----------

func (h *ProcurementHandler) ListResearches(c *gin.Context) {
	items, err := h.researchRepo.List()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, items)
}

type researchItemInput struct {
	NomeProduto   string  `json:"nome_produto"`
	LinkProduto   string  `json:"link_produto"`
	ImagemPath    string  `json:"imagem_path"`
	ValorEstimado float64 `json:"valor_estimado"`
	Quantidade    float64 `json:"quantidade"`
	TipoProduto   string  `json:"tipo_produto"`
}

type researchInput struct {
	Titulo        string              `json:"titulo"`
	Justificativa string              `json:"justificativa"`
	Status        string              `json:"status"`
	Items         []researchItemInput `json:"items"`
}

func (h *ProcurementHandler) CreateResearch(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	var in researchInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if in.Titulo == "" || in.Justificativa == "" || len(in.Items) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Título, justificativa e ao menos um item são obrigatórios"})
		return
	}
	num, err := h.researchRepo.GenerateResearchNumber(time.Now())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	status := models.PResearchStatusPendente
	if in.Status == models.PResearchStatusRascunho {
		status = models.PResearchStatusRascunho
	}
	research := &models.PurchaseResearch{
		Numero:        num,
		SolicitanteID: user.ID,
		Titulo:        in.Titulo,
		Justificativa: in.Justificativa,
		Status:        status,
		DataCriacao:   time.Now(),
	}
	for _, it := range in.Items {
		item := models.PurchaseResearchItem{
			NomeProduto:   it.NomeProduto,
			ValorEstimado: it.ValorEstimado,
			Quantidade:    it.Quantidade,
			TipoProduto:   "Consumo",
			Aprovado:      true,
		}
		if it.Quantidade == 0 {
			item.Quantidade = 1
		}
		if it.TipoProduto != "" {
			item.TipoProduto = it.TipoProduto
		}
		if it.LinkProduto != "" {
			item.LinkProduto = &it.LinkProduto
		}
		if it.ImagemPath != "" {
			item.ImagemPath = &it.ImagemPath
		}
		research.Items = append(research.Items, item)
	}
	if err := h.researchRepo.Create(research); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	h.logHistory("purchase_researches", research.ID, user.ID, "Criou Pesquisa de Compra")
	c.JSON(http.StatusCreated, research)
}

func (h *ProcurementHandler) GetResearch(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	research, err := h.researchRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Pesquisa não encontrada"})
		return
	}
	c.JSON(http.StatusOK, research)
}

func (h *ProcurementHandler) SendResearch(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	research, err := h.researchRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Pesquisa não encontrada"})
		return
	}
	if research.Status != models.PResearchStatusRascunho {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Esta pesquisa não está em rascunho"})
		return
	}
	research.Status = models.PResearchStatusPendente
	if err := h.researchRepo.Update(research); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	h.logHistory("purchase_researches", research.ID, user.ID, "Enviou pesquisa para aprovação")
	c.JSON(http.StatusOK, research)
}

func (h *ProcurementHandler) DecideResearch(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	research, err := h.researchRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Pesquisa não encontrada"})
		return
	}
	var in struct {
		Acao            string `json:"acao"` // "aprovar" / "rejeitar"
		Justificativa   string `json:"justificativa_decisao"`
		CentroCustoID   uint   `json:"centro_custo_id"`
		ApprovedItemIDs []uint `json:"approved_item_ids"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if in.Acao == "aprovar" {
		if in.CentroCustoID == 0 || len(in.ApprovedItemIDs) == 0 {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Centro de custo e ao menos um item aprovado são obrigatórios"})
			return
		}
		req, err := h.convertResearchToRequest(research, user.ID, in.ApprovedItemIDs, in.CentroCustoID, in.Justificativa)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		research.Status = models.PResearchStatusAprovada
		_ = h.researchRepo.Update(research)
		h.logHistory("purchase_researches", research.ID, user.ID, "Converteu Pesquisa em Solicitação de Compra")
		c.JSON(http.StatusOK, req)
		return
	}
	research.Status = models.PResearchStatusReprovada
	_ = h.researchRepo.Update(research)
	h.logHistory("purchase_researches", research.ID, user.ID, "Rejeitou Pesquisa: "+in.Justificativa)
	c.JSON(http.StatusOK, research)
}

// convertResearchToRequest mirrors convert_research_to_purchase_request.
func (h *ProcurementHandler) convertResearchToRequest(
	research *models.PurchaseResearch, userID uint, approvedItemIDs []uint, centroCustoID uint, justificativa string,
) (*models.PurchaseRequest, error) {
	approvedSet := map[uint]bool{}
	for _, id := range approvedItemIDs {
		approvedSet[id] = true
	}

	// Default "Geral" category
	category, err := h.categoryRepo.GetByName("Geral")
	if err != nil {
		category = &models.PurchaseCategory{Nome: "Geral", Descricao: strPtr("Categoria padrão para produtos criados por cotação"), Ativo: true}
		if err := h.categoryRepo.Create(category); err != nil {
			return nil, err
		}
	}

	num, err := h.requestRepo.GenerateRequestNumber(time.Now())
	if err != nil {
		return nil, err
	}
	req := &models.PurchaseRequest{
		Numero:         num,
		SolicitanteID:  research.SolicitanteID,
		DepartamentoID: 1,
		CentroCustoID:  centroCustoID,
		Justificativa:  justificativa,
		Urgencia:       models.UrgencyMedia,
		Status:         models.PRStatusPendente,
		DataCriacao:    time.Now(),
	}
	if req.Justificativa == "" {
		req.Justificativa = fmt.Sprintf("Gerado a partir da Pesquisa de Compra %s", research.Numero)
	}
	if req.SolicitanteID == 0 {
		req.SolicitanteID = userID
	}
	if user, err := h.userRepo.GetByID(userID); err == nil && user.DepartamentoID != nil {
		req.DepartamentoID = *user.DepartamentoID
	}

	for _, item := range research.Items {
		if !approvedSet[item.ID] {
			continue
		}
		product, err := h.productRepo.GetByName(item.NomeProduto)
		if err != nil {
			prodType := models.ProductTypeEquipamento
			if item.TipoProduto == models.ResearchConsumo {
				prodType = models.ProductTypeMaterialConsumo
			}
			product = &models.PurchaseProduct{
				Codigo:      fmt.Sprintf("PRD-%s", strings.ToUpper(uuid.New().String()[:8])),
				Nome:        item.NomeProduto,
				CategoriaID: category.ID,
				Unidade:     "UN",
				Tipo:        prodType,
				Ativo:       true,
			}
			if item.ImagemPath != nil {
				product.ImagemPath = item.ImagemPath
			}
			desc := fmt.Sprintf("Produto criado automaticamente a partir da Pesquisa de Compra %s", research.Numero)
			product.Descricao = &desc
			if err := h.productRepo.Create(product); err != nil {
				return nil, err
			}
			// Initialize zero stock for consumables
			if prodType == models.ProductTypeMaterialConsumo {
				_ = h.stockRepo.Create(&models.MaterialStock{ProductID: product.ID, QuantidadeSaldo: 0})
			}
		}
		item2 := models.PurchaseRequestItem{
			ProductID:     product.ID,
			Quantidade:    item.Quantidade,
			ValorEstimado: item.ValorEstimado,
		}
		if item.LinkProduto != nil && *item.LinkProduto != "" {
			obs := fmt.Sprintf("Origem: Link %s", *item.LinkProduto)
			item2.Observacao = &obs
		}
		req.Itens = append(req.Itens, item2)
	}
	if err := h.requestRepo.Create(req); err != nil {
		return nil, err
	}
	return req, nil
}

// ---------- Kanban integration ----------

// KanbanPurchaseRequest creates a purchase request from a kanban card (Python kanban.py solicit-compra).
func (h *ProcurementHandler) KanbanPurchaseRequest(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	cardID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	card, err := h.cardRepo.GetByID(uint(cardID))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Card não encontrado"})
		return
	}
	var in struct {
		TipoItem       string  `json:"tipo_item"`
		NomeProduto    string  `json:"nome_produto"`
		Quantidade     float64 `json:"quantidade"`
		ValorEstimado  float64 `json:"valor_estimado"`
		DepartamentoID *uint   `json:"departamento_id"`
		CentroCustoID  *uint   `json:"centro_custo_id"`
		Justificativa  string  `json:"justificativa"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if in.NomeProduto == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Nome do produto é obrigatório"})
		return
	}
	if in.Quantidade <= 0 {
		in.Quantidade = 1
	}

	// 1. Category
	category, err := h.categoryRepo.First()
	if err != nil {
		category = &models.PurchaseCategory{Nome: "TI / Suprimentos", Descricao: strPtr("Categoria padrão TI"), Ativo: true}
		if err := h.categoryRepo.Create(category); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
	}

	// 2. Product
	product, err := h.productRepo.GetByName(in.NomeProduto)
	if err != nil {
		prodType := models.ProductTypeEquipamento
		if in.TipoItem == models.ResearchConsumo {
			prodType = models.ProductTypeMaterialConsumo
		}
		product = &models.PurchaseProduct{
			Codigo:      fmt.Sprintf("PROD-KB-%s", strings.ToUpper(uuid.New().String()[:6])),
			Nome:        strings.TrimSpace(in.NomeProduto),
			CategoriaID: category.ID,
			Tipo:        prodType,
			Unidade:     "UN",
			Ativo:       true,
		}
		if err := h.productRepo.Create(product); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
	}

	// 3. Department & cost center
	var deptID, ccID uint
	if in.DepartamentoID != nil {
		deptID = *in.DepartamentoID
	} else if user.DepartamentoID != nil {
		deptID = *user.DepartamentoID
	} else {
		deptID = 1
	}
	if in.CentroCustoID != nil {
		ccID = *in.CentroCustoID
	} else {
		if cc, err := h.ccRepo.First(); err == nil {
			ccID = cc.ID
		} else {
			cc := &models.CostCenter{Codigo: "CC-TI-01", Nome: "TI / Operações", AlertaLimite: true}
			_ = h.ccRepo.Create(cc)
			ccID = cc.ID
		}
	}

	// 4. Request
	num, err := h.requestRepo.GenerateRequestNumber(time.Now())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	just := in.Justificativa
	if just == "" {
		just = fmt.Sprintf("Solicitação de Compra gerada via Kanban (Card #%d: %s)", card.ID, card.Titulo)
	}
	urgencia := models.UrgencyMedia
	if card.Prioridade == models.CardPriorityAlta || card.Prioridade == models.CardPriorityUrgente {
		urgencia = models.UrgencyAlta
	}
	req := &models.PurchaseRequest{
		Numero:         num,
		SolicitanteID:  user.ID,
		DepartamentoID: deptID,
		CentroCustoID:  ccID,
		Justificativa:  just,
		Urgencia:       urgencia,
		Status:         models.PRStatusPendente,
		DataCriacao:    time.Now(),
	}
	obs := fmt.Sprintf("Item para a tarefa Kanban #%d", card.ID)
	req.Itens = append(req.Itens, models.PurchaseRequestItem{
		ProductID:     product.ID,
		Quantidade:    in.Quantidade,
		ValorEstimado: in.ValorEstimado,
		Observacao:    &obs,
	})
	if err := h.requestRepo.Create(req); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	card.PurchaseRequestID = &req.ID
	tipoItem := in.TipoItem
	if tipoItem == "" {
		tipoItem = "Consumo"
	}
	card.TipoItemNecessario = &tipoItem
	_ = h.cardRepo.Update(card)

	_ = h.interactionRepo.Create(&models.KanbanCardInteraction{
		CardID:    card.ID,
		UsuarioID: user.ID,
		Mensagem:  fmt.Sprintf("Gerou a solicitação de compra %s para '%s'.", num, in.NomeProduto),
		Tipo:      models.InteractionSistemaSupr,
	})

	c.JSON(http.StatusCreated, req)
}

// KanbanLinkStock links a material stock item to a kanban card (Python kanban.py vincular-estoque).
func (h *ProcurementHandler) KanbanLinkStock(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	cardID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	card, err := h.cardRepo.GetByID(uint(cardID))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Card não encontrado"})
		return
	}
	var in struct {
		StockID         uint    `json:"stock_id"`
		QuantidadeUsar  float64 `json:"quantidade_usar"`
		DarBaixaEstoque bool    `json:"dar_baixa_estoque"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	stock, err := h.stockRepo.GetByID(in.StockID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Item de estoque não encontrado"})
		return
	}

	card.MaterialStockID = &stock.ID
	tipoItem := "Estoque"
	card.TipoItemNecessario = &tipoItem

	if in.DarBaixaEstoque && in.QuantidadeUsar > 0 {
		_, _ = h.stockRepo.CreateOrUpdate(
			stock.ProductID, in.QuantidadeUsar, models.StockSaida, user.ID,
			fmt.Sprintf("Baixa/Uso de Estoque no Card Kanban #%d (%s)", card.ID, card.Titulo),
			"kanban_cards", &card.ID,
		)
	}
	_ = h.cardRepo.Update(card)

	prodName := "Material"
	if stock.Product != nil {
		prodName = stock.Product.Nome
	}
	_ = h.interactionRepo.Create(&models.KanbanCardInteraction{
		CardID:    card.ID,
		UsuarioID: user.ID,
		Mensagem:  fmt.Sprintf("Alocou %.2f UN do item de estoque '%s'.", in.QuantidadeUsar, prodName),
		Tipo:      models.InteractionSistemaSupr,
	})

	c.JSON(http.StatusOK, card)
}
