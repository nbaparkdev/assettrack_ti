package repository

import (
	"github.com/assettrack/backend/internal/models"
	"gorm.io/gorm"
)

type KanbanProjectRepository struct {
	db *gorm.DB
}

func NewKanbanProjectRepository(db *gorm.DB) *KanbanProjectRepository {
	return &KanbanProjectRepository{db: db}
}

func (r *KanbanProjectRepository) List(includeArchived bool) ([]models.KanbanProject, error) {
	var projects []models.KanbanProject
	q := r.db.Preload("Criador").Preload("Participantes")
	if !includeArchived {
		q = q.Where("is_archived = false")
	}
	err := q.Order("created_at desc").Find(&projects).Error
	return projects, err
}

func (r *KanbanProjectRepository) GetByID(id uint) (*models.KanbanProject, error) {
	var project models.KanbanProject
	err := r.db.Preload("Criador").Preload("Participantes").
		Preload("Colunas", func(db *gorm.DB) *gorm.DB { return db.Order("ordem asc") }).
		Preload("Colunas.Cards", func(db *gorm.DB) *gorm.DB { return db.Order("ordem asc") }).
		Preload("Colunas.Cards.Criador").
		Preload("Colunas.Cards.Responsavel").
		Preload("Colunas.Cards.Participantes").
		Preload("Colunas.Cards.Ativos").
		Preload("Colunas.Cards.Anexos").
		First(&project, id).Error
	if err != nil {
		return nil, err
	}
	return &project, nil
}

func (r *KanbanProjectRepository) Create(project *models.KanbanProject) error {
	return r.db.Create(project).Error
}

func (r *KanbanProjectRepository) Update(project *models.KanbanProject) error {
	return r.db.Save(project).Error
}

// ReplaceParticipantes syncs the many2many participants of a project.
func (r *KanbanProjectRepository) ReplaceParticipantes(project *models.KanbanProject, userIDs []uint) error {
	var users []models.User
	if len(userIDs) > 0 {
		if err := r.db.Where("id IN ?", userIDs).Find(&users).Error; err != nil {
			return err
		}
	}
	return r.db.Model(project).Association("Participantes").Replace(users)
}

type KanbanColumnRepository struct {
	db *gorm.DB
}

func NewKanbanColumnRepository(db *gorm.DB) *KanbanColumnRepository {
	return &KanbanColumnRepository{db: db}
}

func (r *KanbanColumnRepository) Create(col *models.KanbanColumn) error {
	return r.db.Create(col).Error
}

func (r *KanbanColumnRepository) CountByProject(projectID uint) (int64, error) {
	var count int64
	err := r.db.Model(&models.KanbanColumn{}).Where("project_id = ?", projectID).Count(&count).Error
	return count, err
}

func (r *KanbanColumnRepository) GetByID(id uint) (*models.KanbanColumn, error) {
	var col models.KanbanColumn
	err := r.db.First(&col, id).Error
	if err != nil {
		return nil, err
	}
	return &col, nil
}

type KanbanCardRepository struct {
	db *gorm.DB
}

func NewKanbanCardRepository(db *gorm.DB) *KanbanCardRepository {
	return &KanbanCardRepository{db: db}
}

func (r *KanbanCardRepository) GetByID(id uint) (*models.KanbanCard, error) {
	var card models.KanbanCard
	err := r.db.Preload("Criador").Preload("Responsavel").
		Preload("Participantes").Preload("Ativos").
		Preload("Anexos").
		Preload("Interacoes", func(db *gorm.DB) *gorm.DB { return db.Order("created_at asc") }).
		Preload("Interacoes.Usuario").
		Preload("Column").
		First(&card, id).Error
	if err != nil {
		return nil, err
	}
	return &card, nil
}

func (r *KanbanCardRepository) CountByColumn(columnID uint) (int64, error) {
	var count int64
	err := r.db.Model(&models.KanbanCard{}).Where("column_id = ?", columnID).Count(&count).Error
	return count, err
}

func (r *KanbanCardRepository) Create(card *models.KanbanCard) error {
	return r.db.Create(card).Error
}

