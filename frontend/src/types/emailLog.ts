export interface EmailLog {
  id: number;
  recipient: string;
  subject: string;
  body: string;
  sent_at: string;
  status: 'SUCCESS' | 'FAILED';
  error_message?: string;
}

export interface EmailLogResponse {
  data: EmailLog[];
  total: number;
}
