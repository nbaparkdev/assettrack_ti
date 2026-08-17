package handler

import (
	"fmt"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/assettrack/backend/internal/middleware"
	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/repository"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

const pmPhotoUploadDir = "uploads/maintenance"

var pmPeriodicityDays = map[string]int{
	models.PeriodicidadeDiaria:        1,
	models.PeriodicidadeSemanal:       7,
	models.PeriodicidadeQuinzenal:     15,
	models.PeriodicidadeMensal:        30,
	models.PeriodicidadeBimestral:     60,
	models.PeriodicidadeTrimestral:    90,
	models.PeriodicidadeSemestral:     180,
	models.PeriodicidadeAnual:         365,
	models.PeriodicidadePersonalizada: 0, // uses dias_personalizado
}

var pmSystemTypes = []string{
	models.MaintTypePreventiva, models.MaintTypePreditiva, models.MaintTypeInspecao,
	models.MaintTypeCalibracao, models.MaintTypeLubrificacao, models.MaintTypeLimpeza,
	models.MaintTypeAtualizacao, models.MaintTypeCorretiva, models.MaintTypePersonalizada,
}

type PreventiveHandler struct {
	planRepo       *repository.PMPlanRepository
	checklistRepo  *repository.PMChecklistRepository
	itemRepo       *repository.PMChecklistItemRepository
	planAssetRepo  *repository.PMPlanAssetRepository
	orderRepo      *repository.PMOrderRepository
	execRepo       *repository.PMExecutionRepository
	historyRepo    *repository.PMHistoryRepository
	materialRepo   *repository.PMMaterialRepository
	photoRepo      *repository.PMPhotoRepository
	notifRepo      *repository.PMNotificationRepository
	customTypeRepo *repository.PMCustomTypeRepository
	assetRepo      *repository.AssetRepository
	userRepo       *repository.UserRepository
	categoryRepo   *repository.AssetCategoryRepository
}

func NewPreventiveHandler(
	planRepo *repository.PMPlanRepository,
	checklistRepo *repository.PMChecklistRepository,
	itemRepo *repository.PMChecklistItemRepository,
	planAssetRepo *repository.PMPlanAssetRepository,
	orderRepo *repository.PMOrderRepository,
	execRepo *repository.PMExecutionRepository,
	historyRepo *repository.PMHistoryRepository,
	materialRepo *repository.PMMaterialRepository,
	photoRepo *repository.PMPhotoRepository,
	notifRepo *repository.PMNotificationRepository,
	customTypeRepo *repository.PMCustomTypeRepository,
	assetRepo *repository.AssetRepository,
	userRepo *repository.UserRepository,
	categoryRepo *repository.AssetCategoryRepository,
) *PreventiveHandler {
	return &PreventiveHandler{
		planRepo:       planRepo,
		checklistRepo:  checklistRepo,
		itemRepo:       itemRepo,
		planAssetRepo:  planAssetRepo,
		orderRepo:      orderRepo,
		execRepo:       execRepo,
		historyRepo:    historyRepo,
		materialRepo:   materialRepo,
		photoRepo:      photoRepo,
		notifRepo:      notifRepo,
		customTypeRepo: customTypeRepo,
		assetRepo:      assetRepo,
		userRepo:       userRepo,
		categoryRepo:   categoryRepo,
	}
}

// pmAdmin checks roles allowed to delete/cancel (admin, gerente_ti, gerente_infra).
func pmAdmin(user *models.User) bool {
	if user == nil {
		return false
	}
	return user.Role == models.RoleAdmin || user.Role == models.RoleGerente || user.Role == models.RoleGerenteInfra
}

// normalizeEnumValue matches an input against candidate values case-insensitively.
func normalizeEnumValue(input string, candidates []string, fallback string) string {
	for _, c := range candidates {
		if strings.EqualFold(c, input) {
			return c
		}
	}
	return fallback
}

// ---------- Plans ----------

func (h *PreventiveHandler) ListPlans(c *gin.Context) {
	plans, err := h.planRepo.List()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, plans)
}

type planInput struct {
	Nome              string  `json:"nome"`
	Tipo              string  `json:"tipo"`
	Periodicidade     string  `json:"periodicidade"`
	Criticidade       string  `json:"criticidade"`
	Prioridade        string  `json:"prioridade"`
	Descricao         string  `json:"descricao"`
	Ativo             *bool   `json:"ativo"`
	DiasPersonalizado *int    `json:"dias_personalizado"`
	ResponsavelID     *uint   `json:"responsavel_id"`
	DepartamentoID    *uint   `json:"departamento_id"`
	CategoriaID       *uint   `json:"categoria_id"`
	ProximaExecucao   *string `json:"proxima_execucao"`
}

