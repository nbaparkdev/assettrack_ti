import { apiClient, API_BASE_URL } from './client';

export interface AppVersionInfo {
  version_code: number;
  version_name: string;
  release_date: string;
  download_url: string;
  apk_filename?: string;
  apk_size_bytes: number;
  apk_size_formatted: string;
  min_android_version: string;
  release_notes: string;
}

export interface AppPublishStatus {
  is_running: boolean;
  progress: string;
  error?: string;
}

export const appVersionApi = {
  getVersion: async (): Promise<AppVersionInfo> => {
    const res = await apiClient.get<AppVersionInfo>('/app/version');
    return res.data;
  },

  getDownloadUrl: (): string => {
    return `${API_BASE_URL}/app/download`;
  },

  publishMobileApk: async (): Promise<{ message: string }> => {
    const res = await apiClient.post<{ message: string }>('/admin/mobile/publish-apk');
    return res.data;
  },

  getPublishStatus: async (): Promise<AppPublishStatus> => {
    const res = await apiClient.get<AppPublishStatus>('/admin/mobile/publish-apk/status');
    return res.data;
  },
};
