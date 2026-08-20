package handler

import (
	"encoding/json"
	"fmt"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/assettrack/backend/internal/middleware"
	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/repository"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

const kanbanUploadDir = "uploads/kanban"
const defaultKanbanBoardBackgroundColor = "#212121"
const defaultKanbanBoardPattern = "glow"

// KanbanEvent is a server-sent event payload.
type KanbanEvent struct {
	Type    string      `json:"type"`
	Payload interface{} `json:"payload"`
}

// SSEClient is a subscribed user connection.
type SSEClient struct {
	userID uint
	ch     chan KanbanEvent
}

// KanbanSSEBroker broadcasts events to subscribed users.
type KanbanSSEBroker struct {
	mu      sync.RWMutex
	clients map[uint]map[*SSEClient]bool
}

func NewKanbanSSEBroker() *KanbanSSEBroker {
	return &KanbanSSEBroker{clients: make(map[uint]map[*SSEClient]bool)}
}

func (b *KanbanSSEBroker) Subscribe(userID uint) *SSEClient {
	client := &SSEClient{userID: userID, ch: make(chan KanbanEvent, 16)}
	b.mu.Lock()
	if b.clients[userID] == nil {
		b.clients[userID] = make(map[*SSEClient]bool)
	}
	b.clients[userID][client] = true
	b.mu.Unlock()
	return client
}

func (b *KanbanSSEBroker) Unsubscribe(client *SSEClient) {
	b.mu.Lock()
	if users, ok := b.clients[client.userID]; ok {
		delete(users, client)
		if len(users) == 0 {
			delete(b.clients, client.userID)
		}
	}
	b.mu.Unlock()
	close(client.ch)
}

func (b *KanbanSSEBroker) BroadcastToUsers(userIDs []uint, event KanbanEvent) {
	b.mu.RLock()
	defer b.mu.RUnlock()
	for _, uid := range userIDs {
		if clients, ok := b.clients[uid]; ok {
			for client := range clients {
				select {
				case client.ch <- event:
				default:
					// Slow client — drop event
				}
			}
		}
	}
}

type KanbanHandler struct {
	projectRepo     *repository.KanbanProjectRepository
	columnRepo      *repository.KanbanColumnRepository
	cardRepo        *repository.KanbanCardRepository
	interactionRepo *repository.KanbanInteractionRepository
	attachmentRepo  *repository.KanbanAttachmentRepository
	notifRepo       *repository.KanbanNotificationRepository
	userRepo        *repository.UserRepository
	broker          *KanbanSSEBroker
}

func NewKanbanHandler(
	projectRepo *repository.KanbanProjectRepository,
	columnRepo *repository.KanbanColumnRepository,
	cardRepo *repository.KanbanCardRepository,
	interactionRepo *repository.KanbanInteractionRepository,
	attachmentRepo *repository.KanbanAttachmentRepository,
	notifRepo *repository.KanbanNotificationRepository,
	userRepo *repository.UserRepository,
	broker *KanbanSSEBroker,
) *KanbanHandler {
	return &KanbanHandler{
		projectRepo:     projectRepo,
		columnRepo:      columnRepo,
		cardRepo:        cardRepo,
		interactionRepo: interactionRepo,
		attachmentRepo:  attachmentRepo,
		notifRepo:       notifRepo,
		userRepo:        userRepo,
		broker:          broker,
	}
}

var defaultKanbanColumns = []struct {
	Nome string
	Cor  string
}{
	{"A Fazer", "#3B82F6"},
	{"Em Andamento", "#F59E0B"},
	{"Aguardando Compras", "#8B5CF6"},
	{"Concluído", "#10B981"},
}

// userCanAccessProject checks if the user is admin, the creator, or a participant.
func (h *KanbanHandler) userCanAccessProject(user *models.User, project *models.KanbanProject) bool {
	if user.Role == models.RoleAdmin || project.CriadorID == user.ID {
		return true
	}
	for _, p := range project.Participantes {
		if p.ID == user.ID {
			return true
		}
	}
	return false
}

// projectParticipantIDs returns unique user IDs to notify about a project.
func (h *KanbanHandler) projectParticipantIDs(project *models.KanbanProject) []uint {
	ids := map[uint]bool{project.CriadorID: true}
	for _, p := range project.Participantes {
		ids[p.ID] = true
	}
	result := make([]uint, 0, len(ids))
	for id := range ids {
		result = append(result, id)
	}
	return result
}

func (h *KanbanHandler) notify(userIDs []uint, autorID uint, tipo, titulo, mensagem string, projectID, cardID *uint) {
	for _, uid := range userIDs {
		link := fmt.Sprintf("/kanban")
		_ = h.notifRepo.Create(&models.KanbanNotification{
			UserID:    uid,
			AutorID:   &autorID,
			ProjectID: projectID,
			CardID:    cardID,
			Tipo:      tipo,
			Titulo:    titulo,
			Mensagem:  mensagem,
			Link:      &link,
			Lida:      uid == autorID,
		})
	}
	h.broker.BroadcastToUsers(userIDs, KanbanEvent{Type: "kanban_update", Payload: gin.H{"tipo": tipo, "mensagem": mensagem}})
}

// ---------- Projects ----------

func (h *KanbanHandler) ListProjects(c *gin.Context) {
	includeArchived := c.Query("incluir_arquivados") == "true"
	projects, err := h.projectRepo.List(includeArchived)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	user := middleware.GetCurrentUser(c)
	accessible := make([]models.KanbanProject, 0)
	for _, p := range projects {
		if h.userCanAccessProject(user, &p) {
			accessible = append(accessible, p)
		}
	}
	c.JSON(http.StatusOK, accessible)
}

func (h *KanbanHandler) CreateProject(c *gin.Context) {
	user := middleware.GetCurrentUser(c)

	var in struct {
		Titulo               string `json:"titulo"`
		Descricao            string `json:"descricao"`
		BoardBackgroundColor string `json:"board_background_color"`
		BoardPattern         string `json:"board_pattern"`
		RelatedToMaintenance bool   `json:"related_to_maintenance"`
		RelatedToPreventive  bool   `json:"related_to_preventive"`
		PreventivePlanID     *uint  `json:"preventive_plan_id"`
		ParticipanteIDs      []uint `json:"participante_ids"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if strings.TrimSpace(in.Titulo) == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Título é obrigatório"})
		return
	}

	// Include creator in participants
	participantIDs := append([]uint{user.ID}, in.ParticipanteIDs...)
	var participants []models.User
	if len(participantIDs) > 0 {
		if err := h.userRepo.DB().Where("id IN ?", uniqueUints(participantIDs)).Find(&participants).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
	}

	var preventivePlanID *uint
	if in.RelatedToPreventive && in.PreventivePlanID != nil {
		var plan models.MaintenancePlan
		if err := h.userRepo.DB().First(&plan, *in.PreventivePlanID).Error; err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Plano preventivo não encontrado"})
			return
		}
		preventivePlanID = in.PreventivePlanID
	}

	project := &models.KanbanProject{
		Titulo:               strings.TrimSpace(in.Titulo),
		BoardBackgroundColor: normalizeHexColor(in.BoardBackgroundColor, defaultKanbanBoardBackgroundColor),
		BoardPattern:         normalizeBoardPattern(in.BoardPattern),
		RelatedToMaintenance: in.RelatedToMaintenance,
		RelatedToPreventive:  in.RelatedToPreventive,
		PreventivePlanID:     preventivePlanID,
		CriadorID:            user.ID,
		IsActive:             true,
		Participantes:        participants,
	}
	if strings.TrimSpace(in.Descricao) != "" {
		d := strings.TrimSpace(in.Descricao)
		project.Descricao = &d
	}

	if err := h.projectRepo.Create(project); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Default columns
	for idx, col := range defaultKanbanColumns {
		_ = h.columnRepo.Create(&models.KanbanColumn{
			ProjectID: project.ID,
			Nome:      col.Nome,
			Cor:       col.Cor,
			Ordem:     idx,
			IsDefault: true,
		})
	}

	h.notify(h.projectParticipantIDs(project), user.ID, models.NotifProjetoAdicionado,
		"Novo projeto de Kanban",
		fmt.Sprintf("%s criou o projeto '%s'.", user.Nome, project.Titulo),
		&project.ID, nil)

	loaded, _ := h.projectRepo.GetByID(project.ID)
	if loaded == nil {
		loaded = project
	}
	c.JSON(http.StatusCreated, loaded)
}

func (h *KanbanHandler) GetProjectBoard(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	project, err := h.projectRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Projeto não encontrado"})
		return
	}

	if !h.userCanAccessProject(user, project) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Acesso não autorizado a este projeto"})
		return
	}

	// Board progress (like Python)
	totalCards := 0
	for _, col := range project.Colunas {
		totalCards += len(col.Cards)
	}
	numCols := len(project.Colunas)
	boardProgress := 0
	if totalCards > 0 && numCols > 1 {
		weighted := 0.0
		for idx, col := range project.Colunas {
			weighted += float64(len(col.Cards)) * (float64(idx) / float64(numCols-1))
		}
		boardProgress = int((weighted / float64(totalCards)) * 100)
	}

	c.JSON(http.StatusOK, gin.H{
		"project":        project,
		"board_progress": boardProgress,
		"total_cards":    totalCards,
	})
}

func (h *KanbanHandler) UpdateProject(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	project, err := h.projectRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Projeto não encontrado"})
		return
	}

	if !h.userCanAccessProject(user, project) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Acesso negado"})
		return
	}

	var in struct {
		Titulo               string  `json:"titulo"`
		Descricao            string  `json:"descricao"`
		BoardBackgroundColor *string `json:"board_background_color"`
		BoardPattern         *string `json:"board_pattern"`
		RelatedToMaintenance *bool   `json:"related_to_maintenance"`
		RelatedToPreventive  *bool   `json:"related_to_preventive"`
		PreventivePlanID     *uint   `json:"preventive_plan_id"`
		ParticipanteIDs      []uint  `json:"participante_ids"`
		IsActive             *bool   `json:"is_active"`
		IsArchived           *bool   `json:"is_archived"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	project.Titulo = strings.TrimSpace(in.Titulo)
	if strings.TrimSpace(in.Descricao) != "" {
		d := strings.TrimSpace(in.Descricao)
		project.Descricao = &d
	} else {
		project.Descricao = nil
	}
	if in.BoardBackgroundColor != nil {
		project.BoardBackgroundColor = normalizeHexColor(*in.BoardBackgroundColor, defaultKanbanBoardBackgroundColor)
	}
	if in.BoardPattern != nil {
		project.BoardPattern = normalizeBoardPattern(*in.BoardPattern)
	}
	if in.RelatedToMaintenance != nil {
		project.RelatedToMaintenance = *in.RelatedToMaintenance
	}
	if in.RelatedToPreventive != nil {
		project.RelatedToPreventive = *in.RelatedToPreventive
	}
	if in.RelatedToPreventive != nil && !project.RelatedToPreventive {
		project.PreventivePlanID = nil
	} else if in.PreventivePlanID != nil {
		var plan models.MaintenancePlan
		if err := h.userRepo.DB().First(&plan, *in.PreventivePlanID).Error; err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Plano preventivo não encontrado"})
			return
		}
		project.PreventivePlanID = in.PreventivePlanID
	}
	if in.IsActive != nil {
		project.IsActive = *in.IsActive
	}
	if in.IsArchived != nil {
		project.IsArchived = *in.IsArchived
	}
	project.UpdatedAt = time.Now()

	if err := h.projectRepo.Update(project); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	if in.ParticipanteIDs != nil {
		participantIDs := append([]uint{project.CriadorID}, in.ParticipanteIDs...)
		_ = h.projectRepo.ReplaceParticipantes(project, uniqueUints(participantIDs))
	}

	h.notify(h.projectParticipantIDs(project), user.ID, models.NotifProjetoAdicionado,
		"Projeto atualizado",
		fmt.Sprintf("%s atualizou o projeto '%s'.", user.Nome, project.Titulo),
		&project.ID, nil)

	c.JSON(http.StatusOK, project)
}

func (h *KanbanHandler) DuplicateProject(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	project, err := h.projectRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Projeto não encontrado"})
		return
	}
	if !h.userCanAccessProject(user, project) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Acesso negado"})
		return
	}

	var in struct {
		IncluirCartoes bool `json:"incluir_cartoes"`
	}
	_ = c.ShouldBindJSON(&in)

	participantIDs := make([]uint, 0, len(project.Participantes)+1)
	participantIDs = append(participantIDs, user.ID)
	for _, participant := range project.Participantes {
		participantIDs = append(participantIDs, participant.ID)
	}

	var participants []models.User
	if err := h.userRepo.DB().Where("id IN ?", uniqueUints(participantIDs)).Find(&participants).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	duplicate := &models.KanbanProject{
		Titulo:               strings.TrimSpace(project.Titulo) + " (Cópia)",
		Descricao:            project.Descricao,
		BoardBackgroundColor: normalizeHexColor(project.BoardBackgroundColor, defaultKanbanBoardBackgroundColor),
		BoardPattern:         normalizeBoardPattern(project.BoardPattern),
		RelatedToMaintenance: project.RelatedToMaintenance,
		RelatedToPreventive:  project.RelatedToPreventive,
		PreventivePlanID:     project.PreventivePlanID,
		CriadorID:            user.ID,
		IsActive:             true,
		IsArchived:           false,
		Participantes:        participants,
	}

	if err := h.projectRepo.Create(duplicate); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	columnMap := make(map[uint]uint, len(project.Colunas))
	for idx, col := range project.Colunas {
		newCol := &models.KanbanColumn{
			ProjectID: duplicate.ID,
			Nome:      col.Nome,
			Cor:       col.Cor,
			Ordem:     idx,
			IsDefault: col.IsDefault,
		}
		if err := h.columnRepo.Create(newCol); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		columnMap[col.ID] = newCol.ID
	}

	if in.IncluirCartoes {
		for _, col := range project.Colunas {
			for _, card := range col.Cards {
				newColumnID, ok := columnMap[col.ID]
				if !ok {
					continue
				}

				duplicateCard := &models.KanbanCard{
					ProjectID:     duplicate.ID,
					ColumnID:      newColumnID,
					Titulo:        card.Titulo,
					Descricao:     card.Descricao,
					ChecklistJSON: card.ChecklistJSON,
					CriadorID:     user.ID,
					ResponsavelID: card.ResponsavelID,
					Prioridade:    card.Prioridade,
					DataEntrega:   card.DataEntrega,
					Ordem:         card.Ordem,
				}
				if err := h.cardRepo.Create(duplicateCard); err != nil {
					c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
					return
				}

				if len(card.Participantes) > 0 {
					cardParticipantIDs := make([]uint, 0, len(card.Participantes))
					for _, participant := range card.Participantes {
						cardParticipantIDs = append(cardParticipantIDs, participant.ID)
					}
					if err := h.cardRepo.ReplaceParticipantes(duplicateCard, uniqueUints(cardParticipantIDs)); err != nil {
						c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
						return
					}
				}

				if len(card.Ativos) > 0 {
					assetIDs := make([]uint, 0, len(card.Ativos))
					for _, asset := range card.Ativos {
						assetIDs = append(assetIDs, asset.ID)
					}
					if err := h.cardRepo.ReplaceAssets(duplicateCard, uniqueUints(assetIDs)); err != nil {
						c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
						return
					}
				}
			}
		}
	}

	h.notify(h.projectParticipantIDs(duplicate), user.ID, models.NotifProjetoAdicionado,
		"Projeto duplicado",
		fmt.Sprintf("%s duplicou o projeto '%s'.", user.Nome, project.Titulo),
		&duplicate.ID, nil)

	loaded, _ := h.projectRepo.GetByID(duplicate.ID)
	if loaded == nil {
		loaded = duplicate
	}
	c.JSON(http.StatusCreated, loaded)
}