func (h *PreventiveHandler) CreatePlan(c *gin.Context) {
	var in planInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if in.Nome == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Nome é obrigatório"})
		return
	}

	now := time.Now()
	codigo, err := h.planRepo.GeneratePlanCode(now)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	plan := &models.MaintenancePlan{
		Nome:              in.Nome,
		Codigo:            codigo,
		Tipo:              normalizeEnumValue(in.Tipo, pmSystemTypes, models.MaintTypePreventiva),
		Periodicidade:     normalizeEnumValue(in.Periodicidade, []string{models.PeriodicidadeDiaria, models.PeriodicidadeSemanal, models.PeriodicidadeQuinzenal, models.PeriodicidadeMensal, models.PeriodicidadeBimestral, models.PeriodicidadeTrimestral, models.PeriodicidadeSemestral, models.PeriodicidadeAnual, models.PeriodicidadePersonalizada}, models.PeriodicidadeMensal),
		Criticidade:       normalizeEnumValue(in.Criticidade, []string{models.CriticalityBaixa, models.CriticalityMedia, models.CriticalityAlta, models.CriticalityCritica}, models.CriticalityMedia),
		Prioridade:        normalizeEnumValue(in.Prioridade, []string{models.PriorityBaixa, models.PriorityMedia, models.PriorityAlta, models.PriorityUrgente}, models.PriorityMedia),
		Ativo:             true,
		DataCriacao:       now,
		ProximaExecucao:   now,
		ResponsavelID:     in.ResponsavelID,
		DepartamentoID:    in.DepartamentoID,
		CategoriaID:       in.CategoriaID,
		DiasPersonalizado: in.DiasPersonalizado,
	}
	if in.Descricao != "" {
		plan.Descricao = &in.Descricao
	}
	if in.ProximaExecucao != nil && *in.ProximaExecucao != "" {
		if t, err := time.Parse(time.RFC3339, *in.ProximaExecucao); err == nil {
			plan.ProximaExecucao = t
		}
	}

	if err := h.planRepo.Create(plan); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, plan)
}

func (h *PreventiveHandler) GetPlan(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	plan, err := h.planRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Plano não encontrado"})
		return
	}

	// Include orders of the plan (recent 20)
	orders, _ := h.orderRepo.List("", 0, 100)
	planOrders := make([]models.MaintenanceOrder, 0)
	for _, o := range orders {
		if o.PlanID != nil && *o.PlanID == uint(id) && len(planOrders) < 20 {
			planOrders = append(planOrders, o)
		}
	}

	c.JSON(http.StatusOK, gin.H{"plan": plan, "orders": planOrders})
}

func (h *PreventiveHandler) UpdatePlan(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	plan, err := h.planRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Plano não encontrado"})
		return
	}

	var in planInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	plan.Nome = in.Nome
	plan.Tipo = normalizeEnumValue(in.Tipo, pmSystemTypes, models.MaintTypePreventiva)
	plan.Periodicidade = normalizeEnumValue(in.Periodicidade, []string{models.PeriodicidadeDiaria, models.PeriodicidadeSemanal, models.PeriodicidadeQuinzenal, models.PeriodicidadeMensal, models.PeriodicidadeBimestral, models.PeriodicidadeTrimestral, models.PeriodicidadeSemestral, models.PeriodicidadeAnual, models.PeriodicidadePersonalizada}, models.PeriodicidadeMensal)
	plan.Criticidade = normalizeEnumValue(in.Criticidade, []string{models.CriticalityBaixa, models.CriticalityMedia, models.CriticalityAlta, models.CriticalityCritica}, models.CriticalityMedia)
	plan.Prioridade = normalizeEnumValue(in.Prioridade, []string{models.PriorityBaixa, models.PriorityMedia, models.PriorityAlta, models.PriorityUrgente}, models.PriorityMedia)
	if in.Ativo != nil {
		plan.Ativo = *in.Ativo
	}
	if plan.Periodicidade == models.PeriodicidadePersonalizada {
		plan.DiasPersonalizado = in.DiasPersonalizado
	} else {
		plan.DiasPersonalizado = nil
	}
	if in.Descricao != "" {
		plan.Descricao = &in.Descricao
	}
	plan.ResponsavelID = in.ResponsavelID
	plan.CategoriaID = in.CategoriaID

	if err := h.planRepo.Update(plan); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, plan)
}

func (h *PreventiveHandler) DeletePlan(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	if !pmAdmin(user) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Não autorizado"})
		return
	}

	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	if _, err := h.planRepo.GetByID(uint(id)); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Plano não encontrado"})
		return
	}

	count, err := h.planRepo.CountNonCancelledOrders(uint(id))
	if err == nil && count > 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Não é possível excluir o plano porque existem ordens de serviço ativas ou concluídas associadas a ele. Recomendamos inativar o plano."})
		return
	}

	// Delete notifications linked to the plan (orders cascade with plan deletion)
	_ = h.notifRepo.DeleteByPlan(uint(id))

	if err := h.planRepo.Delete(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Plano excluído"})
}

// ---------- Checklists ----------

