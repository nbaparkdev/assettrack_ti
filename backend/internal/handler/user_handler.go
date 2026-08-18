package handler

import (
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/assettrack/backend/internal/dto"
	"github.com/assettrack/backend/internal/middleware"
	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/repository"
	"github.com/assettrack/backend/internal/service"
	"github.com/gin-gonic/gin"
	"golang.org/x/crypto/bcrypt"
)

type UserHandler struct {
	userRepo *repository.UserRepository
	authSvc  *service.AuthService
}

func NewUserHandler(userRepo *repository.UserRepository, authSvc *service.AuthService) *UserHandler {
	return &UserHandler{userRepo: userRepo, authSvc: authSvc}
}

// List GET /api/v1/users
func (h *UserHandler) List(c *gin.Context) {
	skip, _ := strconv.Atoi(c.DefaultQuery("skip", "0"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))

	users, err := h.userRepo.GetMulti(skip, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"detail": "Failed to fetch users"})
		return
	}

	result := make([]dto.UserResponse, len(users))
	for i, u := range users {
		result[i] = *toUserResponse(&u)
	}
	c.JSON(http.StatusOK, result)
}

// Create POST /api/v1/users
func (h *UserHandler) Create(c *gin.Context) {
	var req dto.UserCreateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"detail": err.Error()})
		return
	}

	if h.userRepo.EmailExists(req.Email) {
		c.JSON(http.StatusBadRequest, gin.H{"detail": "The user with this email already exists in the system."})
		return
	}

	hash, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"detail": "Failed to hash password"})
		return
	}

	role := req.Role
	if role == "" {
		role = models.RoleUsuario
	}

	user := &models.User{
		Email:          req.Email,
		HashedPassword: string(hash),
		Nome:           req.Nome,
		Role:           role,
		IsActive:       req.IsActive,
		DepartamentoID: req.DepartamentoID,
	}
	if req.Matricula != "" {
		user.Matricula = &req.Matricula
	}
	if req.Cargo != "" {
		user.Cargo = &req.Cargo
	}

	if err := h.userRepo.Create(user); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"detail": "Failed to create user"})
		return
	}

	created, _ := h.userRepo.GetByID(user.ID)
	c.JSON(http.StatusOK, toUserResponse(created))
}

// GetByID GET /api/v1/users/:id
func (h *UserHandler) GetByID(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"detail": "Invalid user ID"})
		return
	}

	user, err := h.userRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"detail": "User not found"})
		return
	}

	c.JSON(http.StatusOK, toUserResponse(user))
}

// Update PUT /api/v1/users/:id
func (h *UserHandler) Update(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"detail": "Invalid user ID"})
		return
	}

	user, err := h.userRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"detail": "User not found"})
		return
	}

	var req dto.UserUpdateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"detail": err.Error()})
		return
	}

	if req.Email != nil {
		user.Email = *req.Email
	}
	if req.Nome != nil {
		user.Nome = *req.Nome
	}
	if req.Matricula != nil {
		user.Matricula = req.Matricula
	}
	if req.Cargo != nil {
		user.Cargo = req.Cargo
	}
	if req.Role != nil {
		user.Role = *req.Role
	}
	if req.IsActive != nil {
		user.IsActive = *req.IsActive
	}
	if req.DepartamentoID != nil {
		user.DepartamentoID = req.DepartamentoID
	}
	if req.Password != nil {
		hash, err := bcrypt.GenerateFromPassword([]byte(*req.Password), bcrypt.DefaultCost)
		if err == nil {
			user.HashedPassword = string(hash)
		}
	}

	if err := h.userRepo.Update(user); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"detail": "Failed to update user"})
		return
	}

	updated, _ := h.userRepo.GetByID(user.ID)
	c.JSON(http.StatusOK, toUserResponse(updated))
}

