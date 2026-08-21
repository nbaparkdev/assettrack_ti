package handler

import (
	"fmt"
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
)

type ServiceDeskHandler struct {
	repo *repository.ServiceDeskRepository
}

func NewServiceDeskHandler(repo *repository.ServiceDeskRepository) *ServiceDeskHandler {
	return &ServiceDeskHandler{repo: repo}
}

func isStaff(role string) bool {
	return role == models.RoleAdmin || role == models.RoleGerente || role == models.RoleGerenteInfra || role == models.RoleTecnico
}

// Categories
func (h *ServiceDeskHandler) ListCategories(c *gin.Context) {
	cats, err := h.repo.ListCategories()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, cats)
}

func (h *ServiceDeskHandler) CreateCategory(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	if !isStaff(user.Role) {
		c.JSON(http.StatusForbidden, gin.H{"detail": "Permissão negada"})
		return
	}

	var cat models.ServiceCategory
	if err := c.ShouldBindJSON(&cat); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"detail": err.Error()})
		return
	}

	if err := h.repo.CreateCategory(&cat); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"detail": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, cat)
}

// Definitions
func (h *ServiceDeskHandler) ListDefinitions(c *gin.Context) {
	defs, err := h.repo.ListDefinitions()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, defs)
}

func (h *ServiceDeskHandler) CreateDefinition(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	if !isStaff(user.Role) {
		c.JSON(http.StatusForbidden, gin.H{"detail": "Permissão negada"})
		return
	}

	var def models.ServiceDefinition
	if err := c.ShouldBindJSON(&def); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"detail": err.Error()})
		return
	}

	if err := h.repo.CreateDefinition(&def); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"detail": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, def)
}

// Tickets
func (h *ServiceDeskHandler) ListTickets(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	skip, _ := strconv.Atoi(c.DefaultQuery("skip", "0"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))

	var filterUser *uint
	if !isStaff(user.Role) {
		filterUser = &user.ID
	}

	tickets, err := h.repo.ListTickets(filterUser, skip, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, tickets)
}

func (h *ServiceDeskHandler) GetTicketByID(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	ticket, err := h.repo.GetTicketByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Chamado não encontrado"})
		return
	}

	// Permission: standard users can only view their own tickets
	if !isStaff(user.Role) && ticket.SolicitanteID != user.ID {
		c.JSON(http.StatusForbidden, gin.H{"detail": "Permissão negada"})
		return
	}

	c.JSON(http.StatusOK, ticket)
}

func (h *ServiceDeskHandler) CreateTicket(c *gin.Context) {
	user := middleware.GetCurrentUser(c)

	var ticket models.ServiceTicket
	if err := c.ShouldBindJSON(&ticket); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"detail": err.Error()})
		return
	}

	ticket.SolicitanteID = user.ID
	ticket.Status = models.ServiceStatusAberto

	if err := h.repo.CreateTicket(&ticket); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"detail": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, ticket)
}