func (h *PreventiveHandler) AddChecklist(c *gin.Context) {
	planID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	var in struct {
		Nome string `json:"nome"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if _, err := h.planRepo.GetByID(uint(planID)); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Plano não encontrado"})
		return
	}

	count, _ := h.checklistRepo.CountByPlan(uint(planID))
	checklist := &models.MaintenanceChecklist{
		PlanID: uint(planID),
		Nome:   in.Nome,
		Ordem:  int(count),
	}
	if err := h.checklistRepo.Create(checklist); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, checklist)
}

func (h *PreventiveHandler) DeleteChecklist(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	if !pmAdmin(user) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Não autorizado"})
		return
	}

	checklistID, err := strconv.ParseUint(c.Param("checklistId"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	if err := h.checklistRepo.Delete(uint(checklistID)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Checklist excluído"})
}

func (h *PreventiveHandler) AddChecklistItem(c *gin.Context) {
	checklistID, err := strconv.ParseUint(c.Param("checklistId"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	var in struct {
		Descricao   string `json:"descricao"`
		Obrigatorio *bool  `json:"obrigatorio"`
		RequerFoto  *bool  `json:"requer_foto"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	checklist, err := h.checklistRepo.GetByID(uint(checklistID))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Checklist não encontrado"})
		return
	}

	count, _ := h.itemRepo.CountByChecklist(uint(checklistID))
	item := &models.MaintenanceChecklistItem{
		ChecklistID: uint(checklistID),
		Descricao:   in.Descricao,
		Obrigatorio: true,
		RequerFoto:  false,
		Ordem:       int(count),
	}
	if in.Obrigatorio != nil {
		item.Obrigatorio = *in.Obrigatorio
	}
	if in.RequerFoto != nil {
		item.RequerFoto = *in.RequerFoto
	}
	_ = checklist

	if err := h.itemRepo.Create(item); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, item)
}

