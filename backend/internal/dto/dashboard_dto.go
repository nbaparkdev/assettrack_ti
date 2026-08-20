package dto

type DashboardStatsResponse struct {
	TotalAssetsInMaintenance int64          `json:"total_assets_maintenance"`
	TicketsOpen              int64          `json:"tickets_open"`
	TicketsResolved          int64          `json:"tickets_resolved"`
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
