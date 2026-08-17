import { apiClient as api } from './client';

export interface AlertSummary {
  id: number;
  title: string;
  severity: string;
  created_at: string;
}

export interface DashboardStats {
  total_assets_maintenance: number;
  tickets_open: number;
  tickets_resolved: number;
  supplier_cost_monthly: number;
  pending_asset_requests: number;
  active_alerts: AlertSummary[] | null;
}

export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    const res = await api.get<DashboardStats>('/dashboard/stats');
    return res.data;
  },
};
