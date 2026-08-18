package handler

import (
	"net/http"
	"strconv"

	"github.com/assettrack/backend/internal/repository"
	"github.com/gin-gonic/gin"
)

type EmailLogHandler struct {
	repo repository.EmailLogRepository
}

func NewEmailLogHandler(repo repository.EmailLogRepository) *EmailLogHandler {
	return &EmailLogHandler{repo: repo}
}

func (h *EmailLogHandler) List(c *gin.Context) {
	limitStr := c.DefaultQuery("limit", "20")
	offsetStr := c.DefaultQuery("offset", "0")

	limit, err := strconv.Atoi(limitStr)
	if err != nil {
		limit = 20
	}
	offset, err := strconv.Atoi(offsetStr)
	if err != nil {
		offset = 0
	}

	logs, total, err := h.repo.List(c.Request.Context(), limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch email logs"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data":  logs,
		"total": total,
	})
}
