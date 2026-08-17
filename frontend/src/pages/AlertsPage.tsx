import React, { useState, useEffect, useRef } from 'react';
import { alertsApi } from '../api/alerts';
import type { EmergencyAlert, Aviso } from '../types/alerts';
import { useAuthStore } from '../stores/authStore';
import { ShieldAlert, Siren, Bell, Plus, Trash2, Edit2, X, CheckCircle2 } from 'lucide-react';

const staffRoles = ['admin', 'gerente_ti', 'gerente_infra', 'tecnico'];

export const AlertsPage: React.FC = () => {
  const user = useAuthStore().user;
  const isStaff = user ? staffRoles.includes(user.role) : false;
  const canManageAvisos = user ? ['admin', 'gerente_ti', 'gerente_infra'].includes(user.role) : false;

  const [motivo, setMotivo] = useState('');
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [history, setHistory] = useState<EmergencyAlert[]>([]);
  const [avisos, setAvisos] = useState<Aviso[]>([]);
  const [liveAlerts, setLiveAlerts] = useState<any[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Aviso form
  const [avisoModal, setAvisoModal] = useState(false);
  const [editAvisoId, setEditAvisoId] = useState<number | null>(null);
  const [aTitulo, setATitulo] = useState('');
  const [aTexto, setATexto] = useState('');
  const [aLink, setALink] = useState('');
  const [aLinkTexto, setALinkTexto] = useState('');
  const [aInicio, setAInicio] = useState('');
  const [aFim, setAFim] = useState('');

  const fetchData = async () => {
    try {
      setHistory(await alertsApi.history());
      setAvisos(await alertsApi.listAvisos());
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchData();
    return () => eventSourceRef.current?.close();
  }, []);

  // SSE for staff
  useEffect(() => {
    if (!isStaff) return;
    const token = localStorage.getItem('token');
    const es = new EventSource(`/api/v1/alertas/stream?token=${token}`);
    es.addEventListener('emergency_alert', (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        setLiveAlerts((prev) => [data, ...prev].slice(0, 5));
        fetchData();
      } catch { /* ignore */ }
    });
    es.onerror = () => { /* EventSource auto-reconnects */ };
    eventSourceRef.current = es;
    return () => es.close();
  }, [isStaff]);

  const submitAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!motivo.trim()) return;
    setSending(true);
    try {
      await alertsApi.sendAlert(motivo);
      setMotivo('');
      setSent(true);
      setTimeout(() => setSent(false), 5000);
    } catch (err) {
      window.alert('Erro ao enviar alerta');
    } finally {
      setSending(false);
    }
  };

  const openAvisoModal = (aviso?: Aviso) => {
    setEditAvisoId(aviso?.id ?? null);
    setATitulo(aviso?.titulo ?? '');
    setATexto(aviso?.texto ?? '');
    setALink(aviso?.link_url ?? '');
    setALinkTexto(aviso?.link_texto ?? '');
    setAInicio(aviso?.programado_inicio ? aviso.programado_inicio.slice(0, 16) : '');
    setAFim(aviso?.programado_fim ? aviso.programado_fim.slice(0, 16) : '');
    setAvisoModal(true);
  };

  const submitAviso = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        titulo: aTitulo,
        texto: aTexto || undefined,
        link_url: aLink || undefined,
        link_texto: aLinkTexto || undefined,
        programado_inicio: aInicio ? new Date(aInicio).toISOString() : undefined,
        programado_fim: aFim ? new Date(aFim).toISOString() : undefined,
      };
      if (editAvisoId) await alertsApi.updateAviso(editAvisoId, payload);
      else await alertsApi.createAviso(payload);
      setAvisoModal(false);
      fetchData();
    } catch (err) {
      window.alert('Erro ao salvar aviso');
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0">Alertas & Avisos</h1>
        <p className="text-brand-muted text-sm mt-1">Alertas emergenciais em tempo real e avisos do sistema.</p>
      </div>

      {/* Live alerts (staff) */}
      {isStaff && liveAlerts.length > 0 && (
        <div className="space-y-2">
          {liveAlerts.map((a, i) => (
            <div key={i} className="border border-red-500/40 bg-red-500/10 p-4">
              <div className="flex items-center space-x-2 text-red-400 font-mono text-xs uppercase">
                <Siren size={16} />
                <span>Alerta recebido — {a.created_at}</span>
              </div>
              <div className="mt-2 text-sm text-brand-text">
                <strong>{a.usuario_nome}</strong> ({a.setor_nome}) — {a.motivo}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trigger alert */}
        <div className="border border-brand-border bg-brand-card p-6 space-y-4">
          <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-brand-text flex items-center">
            <ShieldAlert size={16} className="mr-2 text-red-400" /> Disparar alerta emergencial
          </h3>
          <p className="text-sm text-brand-muted">
            Aciona a equipe de TI em tempo real. Informe o motivo da emergência.
          </p>
          <form onSubmit={submitAlert} className="space-y-3">
            <textarea
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              rows={4}
              required
              placeholder="Descreva o problema urgente..."
              className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-red-500/50"
            />
            <button
              type="submit"
              disabled={sending}
              className="bg-red-500/20 text-red-400 border border-red-500/40 px-4 py-2.5 font-bold font-mono uppercase tracking-wider text-xs hover:bg-red-500/30 disabled:opacity-50 w-full"
            >
              {sending ? 'Enviando...' : 'Transmitir alerta'}
            </button>
            {sent && (
              <div className="text-green-400 text-xs font-mono uppercase flex items-center">
                <CheckCircle2 size={14} className="mr-1" /> Alerta transmitido com sucesso!
              </div>
            )}
          </form>
        </div>

        {/* Alert history (staff) */}
        {isStaff && (
          <div className="border border-brand-border bg-brand-card">
            <div className="p-4 border-b border-brand-border text-sm font-bold font-mono uppercase tracking-wider text-brand-text flex items-center">
              <Bell size={16} className="mr-2" /> Histórico de alertas
            </div>
            <div className="divide-y divide-brand-border/60 max-h-96 overflow-y-auto">
              {history.map((a) => (
                <div key={a.id} className={`p-4 ${a.atendido ? 'opacity-60' : ''}`}>
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="font-mono text-xs text-brand-primary">
                        {a.usuario_nome} — {a.setor_nome ?? '—'}
                      </span>
                      <p className="text-sm text-brand-text mt-1 m-0">{a.motivo}</p>
                      <span className="text-xs font-mono text-brand-muted">{new Date(a.created_at).toLocaleString('pt-BR')}</span>
                    </div>
                    {!a.atendido && (
                      <button
                        onClick={async () => {
                          await alertsApi.markAtendido(a.id);
                          fetchData();
                        }}
                        className="text-green-400 border border-green-500/30 px-2.5 py-1.5 font-mono text-xs uppercase hover:bg-green-500/10"
                      >
                        Atender
                      </button>
                    )}
                  </div>
                  {a.atendido && a.atendido_por && (
                    <div className="text-xs font-mono text-green-400 mt-1">Atendido por {a.atendido_por.nome}</div>
                  )}
                </div>
              ))}
              {history.length === 0 && (
                <div className="p-6 text-center text-brand-muted font-mono text-xs">Nenhum alerta registrado.</div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Avisos */}
      <div className="border border-brand-border bg-brand-card">
        <div className="p-4 border-b border-brand-border flex justify-between items-center">
          <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-brand-text m-0">Avisos do sistema</h3>
          {canManageAvisos && (
            <button onClick={() => openAvisoModal()}
              className="bg-brand-primary text-brand-dark font-bold font-mono px-3 py-2 uppercase tracking-wider text-xs flex items-center space-x-1.5">
              <Plus size={14} />
              <span>Novo Aviso</span>
            </button>
          )}
        </div>
        <div className="divide-y divide-brand-border/60">
          {avisos.map((a) => (
            <div key={a.id} className="p-4 flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-brand-text">{a.titulo}</span>
                  <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 border ${a.ativo ? 'border-green-500/30 text-green-400' : 'border-brand-border text-brand-muted'}`}>
                    {a.ativo ? 'Ativo' : 'Inativo'}
                  </span>
                </div>
                {a.texto && <p className="text-sm text-brand-muted mt-1 m-0">{a.texto}</p>}
                {a.link_url && (
                  <a href={a.link_url} target="_blank" rel="noreferrer" className="text-brand-primary text-sm mt-1 inline-block">
                    {a.link_texto ?? a.link_url}
                  </a>
                )}
              </div>
              {canManageAvisos && (
                <div className="flex space-x-2">
                  <button onClick={async () => { await alertsApi.toggleAviso(a.id); fetchData(); }}
                    title={a.ativo ? 'Desativar' : 'Ativar'}
                    className="text-brand-muted border border-brand-border px-2 py-1.5 hover:text-brand-text">
                    {a.ativo ? 'Desativar' : 'Ativar'}
                  </button>
                  <button onClick={() => openAvisoModal(a)} className="text-brand-primary border border-brand-primary/30 px-2 py-1.5">
                    <Edit2 size={14} />
                  </button>
                  <button onClick={async () => {
                    if (!window.confirm('Excluir aviso?')) return;
                    await alertsApi.deleteAviso(a.id);
                    fetchData();
                  }} className="text-red-400 border border-red-500/30 px-2 py-1.5">
                    <Trash2 size={14} />
                  </button>
                </div>
              )}
            </div>
          ))}
          {avisos.length === 0 && (
            <div className="p-6 text-center text-brand-muted font-mono text-xs">Nenhum aviso cadastrado.</div>
          )}
        </div>
      </div>

      {/* Aviso Modal */}
      {avisoModal && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg border border-brand-border bg-brand-card p-6 space-y-6">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">
                {editAvisoId ? 'Editar Aviso' : 'Novo Aviso'}
              </h3>
              <button onClick={() => setAvisoModal(false)} className="text-brand-muted hover:text-brand-text"><X size={20} /></button>
            </div>
            <form onSubmit={submitAviso} className="space-y-4">
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Título *</label>
                <input type="text" required value={aTitulo} onChange={(e) => setATitulo(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Texto</label>
                <textarea value={aTexto} onChange={(e) => setATexto(e.target.value)} rows={3}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Link (opcional)</label>
                  <input type="text" value={aLink} onChange={(e) => setALink(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Texto do botão</label>
                  <input type="text" value={aLinkTexto} onChange={(e) => setALinkTexto(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Início programado</label>
                  <input type="datetime-local" value={aInicio} onChange={(e) => setAInicio(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Fim programado</label>
                  <input type="datetime-local" value={aFim} onChange={(e) => setAFim(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" />
                </div>
              </div>
              <div className="flex justify-end space-x-3 pt-4 border-t border-brand-border">
                <button type="button" onClick={() => setAvisoModal(false)} className="border border-brand-border px-4 py-2 font-mono text-xs uppercase">Cancelar</button>
                <button type="submit" className="bg-brand-primary text-brand-dark font-bold font-mono px-4 py-2 uppercase text-xs">Salvar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
