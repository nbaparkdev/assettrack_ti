import React, { useState, useEffect, useRef } from 'react';
import { kanbanApi } from '../api/kanban';
import { usersApi } from '../api/users';
import { assetsApi } from '../api/assets';
import type {
  KanbanProject,
  KanbanCard,
  KanbanColumn,
  KanbanNotification,
} from '../types/kanban';
import { CARD_PRIORITIES, priorityColor } from '../types/kanban';
import {
  Plus, X, ShieldAlert, Bell, Paperclip, MessageSquare, Trash2, Columns3,
} from 'lucide-react';

export const KanbanPage: React.FC = () => {
  const [projects, setProjects] = useState<KanbanProject[]>([]);
  const [board, setBoard] = useState<{ project: KanbanProject; board_progress: number; total_cards: number } | null>(null);
  const [cardDetail, setCardDetail] = useState<KanbanCard | null>(null);
  const [notifs, setNotifs] = useState<KanbanNotification[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Users/assets lookups
  const [users, setUsers] = useState<{ id: number; nome: string }[]>([]);
  const [_assets, setAssets] = useState<{ id: number; nome: string }[]>([]);

  // Project form
  const [projModal, setProjModal] = useState(false);
  const [pTitle, setPTitle] = useState('');
  const [pDesc, setPDesc] = useState('');
  const [pParticipants, setPParticipants] = useState<number[]>([]);

  // Card form
  const [cardModal, setCardModal] = useState(false);
  const [cTitle, setCTitle] = useState('');
  const [cDesc, setCDesc] = useState('');
  const [cColumn, setCColumn] = useState<number | null>(null);
  const [cPriority, setCPriority] = useState('media');
  const [cResponsavel, setCResponsavel] = useState<number | null>(null);
  const [cDue, setCDue] = useState('');
  const [cParticipants, setCParticipants] = useState<number[]>([]);
  const [cAssets, setCAssets] = useState<number[]>([]);

  // Comment form
  const [comment, setComment] = useState('');

  // SSE
  const eventSourceRef = useRef<EventSource | null>(null);

  const showError = (err: any) => {
    setError(err.response?.data?.error || 'Erro na operação');
    setTimeout(() => setError(null), 5000);
  };

  const fetchProjects = async () => {
    setLoading(true);
    try {
      setProjects(await kanbanApi.listProjects());
      setUnread(await kanbanApi.unreadCount());
      setNotifs(await kanbanApi.listNotifications());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
    usersApi.list(0, 200).then((u) => setUsers(u.map((x) => ({ id: x.id, nome: x.nome })))).catch(() => {});
    assetsApi.list(0, 300).then((a) => setAssets(a.map((x) => ({ id: x.id, nome: x.nome })))).catch(() => {});
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  const connectSSE = () => {
    if (eventSourceRef.current) return;
    const token = localStorage.getItem('token');
    const es = new EventSource(`/api/v1/kanban/sse?token=${token}`);
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data && data.tipo) {
          fetchProjects();
          if (board) openBoard(board.project.id);
        }
      } catch { /* ping */ }
    };
    es.onerror = () => {
      es.close();
      eventSourceRef.current = null;
      setTimeout(connectSSE, 10000);
    };
    eventSourceRef.current = es;
  };

  useEffect(() => {
    connectSSE();
  }, []);

  const openBoard = async (projectId: number) => {
    setLoading(true);
    try {
      setBoard(await kanbanApi.getBoard(projectId));
    } catch (err) {
      showError(err);
    } finally {
      setLoading(false);
    }
  };

  const openCard = async (cardId: number) => {
    try {
      setCardDetail(await kanbanApi.getCard(cardId));
    } catch (err) {
      showError(err);
    }
  };

  const submitProject = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await kanbanApi.createProject({ titulo: pTitle, descricao: pDesc, participante_ids: pParticipants });
      setProjModal(false);
      fetchProjects();
    } catch (err) {
      showError(err);
    }
  };

  const openCardModal = (columnId: number) => {
    setCTitle('');
    setCDesc('');
    setCColumn(columnId);
    setCPriority('media');
    setCResponsavel(null);
    setCDue('');
    setCParticipants([]);
    setCAssets([]);
    setCardModal(true);
  };

  const submitCard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!board || !cColumn) return;
    try {
      await kanbanApi.createCard({
        project_id: board.project.id,
        column_id: cColumn,
        titulo: cTitle,
        descricao: cDesc || undefined,
        responsavel_id: cResponsavel ?? undefined,
        prioridade: cPriority,
        data_entrega: cDue || undefined,
        participante_ids: cParticipants,
        ativo_ids: cAssets,
      });
      setCardModal(false);
      openBoard(board.project.id);
    } catch (err) {
      showError(err);
    }
  };

  const moveCard = async (card: KanbanCard, column: KanbanColumn) => {
    if (card.column_id === column.id) return;
    try {
      await kanbanApi.moveCard(card.id, column.id, column.cards ? column.cards.length : 0);
      if (board) openBoard(board.project.id);
      if (cardDetail?.id === card.id) openCard(card.id);
    } catch (err) {
      showError(err);
    }
  };

  const submitComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cardDetail || !comment.trim()) return;
    try {
      await kanbanApi.addComment(cardDetail.id, comment);
      setComment('');
      openCard(cardDetail.id);
    } catch (err) {
      showError(err);
    }
  };

  const uploadFile = async (cardId: number, file: File) => {
    try {
      await kanbanApi.uploadAttachment(cardId, file);
      openCard(cardId);
    } catch (err) {
      showError(err);
    }
  };

  const addLink = async (cardId: number) => {
    const url = window.prompt('URL do link:');
    if (!url) return;
    const nome = window.prompt('Nome do link:') ?? url;
    try {
      await kanbanApi.uploadAttachment(cardId, undefined, url, nome);
      openCard(cardId);
    } catch (err) {
      showError(err);
    }
  };

  const deleteCard = async (card: KanbanCard) => {
    if (!window.confirm(`Excluir cartão "${card.titulo}"?`)) return;
    try {
      await kanbanApi.deleteCard(card.id);
      setCardDetail(null);
      if (board) openBoard(board.project.id);
    } catch (err) {
      showError(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0">Kanban</h1>
          <p className="text-brand-muted text-sm mt-1">Projetos e cartões de tarefas.</p>
        </div>
        <div className="flex items-center space-x-3">
          <button onClick={() => setProjModal(true)}
            className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs flex items-center space-x-1.5">
            <Plus size={16} />
            <span>Novo Projeto</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 border border-red-500/30 bg-red-500/5 text-red-400 text-xs font-mono flex items-center space-x-2">
          <ShieldAlert size={16} />
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <div className="p-12 text-center flex flex-col items-center justify-center space-y-4">
          <div className="w-8 h-8 border-2 border-brand-primary border-t-transparent animate-spin" />
          <span className="font-mono text-xs text-brand-muted uppercase">Carregando...</span>
        </div>
      )}

      {/* Board view */}
      {!loading && board && (
        <div>
          <div className="flex items-center space-x-3 mb-4">
            <button onClick={() => { setBoard(null); fetchProjects(); }}
              className="text-brand-muted hover:text-brand-text font-mono text-xs uppercase">← Projetos</button>
            <h2 className="text-xl font-bold font-mono uppercase tracking-wider text-brand-text m-0">{board.project.titulo}</h2>
            <span className="text-xs font-mono text-brand-muted">{board.total_cards} cartões · {board.board_progress}%</span>
          </div>

          <div className="flex gap-4 overflow-x-auto pb-4">
            {board.project.colunas?.map((col) => (
              <div key={col.id} className="min-w-64 w-64 border border-brand-border bg-brand-card flex flex-col">
                <div className="p-3 border-b border-brand-border flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5" style={{ backgroundColor: col.cor }} />
                    <span className="font-mono text-xs uppercase tracking-wider text-brand-text">{col.nome}</span>
                  </div>
                  <span className="text-xs font-mono text-brand-muted">{col.cards?.length ?? 0}</span>
                </div>
                <div className="p-2 space-y-2 flex-1">
                  {col.cards?.map((card) => (
                    <div key={card.id} className="border border-brand-border bg-brand-dark/30 p-3 cursor-pointer hover:border-brand-primary/50 transition-colors"
                      onClick={() => openCard(card.id)}>
                      <div className="text-sm text-brand-text font-medium">{card.titulo}</div>
                      <div className="flex items-center justify-between mt-2">
                        <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 border ${priorityColor[card.prioridade] ?? 'border-brand-border'}`}>
                          {card.prioridade}
                        </span>
                        {card.responsavel && (
                          <span className="text-xs font-mono text-brand-muted">{card.responsavel.nome.split(' ')[0]}</span>
                        )}
                      </div>
                    </div>
                  ))}
                  <button onClick={() => openCardModal(col.id)}
                    className="w-full text-center py-2 text-xs font-mono uppercase text-brand-muted hover:text-brand-primary border border-dashed border-brand-border hover:border-brand-primary/50">
                    + Cartão
                  </button>
                </div>
                {/* Move target */}
                {board.project.colunas && board.project.colunas.length > 1 && (
                  <div className="p-2 border-t border-brand-border/60">
                    <span className="text-[10px] font-mono uppercase text-brand-muted">Mover para cá: </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Projects list */}
      {!loading && !board && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((p) => (
            <div key={p.id} className="border border-brand-border bg-brand-card p-4 space-y-3 cursor-pointer hover:border-brand-primary/50"
              onClick={() => openBoard(p.id)}>
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-brand-text m-0">{p.titulo}</h3>
                {p.is_archived && (
                  <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 border border-brand-border text-brand-muted">Arquivado</span>
                )}
              </div>
              <p className="text-sm text-brand-muted m-0">{p.descricao ?? '—'}</p>
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-brand-muted">
                  {p.participantes?.length ?? 0} participantes · criado por {p.criador?.nome ?? '—'}
                </span>
                <Columns3 size={14} className="text-brand-primary" />
              </div>
            </div>
          ))}
          {projects.length === 0 && (
            <div className="col-span-3 p-12 text-center text-brand-muted font-mono text-sm">
              Nenhum projeto de Kanban.
            </div>
          )}
        </div>
      )}

      {/* Notifications */}
      <div className="border border-brand-border bg-brand-card">
        <div className="p-3 border-b border-brand-border flex items-center justify-between">
          <span className="text-xs font-mono uppercase tracking-wider text-brand-muted flex items-center">
            <Bell size={14} className="mr-2" /> Notificações {unread > 0 && `(${unread} não lidas)`}
          </span>
          <button onClick={async () => { await kanbanApi.markAllNotificationsRead(); fetchProjects(); }}
            className="text-xs font-mono uppercase text-brand-primary">Marcar lidas</button>
        </div>
        <div className="divide-y divide-brand-border/60 max-h-64 overflow-y-auto">
          {notifs.map((n) => (
            <div key={n.id} className={`p-3 text-sm ${n.lida ? '' : 'bg-brand-primary/5'}`}>
              <div className="flex justify-between">
                <span className="font-mono text-xs uppercase text-brand-primary">{n.titulo}</span>
                <span className="text-xs font-mono text-brand-muted">{new Date(n.created_at).toLocaleString('pt-BR')}</span>
              </div>
              <div className="text-brand-text mt-1">{n.mensagem}</div>
            </div>
          ))}
          {notifs.length === 0 && (
            <div className="p-6 text-center text-brand-muted font-mono text-xs">Nenhuma notificação.</div>
          )}
        </div>
      </div>

      {/* Project Modal */}
      {projModal && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg border border-brand-border bg-brand-card p-6 space-y-6">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">Novo Projeto</h3>
              <button onClick={() => setProjModal(false)} className="text-brand-muted hover:text-brand-text"><X size={20} /></button>
            </div>
            <form onSubmit={submitProject} className="space-y-4">
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Título *</label>
                <input type="text" required value={pTitle} onChange={(e) => setPTitle(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary" />
              </div>
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Descrição</label>
                <textarea value={pDesc} onChange={(e) => setPDesc(e.target.value)} rows={3}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Participantes</label>
                <div className="flex flex-wrap gap-2">
                  {users.map((u) => (
                    <label key={u.id} className="flex items-center space-x-1 text-xs font-mono text-brand-muted cursor-pointer">
                      <input type="checkbox" checked={pParticipants.includes(u.id)}
                        onChange={(e) => setPParticipants(e.target.checked ? [...pParticipants, u.id] : pParticipants.filter((x) => x !== u.id))}
                        className="accent-brand-primary" />
                      <span>{u.nome}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="flex justify-end space-x-3 pt-4 border-t border-brand-border">
                <button type="button" onClick={() => setProjModal(false)} className="border border-brand-border px-4 py-2 font-mono text-xs uppercase">Cancelar</button>
                <button type="submit" className="bg-brand-primary text-brand-dark font-bold font-mono px-4 py-2 uppercase text-xs">Criar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Card Modal (create) */}
      {cardModal && board && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg border border-brand-border bg-brand-card p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">Novo Cartão</h3>
              <button onClick={() => setCardModal(false)} className="text-brand-muted hover:text-brand-text"><X size={20} /></button>
            </div>
            <form onSubmit={submitCard} className="space-y-4">
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Título *</label>
                <input type="text" required value={cTitle} onChange={(e) => setCTitle(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Descrição</label>
                <textarea value={cDesc} onChange={(e) => setCDesc(e.target.value)} rows={3}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Prioridade</label>
                  <select value={cPriority} onChange={(e) => setCPriority(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                    {CARD_PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Responsável</label>
                  <select value={cResponsavel ?? ''} onChange={(e) => setCResponsavel(e.target.value ? Number(e.target.value) : null)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                    <option value="">—</option>
                    {users.map((u) => <option key={u.id} value={u.id}>{u.nome}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Data de entrega</label>
                <input type="date" value={cDue} onChange={(e) => setCDue(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Participantes</label>
                <div className="flex flex-wrap gap-2">
                  {users.map((u) => (
                    <label key={u.id} className="flex items-center space-x-1 text-xs font-mono text-brand-muted cursor-pointer">
                      <input type="checkbox" checked={cParticipants.includes(u.id)}
                        onChange={(e) => setCParticipants(e.target.checked ? [...cParticipants, u.id] : cParticipants.filter((x) => x !== u.id))}
                        className="accent-brand-primary" />
                      <span>{u.nome}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="flex justify-end space-x-3 pt-4 border-t border-brand-border">
                <button type="button" onClick={() => setCardModal(false)} className="border border-brand-border px-4 py-2 font-mono text-xs uppercase">Cancelar</button>
                <button type="submit" className="bg-brand-primary text-brand-dark font-bold font-mono px-4 py-2 uppercase text-xs">Criar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Card Detail Modal */}
      {cardDetail && board && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-2xl border border-brand-border bg-brand-card p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <div>
                <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">{cardDetail.titulo}</h3>
                <div className="flex items-center space-x-2 mt-1">
                  <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 border ${priorityColor[cardDetail.prioridade] ?? 'border-brand-border'}`}>
                    {cardDetail.prioridade}
                  </span>
                  <span className="text-xs font-mono text-brand-muted">{cardDetail.column?.nome ?? '—'}</span>
                  {cardDetail.responsavel && (
                    <span className="text-xs font-mono text-brand-muted">· {cardDetail.responsavel.nome}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button onClick={() => deleteCard(cardDetail)} className="text-red-400 border border-red-500/30 px-2 py-1.5">
                  <Trash2 size={14} />
                </button>
                <button onClick={() => setCardDetail(null)} className="text-brand-muted hover:text-brand-text"><X size={20} /></button>
              </div>
            </div>

            {/* Move to column */}
            <div>
              <span className="text-xs font-mono uppercase text-brand-muted">Mover para:</span>
              <div className="flex flex-wrap gap-2 mt-2">
                {board.project.colunas?.map((col) => (
                  <button key={col.id}
                    onClick={() => moveCard(cardDetail, col)}
                    disabled={col.id === cardDetail.column_id}
                    className={`px-3 py-1.5 text-xs font-mono uppercase border transition-colors ${
                      col.id === cardDetail.column_id
                        ? 'border-brand-primary/50 bg-brand-primary/10 text-brand-primary'
                        : 'border-brand-border text-brand-muted hover:text-brand-text hover:border-brand-primary/50'
                    }`}>
                    {col.nome}
                  </button>
                ))}
              </div>
            </div>

            <p className="text-sm text-brand-text whitespace-pre-wrap m-0">{cardDetail.descricao ?? 'Sem descrição.'}</p>

            {/* Attachments */}
            <div className="border border-brand-border">
              <div className="p-3 border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase text-brand-muted flex justify-between items-center">
                <span className="flex items-center"><Paperclip size={14} className="mr-2" /> Anexos ({cardDetail.anexos?.length ?? 0})</span>
                <span className="flex space-x-2">
                  <label className="cursor-pointer text-brand-primary">
                    Arquivo
                    <input type="file" className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) uploadFile(cardDetail.id, f);
                        e.target.value = '';
                      }} />
                  </label>
                  <button onClick={() => addLink(cardDetail.id)} className="text-brand-primary">Link</button>
                </span>
              </div>
              <div className="divide-y divide-brand-border/60">
                {cardDetail.anexos?.map((a) => (
                  <div key={a.id} className="p-3 flex justify-between items-center text-sm">
                    {a.tipo === 'imagem' ? (
                      <img src={a.url} alt={a.nome} className="h-16 object-cover border border-brand-border" />
                    ) : (
                      <a href={a.url} target="_blank" rel="noreferrer" className="text-brand-primary">{a.nome}</a>
                    )}
                    <button onClick={async () => {
                      if (!window.confirm('Excluir anexo?')) return;
                      await kanbanApi.deleteAttachment(a.id);
                      openCard(cardDetail.id);
                    }} className="text-red-400 border border-red-500/30 px-2 py-1">
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))}
                {(cardDetail.anexos ?? []).length === 0 && (
                  <div className="p-4 text-center text-brand-muted font-mono text-xs">Sem anexos.</div>
                )}
              </div>
            </div>

            {/* Interactions */}
            <div className="border border-brand-border">
              <div className="p-3 border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase text-brand-muted flex items-center">
                <MessageSquare size={14} className="mr-2" /> Comentários e atividades
              </div>
              <div className="divide-y divide-brand-border/60 max-h-48 overflow-y-auto">
                {cardDetail.interacoes?.map((i) => (
                  <div key={i.id} className="p-3 text-sm">
                    <div className="flex justify-between">
                      <span className="font-mono text-xs text-brand-primary">{i.usuario?.nome ?? '—'}</span>
                      <span className="text-xs font-mono text-brand-muted">{new Date(i.created_at).toLocaleString('pt-BR')}</span>
                    </div>
                    <div className={`text-brand-text mt-1 ${i.tipo !== 'comentario' ? 'italic text-brand-muted' : ''}`}>{i.mensagem}</div>
                  </div>
                ))}
                {(cardDetail.interacoes ?? []).length === 0 && (
                  <div className="p-4 text-center text-brand-muted font-mono text-xs">Sem atividades.</div>
                )}
              </div>
              <form onSubmit={submitComment} className="p-3 border-t border-brand-border flex space-x-2">
                <input type="text" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Comentar..."
                  className="flex-1 bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary" />
                <button type="submit" className="bg-brand-primary text-brand-dark font-bold font-mono px-4 uppercase text-xs">Enviar</button>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