func (r *KanbanCardRepository) Update(card *models.KanbanCard) error {
	return r.db.Save(card).Error
}

func (r *KanbanCardRepository) Delete(card *models.KanbanCard) error {
	return r.db.Select("Interacoes", "Anexos").Delete(card).Error
}

// MoveCard updates column and order.
func (r *KanbanCardRepository) MoveCard(cardID, columnID uint, ordem int) error {
	return r.db.Model(&models.KanbanCard{}).Where("id = ?", cardID).
		Updates(map[string]interface{}{"column_id": columnID, "ordem": ordem, "updated_at": gorm.Expr("CURRENT_TIMESTAMP")}).Error
}

// ReplaceParticipantes syncs card participants.
func (r *KanbanCardRepository) ReplaceParticipantes(card *models.KanbanCard, userIDs []uint) error {
	var users []models.User
	if len(userIDs) > 0 {
		if err := r.db.Where("id IN ?", userIDs).Find(&users).Error; err != nil {
			return err
		}
	}
	return r.db.Model(card).Association("Participantes").Replace(users)
}

// ReplaceAssets syncs card linked assets.
func (r *KanbanCardRepository) ReplaceAssets(card *models.KanbanCard, assetIDs []uint) error {
	var assets []models.Asset
	if len(assetIDs) > 0 {
		if err := r.db.Where("id IN ?", assetIDs).Find(&assets).Error; err != nil {
			return err
		}
	}
	return r.db.Model(card).Association("Ativos").Replace(assets)
}

type KanbanInteractionRepository struct {
	db *gorm.DB
}

func NewKanbanInteractionRepository(db *gorm.DB) *KanbanInteractionRepository {
	return &KanbanInteractionRepository{db: db}
}

func (r *KanbanInteractionRepository) Create(interaction *models.KanbanCardInteraction) error {
	return r.db.Create(interaction).Error
}

type KanbanAttachmentRepository struct {
	db *gorm.DB
}

func NewKanbanAttachmentRepository(db *gorm.DB) *KanbanAttachmentRepository {
	return &KanbanAttachmentRepository{db: db}
}

func (r *KanbanAttachmentRepository) Create(att *models.KanbanAttachment) error {
	return r.db.Create(att).Error
}

func (r *KanbanAttachmentRepository) GetByID(id uint) (*models.KanbanAttachment, error) {
	var att models.KanbanAttachment
	err := r.db.First(&att, id).Error
	if err != nil {
		return nil, err
	}
	return &att, nil
}

func (r *KanbanAttachmentRepository) Delete(id uint) error {
	return r.db.Delete(&models.KanbanAttachment{}, id).Error
}

type KanbanNotificationRepository struct {
	db *gorm.DB
}

func NewKanbanNotificationRepository(db *gorm.DB) *KanbanNotificationRepository {
	return &KanbanNotificationRepository{db: db}
}

func (r *KanbanNotificationRepository) Create(n *models.KanbanNotification) error {
	return r.db.Create(n).Error
}

func (r *KanbanNotificationRepository) UnreadCount(userID uint) (int64, error) {
	var count int64
	err := r.db.Model(&models.KanbanNotification{}).
		Where("user_id = ? AND lida = false", userID).Count(&count).Error
	return count, err
}

func (r *KanbanNotificationRepository) ListByUser(userID uint, limit int) ([]models.KanbanNotification, error) {
	var notifs []models.KanbanNotification
	err := r.db.Preload("Autor").Where("user_id = ?", userID).
		Order("created_at desc").Limit(limit).Find(&notifs).Error
	return notifs, err
}

func (r *KanbanNotificationRepository) MarkRead(notifID, userID uint) error {
	return r.db.Model(&models.KanbanNotification{}).
		Where("id = ? AND user_id = ?", notifID, userID).
		Update("lida", true).Error
}

func (r *KanbanNotificationRepository) MarkAllRead(userID uint) error {
	return r.db.Model(&models.KanbanNotification{}).
		Where("user_id = ? AND lida = false", userID).
		Update("lida", true).Error
}
