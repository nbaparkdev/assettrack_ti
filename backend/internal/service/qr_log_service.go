package service

import (
	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/repository"
	"github.com/assettrack/backend/pkg/utils"
	"github.com/gin-gonic/gin"
)

type QRLogService struct {
	repo *repository.QRLogRepository
}

func NewQRLogService(repo *repository.QRLogRepository) *QRLogService {
	return &QRLogService{repo: repo}
}

func (s *QRLogService) getClientIP(c *gin.Context) string {
	if forwarded := c.GetHeader("X-Forwarded-For"); forwarded != "" {
		return forwarded
	}
	return c.ClientIP()
}

func (s *QRLogService) LogAction(c *gin.Context, userID uint, action string, actorID *uint, details *string, success bool) {
	ip := s.getClientIP(c)
	log := &models.QRLog{
		UserID:    &userID,
		ActorID:   actorID,
		Action:    action,
		IPAddress: &ip,
		Details:   details,
		Success:   success,
		Timestamp: utils.NowSP(),
	}
	_ = s.repo.Create(log)
}

func (s *QRLogService) LogLogin(c *gin.Context, userID uint, success bool) {
	action := models.QRActionLogin
	if !success {
		action = models.QRActionLoginFailed
	}
	s.LogAction(c, userID, action, nil, nil, success)
}

func (s *QRLogService) LogRegenerate(c *gin.Context, userID uint) {
	s.LogAction(c, userID, models.QRActionRegenerate, nil, nil, true)
}

func (s *QRLogService) LogPINAction(c *gin.Context, userID uint, isChange bool) {
	action := models.QRActionPINSet
	if isChange {
		action = models.QRActionPINChanged
	}
	s.LogAction(c, userID, action, nil, nil, true)
}
