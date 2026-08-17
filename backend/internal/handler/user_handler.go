package handler

import (
	"net/http"
	"strconv"

	"github.com/assettrack/backend/internal/dto"
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