func (h *PreventiveHandler) DeleteChecklistItem(c *gin.Context) {
	itemID, err := strconv.ParseUint(c.Param("itemId"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	if err := h.itemRepo.Delete(uint(itemID)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Item excluído"})
}

// ---------- Plan Assets ----------

func (h *PreventiveHandler) AddPlanAsset(c *gin.Context) {
	planID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	var in struct {
		AssetID uint `json:"asset_id"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	existing, err := h.planAssetRepo.GetByPlanAndAsset(uint(planID), in.AssetID)
	if err == nil && existing != nil {
		c.JSON(http.StatusOK, existing)
		return
	}

	link := &models.MaintenancePlanAsset{PlanID: uint(planID), AssetID: in.AssetID}
	if err := h.planAssetRepo.Create(link); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, link)
}

func (h *PreventiveHandler) RemovePlanAsset(c *gin.Context) {
	linkID, err := strconv.ParseUint(c.Param("linkId"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	if err := h.planAssetRepo.Delete(uint(linkID)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Vínculo removido"})
}

// ---------- Orders ----------

func (h *PreventiveHandler) ListOrders(c *gin.Context) {
	status := c.Query("status")
	skip, _ := strconv.Atoi(c.DefaultQuery("skip", "0"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))

	orders, err := h.orderRepo.List(status, skip, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, orders)
}

type orderInput struct {
	Tipo                string  `json:"tipo"`
	Prioridade          string  `json:"prioridade"`
	Descricao           string  `json:"descricao"`
	AssetID             *uint   `json:"asset_id"`
	InfraPredialServico *string `json:"infra_predial_servico"`
	PlanID              *uint   `json:"plan_id"`
	TecnicoID           *uint   `json:"tecnico_id"`
	DataAgendada        *string `json:"data_agendada"`
}

func (h *PreventiveHandler) CreateOrder(c *gin.Context) {
	user := middleware.GetCurrentUser(c)

	var in orderInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	numero, err := h.orderRepo.GenerateOrderNumber(time.Now())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Custom type handling (like Python: "custom:Name" → Personalizada + [TIPO: ...])
	finalTipo := in.Tipo
	finalObs := in.Descricao
	if strings.HasPrefix(in.Tipo, "custom:") {
		customName := strings.TrimSpace(strings.TrimPrefix(in.Tipo, "custom:"))
		isSystem := false
		for _, t := range pmSystemTypes {
			if strings.EqualFold(t, customName) {
				isSystem = true
				break
			}
		}
		if isSystem {
			finalTipo = customName
		} else {
			finalTipo = models.MaintTypePersonalizada
			finalObs = fmt.Sprintf("[TIPO: %s]\n%s", customName, in.Descricao)
		}
	}

	order := &models.MaintenanceOrder{
		Numero:        numero,
		AssetID:       in.AssetID,
		Tipo:          normalizeEnumValue(finalTipo, pmSystemTypes, models.MaintTypePersonalizada),
		Prioridade:    normalizeEnumValue(in.Prioridade, []string{models.PriorityBaixa, models.PriorityMedia, models.PriorityAlta, models.PriorityUrgente}, models.PriorityMedia),
		Status:        models.PMStatusAberta,
		DataAbertura:  time.Now(),
		PlanID:        in.PlanID,
		TecnicoID:     in.TecnicoID,
		SolicitanteID: &user.ID,
	}
	if in.AssetID == nil && in.InfraPredialServico != nil && *in.InfraPredialServico != "" {
		order.InfraPredialServico = in.InfraPredialServico
	}
	if finalObs != "" {
		order.Observacoes = &finalObs
	}
	if in.DataAgendada != nil && *in.DataAgendada != "" {
		if t, err := time.Parse(time.RFC3339, *in.DataAgendada); err == nil {
			order.DataAgendada = &t
		}
	}

	if err := h.orderRepo.Create(order); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Notify assigned technician
	if order.TecnicoID != nil {
		h.notifyOrderAssigned(*order)
	}

	c.JSON(http.StatusCreated, order)
}

func (h *PreventiveHandler) notifyOrderAssigned(order models.MaintenanceOrder) {
	assetName := "Manutenção de Infra Predial"
	var patrimonio string
	if order.InfraPredialServico != nil && *order.InfraPredialServico != "" {
		assetName = *order.InfraPredialServico
	}
	if order.AssetID != nil {
		if asset, err := h.assetRepo.GetByID(*order.AssetID); err == nil && asset != nil {
			assetName = asset.Nome
			patrimonio = asset.EPatrimonio
		}
	}
	dataStr := "Não agendada"
	if order.DataAgendada != nil {
		dataStr = order.DataAgendada.Format("02/01/2006 15:04")
	}
	msg := fmt.Sprintf("Você foi designado como responsável por uma nova Ordem de Serviço de manutenção.\n\nOS Código: %s\nEquipamento/Ativo: %s%s\nPrioridade: %s\nData Agendada: %s",
		order.Numero, assetName, map[bool]string{true: " (Patrimônio: " + patrimonio + ")", false: ""}[patrimonio != ""], strings.ToUpper(order.Prioridade), dataStr)
	_ = h.notifRepo.Create(&models.MaintenanceNotification{
		OrderID:   &order.ID,
		UsuarioID: *order.TecnicoID,
		Tipo:      "order_assigned",
		Mensagem:  msg,
	})
}

func (h *PreventiveHandler) GetOrder(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	order, err := h.orderRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ordem de serviço não encontrada"})
		return
	}

	// Resolve checklists from the order's plan, merged with executions
	var checklists []models.MaintenanceChecklist
	if order.PlanID != nil {
		checklists, _ = h.checklistRepo.ListByPlan(*order.PlanID)
	}

	c.JSON(http.StatusOK, gin.H{"order": order, "checklists": checklists})
}

func (h *PreventiveHandler) UpdateOrder(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	order, err := h.orderRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ordem não encontrada"})
		return
	}

	var in struct {
		Tipo         string  `json:"tipo"`
		Status       string  `json:"status"`
		Prioridade   string  `json:"prioridade"`
		Criticidade  string  `json:"criticidade"`
		Observacoes  string  `json:"observacoes"`
		TecnicoID    *uint   `json:"tecnico_id"`
		DataAgendada *string `json:"data_agendada"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	statusAnterior := order.Status
	tecnicoAnteriorID := order.TecnicoID

	// Custom type processing
	finalTipo := in.Tipo
	finalObs := in.Observacoes
	if strings.HasPrefix(in.Tipo, "custom:") {
		customName := strings.TrimSpace(strings.TrimPrefix(in.Tipo, "custom:"))
		isSystem := false
		for _, t := range pmSystemTypes {
			if strings.EqualFold(t, customName) {
				isSystem = true
				break
			}
		}
		if isSystem {
			finalTipo = customName
		} else {
			finalTipo = models.MaintTypePersonalizada
			finalObs = fmt.Sprintf("[TIPO: %s]\n%s", customName, strings.TrimPrefix(finalObs, "[TIPO: "))
		}
	}

	order.Tipo = normalizeEnumValue(finalTipo, pmSystemTypes, models.MaintTypePersonalizada)
	order.Status = normalizeEnumValue(in.Status, []string{models.PMStatusAberta, models.PMStatusAgendada, models.PMStatusEmAndamento, models.PMStatusAguardandoPeca, models.PMStatusPausada, models.PMStatusConcluida, models.PMStatusCancelada}, statusAnterior)
	order.Prioridade = normalizeEnumValue(in.Prioridade, []string{models.PriorityBaixa, models.PriorityMedia, models.PriorityAlta, models.PriorityUrgente}, models.PriorityMedia)
	order.Criticidade = normalizeEnumValue(in.Criticidade, []string{models.CriticalityBaixa, models.CriticalityMedia, models.CriticalityAlta, models.CriticalityCritica}, models.CriticalityMedia)
	order.TecnicoID = in.TecnicoID
	order.DataAgendada = nil
	if in.DataAgendada != nil && *in.DataAgendada != "" {
		if t, err := time.Parse(time.RFC3339, *in.DataAgendada); err == nil {
			order.DataAgendada = &t
		}
	}
	order.Observacoes = &finalObs

	// History entry when status changed via form
	if statusAnterior != order.Status {
		_ = h.historyRepo.Create(&models.MaintenanceHistory{
			OrderID:        order.ID,
			Acao:           "Edição de Ordem",
			Descricao:      fmt.Sprintf("Ordem atualizada administrativamente por %s. Status alterado.", user.Nome),
			UsuarioID:      &user.ID,
			StatusAnterior: &statusAnterior,
			StatusNovo:     &order.Status,
		})
	}

	if err := h.orderRepo.Update(order); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Notify on technician reassignment
	if order.TecnicoID != nil && (tecnicoAnteriorID == nil || *tecnicoAnteriorID != *order.TecnicoID) {
		h.notifyOrderAssigned(*order)
	}

	c.JSON(http.StatusOK, order)
}

func (h *PreventiveHandler) DeleteOrder(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	if !pmAdmin(user) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Não autorizado"})
		return
	}

	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	order, err := h.orderRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ordem não encontrada"})
		return
	}

	if order.Status == models.PMStatusConcluida {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Não é possível excluir ordens de serviço com status Concluída."})
		return
	}

	_ = h.notifRepo.DeleteByOrder(uint(id))

	if err := h.orderRepo.Delete(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Ordem excluída"})
}

// ---------- Status transitions ----------

func (h *PreventiveHandler) StartOrder(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	order, err := h.orderRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ordem não encontrada"})
		return
	}

	if order.Status != models.PMStatusAberta && order.Status != models.PMStatusAgendada && order.Status != models.PMStatusPausada {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Ordem não pode ser iniciada no status atual"})
		return
	}

	statusAnterior := order.Status
	now := time.Now()
	order.Status = models.PMStatusEmAndamento
	order.DataInicio = &now
	if order.TecnicoID == nil {
		order.TecnicoID = &user.ID
	}

	_ = h.historyRepo.Create(&models.MaintenanceHistory{
		OrderID:        order.ID,
		Acao:           "Ordem Iniciada",
		Descricao:      fmt.Sprintf("Ordem iniciada por %s", user.Nome),
		UsuarioID:      &user.ID,
		StatusAnterior: &statusAnterior,
		StatusNovo:     &order.Status,
	})

	if err := h.orderRepo.Update(order); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, order)
}

func (h *PreventiveHandler) PauseOrder(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	order, err := h.orderRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ordem não encontrada"})
		return
	}

	if order.Status != models.PMStatusEmAndamento {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Somente ordens em andamento podem ser pausadas"})
		return
	}

	var in struct {
		Motivo string `json:"motivo"`
	}
	_ = c.ShouldBindJSON(&in)

	statusAnterior := order.Status
	now := time.Now()
	order.Status = models.PMStatusPausada
	order.DataPausa = &now

	// Accumulate elapsed minutes
	if order.DataInicio != nil {
		elapsed := int(now.Sub(*order.DataInicio).Minutes())
		current := 0
		if order.TempoTotalMinutos != nil {
			current = *order.TempoTotalMinutos
		}
		total := current + elapsed
		order.TempoTotalMinutos = &total
	}

	desc := fmt.Sprintf("Ordem pausada por %s", user.Nome)
	if in.Motivo != "" {
		desc += fmt.Sprintf(". Motivo: %s", in.Motivo)
	}
	_ = h.historyRepo.Create(&models.MaintenanceHistory{
		OrderID:        order.ID,
		Acao:           "Ordem Pausada",
		Descricao:      desc,
		UsuarioID:      &user.ID,
		StatusAnterior: &statusAnterior,
		StatusNovo:     &order.Status,
	})

	if err := h.orderRepo.Update(order); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, order)
}