func (h *KanbanHandler) ToggleProjectStatus(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	project, err := h.projectRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Projeto não encontrado"})
		return
	}
	if !h.userCanAccessProject(user, project) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Acesso negado"})
		return
	}

	var in struct {
		Acao string `json:"acao"` // archive, unarchive, deactivate, activate
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	switch in.Acao {
	case "archive":
		project.IsArchived = true
	case "unarchive":
		project.IsArchived = false
	case "deactivate":
		project.IsActive = false
	case "activate":
		project.IsActive = true
		project.IsArchived = false
	default:
		c.JSON(http.StatusBadRequest, gin.H{"error": "Ação inválida"})
		return
	}
	project.UpdatedAt = time.Now()

	if err := h.projectRepo.Update(project); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, project)
}

func (h *KanbanHandler) AddColumn(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	projectID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	project, err := h.projectRepo.GetByID(uint(projectID))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Projeto não encontrado"})
		return
	}
	if !h.userCanAccessProject(user, project) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Acesso negado"})
		return
	}

	var in struct {
		Nome string `json:"nome"`
		Cor  string `json:"cor"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if strings.TrimSpace(in.Nome) == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Nome é obrigatório"})
		return
	}

	count, _ := h.columnRepo.CountByProject(uint(projectID))
	cor := in.Cor
	if cor == "" {
		cor = "#6B7280"
	}
	col := &models.KanbanColumn{
		ProjectID: uint(projectID),
		Nome:      strings.TrimSpace(in.Nome),
		Cor:       cor,
		Ordem:     int(count),
	}
	if err := h.columnRepo.Create(col); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, col)
}

func (h *KanbanHandler) UpdateColumn(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	columnID, err := strconv.ParseUint(c.Param("columnId"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	col, err := h.columnRepo.GetByID(uint(columnID))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Coluna não encontrada"})
		return
	}

	project, err := h.projectRepo.GetByID(col.ProjectID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Projeto não encontrado"})
		return
	}
	if !h.userCanAccessProject(user, project) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Acesso negado"})
		return
	}

	var in struct {
		Nome  *string `json:"nome"`
		Cor   *string `json:"cor"`
		Ordem *int    `json:"ordem"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if in.Nome != nil {
		nome := strings.TrimSpace(*in.Nome)
		if nome == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Nome é obrigatório"})
			return
		}
		col.Nome = nome
	}

	if in.Cor != nil {
		cor := strings.TrimSpace(*in.Cor)
		if cor == "" {
			cor = "#6B7280"
		}
		col.Cor = cor
	}

	if in.Ordem != nil {
		col.Ordem = *in.Ordem
	}

	if err := h.columnRepo.Update(col); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, col)
}

