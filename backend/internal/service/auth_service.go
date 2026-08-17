package service

import (
	"fmt"
	"time"

	"github.com/assettrack/backend/internal/config"
	"github.com/assettrack/backend/internal/dto"
	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/repository"
	apperr "github.com/assettrack/backend/pkg/errors"
	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"
)

type AuthService struct {
	userRepo *repository.UserRepository
	cfg      *config.Config
}

func NewAuthService(userRepo *repository.UserRepository, cfg *config.Config) *AuthService {
	return &AuthService{userRepo: userRepo, cfg: cfg}
}

// Login authenticates user and returns JWT token
func (s *AuthService) Login(req dto.LoginRequest) (*dto.TokenResponse, error) {
	user, err := s.userRepo.GetByEmail(req.Username)
	if err != nil {
		return nil, apperr.NewUnauthorized("Incorrect username or password")
	}

	if err := bcrypt.CompareHashAndPassword([]byte(user.HashedPassword), []byte(req.Password)); err != nil {
		return nil, apperr.NewUnauthorized("Incorrect username or password")
	}

	if !user.IsActive {
		return nil, apperr.NewUnauthorized("Inactive user")
	}

	token, err := s.createAccessToken(user.Email, user.Role)
	if err != nil {
		return nil, apperr.NewInternal("Failed to create token")
	}

	return &dto.TokenResponse{
		AccessToken: token,
		TokenType:   "bearer",
	}, nil
}

// Register creates a new user (admin only)
func (s *AuthService) Register(req dto.UserCreateRequest) (*models.User, error) {
	if s.userRepo.EmailExists(req.Email) {
		return nil, apperr.NewBadRequest("The user with this email already exists in the system.")
	}

	hash, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, apperr.NewInternal("Failed to hash password")
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

	if err := s.userRepo.Create(user); err != nil {
		return nil, apperr.NewInternal(fmt.Sprintf("Failed to create user: %v", err))
	}

	// Reload with relationships
	created, _ := s.userRepo.GetByID(user.ID)
	return created, nil
}

// CreateAccessToken generates a JWT with email and role
func (s *AuthService) createAccessToken(email, role string) (string, error) {
	claims := jwt.MapClaims{
		"sub":  email,
		"role": role,
		"exp":  time.Now().Add(s.cfg.AccessTokenExpireMin).Unix(),
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(s.cfg.SecretKey))
}

// CreateAccessTokenForUser creates JWT for a given user (used by QR login)
func (s *AuthService) CreateAccessTokenForUser(user *models.User) (string, error) {
	return s.createAccessToken(user.Email, user.Role)
}

// ValidateToken parses and validates a JWT token, returns email and role
func (s *AuthService) ValidateToken(tokenString string) (string, string, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(s.cfg.SecretKey), nil
	})
	if err != nil {
		return "", "", err
	}

	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok || !token.Valid {
		return "", "", fmt.Errorf("invalid token")
	}

	email, _ := claims["sub"].(string)
	role, _ := claims["role"].(string)
	return email, role, nil
}

// HashPassword hashes a password with bcrypt
func HashPassword(password string) (string, error) {
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return "", err
	}
	return string(hash), nil
}

// VerifyPassword checks bcrypt hash
func VerifyPassword(password, hash string) bool {
	return bcrypt.CompareHashAndPassword([]byte(hash), []byte(password)) == nil
}

// VerifyPIN checks bcrypt-hashed PIN
func VerifyPIN(pin, hash string) bool {
	return bcrypt.CompareHashAndPassword([]byte(hash), []byte(pin)) == nil
}
