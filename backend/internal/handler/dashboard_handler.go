package handler

import (
	"net/http"
	"strings"
	"time"

	"github.com/assettrack/backend/internal/dto"
	"github.com/assettrack/backend/internal/middleware"
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

	// 1. Assets count by Status
	h.db.Model(&models.Asset{}).Where("LOWER(status) IN ('manutenção', 'manutencao', 'em manutenção', 'em_manutencao') OR LOWER(status) LIKE '%manuten%'").Count(&response.TotalAssetsInMaintenance)
	h.db.Model(&models.Asset{}).Where("LOWER(status) IN ('disponível', 'disponivel')").Count(&response.TotalAssetsDisponivel)
	h.db.Model(&models.Asset{}).Where("LOWER(status) IN ('em uso', 'em_uso', 'uso')").Count(&response.TotalAssetsEmUso)
	h.db.Model(&models.Asset{}).Where("LOWER(status) IN ('armazenado', 'armazenamento')").Count(&response.TotalAssetsArmazenado)
	h.db.Model(&models.Asset{}).Where("LOWER(status) IN ('baixado', 'baixa')").Count(&response.TotalAssetsBaixado)

	// 2. Open vs Resolved vs Closed Tickets
	h.db.Model(&models.ServiceTicket{}).Where("LOWER(status) NOT IN ('resolvido', 'fechado', 'cancelado')").Count(&response.TicketsOpen)
	h.db.Model(&models.ServiceTicket{}).Where("LOWER(status) = ?", "resolvido").Count(&response.TicketsResolved)
	h.db.Model(&models.ServiceTicket{}).Where("LOWER(status) IN ('fechado', 'cancelado')").Count(&response.TicketsClosed)

	// 3. Supplier Cost Monthly
	now := time.Now()
	startOfMonth := time.Date(now.Year(), now.Month(), 1, 0, 0, 0, 0, now.Location())
	
	var totalCost *float64
	h.db.Model(&models.PurchaseOrder{}).
		Select("SUM(valor_total)").
		Where("UPPER(status) IN ('APROVADO', 'RECEBIDO', 'ACEITO', 'RECEBIDO TOTALMENTE') AND data_emissao >= ?", startOfMonth).
		Scan(&totalCost)

	if totalCost != nil {
		response.SupplierCostMonthly = *totalCost
	} else {
		response.SupplierCostMonthly = 0.0
	}

	// 4. Pending Asset Requests
	h.db.Model(&models.Solicitacao{}).Where("LOWER(status) = ?", "pendente").Count(&response.PendingAssetRequests)

	// 5. Main Alerts (Emergency Alerts + Pending Asset Requests + Assets in Maintenance)
	var alerts []models.EmergencyAlert
	h.db.Where("atendido = ?", false).Order("created_at DESC").Limit(5).Find(&alerts)
	
	for _, a := range alerts {
		response.ActiveAlerts = append(response.ActiveAlerts, dto.AlertSummary{
			ID:        a.ID,
			Title:     "Alerta Crítico: " + a.UsuarioNome + " (" + a.Motivo + ")",
			Severity:  "CRITICAL",
			CreatedAt: a.CreatedAt.Format(time.RFC3339),
		})
	}

	// Also fetch active maintenance items (Oficina / Manutenções) to display as Alerts
	var activeMaint []models.Manutencao
	h.db.Preload("Asset").Where("LOWER(status) IN ?", []string{"em_andamento", "pendente"}).Order("data_entrada DESC").Limit(5).Find(&activeMaint)

	for _, m := range activeMaint {
		assetStr := "Equipamento"
		if m.Asset != nil {
			assetStr = m.Asset.Nome
			if m.Asset.EPatrimonio != "" {
				assetStr += " (" + m.Asset.EPatrimonio + ")"
			}
		}
		response.ActiveAlerts = append(response.ActiveAlerts, dto.AlertSummary{
			ID:        m.ID,
			Title:     "Equipamento em Manutenção (Oficina): " + assetStr + " — " + m.Motivo,
			Severity:  "WARNING",
			CreatedAt: m.DataEntrada.Format(time.RFC3339),
		})
	}

	// Also fetch pending or approved asset solicitations to display as Alerts on the main dashboard!
	var pendingSol []models.Solicitacao
	h.db.Preload("Solicitante").Preload("Asset").Where("LOWER(status) IN ?", []string{"pendente", "aprovada"}).Order("data_solicitacao DESC").Limit(5).Find(&pendingSol)

	for _, s := range pendingSol {
		userStr := "Usuário"
		if s.Solicitante != nil {
			userStr = s.Solicitante.Nome
		}
		assetStr := "Equipamento"
		if s.Asset != nil {
			assetStr = s.Asset.Nome
		}

		title := ""
		severity := "WARNING"
		if strings.EqualFold(string(s.Status), "pendente") {
			title = "Solicitação de Ativo Pendente: " + userStr + " solicitou " + assetStr
			severity = "WARNING"
		} else {
			title = "Ativo Aprovado Aguardando Entrega: " + assetStr + " para " + userStr
			severity = "INFO"
		}

		response.ActiveAlerts = append(response.ActiveAlerts, dto.AlertSummary{
			ID:        s.ID,
			Title:     title,
			Severity:  severity,
			CreatedAt: s.DataSolicitacao.Format(time.RFC3339),
		})
	}

	// 5. Pending Maintenance Requests (SolicitacaoManutencao)
	h.db.Model(&models.SolicitacaoManutencao{}).Where("LOWER(status) = ?", "pendente").Count(&response.PendingMaintenanceReqs)

	var pendingReqs []models.SolicitacaoManutencao
	h.db.Preload("Solicitante").Preload("Asset").Where("LOWER(status) = ?", "pendente").Order("data_solicitacao DESC").Limit(5).Find(&pendingReqs)

	for _, r := range pendingReqs {
		userStr := "Usuário"
		if r.Solicitante != nil {
			userStr = r.Solicitante.Nome
		}
		assetStr := "Equipamento"
		if r.Asset != nil {
			assetStr = r.Asset.Nome
		}
		response.ActiveAlerts = append(response.ActiveAlerts, dto.AlertSummary{
			ID:        r.ID,
			Title:     "Nova Solicitação de Manutenção: " + assetStr + " (por " + userStr + ")",
			Severity:  "CRITICAL",
			CreatedAt: r.DataSolicitacao.Format(time.RFC3339),
		})
	}

	// 6. Open Service Desk Ticket Alerts (for Admins, Managers and Technicians)
	currentUser := middleware.GetCurrentUser(c)
	if currentUser != nil && currentUser.IsManagerOrAbove() {
		var openTickets []models.ServiceTicket
		h.db.Preload("Solicitante").Where("LOWER(status) = ?", "aberto").Order("data_abertura DESC").Limit(5).Find(&openTickets)

		for _, t := range openTickets {
			solicitanteName := "Usuário"
			if t.Solicitante != nil {
				solicitanteName = t.Solicitante.Nome
			}
			response.ActiveAlerts = append(response.ActiveAlerts, dto.AlertSummary{
				ID:        t.ID,
				Title:     "Chamado Aberto: " + t.Titulo + " (por " + solicitanteName + ")",
				Severity:  "WARNING",
				CreatedAt: t.DataAbertura.Format(time.RFC3339),
			})
		}
	}

	c.JSON(http.StatusOK, response)
}

