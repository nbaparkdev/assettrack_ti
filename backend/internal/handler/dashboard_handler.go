package handler

import (
	"net/http"
	"time"

	"github.com/assettrack/backend/internal/dto"
	"github.com/assettrack/backend/internal/models"
	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

type DashboardHandler struct {
	db *gorm.DB
}

func NewDashboardHandler(db *gorm.DB) *DashboardHandler {
	return &DashboardHandler{db: db}
}

// GetStats GET /api/v1/dashboard/stats
func (h *DashboardHandler) GetStats(c *gin.Context) {
	var response dto.DashboardStatsResponse

	// 1. Total Assets in Maintenance (status = 'MANUTENCAO')
	h.db.Model(&models.Asset{}).Where("status = ?", "MANUTENCAO").Count(&response.TotalAssetsInMaintenance)

	// 2. Open vs Resolved Tickets
	h.db.Model(&models.ServiceTicket{}).Where("status IN ?", []string{"ABERTO", "EM_ANDAMENTO"}).Count(&response.TicketsOpen)
	h.db.Model(&models.ServiceTicket{}).Where("status = ?", "RESOLVIDO").Count(&response.TicketsResolved)

	// 3. Supplier Cost Monthly (PurchaseOrders where Status = 'RECEBIDO' or 'APROVADO' in current month)
	now := time.Now()
	startOfMonth := time.Date(now.Year(), now.Month(), 1, 0, 0, 0, 0, now.Location())
	
	// Assuming PurchaseOrder has TotalAmount
	// If it doesn't have a direct float sum, we might need to sum items. Let's just do raw query summing total_amount.
	var totalCost *float64
	h.db.Model(&models.PurchaseOrder{}).
		Select("SUM(total_amount)").
		Where("status IN ('APROVADO', 'RECEBIDO') AND created_at >= ?", startOfMonth).
		Scan(&totalCost)

	if totalCost != nil {
		response.SupplierCostMonthly = *totalCost
	} else {
		response.SupplierCostMonthly = 0.0
	}

	// 4. Pending Asset Requests
	h.db.Model(&models.Solicitacao{}).Where("status = ?", "PENDENTE").Count(&response.PendingAssetRequests)

	// 5. Main Alerts
	var alerts []models.EmergencyAlert
	h.db.Where("status = ?", "ACTIVE").Order("created_at DESC").Limit(5).Find(&alerts)
	
	for _, a := range alerts {
		response.ActiveAlerts = append(response.ActiveAlerts, dto.AlertSummary{
			ID:        a.ID,
			Title:     a.Title,
			Severity:  a.Severity,
			CreatedAt: a.CreatedAt.Format(time.RFC3339),
		})
	}

	c.JSON(http.StatusOK, response)
}
