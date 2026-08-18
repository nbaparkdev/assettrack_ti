package handler

import (
	"net/http"

	"github.com/assettrack/backend/internal/repository"
	"github.com/gin-gonic/gin"
)

type SettingsHandler struct {
	settingsRepo repository.SystemSettingsRepository
}

func NewSettingsHandler(settingsRepo repository.SystemSettingsRepository) *SettingsHandler {
	return &SettingsHandler{settingsRepo: settingsRepo}
}

func (h *SettingsHandler) GetAll(c *gin.Context) {
	settings, err := h.settingsRepo.GetAllSettings(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch settings"})
		return
	}

	// Format as a map for easier frontend consumption
	result := make(map[string]interface{})
	for _, s := range settings {
		result[s.SettingKey] = s.SettingValue
	}

	c.JSON(http.StatusOK, result)
}

func (h *SettingsHandler) UpdateMany(c *gin.Context) {
	var body map[string]string
	if err := c.ShouldBindJSON(&body); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	for k, v := range body {
		err := h.settingsRepo.SetSetting(c.Request.Context(), k, v, nil)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update setting: " + k})
			return
		}
	}

	c.JSON(http.StatusOK, gin.H{"message": "Settings updated successfully"})
}
