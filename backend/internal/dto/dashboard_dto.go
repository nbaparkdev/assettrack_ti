package dto

type CategoryStat struct {
	Category string `json:"category"`
	Count    int64  `json:"count"`
}

type PriorityStat struct {
	Urgente int64 `json:"urgente"`
	Alta    int64 `json:"alta"`
	Media   int64 `json:"media"`
	Baixa   int64 `json:"baixa"`
}

type RecentActivityItem struct {
	ID        uint   `json:"id"`
	Type      string `json:"type"` // "movimentacao", "solicitacao", "manutencao", "ticket"
	Title     string `json:"title"`
	Subtitle  string `json:"subtitle"`
	Status    string `json:"status"`
	CreatedAt string `json:"created_at"`
}

type DashboardStatsResponse struct {
	TotalAssets              int64                `json:"total_assets"`
	TotalAssetsValue         float64              `json:"total_assets_value"`
	TotalAssetsInMaintenance int64                `json:"total_assets_maintenance"`
	TotalAssetsDisponivel    int64                `json:"total_assets_disponivel"`
	TotalAssetsEmUso         int64                `json:"total_assets_em_uso"`
	TotalAssetsArmazenado    int64                `json:"total_assets_armazenado"`
	TotalAssetsBaixado       int64                `json:"total_assets_baixado"`
	TicketsTotal             int64                `json:"tickets_total"`
	TicketsOpen              int64                `json:"tickets_open"`
	TicketsResolved          int64                `json:"tickets_resolved"`
	TicketsClosed            int64                `json:"tickets_closed"`
	TicketsAvgRating         float64              `json:"tickets_avg_rating"`
	TicketsByPriority        PriorityStat         `json:"tickets_by_priority"`
	AssetsByCategory         []CategoryStat       `json:"assets_by_category"`
	RecentActivities         []RecentActivityItem `json:"recent_activities"`
	SupplierCostMonthly      float64              `json:"supplier_cost_monthly"`
	PendingAssetRequests     int64                `json:"pending_asset_requests"`
	PendingMaintenanceReqs   int64                `json:"pending_maintenance_requests"`
	ActiveAlerts             []AlertSummary       `json:"active_alerts"`
}

type AlertSummary struct {
	ID        uint   `json:"id"`
	Title     string `json:"title"`
	Severity  string `json:"severity"`
	CreatedAt string `json:"created_at"`
	Link      string `json:"link,omitempty"`
}
