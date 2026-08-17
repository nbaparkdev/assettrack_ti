package repository

import (
	"github.com/assettrack/backend/internal/models"
	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
	"time"
)

type UserRepository struct {
	db *gorm.DB
}

func NewUserRepository(db *gorm.DB) *UserRepository {
	return &UserRepository{db: db}
}

func (r *UserRepository) GetByID(id uint) (*models.User, error) {
	var user models.User
	if err := r.db.Preload("Departamento").First(&user, id).Error; err != nil {
		return nil, err
	}
	return &user, nil
}

func (r *UserRepository) GetByEmail(email string) (*models.User, error) {
	var user models.User
	if err := r.db.Preload("Departamento").Where("email = ?", email).First(&user).Error; err != nil {
		return nil, err
	}
	return &user, nil
}

func (r *UserRepository) GetByQRToken(token string) (*models.User, error) {
	var user models.User
	if err := r.db.Preload("Departamento").Where("qr_token = ?", token).First(&user).Error; err != nil {
		return nil, err
	}
	return &user, nil
}

func (r *UserRepository) GetMulti(skip, limit int) ([]models.User, error) {
	var users []models.User
	if err := r.db.Preload("Departamento").Offset(skip).Limit(limit).Find(&users).Error; err != nil {
		return nil, err
	}
	return users, nil
}

func (r *UserRepository) Create(user *models.User) error {
	return r.db.Create(user).Error
}

func (r *UserRepository) Update(user *models.User) error {
	return r.db.Save(user).Error
}

func (r *UserRepository) Delete(id uint) error {
	return r.db.Delete(&models.User{}, id).Error
}

func (r *UserRepository) EmailExists(email string) bool {
	var count int64
	r.db.Model(&models.User{}).Where("email = ?", email).Count(&count)
	return count > 0
}

func (r *UserRepository) RegenerateQRToken(userID uint) (string, error) {
	newToken := uuid.New().String()
	now := time.Now().UTC()

	if err := r.db.Model(&models.User{}).Where("id = ?", userID).
		Updates(map[string]interface{}{
			"qr_token":            newToken,
			"qr_token_created_at": now,
		}).Error; err != nil {
		return "", err
	}
	return newToken, nil
}

func (r *UserRepository) SetPIN(userID uint, pin string) error {
	hash, err := bcrypt.GenerateFromPassword([]byte(pin), bcrypt.DefaultCost)
	if err != nil {
		return err
	}
	return r.db.Model(&models.User{}).Where("id = ?", userID).
		Update("pin_hash", string(hash)).Error
}