// Delete DELETE /api/v1/users/:id
func (h *UserHandler) Delete(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"detail": "Invalid user ID"})
		return
	}

	activeUser := middleware.GetCurrentUser(c)
	if activeUser == nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}

	if activeUser.ID == uint(id) {
		c.JSON(http.StatusBadRequest, gin.H{"detail": "Você não pode excluir a si mesmo"})
		return
	}

	user, err := h.userRepo.GetByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"detail": "Usuário não encontrado"})
		return
	}

	if err := h.userRepo.Delete(user.ID); err != nil {
		if strings.Contains(err.Error(), "foreign key constraint") || strings.Contains(err.Error(), "violates foreign key") || strings.Contains(err.Error(), "a foreign key constraint fails") || strings.Contains(err.Error(), "SQLSTATE 23503") {
			c.JSON(http.StatusBadRequest, gin.H{"detail": "Não é possível excluir este usuário pois ele possui registros vinculados (como Centro de Custo, Ativos ou Chamados)."})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"detail": "Falha ao excluir usuário"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"detail": "Usuário excluído com sucesso"})
}

// UpdateProfile PUT /api/v1/profile
func (h *UserHandler) UpdateProfile(c *gin.Context) {
	activeUser := middleware.GetCurrentUser(c)
	if activeUser == nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}

	var req dto.UserUpdateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"detail": err.Error()})
		return
	}

	user, err := h.userRepo.GetByID(activeUser.ID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"detail": "User not found"})
		return
	}

	if req.Email != nil { user.Email = *req.Email }
	if req.Nome != nil { user.Nome = *req.Nome }
	if req.Matricula != nil { user.Matricula = req.Matricula }
	
	if err := h.userRepo.Update(user); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"detail": "Failed to update profile"})
		return
	}
	c.JSON(http.StatusOK, toUserResponse(user))
}

// UploadAvatar POST /api/v1/profile/avatar
func (h *UserHandler) UploadAvatar(c *gin.Context) {
	activeUser := middleware.GetCurrentUser(c)
	if activeUser == nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}

	fileHeader, err := c.FormFile("avatar")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Avatar file not provided"})
		return
	}

	ext := strings.ToLower(filepath.Ext(fileHeader.Filename))
	if ext != ".jpg" && ext != ".jpeg" && ext != ".png" && ext != ".webp" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid image format"})
		return
	}

	os.MkdirAll("uploads/avatars", os.ModePerm)
	filename := fmt.Sprintf("avatar_%d_%d%s", activeUser.ID, time.Now().Unix(), ext)
	dst := filepath.Join("uploads", "avatars", filename)

	if err := c.SaveUploadedFile(fileHeader, dst); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save avatar"})
		return
	}

	publicPath := fmt.Sprintf("/uploads/avatars/%s", filename)
	
	user, _ := h.userRepo.GetByID(activeUser.ID)
	user.AvatarURL = &publicPath
	h.userRepo.Update(user)

	c.JSON(http.StatusOK, gin.H{"avatar_url": publicPath})
}

// ChangePassword PUT /api/v1/profile/password
func (h *UserHandler) ChangePassword(c *gin.Context) {
	activeUser := middleware.GetCurrentUser(c)
	if activeUser == nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}

	var req dto.ChangePasswordRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	user, _ := h.userRepo.GetByID(activeUser.ID)
	if err := bcrypt.CompareHashAndPassword([]byte(user.HashedPassword), []byte(req.CurrentPassword)); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Senha atual incorreta"})
		return
	}

	hash, err := bcrypt.GenerateFromPassword([]byte(req.NewPassword), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to hash password"})
		return
	}

	user.HashedPassword = string(hash)
	h.userRepo.Update(user)

	c.JSON(http.StatusOK, gin.H{"message": "Senha atualizada com sucesso"})
}

// toUserResponse converts model to DTO
func toUserResponse(u *models.User) *dto.UserResponse {
	if u == nil {
		return nil
	}
	resp := &dto.UserResponse{
		ID:             u.ID,
		Email:          u.Email,
		Nome:           u.Nome,
		Matricula:      u.Matricula,
		Cargo:          u.Cargo,
		Role:           u.Role,
		IsActive:       u.IsActive,
		AvatarURL:      u.AvatarURL,
		DepartamentoID: u.DepartamentoID,
	}
	if u.Departamento != nil {
		resp.Departamento = &dto.DepartamentoDTO{
			ID:   u.Departamento.ID,
			Nome: u.Departamento.Nome,
		}
	}
	return resp
}
