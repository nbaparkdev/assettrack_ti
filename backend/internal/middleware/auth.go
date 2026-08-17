package middleware

import (
	"net/http"
	"strings"

	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/repository"
	"github.com/assettrack/backend/internal/service"
	"github.com/gin-gonic/gin"
)

const (
	ContextUserKey = "current_user"
)

// AuthMiddleware validates JWT and injects user into context
func AuthMiddleware(authSvc *service.AuthService, userRepo *repository.UserRepository) gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
				"detail": "Could not validate credentials",
			})
			return
		}

		parts := strings.SplitN(authHeader, " ", 2)
		if len(parts) != 2 || strings.ToLower(parts[0]) != "bearer" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
				"detail": "Could not validate credentials",
			})
			return
		}

		email, _, err := authSvc.ValidateToken(parts[1])
		if err != nil || email == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
				"detail": "Could not validate credentials",
			})
			return
		}

		user, err := userRepo.GetByEmail(email)
		if err != nil {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
				"detail": "Could not validate credentials",
			})
			return
		}

		c.Set(ContextUserKey, user)
		c.Next()
	}
}

// RequireActive ensures user is active
func RequireActive() gin.HandlerFunc {
	return func(c *gin.Context) {
		user := GetCurrentUser(c)
		if user == nil || !user.IsActive {
			c.AbortWithStatusJSON(http.StatusBadRequest, gin.H{"detail": "Inactive user"})
			return
		}
		c.Next()
	}
}

// RequireAdmin ensures user is admin
func RequireAdmin() gin.HandlerFunc {
	return func(c *gin.Context) {
		user := GetCurrentUser(c)
		if user == nil || !user.IsAdmin() {
			c.AbortWithStatusJSON(http.StatusForbidden, gin.H{
				"detail": "The user doesn't have enough privileges",
			})
			return
		}
		c.Next()
	}
}

// RequireManagerOrAbove ensures user has elevated permissions
func RequireManagerOrAbove() gin.HandlerFunc {
	return func(c *gin.Context) {
		user := GetCurrentUser(c)
		if user == nil || !user.IsManagerOrAbove() {
			c.AbortWithStatusJSON(http.StatusForbidden, gin.H{
				"detail": "The user doesn't have enough privileges",
			})
			return
		}
		c.Next()
	}
}

// GetCurrentUser extracts user from gin context
func GetCurrentUser(c *gin.Context) *models.User {
	val, exists := c.Get(ContextUserKey)
	if !exists {
		return nil
	}
	user, ok := val.(*models.User)
	if !ok {
		return nil
	}
	return user
}
