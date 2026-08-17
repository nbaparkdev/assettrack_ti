package handler

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/repository"
	"github.com/assettrack/backend/internal/service"
	"github.com/gin-gonic/gin"
)

type WebhookHandler struct {
	repo       *repository.WebhookRepository
	dispatcher *service.WebhookDispatcher
}

func NewWebhookHandler(repo *repository.WebhookRepository, dispatcher *service.WebhookDispatcher) *WebhookHandler {
	return &WebhookHandler{
		repo:       repo,
		dispatcher: dispatcher,
	}
}

func (h *WebhookHandler) List(c *gin.Context) {
	webhooks, err := h.repo.List()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao listar webhooks"})
		return
	}
	c.JSON(http.StatusOK, webhooks)
}

func (h *WebhookHandler) GetByID(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	w, err := h.repo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Webhook não encontrado"})
		return
	}
	c.JSON(http.StatusOK, w)
}

type webhookInput struct {
	Nome              string   `json:"nome" binding:"required"`
	URL               string   `json:"url" binding:"required"`
	IsActive          *bool    `json:"is_active"`
	SecretKey         *string  `json:"secret_key"`
	EventosPermitidos []string `json:"eventos_permitidos"`
}

func (h *WebhookHandler) Create(c *gin.Context) {
	var in webhookInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Dados inválidos: " + err.Error()})
		return
	}

	eventosBytes, _ := json.Marshal(in.EventosPermitidos)

	w := &models.Webhook{
		Nome:              in.Nome,
		URL:               in.URL,
		EventosPermitidos: string(eventosBytes),
		SecretKey:         in.SecretKey,
	}
	if in.IsActive != nil {
		w.IsActive = *in.IsActive
	} else {
		w.IsActive = true
	}

	if err := h.repo.Create(w); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao criar webhook"})
		return
	}

	c.JSON(http.StatusCreated, w)
}

func (h *WebhookHandler) Update(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	w, err := h.repo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Webhook não encontrado"})
		return
	}

	var in webhookInput
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Dados inválidos: " + err.Error()})
		return
	}

	w.Nome = in.Nome
	w.URL = in.URL
	w.SecretKey = in.SecretKey
	if in.IsActive != nil {
		w.IsActive = *in.IsActive
	}
	
	eventosBytes, _ := json.Marshal(in.EventosPermitidos)
	w.EventosPermitidos = string(eventosBytes)

	if err := h.repo.Update(w); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao atualizar webhook"})
		return
	}

	c.JSON(http.StatusOK, w)
}

func (h *WebhookHandler) Delete(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	if err := h.repo.Delete(uint(id)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao excluir webhook"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Webhook excluído com sucesso"})
}

func (h *WebhookHandler) Test(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	w, err := h.repo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Webhook não encontrado"})
		return
	}

	sucesso, msg := h.dispatcher.TestWebhook(*w)
	c.JSON(http.StatusOK, gin.H{
		"sucesso": sucesso,
		"message": msg,
	})
}

func (h *WebhookHandler) Logs(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "ID inválido"})
		return
	}

	logs, err := h.repo.GetLogs(uint(id), 100)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao buscar logs do webhook"})
		return
	}

	c.JSON(http.StatusOK, logs)
}