func (h *ServiceDeskHandler) UpdateTicket(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	ticket, err := h.repo.GetTicketByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Chamado não encontrado"})
		return
	}

	// Permission: only staff or the ticket owner (under specific fields) can update
	isOwner := ticket.SolicitanteID == user.ID
	if !isStaff(user.Role) && !isOwner {
		c.JSON(http.StatusForbidden, gin.H{"detail": "Permissão negada"})
		return
	}

	var req struct {
		Status             *models.ServiceStatus   `json:"status"`
		Prioridade         *models.ServicePriority `json:"prioridade"`
		TecnicoID          *uint                   `json:"tecnico_id"`
		ResponsavelID      *uint                   `json:"responsavel_id"`
		Solucao            *string                 `json:"solucao"`
		NotaResolucao      *string                 `json:"nota_resolucao"`
		FeedbackUsuario    *string                 `json:"feedback_usuario"`
		ComentarioFeedback *string                 `json:"comentario_feedback"`
		Avaliacao          *int                    `json:"avaliacao"`
		NotaFeedback       *int                    `json:"nota_feedback"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"detail": err.Error()})
		return
	}

	// Normalize technician ID
	if req.TecnicoID == nil && req.ResponsavelID != nil {
		req.TecnicoID = req.ResponsavelID
	}
	// Normalize solution note
	if req.Solucao == nil && req.NotaResolucao != nil {
		req.Solucao = req.NotaResolucao
	}
	// Normalize feedback text
	if req.FeedbackUsuario == nil && req.ComentarioFeedback != nil {
		req.FeedbackUsuario = req.ComentarioFeedback
	}
	// Normalize rating
	if req.Avaliacao == nil && req.NotaFeedback != nil {
		req.Avaliacao = req.NotaFeedback
	}

	// Non-staff can update feedback/avaliacao on tickets they own
	if !isStaff(user.Role) {
		if req.Prioridade != nil || req.TecnicoID != nil || req.Solucao != nil {
			c.JSON(http.StatusForbidden, gin.H{"detail": "Apenas técnicos e gerentes podem modificar metadados do chamado"})
			return
		}
		if req.Status != nil {
			stStr := strings.ToLower(string(*req.Status))
			if stStr == "fechado" || stStr == "resolvido" {
				ticket.Status = models.ServiceStatusFechado
				now := time.Now()
				ticket.DataFechamento = &now
			} else {
				c.JSON(http.StatusForbidden, gin.H{"detail": "Usuários comuns só podem encerrar o chamado ao avaliar"})
				return
			}
		}
		if req.FeedbackUsuario != nil {
			ticket.FeedbackUsuario = req.FeedbackUsuario
		}
		if req.Avaliacao != nil {
			ticket.Avaliacao = req.Avaliacao
		}
	} else {
		// Staff updates
		if req.Status != nil {
			stStr := strings.ToLower(string(*req.Status))
			if stStr == "fechado" {
				ticket.Status = models.ServiceStatusFechado
			} else if stStr == "resolvido" {
				ticket.Status = models.ServiceStatusResolvido
			} else if stStr == "em_andamento" || stStr == "em andamento" || stStr == "em_atendimento" {
				ticket.Status = models.ServiceStatusEmAtendimento
			} else if stStr == "cancelado" {
				ticket.Status = models.ServiceStatusCancelado
			} else {
				ticket.Status = *req.Status
			}

			if ticket.Status == models.ServiceStatusResolvido || ticket.Status == models.ServiceStatusFechado || ticket.Status == models.ServiceStatusCancelado {
				now := time.Now()
				ticket.DataFechamento = &now
			}
		}
		if req.Prioridade != nil {
			ticket.Prioridade = *req.Prioridade
		}
		if req.TecnicoID != nil {
			ticket.TecnicoID = req.TecnicoID
		}
		if req.Solucao != nil {
			ticket.Solucao = req.Solucao
		}
		if req.FeedbackUsuario != nil {
			ticket.FeedbackUsuario = req.FeedbackUsuario
		}
		if req.Avaliacao != nil {
			ticket.Avaliacao = req.Avaliacao
		}
	}

	if err := h.repo.UpdateTicket(ticket); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"detail": err.Error()})
		return
	}
	c.JSON(http.StatusOK, ticket)
}

// Interactions
func (h *ServiceDeskHandler) CreateInteraction(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	id, err := strconv.ParseUint(c.Param("id"), 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	ticket, err := h.repo.GetTicketByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Chamado não encontrado"})
		return
	}

	if !isStaff(user.Role) && ticket.SolicitanteID != user.ID {
		c.JSON(http.StatusForbidden, gin.H{"detail": "Permissão negada"})
		return
	}

	var inter models.ServiceTicketInteraction
	if err := c.ShouldBindJSON(&inter); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"detail": err.Error()})
		return
	}

	inter.TicketID = ticket.ID
	inter.UsuarioID = user.ID
	if inter.Tipo == "" {
		inter.Tipo = "Comentário"
	}

	if err := h.repo.CreateInteraction(&inter); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"detail": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, inter)
}

func (h *ServiceDeskHandler) UploadInteractionAttachment(c *gin.Context) {
	fileHeader, err := c.FormFile("arquivo")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Arquivo não fornecido"})
		return
	}

	ext := strings.ToLower(filepath.Ext(fileHeader.Filename))
	validExts := map[string]bool{
		".png": true, ".jpg": true, ".jpeg": true, ".gif": true, ".webp": true,
		".pdf": true, ".doc": true, ".docx": true, ".xls": true, ".xlsx": true,
		".txt": true, ".zip": true, ".rar": true,
	}
	if !validExts[ext] {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Extensão de arquivo não permitida"})
		return
	}

	os.MkdirAll("uploads/servicos", os.ModePerm)
	filename := fmt.Sprintf("ticket_%s_%d%s", c.Param("id"), time.Now().UnixNano(), ext)
	dst := filepath.Join("uploads", "servicos", filename)

	if err := c.SaveUploadedFile(fileHeader, dst); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Falha ao salvar anexo"})
		return
	}

	publicPath := fmt.Sprintf("/uploads/servicos/%s", filename)
	c.JSON(http.StatusOK, gin.H{"url": publicPath})
}

func (h *ServiceDeskHandler) UploadTicketAttachment(c *gin.Context) {
	fileHeader, err := c.FormFile("arquivo")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Arquivo não fornecido"})
		return
	}

	ext := strings.ToLower(filepath.Ext(fileHeader.Filename))
	validExts := map[string]bool{
		".png": true, ".jpg": true, ".jpeg": true, ".gif": true, ".webp": true,
		".pdf": true, ".doc": true, ".docx": true, ".xls": true, ".xlsx": true,
		".txt": true, ".zip": true, ".rar": true,
	}
	if !validExts[ext] {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Extensão de arquivo não permitida"})
		return
	}

	os.MkdirAll("uploads/servicos", os.ModePerm)
	filename := fmt.Sprintf("ticket_new_%d%s", time.Now().UnixNano(), ext)
	dst := filepath.Join("uploads", "servicos", filename)

	if err := c.SaveUploadedFile(fileHeader, dst); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Falha ao salvar anexo"})
		return
	}

	publicPath := fmt.Sprintf("/uploads/servicos/%s", filename)
	c.JSON(http.StatusOK, gin.H{"url": publicPath})
}