// ---------- Cards ----------

func (h *KanbanHandler) CreateCard(c *gin.Context) {
	user := middleware.GetCurrentUser(c)

	var in struct {
		ProjectID       uint                         `json:"project_id"`
		ColumnID        uint                         `json:"column_id"`
		Titulo          string                       `json:"titulo"`
		Descricao       string                       `json:"descricao"`
		ChecklistItems  []kanbanChecklistItemPayload `json:"checklist_items"`
		ResponsavelID   *uint                        `json:"responsavel_id"`
		Prioridade      string                       `json:"prioridade"`
		DataEntrega     *string                      `json:"data_entrega"`
		ParticipanteIDs []uint                       `json:"participante_ids"`
		AtivoIDs        []uint                       `json:"ativo_ids"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if strings.TrimSpace(in.Titulo) == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Título é obrigatório"})
		return
	}

	project, err := h.projectRepo.GetByID(in.ProjectID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Projeto não encontrado"})
		return
	}
	if !h.userCanAccessProject(user, project) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Acesso negado"})
		return
	}

	count, _ := h.cardRepo.CountByColumn(in.ColumnID)
	prioridade := normalizeEnumValue(in.Prioridade, []string{models.CardPriorityBaixa, models.CardPriorityMedia, models.CardPriorityAlta, models.CardPriorityUrgente}, models.CardPriorityMedia)

	card := &models.KanbanCard{
		ProjectID:     in.ProjectID,
		ColumnID:      in.ColumnID,
		Titulo:        strings.TrimSpace(in.Titulo),
		CriadorID:     user.ID,
		ResponsavelID: in.ResponsavelID,
		Prioridade:    prioridade,
		Ordem:         int(count),
	}
	if strings.TrimSpace(in.Descricao) != "" {
		d := strings.TrimSpace(in.Descricao)
		card.Descricao = &d
	}
	checklistJSON, err := marshalKanbanChecklist(in.ChecklistItems)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Checklist inválido"})
		return
	}
	card.ChecklistJSON = checklistJSON
	if in.DataEntrega != nil && *in.DataEntrega != "" {
		if t, err := time.Parse("2006-01-02", *in.DataEntrega); err == nil {
			card.DataEntrega = &t
		}
	}

	if err := h.cardRepo.Create(card); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Participants and assets
	var participants []models.User
	if len(in.ParticipanteIDs) > 0 {
		_ = h.userRepo.DB().Where("id IN ?", in.ParticipanteIDs).Find(&participants).Error
		_ = h.cardRepo.ReplaceParticipantes(card, in.ParticipanteIDs)
	}
	if len(in.AtivoIDs) > 0 {
		_ = h.cardRepo.ReplaceAssets(card, in.AtivoIDs)
		h.syncKanbanAssetsMaintenance(card, in.AtivoIDs, user.ID, "")
	}

	// Notify assignees
	notifyIDs := in.ParticipanteIDs
	if card.ResponsavelID != nil {
		notifyIDs = append(notifyIDs, *card.ResponsavelID)
	}
	if len(notifyIDs) > 0 {
		h.notify(uniqueUints(notifyIDs), user.ID, models.NotifCartaoAtribuido,
			"Novo cartão no Kanban",
			fmt.Sprintf("%s criou o cartão '%s' no projeto '%s'.", user.Nome, card.Titulo, project.Titulo),
			&project.ID, &card.ID)
	}

	loaded, _ := h.cardRepo.GetByID(card.ID)
	if loaded == nil {
		loaded = card
	}
	c.JSON(http.StatusCreated, loaded)
}

func (h *KanbanHandler) GetCard(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	card, err := h.cardRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Cartão não encontrado"})
		return
	}

	project, err := h.projectRepo.GetByID(card.ProjectID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Projeto não encontrado"})
		return
	}
	if !h.userCanAccessProject(user, project) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Acesso negado"})
		return
	}

	c.JSON(http.StatusOK, card)
}

func (h *KanbanHandler) UpdateCard(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	card, err := h.cardRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Cartão não encontrado"})
		return
	}

	var in struct {
		Titulo          string                       `json:"titulo"`
		Descricao       string                       `json:"descricao"`
		ChecklistItems  []kanbanChecklistItemPayload `json:"checklist_items"`
		ColumnID        uint                         `json:"column_id"`
		ResponsavelID   *uint                        `json:"responsavel_id"`
		Prioridade      string                       `json:"prioridade"`
		DataEntrega     *string                      `json:"data_entrega"`
		ParticipanteIDs []uint                       `json:"participante_ids"`
		AtivoIDs        []uint                       `json:"ativo_ids"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	card.Titulo = strings.TrimSpace(in.Titulo)
	if strings.TrimSpace(in.Descricao) != "" {
		d := strings.TrimSpace(in.Descricao)
		card.Descricao = &d
	} else {
		card.Descricao = nil
	}
	checklistJSON, err := marshalKanbanChecklist(in.ChecklistItems)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Checklist inválido"})
		return
	}
	card.ChecklistJSON = checklistJSON
	card.ColumnID = in.ColumnID
	card.ResponsavelID = in.ResponsavelID
	card.Prioridade = normalizeEnumValue(in.Prioridade, []string{models.CardPriorityBaixa, models.CardPriorityMedia, models.CardPriorityAlta, models.CardPriorityUrgente}, models.CardPriorityMedia)
	card.DataEntrega = nil
	if in.DataEntrega != nil && *in.DataEntrega != "" {
		if t, err := time.Parse("2006-01-02", *in.DataEntrega); err == nil {
			card.DataEntrega = &t
		}
	}
	card.UpdatedAt = time.Now()

	if err := h.cardRepo.Update(card); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	_ = h.cardRepo.ReplaceParticipantes(card, in.ParticipanteIDs)
	_ = h.cardRepo.ReplaceAssets(card, in.AtivoIDs)
	if len(in.AtivoIDs) > 0 {
		h.syncKanbanAssetsMaintenance(card, in.AtivoIDs, user.ID, "")
	}

	notifyIDs := in.ParticipanteIDs
	if card.ResponsavelID != nil {
		notifyIDs = append(notifyIDs, *card.ResponsavelID)
	}
	if len(notifyIDs) > 0 {
		h.notify(uniqueUints(notifyIDs), user.ID, models.NotifCartaoAtribuido,
			"Cartão atualizado",
			fmt.Sprintf("%s atualizou o cartão '%s'.", user.Nome, card.Titulo),
			&card.ProjectID, &card.ID)
	}

	loaded, _ := h.cardRepo.GetByID(card.ID)
	if loaded == nil {
		loaded = card
	}
	c.JSON(http.StatusOK, loaded)
}