func (h *PreventiveHandler) CompleteOrder(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	order, err := h.orderRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ordem não encontrada"})
		return
	}

	if order.Status == models.PMStatusConcluida || order.Status == models.PMStatusCancelada {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Ordem já finalizada"})
		return
	}

	var in struct {
		Solucao    string  `json:"solucao"`
		CustoTotal *string `json:"custo_total"`
	}
	_ = c.ShouldBindJSON(&in)

	statusAnterior := order.Status
	now := time.Now()
	order.Status = models.PMStatusConcluida
	order.DataConclusao = &now
	if in.Solucao != "" {
		order.Solucao = &in.Solucao
	}

	// Total time
	if order.DataInicio != nil {
		elapsed := int(now.Sub(*order.DataInicio).Minutes())
		current := 0
		if order.TempoTotalMinutos != nil {
			current = *order.TempoTotalMinutos
		}
		total := current + elapsed
		order.TempoTotalMinutos = &total
	}

	// Cost = materials + extra
	totalMaterials, _ := h.materialRepo.SumByOrder(order.ID)
	extraCost := 0.0
	if in.CustoTotal != nil && strings.TrimSpace(*in.CustoTotal) != "" {
		clean := *in.CustoTotal
		if strings.Contains(clean, ",") {
			clean = strings.ReplaceAll(clean, ".", "")
			clean = strings.ReplaceAll(clean, ",", ".")
		}
		if v, err := strconv.ParseFloat(clean, 64); err == nil {
			extraCost = v
		}
	}
	totalCost := totalMaterials + extraCost
	order.CustoTotal = &totalCost

	// Update plan dates
	if order.PlanID != nil {
		if plan, err := h.planRepo.GetByID(*order.PlanID); err == nil && plan != nil {
			plan.DataUltimaExecucao = &now
			days := pmPeriodicityDays[plan.Periodicidade]
			if days == 0 {
				if plan.DiasPersonalizado != nil {
					days = *plan.DiasPersonalizado
				} else {
					days = 30
				}
			}
			next := now.AddDate(0, 0, days)
			plan.ProximaExecucao = next
			_ = h.planRepo.Update(plan)
		}
	}

	desc := fmt.Sprintf("Ordem concluída por %s", user.Nome)
	if in.Solucao != "" {
		sol := in.Solucao
		if len(sol) > 100 {
			sol = sol[:100]
		}
		desc += fmt.Sprintf(". Solução: %s", sol)
	}
	_ = h.historyRepo.Create(&models.MaintenanceHistory{
		OrderID:        order.ID,
		Acao:           "Ordem Concluída",
		Descricao:      desc,
		UsuarioID:      &user.ID,
		StatusAnterior: &statusAnterior,
		StatusNovo:     &order.Status,
	})

	if err := h.orderRepo.Update(order); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Notify managers
	h.notifyOrderCompleted(*order, user.Nome)

	c.JSON(http.StatusOK, order)
}

