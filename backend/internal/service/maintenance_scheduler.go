package service

import (
	"fmt"
	"log"
	"time"

	"github.com/assettrack/backend/internal/models"
	"github.com/assettrack/backend/internal/repository"
	"gorm.io/gorm"
)

// MaintenanceScheduler periodically generates preventive maintenance orders
// from active plans that reached their next execution date (idempotent).
type MaintenanceScheduler struct {
	db            *gorm.DB
	planRepo      *repository.PMPlanRepository
	planAssetRepo *repository.PMPlanAssetRepository
	orderRepo     *repository.PMOrderRepository
	historyRepo   *repository.PMHistoryRepository
	notifRepo     *repository.PMNotificationRepository
	categoryRepo  *repository.AssetCategoryRepository
}

func NewMaintenanceScheduler(
	db *gorm.DB,
	planRepo *repository.PMPlanRepository,
	planAssetRepo *repository.PMPlanAssetRepository,
	orderRepo *repository.PMOrderRepository,
	historyRepo *repository.PMHistoryRepository,
	notifRepo *repository.PMNotificationRepository,
	categoryRepo *repository.AssetCategoryRepository,
) *MaintenanceScheduler {
	return &MaintenanceScheduler{
		db:            db,
		planRepo:      planRepo,
		planAssetRepo: planAssetRepo,
		orderRepo:     orderRepo,
		historyRepo:   historyRepo,
		notifRepo:     notifRepo,
		categoryRepo:  categoryRepo,
	}
}

// Start launches the periodic check loop (default every hour).
func (s *MaintenanceScheduler) Start(interval time.Duration) {
	if interval <= 0 {
		interval = time.Hour
	}
	go func() {
		log.Printf("🔧 Maintenance scheduler started (interval: %s)", interval)
		for {
			s.CheckAndGenerate()
			time.Sleep(interval)
		}
	}()
}

// CheckAndGenerate verifies due plans and generates orders.
func (s *MaintenanceScheduler) CheckAndGenerate() {
	now := time.Now()

	var plans []models.MaintenancePlan
	if err := s.db.Preload("Assets.Asset").Preload("Categoria").
		Where("ativo = true AND proxima_execucao <= ?", now).Find(&plans).Error; err != nil {
		log.Printf("[SCHEDULER] Error loading due plans: %v", err)
		return
	}

	for _, plan := range plans {
		// 1. Qualified assets: explicit links, else category assets
		var assets []models.Asset
		if len(plan.Assets) > 0 {
			for _, pa := range plan.Assets {
				if pa.Asset != nil {
					assets = append(assets, *pa.Asset)
				}
			}
		} else if plan.CategoriaID != nil {
			var catAssets []models.Asset
			if err := s.db.Where("categoria_id = ?", *plan.CategoriaID).Find(&catAssets).Error; err == nil {
				assets = catAssets
			}
		}

		if len(assets) == 0 {
			log.Printf("[SCHEDULER] Plan %s has no linked assets or category. Advancing next execution.", plan.Codigo)
			s.advancePlan(plan)
			continue
		}

		todayStart := time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, now.Location())
		todayEnd := todayStart.AddDate(0, 0, 1)

		created := 0
		for _, asset := range assets {
			// 2. Idempotency: an open order for this plan+asset today?
			existing, err := s.orderRepo.ExistingOrderToday(plan.ID, asset.ID, todayStart, todayEnd)
			if err == nil && existing != nil {
				log.Printf("[SCHEDULER] Order already exists today for plan %s / asset %s (%s). Skipping.", plan.Codigo, asset.Nome, existing.Numero)
				continue
			}

			// 3. Generate order number
			numero, err := s.orderRepo.GenerateOrderNumber(now)
			if err != nil {
				log.Printf("[SCHEDULER] Error generating order number: %v", err)
				continue
			}

			desc := ""
			if plan.Descricao != nil && *plan.Descricao != "" {
				desc = *plan.Descricao
			} else {
				desc = fmt.Sprintf("Ordem de manutenção gerada automaticamente a partir do plano %s (%s).", plan.Nome, plan.Codigo)
			}

			order := &models.MaintenanceOrder{
				Numero:       numero,
				PlanID:       &plan.ID,
				AssetID:      &asset.ID,
				TecnicoID:    plan.ResponsavelID,
				Status:       models.PMStatusAberta,
				Prioridade:   plan.Prioridade,
				Criticidade:  plan.Criticidade,
				Tipo:         plan.Tipo,
				Observacoes:  &desc,
				DataAbertura: now,
				DataAgendada: &now,
			}
			if err := s.orderRepo.Create(order); err != nil {
				log.Printf("[SCHEDULER] Error creating order: %v", err)
				continue
			}

			_ = s.historyRepo.Create(&models.MaintenanceHistory{
				OrderID:    order.ID,
				Acao:       "Ordem Criada",
				Descricao:  "Ordem de serviço gerada automaticamente pelo sistema a partir do plano de manutenção.",
				StatusNovo: &order.Status,
			})

			// Notify the plan's responsible technician
			if plan.ResponsavelID != nil {
				_ = s.notifRepo.Create(&models.MaintenanceNotification{
					OrderID:   &order.ID,
					UsuarioID: *plan.ResponsavelID,
					Tipo:      "order_assigned",
					Mensagem: fmt.Sprintf("Nova ordem de serviço gerada automaticamente pelo plano %s.\n\nOS Código: %s\nEquipamento/Ativo: %s\nPrioridade: %s",
						plan.Codigo, order.Numero, asset.Nome, plan.Prioridade),
				})
			}

			created++
		}

		s.advancePlan(plan)
		log.Printf("[SCHEDULER] Plan %s processed: %d orders created.", plan.Codigo, created)
	}
}

// advancePlan updates the plan's last/next execution dates.
func (s *MaintenanceScheduler) advancePlan(plan models.MaintenancePlan) {
	now := time.Now()
	plan.DataUltimaExecucao = &now

	days := periodicityDays(plan.Periodicidade)
	if days == 0 {
		if plan.DiasPersonalizado != nil {
			days = *plan.DiasPersonalizado
		} else {
			days = 30
		}
	}
	next := now.AddDate(0, 0, days)
	plan.ProximaExecucao = next

	if err := s.planRepo.Update(&plan); err != nil {
		log.Printf("[SCHEDULER] Error updating plan %s: %v", plan.Codigo, err)
	}
}

func periodicityDays(periodicidade string) int {
	switch periodicidade {
	case models.PeriodicidadeDiaria:
		return 1
	case models.PeriodicidadeSemanal:
		return 7
	case models.PeriodicidadeQuinzenal:
		return 15
	case models.PeriodicidadeMensal:
		return 30
	case models.PeriodicidadeBimestral:
		return 60
	case models.PeriodicidadeTrimestral:
		return 90
	case models.PeriodicidadeSemestral:
		return 180
	case models.PeriodicidadeAnual:
		return 365
	default:
		return 0 // personalized
	}
}
