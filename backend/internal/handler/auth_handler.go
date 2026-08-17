package handler

import (
	"net/http"

	"github.com/assettrack/backend/internal/dto"
	"github.com/assettrack/backend/internal/middleware"
	"github.com/assettrack/backend/internal/service"
	apperr "github.com/assettrack/backend/pkg/errors"
	"github.com/gin-gonic/gin"
)

type AuthHandler struct {
	authSvc *service.AuthService
}

func NewAuthHandler(authSvc *service.AuthService) *AuthHandler {
	return &AuthHandler{authSvc: authSvc}
}

// Login POST /api/v1/auth/login
func (h *AuthHandler) Login(c *gin.Context) {
	var req dto.LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"detail": err.Error()})
		return
	}

	resp, err := h.authSvc.Login(req)
	if err != nil {
		if appErr, ok := err.(*apperr.AppError); ok {
			c.JSON(appErr.StatusCode, gin.H{"detail": appErr.Detail})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"detail": "Internal error"})
		return
	}

	c.JSON(http.StatusOK, resp)
}

// Register POST /api/v1/auth/register
func (h *AuthHandler) Register(c *gin.Context) {
	var req dto.UserCreateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"detail": err.Error()})
		return
	}

	user, err := h.authSvc.Register(req)
	if err != nil {
		if appErr, ok := err.(*apperr.AppError); ok {
			c.JSON(appErr.StatusCode, gin.H{"detail": appErr.Detail})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"detail": "Internal error"})
		return
	}

	c.JSON(http.StatusOK, toUserResponse(user))
}

// Me GET /api/v1/auth/me
func (h *AuthHandler) Me(c *gin.Context) {
	user := middleware.GetCurrentUser(c)
	if user == nil {
		c.JSON(http.StatusUnauthorized, gin.H{"detail": "Not authenticated"})
		return
	}
	c.JSON(http.StatusOK, toUserResponse(user))
}