func (h *PreventiveHandler) notifyOrderCompleted(order models.MaintenanceOrder, technicianName string) {
	assetName := "Equipamento"
	if order.AssetID != nil {
		if asset, err := h.assetRepo.GetByID(*order.AssetID); err == nil && asset != nil {
			assetName = asset.Nome
		}
	}
	custo := 0.0
	if order.CustoTotal != nil {
		custo = *order.CustoTotal
	}
	msg := fmt.Sprintf("A Ordem de Serviço %s foi concluída pelo técnico responsável.\n\nCódigo: %s\nEquipamento: %s\nTécnico: %s\nCusto Total: R$ %.2f",
		order.Numero, order.Numero, assetName, technicianName, custo)

	// Notify admins/gerentes
	managers, err := h.userRepo.ListByRoles([]string{models.RoleAdmin, models.RoleGerente, models.RoleGerenteInfra})
	if err == nil {
		for _, mgr := range managers {
			_ = h.notifRepo.Create(&models.MaintenanceNotification{
				OrderID:   &order.ID,
				UsuarioID: mgr.ID,
				Tipo:      "order_completed",
				Mensagem:  msg,
			})
		}
	}
}

func (h *PreventiveHandler) CancelOrder(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	if !pmAdmin(user) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Não autorizado"})
		return
	}

	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	order, err := h.orderRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ordem não encontrada"})
		return
	}

	if order.Status == models.PMStatusConcluida || order.Status == models.PMStatusCancelada {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Ordem já finalizada"})
		return
	}

	var in struct {
		Motivo string `json:"motivo"`
	}
	_ = c.ShouldBindJSON(&in)

	statusAnterior := order.Status
	order.Status = models.PMStatusCancelada

	desc := fmt.Sprintf("Ordem cancelada por %s", user.Nome)
	if in.Motivo != "" {
		desc += fmt.Sprintf(". Motivo: %s", in.Motivo)
	}
	_ = h.historyRepo.Create(&models.MaintenanceHistory{
		OrderID:        order.ID,
		Acao:           "Ordem Cancelada",
		Descricao:      desc,
		UsuarioID:      &user.ID,
		StatusAnterior: &statusAnterior,
		StatusNovo:     &order.Status,
	})

	if err := h.orderRepo.Update(order); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, order)
}

// ---------- Checklist execution ----------

