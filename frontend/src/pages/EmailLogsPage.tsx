import React, { useState, useEffect } from 'react';
import { getEmailLogs } from '../api/emailLogs';
import type { EmailLog } from '../types/emailLog';
import { Mail, RefreshCw, CheckCircle, XCircle } from 'lucide-react';

export const EmailLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<EmailLog[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const response = await getEmailLogs(50, 0);
      setLogs(response.data || []);
      setTotal(response.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Mail className="text-brand-primary" size={28} />
          <h1 className="text-2xl font-bold text-white font-mono uppercase">Logs de E-mail</h1>
        </div>
        <button
          onClick={fetchLogs}
          className="flex items-center gap-2 bg-brand-dark border border-brand-border text-brand-text px-4 py-2 hover:bg-brand-card transition-colors font-mono uppercase text-sm tracking-wider"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Atualizar
        </button>
      </div>

      <div className="bg-brand-card border border-brand-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-brand-dark/50 border-b border-brand-border text-sm text-brand-muted uppercase font-mono tracking-wider">
                <th className="p-4 font-semibold">Data/Hora</th>
                <th className="p-4 font-semibold">Destinatário</th>
                <th className="p-4 font-semibold">Assunto</th>
                <th className="p-4 font-semibold">Status</th>
                <th className="p-4 font-semibold">Detalhes (Erro)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border">
              {logs.map(log => (
                <tr key={log.id} className="hover:bg-brand-dark/30 text-sm text-brand-text transition-colors">
                  <td className="p-4 whitespace-nowrap font-mono text-xs text-brand-muted/80">
                    {new Date(log.sent_at).toLocaleString()}
                  </td>
                  <td className="p-4">{log.recipient}</td>
                  <td className="p-4">{log.subject}</td>
                  <td className="p-4">
                    {log.status === 'SUCCESS' ? (
                      <span className="flex items-center gap-1 text-green-500 font-mono text-xs uppercase">
                        <CheckCircle size={14} /> Sucesso
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-red-500 font-mono text-xs uppercase">
                        <XCircle size={14} /> Falha
                      </span>
                    )}
                  </td>
                  <td className="p-4 text-xs text-red-400/80 max-w-xs truncate font-mono" title={log.error_message}>
                    {log.error_message || '-'}
                  </td>
                </tr>
              ))}
              {logs.length === 0 && !loading && (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-brand-muted font-mono text-sm">
                    Nenhum log de e-mail registrado.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="p-4 border-t border-brand-border bg-brand-dark/30 text-xs font-mono uppercase text-brand-muted tracking-wider">
          Mostrando {logs.length} de {total} logs.
        </div>
      </div>
    </div>
  );
};
