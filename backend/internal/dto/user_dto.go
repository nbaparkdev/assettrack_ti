package dto

// UserCreateRequest - create user payload
type UserCreateRequest struct {
	Email          string `json:"email" binding:"required,email"`
	Password       string `json:"password" binding:"required,min=4"`
	Nome           string `json:"nome" binding:"required"`
	Matricula      string `json:"matricula,omitempty"`
	Cargo          string `json:"cargo,omitempty"`
	Role           string `json:"role,omitempty"`
	IsActive       bool   `json:"is_active"`
	DepartamentoID *uint  `json:"departamento_id,omitempty"`
}

// UserUpdateRequest - update user payload (all optional)
type UserUpdateRequest struct {
	Email          *string `json:"email,omitempty" binding:"omitempty,email"`
	Password       *string `json:"password,omitempty" binding:"omitempty,min=4"`
	Nome           *string `json:"nome,omitempty"`
	Matricula      *string `json:"matricula,omitempty"`
	Cargo          *string `json:"cargo,omitempty"`
	Role           *string `json:"role,omitempty"`
	IsActive       *bool   `json:"is_active,omitempty"`
	DepartamentoID *uint   `json:"departamento_id,omitempty"`
}

// UserResponse - user data returned to clients
type UserResponse struct {
	ID             uint             `json:"id"`
	Email          string           `json:"email"`
	Nome           string           `json:"nome"`
	Matricula      *string          `json:"matricula"`
	Cargo          *string          `json:"cargo"`
	Role           string           `json:"role"`
	IsActive       bool             `json:"is_active"`
	AvatarURL      *string          `json:"avatar_url"`
	DepartamentoID *uint            `json:"departamento_id"`
	Departamento   *DepartamentoDTO `json:"departamento,omitempty"`
}

type ChangePasswordRequest struct {
	CurrentPassword string `json:"current_password" binding:"required"`
	NewPassword     string `json:"new_password" binding:"required,min=4"`
}

// DepartamentoDTO - nested department info
type DepartamentoDTO struct {
	ID   uint   `json:"id"`
	Nome string `json:"nome"`
}