func (h *PreventiveHandler) ExecuteChecklistItem(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	orderID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	if _, err := h.orderRepo.GetByID(uint(orderID)); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ordem não encontrada"})
		return
	}

	checklistItemIDStr := c.PostForm("checklist_item_id")
	if checklistItemIDStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "checklist_item_id é obrigatório"})
		return
	}
	itemID, err := strconv.ParseUint(checklistItemIDStr, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "checklist_item_id inválido"})
		return
	}

	isDone := c.PostForm("concluido") == "on" || c.PostForm("concluido") == "true"
	observacao := c.PostForm("observacao")

	item, err := h.itemRepo.GetByID(uint(itemID))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Item de checklist não encontrado"})
		return
	}

	// Photo handling
	var photo *multipart.FileHeader
	if f, err := c.FormFile("foto"); err == nil {
		photo = f
	}

	if item.RequerFoto && isDone && photo == nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": fmt.Sprintf("A foto é obrigatória para o item: %s", item.Descricao)})
		return
	}

	now := time.Now()
	execution, err := h.execRepo.GetByOrderAndItem(uint(orderID), uint(itemID))
	if err != nil {
		execution = &models.MaintenanceExecution{
			OrderID:         uint(orderID),
			ChecklistItemID: uint(itemID),
			Concluido:       isDone,
			DataExecucao:    &now,
			ExecutadoPorID:  &user.ID,
		}
		if observacao != "" {
			execution.Observacao = &observacao
		}
		if err := h.execRepo.Create(execution); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
	} else {
		execution.Concluido = isDone
		execution.DataExecucao = &now
		execution.ExecutadoPorID = &user.ID
		if observacao != "" {
			execution.Observacao = &observacao
		} else {
			execution.Observacao = nil
		}
		if err := h.execRepo.Update(execution); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
	}

	// Save photo evidence
	if photo != nil && isDone {
		h.saveChecklistPhoto(c, photo, uint(orderID), execution.ID, item, user)
	}

	c.JSON(http.StatusOK, execution)
}

func (h *PreventiveHandler) saveChecklistPhoto(c *gin.Context, photo *multipart.FileHeader, orderID, executionID uint, item *models.MaintenanceChecklistItem, user *models.User) {
	if err := os.MkdirAll(pmPhotoUploadDir, 0o755); err != nil {
		return
	}
	ext := filepath.Ext(photo.Filename)
	filename := fmt.Sprintf("os_%d_exec_%d_%s%s", orderID, executionID, uuid.New().String()[:16], ext)
	filePath := filepath.Join(pmPhotoUploadDir, filename)

	f, err := photo.Open()
	if err != nil {
		return
	}
	defer f.Close()
	data := make([]byte, photo.Size)
	if _, err := f.Read(data); err != nil {
		return
	}
	if err := os.WriteFile(filePath, data, 0o644); err != nil {
		return
	}

	descricao := fmt.Sprintf("Evidência do checklist: %s", item.Descricao)
	_ = h.photoRepo.Create(&models.MaintenancePhoto{
		OrderID:        orderID,
		ExecutionID:    &executionID,
		Tipo:           models.PhotoDurante,
		CaminhoArquivo: "/" + filepath.ToSlash(filePath),
		Descricao:      &descricao,
		UploadPorID:    &user.ID,
	})
}

// ---------- History ----------

func (h *PreventiveHandler) OrderHistory(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	if _, err := h.orderRepo.GetByID(uint(id)); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ordem não encontrada"})
		return
	}

	history, err := h.historyRepo.ListByOrder(uint(id))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, history)
}

// ---------- Materials ----------