func (h *KanbanHandler) MoveCard(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	card, err := h.cardRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Cartão não encontrado"})
		return
	}

	var in struct {
		ColumnID uint   `json:"column_id"`
		Ordem    int    `json:"ordem"`
		Motivo   string `json:"motivo"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	sourceColName := "Coluna"
	if card.Column != nil {
		sourceColName = card.Column.Nome
	}

	if err := h.cardRepo.MoveCard(card.ID, in.ColumnID, in.Ordem); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	targetCol, _ := h.columnRepo.GetByID(in.ColumnID)
	targetColName := "Coluna"
	if targetCol != nil {
		targetColName = targetCol.Nome
	}

	if sourceColName != targetColName {
		_ = h.interactionRepo.Create(&models.KanbanCardInteraction{
			CardID:    card.ID,
			UsuarioID: user.ID,
			Mensagem:  fmt.Sprintf("Moveu o cartão de '%s' para '%s'.", sourceColName, targetColName),
			Tipo:      models.InteractionSistemaMove,
		})

		// Notify card assignees + project participants
		project, _ := h.projectRepo.GetByID(card.ProjectID)
		if project != nil {
			notifyIDs := h.projectParticipantIDs(project)
			h.notify(notifyIDs, user.ID, models.NotifCartaoMovimentado,
				"Cartão movido",
				fmt.Sprintf("O cartão '%s' foi movido de '%s' para '%s'.", card.Titulo, sourceColName, targetColName),
				&card.ProjectID, &card.ID)
		}
	}

	// Sync assets maintenance status if card has assets
	cardFull, _ := h.cardRepo.GetByID(card.ID)
	if cardFull != nil && len(cardFull.Ativos) > 0 {
		var assetIDs []uint
		for _, a := range cardFull.Ativos {
			assetIDs = append(assetIDs, a.ID)
		}
		h.syncKanbanAssetsMaintenance(cardFull, assetIDs, user.ID, in.Motivo)
	}

	c.JSON(http.StatusOK, gin.H{"status": "ok", "card_id": card.ID, "column_id": in.ColumnID})
}

func (h *KanbanHandler) DeleteCard(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	card, err := h.cardRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Cartão não encontrado"})
		return
	}

	// Delete physical attachments
	for _, att := range card.Anexos {
		if strings.HasPrefix(att.URL, "/uploads/") {
			_ = os.Remove(filepath.FromSlash(filepath.Clean(att.URL)))
		}
	}

	if err := h.cardRepo.Delete(card); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Cartão excluído", "project_id": card.ProjectID})
}

// ---------- Attachments ----------

func (h *KanbanHandler) UploadAttachment(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	cardID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	card, err := h.cardRepo.GetByID(uint(cardID))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Cartão não encontrado"})
		return
	}

	var file *multipart.FileHeader
	var att *models.KanbanAttachment

	// File upload
	if f, err := c.FormFile("arquivo"); err == nil {
		file = f
	} else if link := c.PostForm("link"); link != "" {
		// Link type attachment
		att = &models.KanbanAttachment{
			CardID: uint(cardID),
			Nome:   c.PostForm("nome"),
			Tipo:   "link",
			URL:    link,
		}
	}

	if file != nil {
		if err := os.MkdirAll(kanbanUploadDir, 0o755); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		ext := filepath.Ext(file.Filename)
		filename := fmt.Sprintf("card_%d_%d_%s%s", cardID, time.Now().Unix(), uuid.New().String()[:8], ext)
		filePath := filepath.Join(kanbanUploadDir, filename)

		f, err := file.Open()
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		defer f.Close()
		data := make([]byte, file.Size)
		if _, err := f.Read(data); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		if err := os.WriteFile(filePath, data, 0o644); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		tipo := "arquivo"
		switch strings.ToLower(ext) {
		case ".png", ".jpg", ".jpeg", ".gif", ".webp":
			tipo = "imagem"
		}
		att = &models.KanbanAttachment{
			CardID: uint(cardID),
			Nome:   file.Filename,
			Tipo:   tipo,
			URL:    "/" + filepath.ToSlash(filePath),
		}
	}

	if att == nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Envie um arquivo ou um link"})
		return
	}

	if err := h.attachmentRepo.Create(att); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	_ = h.interactionRepo.Create(&models.KanbanCardInteraction{
		CardID:    uint(cardID),
		UsuarioID: user.ID,
		Mensagem:  fmt.Sprintf("Adicionou o anexo '%s'.", att.Nome),
		Tipo:      models.InteractionSistemaAnexo,
	})

	project, _ := h.projectRepo.GetByID(card.ProjectID)
	if project != nil {
		h.notify(h.projectParticipantIDs(project), user.ID, models.NotifAnexoAdicionado,
			"Anexo adicionado",
			fmt.Sprintf("%s adicionou o anexo '%s' ao cartão '%s'.", user.Nome, att.Nome, card.Titulo),
			&card.ProjectID, &card.ID)
	}

	c.JSON(http.StatusCreated, att)
}

func (h *KanbanHandler) DeleteAttachment(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("attachmentId"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	att, err := h.attachmentRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Anexo não encontrado"})
		return
	}

	if strings.HasPrefix(att.URL, "/uploads/") {
		_ = os.Remove(filepath.FromSlash(filepath.Clean(att.URL)))
	}

	if err := h.attachmentRepo.Delete(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	_ = h.interactionRepo.Create(&models.KanbanCardInteraction{
		CardID:    att.CardID,
		UsuarioID: user.ID,
		Mensagem:  fmt.Sprintf("Removeu o anexo '%s'.", att.Nome),
		Tipo:      models.InteractionSistemaAnexo,
	})

	c.JSON(http.StatusOK, gin.H{"message": "Anexo excluído"})
}

// ---------- Comments ----------

func (h *KanbanHandler) AddCardComment(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	cardID, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	card, err := h.cardRepo.GetByID(uint(cardID))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Cartão não encontrado"})
		return
	}

	var in struct {
		Mensagem string `json:"mensagem"`
	}
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if strings.TrimSpace(in.Mensagem) == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Mensagem é obrigatória"})
		return
	}

	interaction := &models.KanbanCardInteraction{
		CardID:    uint(cardID),
		UsuarioID: user.ID,
		Mensagem:  strings.TrimSpace(in.Mensagem),
		Tipo:      models.InteractionComentario,
	}
	if err := h.interactionRepo.Create(interaction); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Load user name for response
	var author models.User
	_ = h.userRepo.DB().First(&author, user.ID).Error
	interaction.Usuario = &author

	project, _ := h.projectRepo.GetByID(card.ProjectID)
	if project != nil {
		h.notify(h.projectParticipantIDs(project), user.ID, models.NotifCartaoAtribuido,
			"Novo comentário",
			fmt.Sprintf("%s comentou no cartão '%s'.", user.Nome, card.Titulo),
			&card.ProjectID, &card.ID)
	}

	c.JSON(http.StatusCreated, interaction)
}

// ---------- Notifications ----------

func (h *KanbanHandler) UnreadCount(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	count, err := h.notifRepo.UnreadCount(user.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"unread_count": count})
}

func (h *KanbanHandler) ListNotifications(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	notifs, err := h.notifRepo.ListByUser(user.ID, 15)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, notifs)
}

func (h *KanbanHandler) MarkNotificationRead(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("notifId"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}
	_ = h.notifRepo.MarkRead(uint(id), user.ID)
	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

func (h *KanbanHandler) MarkAllNotificationsRead(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	if err := h.notifRepo.MarkAllRead(user.ID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

// ---------- SSE ----------

func (h *KanbanHandler) SSEStream(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	client := h.broker.Subscribe(user.ID)
	defer h.broker.Unsubscribe(client)

	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")
	c.Header("X-Accel-Buffering", "no")

	// Initial event
	c.SSEvent("connected", gin.H{"user_id": user.ID})
	c.Writer.Flush()

	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case event := <-client.ch:
			c.SSEvent(event.Type, event.Payload)
			c.Writer.Flush()
		case <-ticker.C:
			c.SSEvent("ping", gin.H{"time": time.Now().Unix()})
			c.Writer.Flush()
		case <-c.Request.Context().Done():
			return
		}
	}
}

func uniqueUints(ids []uint) []uint {
	seen := map[uint]bool{}
	result := make([]uint, 0, len(ids))
	for _, id := range ids {
		if !seen[id] {
			seen[id] = true
			result = append(result, id)
		}
	}
	return result
}

func normalizeHexColor(input string, fallback string) string {
	color := strings.ToUpper(strings.TrimSpace(input))
	if len(color) != 7 || !strings.HasPrefix(color, "#") {
		return fallback
	}
	for _, ch := range color[1:] {
		if !strings.ContainsRune("0123456789ABCDEF", ch) {
			return fallback
		}
	}
	return color
}

func normalizeBoardPattern(input string) string {
	switch strings.ToLower(strings.TrimSpace(input)) {
	case "glow", "grid", "dots", "clean":
		return strings.ToLower(strings.TrimSpace(input))
	default:
		return defaultKanbanBoardPattern
	}
}

type kanbanChecklistItemPayload struct {
	ID        string `json:"id"`
	Titulo    string `json:"titulo"`
	Concluido bool   `json:"concluido"`
}

func sanitizeKanbanChecklist(items []kanbanChecklistItemPayload) []kanbanChecklistItemPayload {
	sanitized := make([]kanbanChecklistItemPayload, 0, len(items))
	for index, item := range items {
		titulo := strings.TrimSpace(item.Titulo)
		if titulo == "" {
			continue
		}
		itemID := strings.TrimSpace(item.ID)
		if itemID == "" {
			itemID = fmt.Sprintf("item-%d", index+1)
		}
		sanitized = append(sanitized, kanbanChecklistItemPayload{
			ID:        itemID,
			Titulo:    titulo,
			Concluido: item.Concluido,
		})
	}
	return sanitized
}

func marshalKanbanChecklist(items []kanbanChecklistItemPayload) (*string, error) {
	sanitized := sanitizeKanbanChecklist(items)
	if len(sanitized) == 0 {
		return nil, nil
	}
	payload, err := json.Marshal(sanitized)
	if err != nil {
		return nil, err
	}
	value := string(payload)
	return &value, nil
}

func (h *KanbanHandler) syncKanbanAssetsMaintenance(card *models.KanbanCard, assetIDs []uint, userID uint, motivo string) {
	if len(assetIDs) == 0 {
		return
	}
	db := h.userRepo.DB()

	// Check column or project name to see if it's maintenance/workshop related
	var col models.KanbanColumn
	var proj models.KanbanProject
	_ = db.First(&col, card.ColumnID).Error
	_ = db.First(&proj, card.ProjectID).Error

	colName := strings.ToLower(col.Nome)
	projName := strings.ToLower(proj.Titulo)

	isOficinaOrMaintenance := proj.RelatedToMaintenance ||
		strings.Contains(colName, "oficina") ||
		strings.Contains(colName, "manuten") ||
		strings.Contains(colName, "reparo") ||
		strings.Contains(projName, "oficina") ||
		strings.Contains(projName, "manuten")

	isConcluido := strings.Contains(colName, "conclu") || strings.Contains(colName, "pronto") || strings.Contains(colName, "finaliz") || strings.Contains(colName, "entregue")

	for _, assetID := range assetIDs {
		var asset models.Asset
		if err := db.First(&asset, assetID).Error; err != nil {
			continue
		}

		if isConcluido {
			// Mark asset as available and conclude maintenance records
			db.Model(&asset).Update("status", models.AssetStatusDisponivel)
			var now = time.Now()
			db.Model(&models.Manutencao{}).
				Where("asset_id = ? AND status = ?", assetID, models.StatusManutencaoEmAndamento).
				Updates(map[string]interface{}{
					"status":         models.StatusManutencaoConcluida,
					"data_conclusao": &now,
				})
			// Also update linked SolicitacaoManutencao
			db.Model(&models.SolicitacaoManutencao{}).
				Where("asset_id = ? AND status IN ?", assetID, []string{
					string(models.StatusMaintAceita),
					string(models.StatusMaintEmAndamento),
				}).
				Updates(map[string]interface{}{
					"status":                 models.StatusMaintAguardandoEntrega,
					"data_conclusao_tecnico": &now,
				})
		} else if isOficinaOrMaintenance {
			// Update asset status to Manutenção
			if asset.Status != models.AssetStatusManutencao {
				db.Model(&asset).Updates(map[string]interface{}{
					"status":      models.AssetStatusManutencao,
					"prev_status": string(asset.Status),
				})
			}

			// Check if an active SolicitacaoManutencao already exists for this asset
			var solCount int64
			db.Model(&models.SolicitacaoManutencao{}).
				Where("asset_id = ? AND status IN ?", assetID, []string{
					string(models.StatusMaintPendente),
					string(models.StatusMaintAceita),
					string(models.StatusMaintEmAndamento),
				}).
				Count(&solCount)

			if solCount == 0 {
				maintMotivo := motivo
				if maintMotivo == "" {
					maintMotivo = fmt.Sprintf("Adicionado à Oficina Kanban: %s", card.Titulo)
				}

				// Create Manutencao record
				maint := models.Manutencao{
					AssetID:       assetID,
					ResponsavelID: card.ResponsavelID,
					Motivo:        maintMotivo,
					Tipo:          models.TipoManutencaoCorretiva,
					DataEntrada:   time.Now(),
					Status:        models.StatusManutencaoEmAndamento,
				}
				if err := db.Create(&maint).Error; err != nil {
					continue
				}

				// Create SolicitacaoManutencao linked to the Manutencao
				now := time.Now()
				responsavelID := card.ResponsavelID
				if responsavelID == nil {
					responsavelID = &userID
				}
				solicitacao := models.SolicitacaoManutencao{
					SolicitanteID:   &userID,
					AssetID:         assetID,
					Descricao:       maintMotivo,
					Prioridade:      models.PrioridadeSolicitacaoMedia,
					DataSolicitacao: now,
					DataResposta:    &now,
					Status:          models.StatusMaintAceita,
					ResponsavelID:   responsavelID,
					ManutencaoID:    &maint.ID,
				}
				_ = db.Create(&solicitacao).Error
			}
		}
	}
}
