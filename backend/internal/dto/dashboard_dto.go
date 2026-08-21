package dto

type DashboardStatsResponse struct {
	TotalAssetsInMaintenance int64          `json:"total_assets_maintenance"`
	TotalAssetsDisponivel    int64          `json:"total_assets_disponivel"`
	TotalAssetsEmUso         int64          `json:"total_assets_em_uso"`
	TotalAssetsArmazenado    int64          `json:"total_assets_armazenado"`
	TotalAssetsBaixado       int64          `json:"total_assets_baixado"`
	TicketsOpen              int64          `json:"tickets_open"`
	TicketsResolved          int64          `json:"tickets_resolved"`
	TicketsClosed            int64          `json:"tickets_closed"`
	SupplierCostMonthly      float64        `json:"supplier_cost_monthly"`
	PendingAssetRequests     int64          `json:"pending_asset_requests"`
	PendingMaintenanceReqs   int64          `json:"pending_maintenance_requests"`
	ActiveAlerts             []AlertSummary `json:"active_alerts"`
}

type AlertSummary struct {
	ID        uint   `json:"id"`
	Title     string `json:"title"`
	Severity  string `json:"severity"`
	CreatedAt string `json:"created_at"`
}
