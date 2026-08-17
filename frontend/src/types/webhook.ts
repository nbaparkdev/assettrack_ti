export interface WebhookLog {
  id: number;
  webhook_id: number;
  evento: string;
  payload_enviado: string;
  response_code: number;
  response_body: string;
  sucesso: boolean;
  created_at: string;
}

export interface Webhook {
  id: number;
  nome: string;
  url: string;
  is_active: boolean;
  secret_key?: string;
  eventos_permitidos: string; // JSON string
  created_at: string;
  updated_at: string;
  logs?: WebhookLog[];
}

export interface WebhookInput {
  nome: string;
  url: string;
  is_active?: boolean;
  secret_key?: string;
  eventos_permitidos: string[];
}
