export type SystemSettings = Record<string, string>;

export interface UpdateSettingsPayload {
  [key: string]: string;
}