func (h *PreventiveHandler) AddOrderMaterial(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	orderID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	if _, err := h.orderRepo.GetByID(uint(orderID)); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ordem de serviço não encontrada"})
		return
	}

	var in struct {
		Produto       string  `json:"produto"`
		Quantidade    float64 `json:"quantidade"`
		ValorUnitario float64 `json:"valor_unitario"`
		Observacao    string  `json:"observacao"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if in.Produto == "" || in.Quantidade <= 0 || in.ValorUnitario <= 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Produto, quantidade e valor unitário são obrigatórios"})
		return
	}

	valorTotal := in.Quantidade * in.ValorUnitario
	material := &models.MaintenanceMaterial{
		OrderID:       uint(orderID),
		Produto:       in.Produto,
		Quantidade:    in.Quantidade,
		ValorUnitario: in.ValorUnitario,
		ValorTotal:    valorTotal,
	}
	if in.Observacao != "" {
		material.Observacao = &in.Observacao
	}

	if err := h.materialRepo.Create(material); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	_ = h.historyRepo.Create(&models.MaintenanceHistory{
		OrderID:   uint(orderID),
		Acao:      "Material Adicionado",
		Descricao: fmt.Sprintf("Material '%s' (x%.2f) adicionado por %s. Valor total: R$ %.2f", in.Produto, in.Quantidade, user.Nome, valorTotal),
		UsuarioID: &user.ID,
	})

	c.JSON(http.StatusCreated, material)
}

func (h *PreventiveHandler) RemoveOrderMaterial(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	orderID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	materialID, err := strconv.ParseUint(c.Param("materialId"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	material, err := h.materialRepo.GetByID(uint(materialID))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Material não encontrado"})
		return
	}

	if err := h.materialRepo.Delete(uint(materialID)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	_ = h.historyRepo.Create(&models.MaintenanceHistory{
		OrderID:   uint(orderID),
		Acao:      "Material Removido",
		Descricao: fmt.Sprintf("Material '%s' removido por %s", material.Produto, user.Nome),
		UsuarioID: &user.ID,
	})

	c.JSON(http.StatusOK, gin.H{"message": "Material removido"})
}

// ---------- Photos ----------

func (h *PreventiveHandler) UploadOrderPhoto(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	orderID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	if _, err := h.orderRepo.GetByID(uint(orderID)); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Ordem não encontrada"})
		return
	}

	photo, err := c.FormFile("foto")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Arquivo de foto não enviado"})
		return
	}

	tipo := c.PostForm("tipo")
	if tipo == "" {
		tipo = models.PhotoDurante
	}
	tipo = normalizeEnumValue(tipo, []string{models.PhotoAntes, models.PhotoDurante, models.PhotoDepois}, models.PhotoDurante)

	descricao := c.PostForm("descricao")

	if err := os.MkdirAll(pmPhotoUploadDir, 0o755); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	ext := filepath.Ext(photo.Filename)
	filename := fmt.Sprintf("os_%d_%d_%s%s", orderID, time.Now().Unix(), uuid.New().String()[:8], ext)
	filePath := filepath.Join(pmPhotoUploadDir, filename)

	f, err := photo.Open()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer f.Close()
	data := make([]byte, photo.Size)
	if _, err := f.Read(data); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if err := os.WriteFile(filePath, data, 0o644); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	record := &models.MaintenancePhoto{
		OrderID:        uint(orderID),
		Tipo:           tipo,
		CaminhoArquivo: "/" + filepath.ToSlash(filePath),
		UploadPorID:    &user.ID,
	}
	if descricao != "" {
		record.Descricao = &descricao
	}
	if err := h.photoRepo.Create(record); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, record)
}

func (h *PreventiveHandler) DeleteOrderPhoto(c *gin.Context) {
	photoID, err := strconv.ParseUint(c.Param("photoId"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	record, err := h.photoRepo.GetByID(uint(photoID))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Foto não encontrada"})
		return
	}

	// Remove physical file
	path := filepath.FromSlash(filepath.Clean(record.CaminhoArquivo))
	_ = os.Remove(path)

	if err := h.photoRepo.Delete(uint(photoID)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Foto excluída"})
}

// ---------- Custom types ----------

func (h *PreventiveHandler) ListCustomTypes(c *gin.Context) {
	types, err := h.customTypeRepo.List()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, types)
}

func (h *PreventiveHandler) CreateCustomType(c *gin.Context) {
	var in struct {
		Nome      string `json:"nome"`
		Descricao string `json:"descricao"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if in.Nome == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Nome é obrigatório"})
		return
	}

	t := &models.CustomMaintenanceType{Nome: in.Nome}
	if in.Descricao != "" {
		t.Descricao = &in.Descricao
	}
	if err := h.customTypeRepo.Create(t); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Já existe um tipo com este nome"})
		return
	}
	c.JSON(http.StatusCreated, t)
}

func (h *PreventiveHandler) UpdateCustomType(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	t, err := h.customTypeRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Tipo não encontrado"})
		return
	}

	var in struct {
		Nome      string `json:"nome"`
		Descricao string `json:"descricao"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	t.Nome = in.Nome
	if in.Descricao != "" {
		t.Descricao = &in.Descricao
	}
	if err := h.customTypeRepo.Update(t); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, t)
}

func (h *PreventiveHandler) DeleteCustomType(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	if err := h.customTypeRepo.Delete(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Tipo excluído"})
}

// ---------- Notifications ----------

func (h *PreventiveHandler) MyNotifications(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	notifs, err := h.notifRepo.ListByUser(user.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, notifs)
}

func (h *PreventiveHandler) MarkNotificationsRead(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	if err := h.notifRepo.MarkAllRead(user.ID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Notificações marcadas como lidas"})
}

// ---------- Dashboard ----------

func (h *PreventiveHandler) Dashboard(c *gin.Context) {
	plans, _ := h.planRepo.List()
	orders, _ := h.orderRepo.List("", 0, 1000)

	activePlans := 0
	for _, p := range plans {
		if p.Ativo {
			activePlans++
		}
	}

	statusCounts := map[string]int{}
	openOrders := 0
	dueSoon := 0
	now := time.Now()
	for _, o := range orders {
		statusCounts[o.Status]++
		if o.Status != models.PMStatusConcluida && o.Status != models.PMStatusCancelada {
			openOrders++
		}
		if o.DataAgendada != nil && (o.Status == models.PMStatusAberta || o.Status == models.PMStatusAgendada) {
			days := o.DataAgendada.Sub(now).Hours() / 24
			if days >= 0 && days <= 7 {
				dueSoon++
			}
		}
	}

	// Plans due
	plansDue := 0
	for _, p := range plans {
		if p.Ativo && p.ProximaExecucao.Before(now.AddDate(0, 0, 7)) {
			plansDue++
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"total_plans":      len(plans),
		"active_plans":     activePlans,
		"plans_due":        plansDue,
		"total_orders":     len(orders),
		"open_orders":      openOrders,
		"due_soon":         dueSoon,
		"orders_by_status": statusCounts,
	})
}
