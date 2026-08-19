import React, { useEffect, useRef, useState } from 'react';
import { kanbanApi } from '../api/kanban';
import { usersApi } from '../api/users';
import { assetsApi } from '../api/assets';
import { toApiFileUrl } from '../api/client';
import type {
  KanbanProject,
  KanbanCard,
  KanbanColumn,
  KanbanNotification,
} from '../types/kanban';
import { CARD_PRIORITIES } from '../types/kanban';
import {
  Bell,
  CalendarDays,
  Columns3,
  Home,
  Info,
  MessageSquare,
  MoreHorizontal,
  Paperclip,
  Plus,
  Search,
  Settings,
  ShieldAlert,
  Star,
  Trash2,
  X,
} from 'lucide-react';

const columnPalette = ['#60A5FA', '#F59E0B', '#A78BFA', '#34D399', '#F87171', '#22D3EE'];
const priorityBadgeClass: Record<string, string> = {
  baixa: 'bg-[#61bd4f] text-white',
  media: 'bg-[#0079bf] text-white',
  alta: 'bg-[#ff9f1a] text-white',
  urgente: 'bg-[#eb5a46] text-white',
};

export const KanbanPage: React.FC = () => {
  const [projects, setProjects] = useState<KanbanProject[]>([]);
  const [board, setBoard] = useState<{ project: KanbanProject; board_progress: number; total_cards: number } | null>(null);
  const [cardDetail, setCardDetail] = useState<KanbanCard | null>(null);
  const [notifs, setNotifs] = useState<KanbanNotification[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [users, setUsers] = useState<{ id: number; nome: string }[]>([]);
  const [_assets, setAssets] = useState<{ id: number; nome: string }[]>([]);

  const [projModal, setProjModal] = useState(false);
  const [pTitle, setPTitle] = useState('');
  const [pDesc, setPDesc] = useState('');
  const [pParticipants, setPParticipants] = useState<number[]>([]);

  const [cardModal, setCardModal] = useState(false);
  const [cTitle, setCTitle] = useState('');
  const [cDesc, setCDesc] = useState('');
  const [cColumn, setCColumn] = useState<number | null>(null);
  const [cPriority, setCPriority] = useState('media');
  const [cResponsavel, setCResponsavel] = useState<number | null>(null);
  const [cDue, setCDue] = useState('');
  const [cParticipants, setCParticipants] = useState<number[]>([]);
  const [cAssets, setCAssets] = useState<number[]>([]);

  const [comment, setComment] = useState('');
  const [moveModal, setMoveModal] = useState<{ card: KanbanCard; column: KanbanColumn } | null>(null);
  const [mMotivo, setMMotivo] = useState('');

  const [columnModalOpen, setColumnModalOpen] = useState(false);
  const [editingColumn, setEditingColumn] = useState<KanbanColumn | null>(null);
  const [columnName, setColumnName] = useState('');
  const [columnColor, setColumnColor] = useState(columnPalette[0]);

  const eventSourceRef = useRef<EventSource | null>(null);

  const showError = (err: any) => {
    setError(err.response?.data?.error || 'Erro na operação');
    setTimeout(() => setError(null), 5000);
  };

  const formatDate = (date?: string) => {
    if (!date) return null;
    return new Date(date).toLocaleDateString('pt-BR');
  };

  const getInitials = (name?: string) => {
    if (!name) return '?';
    return name
      .split(' ')
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join('');
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
      } catch {
        // ping
      }
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
  }, [board]);

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

    const colName = column.nome.toLowerCase();
    const projName = board?.project.titulo?.toLowerCase() || '';
    const isMaintenance = colName.includes('manuten') || colName.includes('oficina') || colName.includes('reparo')
      || projName.includes('oficina') || projName.includes('manuten');

    if (isMaintenance) {
      setMMotivo('');
      setMoveModal({ card, column });
      return;
    }

    try {
      await kanbanApi.moveCard(card.id, column.id, column.cards ? column.cards.length : 0);
      if (board) openBoard(board.project.id);
      if (cardDetail?.id === card.id) openCard(card.id);
    } catch (err) {
      showError(err);
    }
  };

  const confirmMoveCard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!moveModal) return;
    try {
      await kanbanApi.moveCard(
        moveModal.card.id,
        moveModal.column.id,
        moveModal.column.cards ? moveModal.column.cards.length : 0,
        mMotivo,
      );
      setMoveModal(null);
      if (board) openBoard(board.project.id);
      if (cardDetail?.id === moveModal.card.id) openCard(moveModal.card.id);
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

  const openCreateColumnModal = () => {
    setEditingColumn(null);
    setColumnName('');
    setColumnColor(columnPalette[(board?.project.colunas?.length ?? 0) % columnPalette.length]);
    setColumnModalOpen(true);
  };

  const openEditColumnModal = (column: KanbanColumn) => {
    setEditingColumn(column);
    setColumnName(column.nome);
    setColumnColor(column.cor || columnPalette[0]);
    setColumnModalOpen(true);
  };

  const submitColumn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!board || !columnName.trim()) return;
    try {
      if (editingColumn) {
        await kanbanApi.updateColumn(editingColumn.id, { nome: columnName.trim(), cor: columnColor });
      } else {
        await kanbanApi.addColumn(board.project.id, columnName.trim(), columnColor);
      }
      setColumnModalOpen(false);
      setEditingColumn(null);
      setColumnName('');
      await openBoard(board.project.id);
    } catch (err) {
      showError(err);
    }
  };

  const selectedColumn = board?.project.colunas?.find((col) => col.id === cColumn) ?? null;

  return (
    <div className="space-y-6">
      {!board && (
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0">Kanban</h1>
          <p className="text-brand-muted text-sm mt-1">Projetos e cartões de tarefas.</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setProjModal(true)}
            className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs flex items-center space-x-1.5"
          >
            <Plus size={16} />
            <span>Novo Projeto</span>
          </button>
        </div>
      </div>
      )}

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

      {!loading && board && (
        <div className="relative -m-8 min-h-[calc(100vh-4rem)] overflow-hidden bg-[#7bb7df] text-[#172b4d]">
          <div className="absolute inset-x-72 top-16 h-[560px] rounded-full bg-white/10 blur-2xl" />
          <div className="absolute bottom-[-160px] right-[-80px] h-[420px] w-[520px] rounded-full bg-white/14 blur-xl" />

          <div className="relative z-10 flex h-10 items-center justify-between bg-[#51627d]/55 px-3 text-white backdrop-blur">
            <div className="flex items-center gap-1">
              <button className="grid h-8 w-8 place-items-center rounded bg-white/18 hover:bg-white/28" title="Início">
                <Home size={17} />
              </button>
              <button
                onClick={() => {
                  setBoard(null);
                  fetchProjects();
                }}
                className="inline-flex h-8 items-center gap-2 rounded bg-white/18 px-3 text-sm font-bold hover:bg-white/28"
              >
                <Columns3 size={16} />
                Projetos
              </button>
              <div className="ml-1 hidden h-8 w-52 items-center gap-2 rounded bg-white/18 px-3 md:flex">
                <Search size={15} />
                <span className="text-sm text-white/80">Buscar cartões</span>
              </div>
            </div>
            <div className="hidden items-center gap-1 text-lg font-semibold italic opacity-85 md:flex">
              <Columns3 size={18} />
              AssetTrack Board
            </div>
            <div className="flex items-center gap-1">
              <button onClick={openCreateColumnModal} className="grid h-8 w-8 place-items-center rounded bg-white/18 hover:bg-white/28" title="Nova coluna">
                <Plus size={18} />
              </button>
              <button className="grid h-8 w-8 place-items-center rounded bg-white/18 hover:bg-white/28" title="Informações">
                <Info size={17} />
              </button>
              <button className="grid h-8 w-8 place-items-center rounded bg-white/18 hover:bg-white/28" title="Configurações">
                <Settings size={17} />
              </button>
            </div>
          </div>

          <div className="relative z-10 flex h-14 items-center justify-between gap-3 bg-white/24 px-5 text-[#172b4d] backdrop-blur">
            <div className="flex min-w-0 items-center gap-2">
              <h2 className="truncate text-xl font-bold">{board.project.titulo}</h2>
              <button className="grid h-8 w-8 place-items-center rounded bg-white/28 hover:bg-white/45" title="Favoritar">
                <Star size={16} />
              </button>
              <span className="hidden h-8 items-center rounded bg-white/28 px-3 text-sm font-medium md:inline-flex">
                {board.total_cards} cartões
              </span>
              <span className="hidden h-8 items-center rounded bg-white/28 px-3 text-sm font-medium md:inline-flex">
                {board.board_progress}% progresso
              </span>
            </div>

            <div className="flex items-center gap-2">
              <div className="hidden -space-x-2 md:flex">
                {board.project.participantes?.slice(0, 5).map((participant) => (
                  <div
                    key={participant.id}
                    title={participant.nome}
                    className="grid h-8 w-8 place-items-center rounded-full border-2 border-white bg-[#0079bf] text-xs font-bold text-white shadow"
                  >
                    {getInitials(participant.nome)}
                  </div>
                ))}
              </div>
              <button className="hidden h-8 rounded bg-white/28 px-3 text-sm font-medium hover:bg-white/45 md:block">
                Convidar
              </button>
              <button
                onClick={openCreateColumnModal}
                className="inline-flex h-8 items-center gap-2 rounded bg-white/28 px-3 text-sm font-medium hover:bg-white/45"
              >
                <Plus size={15} />
                Lista
              </button>
            </div>
          </div>

          <div className="relative z-10 h-[calc(100vh-10.5rem)] overflow-x-auto overflow-y-hidden px-2 py-2">
            <div className="flex h-full items-start gap-2">
              {board.project.colunas?.map((col) => (
                <section
                  key={col.id}
                  className="max-h-full w-[320px] min-w-[320px] overflow-hidden rounded-[14px] border border-white/30 bg-white/30 text-[#172b4d] shadow-[0_8px_24px_rgba(15,23,42,0.14)] backdrop-blur-md"
                  style={{ backgroundColor: 'rgba(235, 236, 240, 0.72)' }}
                >
                  <div className="flex items-center justify-between border-b border-white/35 px-3 pb-2 pt-3">
                    <div className="flex min-w-0 items-center gap-2">
                      <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: col.cor }} />
                      <h3 className="truncate text-sm font-bold">{col.nome}</h3>
                      <span className="text-xs text-[#5e6c84]">{col.cards?.length ?? 0}</span>
                    </div>
                    <button
                      onClick={() => openEditColumnModal(col)}
                      className="grid h-8 w-8 place-items-center rounded text-[#5e6c84] hover:bg-[#dfe1e6] hover:text-[#172b4d]"
                      title="Editar coluna"
                    >
                      <MoreHorizontal size={18} />
                    </button>
                  </div>

                  <div className="max-h-[calc(100vh-14rem)] space-y-2 overflow-y-auto px-2 pb-2">
                    {col.cards?.map((card) => {
                      const coverImage = card.anexos?.find((attachment) => attachment.tipo === 'imagem');

                      return (
                      <article
                        key={card.id}
                        className="cursor-pointer overflow-hidden rounded-[12px] border border-white/80 bg-white text-[#172b4d] shadow-[0_2px_8px_rgba(9,30,66,0.16)] transition hover:-translate-y-0.5 hover:shadow-[0_10px_18px_rgba(9,30,66,0.18)]"
                        style={{ backgroundColor: '#ffffff', color: '#172b4d' }}
                        onClick={() => openCard(card.id)}
                      >
                        {coverImage && (
                          <div className="h-36 w-full overflow-hidden border-b border-[#e5e7eb] bg-[#dbeafe]">
                            <img
                              src={toApiFileUrl(coverImage.url)}
                              alt={coverImage.nome}
                              className="h-full w-full object-cover"
                            />
                          </div>
                        )}

                        <div className="p-3">
                        <div className="flex items-start justify-between gap-3">
                          <h4 className="line-clamp-3 text-[15px] font-semibold leading-5 text-[#172b4d]" style={{ color: '#172b4d' }}>{card.titulo}</h4>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              openCard(card.id);
                            }}
                            className="mt-0.5 text-[#6b778c] hover:text-[#172b4d]"
                            style={{ color: '#6b778c' }}
                          >
                            <MoreHorizontal size={16} />
                          </button>
                        </div>

                        {card.descricao && (
                          <p className="mt-2 line-clamp-3 text-sm font-medium text-[#334155]" style={{ color: '#334155' }}>{card.descricao}</p>
                        )}

                        <div className="mt-2 flex flex-wrap items-center gap-1.5">
                          <span className={`rounded px-2 py-0.5 text-xs font-bold leading-5 ${priorityBadgeClass[card.prioridade] ?? 'bg-[#b3bac5] text-white'}`}>
                            {card.prioridade}
                          </span>
                          {card.data_entrega && (
                            <span className="inline-flex items-center gap-1 rounded bg-[#fef3c7] px-2 py-0.5 text-xs font-semibold text-[#7c2d12]" style={{ color: '#7c2d12' }}>
                              <CalendarDays size={12} />
                              {formatDate(card.data_entrega)}
                            </span>
                          )}
                          {(card.anexos?.length ?? 0) > 0 && (
                            <span className="inline-flex items-center gap-1 rounded bg-[#e2e8f0] px-1.5 py-0.5 text-xs font-semibold text-[#334155]" style={{ color: '#334155' }}>
                              <Paperclip size={12} />
                              {card.anexos?.length}
                            </span>
                          )}
                        </div>

                        <div className="mt-3 flex items-center justify-between gap-3">
                          <div className="flex -space-x-2">
                            {card.participantes?.slice(0, 3).map((participant) => (
                              <div
                                key={participant.id}
                                title={participant.nome}
                                className="flex h-7 w-7 items-center justify-center rounded-full border-2 border-white bg-[#0079bf] text-[10px] font-bold text-white shadow-sm"
                              >
                                {getInitials(participant.nome)}
                              </div>
                            ))}
                          </div>
                          {card.responsavel && (
                            <div className="text-right">
                              <div className="text-[10px] font-bold uppercase text-[#475569]" style={{ color: '#475569' }}>Resp.</div>
                              <div className="text-xs font-bold text-[#172b4d]" style={{ color: '#172b4d' }}>{card.responsavel.nome.split(' ')[0]}</div>
                            </div>
                          )}
                        </div>
                        </div>
                      </article>
                      );
                    })}

                    <button
                      onClick={() => openCardModal(col.id)}
                      className="flex w-full items-center gap-2 rounded-[10px] px-3 py-2 text-left text-sm text-[#5e6c84] hover:bg-white/45 hover:text-[#172b4d]"
                    >
                      <Plus size={16} />
                      Adicionar outro cartão
                    </button>
                  </div>
                </section>
              ))}

              <button
                onClick={openCreateColumnModal}
                className="flex h-11 w-[280px] min-w-[280px] items-center gap-2 rounded bg-white/28 px-3 text-left text-sm font-medium text-white transition hover:bg-white/40"
              >
                <Plus size={17} />
                Adicionar outra lista
              </button>
            </div>
          </div>
        </div>
      )}

      {!loading && !board && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {projects.map((p) => (
            <div
              key={p.id}
              className="rounded-[24px] border border-white/10 bg-[linear-gradient(135deg,_rgba(15,23,42,0.92),_rgba(30,41,59,0.88))] p-5 shadow-[0_24px_60px_rgba(2,6,23,0.28)] cursor-pointer hover:border-brand-primary/40"
              onClick={() => openBoard(p.id)}
            >
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white m-0">{p.titulo}</h3>
                {p.is_archived && (
                  <span className="text-[10px] font-mono uppercase px-2 py-1 rounded-full border border-white/10 text-slate-300">Arquivado</span>
                )}
              </div>
              <p className="mt-3 text-sm text-slate-300">{p.descricao ?? 'Sem descrição informada.'}</p>
              <div className="mt-5 flex items-center justify-between">
                <span className="text-xs font-mono text-slate-400">
                  {p.participantes?.length ?? 0} participantes
                </span>
                <Columns3 size={16} className="text-brand-primary" />
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

      {!board && (
      <div className="border border-brand-border bg-brand-card rounded-2xl overflow-hidden">
        <div className="p-3 border-b border-brand-border flex items-center justify-between">
          <span className="text-xs font-mono uppercase tracking-wider text-brand-muted flex items-center">
            <Bell size={14} className="mr-2" /> Notificações {unread > 0 && `(${unread} não lidas)`}
          </span>
          <button
            onClick={async () => {
              await kanbanApi.markAllNotificationsRead();
              fetchProjects();
            }}
            className="text-xs font-mono uppercase text-brand-primary"
          >
            Marcar lidas
          </button>
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
      )}

      {projModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded bg-[#f4f5f7] p-5 text-[#172b4d] shadow-[0_18px_64px_rgba(9,30,66,0.38)]">
            <div className="flex justify-between items-center border-b border-[#dfe1e6] pb-3">
              <h3 className="text-base font-bold">Novo projeto</h3>
              <button onClick={() => setProjModal(false)} className="grid h-8 w-8 place-items-center rounded text-[#5e6c84] hover:bg-[#dfe1e6] hover:text-[#172b4d]"><X size={20} /></button>
            </div>
            <form onSubmit={submitProject} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-bold uppercase text-[#5e6c84]">Título *</label>
                <input
                  type="text"
                  required
                  value={pTitle}
                  onChange={(e) => setPTitle(e.target.value)}
                  className="w-full rounded border border-[#dfe1e6] bg-white px-3 py-2 text-sm text-[#172b4d] shadow-inner focus:border-[#0079bf] focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-bold uppercase text-[#5e6c84]">Descrição</label>
                <textarea
                  value={pDesc}
                  onChange={(e) => setPDesc(e.target.value)}
                  rows={3}
                  className="w-full rounded border border-[#dfe1e6] bg-white px-3 py-2 text-sm text-[#172b4d] shadow-inner focus:border-[#0079bf] focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-bold uppercase text-[#5e6c84]">Participantes</label>
                <div className="flex flex-wrap gap-2">
                  {users.map((u) => (
                    <label key={u.id} className="flex cursor-pointer items-center gap-1 rounded bg-white px-2 py-1 text-xs text-[#5e6c84]">
                      <input
                        type="checkbox"
                        checked={pParticipants.includes(u.id)}
                        onChange={(e) => setPParticipants(e.target.checked ? [...pParticipants, u.id] : pParticipants.filter((x) => x !== u.id))}
                        className="accent-brand-primary"
                      />
                      <span>{u.nome}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="flex justify-end space-x-3 pt-4 border-t border-[#dfe1e6]">
                <button type="button" onClick={() => setProjModal(false)} className="rounded px-4 py-2 text-sm font-medium text-[#5e6c84] hover:bg-[#dfe1e6]">Cancelar</button>
                <button type="submit" className="rounded bg-[#0079bf] px-4 py-2 text-sm font-bold text-white hover:bg-[#026aa7]">Criar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {columnModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4 backdrop-blur-sm">
          <div
            className="w-full max-w-xl overflow-hidden rounded bg-[#f4f5f7] p-0 text-[#172b4d] shadow-[0_18px_64px_rgba(9,30,66,0.38)]"
            style={{ backgroundColor: '#f4f5f7', color: '#172b4d' }}
          >
            <div className="border-b border-[#dfe1e6] bg-white px-5 py-4" style={{ backgroundColor: '#ffffff' }}>
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">
                    {editingColumn ? 'Editar lista' : 'Nova lista'}
                  </div>
                  <h3 className="mt-1 text-xl font-bold text-[#172b4d]">
                    {editingColumn ? `Ajustar ${editingColumn.nome}` : 'Criar uma nova coluna no quadro'}
                  </h3>
                  {board && (
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <span className="rounded bg-[#ebecf0] px-2.5 py-1 text-xs font-semibold text-[#44546f]">
                        {board.project.titulo}
                      </span>
                      <span className="rounded bg-[#e6f4ff] px-2.5 py-1 text-xs font-semibold text-[#0052cc]">
                        {board.project.colunas?.length ?? 0} listas
                      </span>
                    </div>
                  )}
                </div>
                <button onClick={() => setColumnModalOpen(false)} className="grid h-8 w-8 place-items-center rounded text-[#5e6c84] hover:bg-[#dfe1e6] hover:text-[#172b4d]"><X size={20} /></button>
              </div>
            </div>
            <form onSubmit={submitColumn} className="space-y-4 p-5">
              <div className="rounded border border-[#dfe1e6] bg-white p-4 shadow-[0_1px_0_rgba(9,30,66,0.12)]" style={{ backgroundColor: '#ffffff' }}>
                <label className="mb-2 block text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Nome da lista</label>
                <input
                  type="text"
                  required
                  value={columnName}
                  onChange={(e) => setColumnName(e.target.value)}
                  placeholder="Ex: Em validacao, Bloqueado, Pronto para entrega"
                  className="w-full border-0 border-b border-[#d0d7de] bg-transparent px-0 py-2 text-lg font-semibold text-[#172b4d] placeholder:text-[#8c9bab] focus:border-[#0079bf] focus:outline-none"
                />

                <label className="mb-2 mt-5 block text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Cor de destaque</label>
                <div className="flex flex-wrap gap-3">
                  {columnPalette.map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setColumnColor(color)}
                      className={`h-10 w-10 rounded-[10px] border-2 shadow-sm transition ${columnColor === color ? 'border-[#172b4d] scale-105' : 'border-transparent opacity-85'}`}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>

              <div className="rounded border border-[#dfe1e6] bg-white p-4 shadow-[0_1px_0_rgba(9,30,66,0.12)]" style={{ backgroundColor: '#ffffff' }}>
                <div className="mb-3 text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Pré-visualização</div>
                <div
                  className="rounded-[14px] border border-white/40 p-3 shadow-[0_8px_24px_rgba(15,23,42,0.10)] backdrop-blur-sm"
                  style={{ backgroundColor: 'rgba(235, 236, 240, 0.72)' }}
                >
                  <div className="flex items-center justify-between border-b border-white/35 pb-2">
                    <div className="flex min-w-0 items-center gap-2">
                      <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: columnColor }} />
                      <span className="truncate text-sm font-bold text-[#172b4d]">{columnName || 'Nome da coluna'}</span>
                      <span className="text-xs text-[#5e6c84]">0</span>
                    </div>
                    <span className="text-xs text-[#5e6c84]">...</span>
                  </div>
                  <div className="mt-3 rounded-[10px] border border-[#dfe1e6] bg-white p-3 text-sm text-[#5e6c84] shadow-[0_2px_8px_rgba(9,30,66,0.10)]">
                    Cartoes desta lista aparecerao aqui
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-[#dfe1e6] pt-4">
                <div className="text-xs font-medium text-[#5e6c84]">
                  A lista sera adicionada ao fluxo atual do quadro.
                </div>
                <div className="flex justify-end space-x-3">
                  <button type="button" onClick={() => setColumnModalOpen(false)} className="rounded px-4 py-2 text-sm font-medium text-[#5e6c84] hover:bg-[#dfe1e6]">Cancelar</button>
                  <button type="submit" className="rounded bg-[#0079bf] px-4 py-2 text-sm font-bold text-white hover:bg-[#026aa7]">
                    {editingColumn ? 'Salvar lista' : 'Criar lista'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {cardModal && board && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4 backdrop-blur-sm">
          <div
            className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded bg-[#f4f5f7] p-0 text-[#172b4d] shadow-[0_18px_64px_rgba(9,30,66,0.38)]"
            style={{ backgroundColor: '#f4f5f7', color: '#172b4d' }}
          >
            <div className="border-b border-[#dfe1e6] bg-white px-5 py-4" style={{ backgroundColor: '#ffffff' }}>
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Novo cartao</div>
                  <h3 className="mt-1 text-xl font-bold text-[#172b4d]">
                    {selectedColumn ? `Adicionar em ${selectedColumn.nome}` : 'Criar cartao'}
                  </h3>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <span className="rounded bg-[#ebecf0] px-2.5 py-1 text-xs font-semibold text-[#44546f]">
                      {board.project.titulo}
                    </span>
                    {selectedColumn && (
                      <span
                        className="inline-flex items-center gap-2 rounded bg-[#e6f4ff] px-2.5 py-1 text-xs font-semibold text-[#0052cc]"
                        style={{ color: '#0052cc' }}
                      >
                        <span className="h-2 w-2 rounded-sm" style={{ backgroundColor: selectedColumn.cor }} />
                        {selectedColumn.nome}
                      </span>
                    )}
                  </div>
                </div>
                <button onClick={() => setCardModal(false)} className="grid h-8 w-8 place-items-center rounded text-[#5e6c84] hover:bg-[#dfe1e6] hover:text-[#172b4d]"><X size={20} /></button>
              </div>
            </div>
            <form onSubmit={submitCard} className="space-y-4 p-5">
              <div className="rounded border border-[#dfe1e6] bg-white p-4 shadow-[0_1px_0_rgba(9,30,66,0.12)]" style={{ backgroundColor: '#ffffff' }}>
                <label className="mb-2 block text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Titulo *</label>
                <input
                  type="text"
                  required
                  value={cTitle}
                  onChange={(e) => setCTitle(e.target.value)}
                  placeholder="Ex: Revisar notebook do financeiro"
                  className="w-full border-0 border-b border-[#d0d7de] bg-transparent px-0 py-2 text-lg font-semibold text-[#172b4d] placeholder:text-[#8c9bab] focus:border-[#0079bf] focus:outline-none"
                  style={{ color: '#172b4d' }}
                />

                <label className="mb-2 mt-5 block text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Descricao</label>
                <textarea
                  value={cDesc}
                  onChange={(e) => setCDesc(e.target.value)}
                  rows={4}
                  placeholder="Adicione contexto, sintomas, passos ou observacoes importantes."
                  className="w-full rounded border border-[#dfe1e6] bg-[#fafbfc] px-3 py-3 text-sm text-[#172b4d] placeholder:text-[#8c9bab] focus:border-[#0079bf] focus:bg-white focus:outline-none"
                  style={{ color: '#172b4d', backgroundColor: '#fafbfc' }}
                />
              </div>

              <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.2fr_0.8fr]">
                <div className="rounded border border-[#dfe1e6] bg-white p-4 shadow-[0_1px_0_rgba(9,30,66,0.12)]" style={{ backgroundColor: '#ffffff' }}>
                  <label className="mb-2 block text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Prioridade</label>
                  <div className="grid grid-cols-2 gap-2">
                    {CARD_PRIORITIES.map((priority) => {
                      const isActive = cPriority === priority;
                      return (
                        <button
                          key={priority}
                          type="button"
                          onClick={() => setCPriority(priority)}
                          className={`rounded border px-3 py-2 text-sm font-semibold capitalize transition ${
                            isActive
                              ? 'border-[#0079bf] bg-[#e6f4ff] text-[#0052cc]'
                              : 'border-[#dfe1e6] bg-white text-[#44546f] hover:border-[#b6c2cf] hover:bg-[#f7f8f9]'
                          }`}
                          style={{
                            color: isActive ? '#0052cc' : '#44546f',
                            backgroundColor: isActive ? '#e6f4ff' : '#ffffff',
                          }}
                        >
                          {priority}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="rounded border border-[#dfe1e6] bg-white p-4 shadow-[0_1px_0_rgba(9,30,66,0.12)]" style={{ backgroundColor: '#ffffff' }}>
                  <label className="mb-2 block text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Responsavel</label>
                  <select
                    value={cResponsavel ?? ''}
                    onChange={(e) => setCResponsavel(e.target.value ? Number(e.target.value) : null)}
                    className="w-full rounded border border-[#dfe1e6] bg-[#fafbfc] px-3 py-2.5 text-sm font-medium text-[#172b4d] focus:border-[#0079bf] focus:bg-white focus:outline-none"
                    style={{ color: '#172b4d', backgroundColor: '#fafbfc' }}
                  >
                    <option value="">Sem responsavel</option>
                    {users.map((u) => <option key={u.id} value={u.id}>{u.nome}</option>)}
                  </select>

                  <label className="mb-2 mt-4 block text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Data de entrega</label>
                  <input
                    type="date"
                    value={cDue}
                    onChange={(e) => setCDue(e.target.value)}
                    className="w-full rounded border border-[#dfe1e6] bg-[#fafbfc] px-3 py-2.5 text-sm font-medium text-[#172b4d] focus:border-[#0079bf] focus:bg-white focus:outline-none"
                    style={{ color: '#172b4d', backgroundColor: '#fafbfc' }}
                  />
                </div>
              </div>

              <div className="rounded border border-[#dfe1e6] bg-white p-4 shadow-[0_1px_0_rgba(9,30,66,0.12)]" style={{ backgroundColor: '#ffffff' }}>
                <label className="mb-3 block text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Participantes</label>
                <div className="flex flex-wrap gap-2">
                  {users.map((u) => {
                    const checked = cParticipants.includes(u.id);
                    return (
                      <label
                        key={u.id}
                        className={`flex cursor-pointer items-center gap-2 rounded border px-3 py-2 text-sm font-medium transition ${
                          checked
                            ? 'border-[#0079bf] bg-[#e6f4ff] text-[#0052cc]'
                            : 'border-[#dfe1e6] bg-[#fafbfc] text-[#44546f] hover:border-[#b6c2cf] hover:bg-white'
                        }`}
                        style={{
                          color: checked ? '#0052cc' : '#44546f',
                          backgroundColor: checked ? '#e6f4ff' : '#fafbfc',
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(e) => setCParticipants(e.target.checked ? [...cParticipants, u.id] : cParticipants.filter((x) => x !== u.id))}
                          className="accent-brand-primary"
                        />
                        <span>{u.nome}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-[#dfe1e6] pt-4">
                <div className="text-xs font-medium text-[#5e6c84]">
                  O cartao sera criado diretamente nesta lista.
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setCardModal(false)}
                    className="rounded border border-[#94a3b8] px-4 py-2 text-sm font-medium text-[#334155] hover:bg-[#dfe1e6]"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="rounded border border-[#2563eb] bg-[#bfdbfe] px-4 py-2 text-sm font-bold text-[#121212] hover:bg-[#93c5fd]"
                    style={{ color: '#121212' }}
                  >
                    Criar cartao
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {cardDetail && board && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4 backdrop-blur-sm">
          <div
            className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded bg-[#f4f5f7] p-5 text-[#172b4d] shadow-[0_18px_64px_rgba(9,30,66,0.38)]"
            style={{ backgroundColor: '#f4f5f7', color: '#172b4d' }}
          >
            <div className="flex justify-between items-center border-b border-[#dfe1e6] pb-3" style={{ color: '#172b4d' }}>
              <div>
                <h3 className="text-xl font-bold text-[#172b4d]" style={{ color: '#172b4d' }}>{cardDetail.titulo}</h3>
                <div className="flex items-center space-x-2 mt-1">
                  <span className={`rounded px-2 py-0.5 text-xs font-bold ${priorityBadgeClass[cardDetail.prioridade] ?? 'bg-[#b3bac5] text-white'}`}>
                    {cardDetail.prioridade}
                  </span>
                  <span className="text-xs font-semibold text-[#475569]" style={{ color: '#475569' }}>{cardDetail.column?.nome ?? '—'}</span>
                  {cardDetail.responsavel && (
                    <span className="text-xs font-semibold text-[#475569]" style={{ color: '#475569' }}>· {cardDetail.responsavel.nome}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button onClick={() => deleteCard(cardDetail)} className="text-red-400 border border-red-500/30 px-2 py-1.5">
                  <Trash2 size={14} />
                </button>
                <button onClick={() => setCardDetail(null)} className="grid h-8 w-8 place-items-center rounded text-[#5e6c84] hover:bg-[#dfe1e6] hover:text-[#172b4d]"><X size={20} /></button>
              </div>
            </div>

            <div style={{ color: '#172b4d' }}>
              <span className="text-xs font-bold uppercase text-[#475569]" style={{ color: '#475569' }}>Mover para:</span>
              <div className="flex flex-wrap gap-2 mt-2">
                {board.project.colunas?.map((col) => (
                  <button
                    key={col.id}
                    onClick={() => moveCard(cardDetail, col)}
                    disabled={col.id === cardDetail.column_id}
                    className={`px-3 py-1.5 text-xs font-mono uppercase border transition-colors ${
                      col.id === cardDetail.column_id
                        ? 'border-[#0079bf] bg-[#e6f4ff] text-[#0052cc]'
                        : 'border-[#dfe1e6] bg-white text-[#5e6c84] hover:border-[#0079bf] hover:text-[#172b4d]'
                    }`}
                    style={{
                      color: col.id === cardDetail.column_id ? '#0052cc' : '#334155',
                      backgroundColor: col.id === cardDetail.column_id ? '#e6f4ff' : '#ffffff',
                    }}
                  >
                    {col.nome}
                  </button>
                ))}
              </div>
            </div>

            <p
              className="m-0 rounded bg-white p-3 text-sm font-medium text-[#172b4d] shadow-[0_1px_0_rgba(9,30,66,0.25)] whitespace-pre-wrap"
              style={{ backgroundColor: '#ffffff', color: '#172b4d' }}
            >
              {cardDetail.descricao ?? 'Sem descrição.'}
            </p>

            <div className="overflow-hidden rounded border border-[#dfe1e6] bg-white" style={{ backgroundColor: '#ffffff', color: '#172b4d' }}>
              <div className="p-3 border-b border-[#dfe1e6] bg-[#ebecf0] text-xs font-bold uppercase text-[#475569] flex justify-between items-center" style={{ backgroundColor: '#ebecf0', color: '#475569' }}>
                <span className="flex items-center"><Paperclip size={14} className="mr-2" /> Anexos ({cardDetail.anexos?.length ?? 0})</span>
                <span className="flex space-x-2">
                  <label className="cursor-pointer text-[#0079bf]" style={{ color: '#0079bf' }}>
                    Arquivo
                    <input
                      type="file"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) uploadFile(cardDetail.id, f);
                        e.target.value = '';
                      }}
                    />
                  </label>
                  <button onClick={() => addLink(cardDetail.id)} className="text-[#0079bf]" style={{ color: '#0079bf' }}>Link</button>
                </span>
              </div>
              <div className="divide-y divide-[#dfe1e6]" style={{ color: '#172b4d' }}>
                {cardDetail.anexos?.map((a) => (
                  <div key={a.id} className="p-3 flex justify-between items-center text-sm" style={{ color: '#172b4d' }}>
                    {a.tipo === 'imagem' ? (
                      <img src={toApiFileUrl(a.url)} alt={a.nome} className="h-16 rounded object-cover border border-[#dfe1e6]" />
                    ) : (
                      <a href={toApiFileUrl(a.url)} target="_blank" rel="noreferrer" className="text-[#0079bf]" style={{ color: '#0079bf' }}>{a.nome}</a>
                    )}
                    <button
                      onClick={async () => {
                        if (!window.confirm('Excluir anexo?')) return;
                        await kanbanApi.deleteAttachment(a.id);
                        openCard(cardDetail.id);
                      }}
                      className="text-red-400 border border-red-500/30 px-2 py-1"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))}
                {(cardDetail.anexos ?? []).length === 0 && (
                  <div className="p-4 text-center text-xs font-medium text-[#475569]" style={{ color: '#475569' }}>Sem anexos.</div>
                )}
              </div>
            </div>

            <div className="overflow-hidden rounded border border-[#dfe1e6] bg-white" style={{ backgroundColor: '#ffffff', color: '#172b4d' }}>
              <div className="p-3 border-b border-[#dfe1e6] bg-[#ebecf0] text-xs font-bold uppercase text-[#475569] flex items-center" style={{ backgroundColor: '#ebecf0', color: '#475569' }}>
                <MessageSquare size={14} className="mr-2" /> Comentários e atividades
              </div>
              <div className="divide-y divide-[#dfe1e6] max-h-48 overflow-y-auto" style={{ color: '#172b4d' }}>
                {cardDetail.interacoes?.map((i) => (
                  <div key={i.id} className="p-3 text-sm" style={{ color: '#172b4d' }}>
                    <div className="flex justify-between">
                      <span className="text-xs font-bold text-[#0079bf]" style={{ color: '#0079bf' }}>{i.usuario?.nome ?? '—'}</span>
                      <span className="text-xs font-semibold text-[#475569]" style={{ color: '#475569' }}>{new Date(i.created_at).toLocaleString('pt-BR')}</span>
                    </div>
                    <div
                      className={`mt-1 font-medium ${i.tipo !== 'comentario' ? 'italic' : ''}`}
                      style={{ color: i.tipo !== 'comentario' ? '#475569' : '#172b4d' }}
                    >
                      {i.mensagem}
                    </div>
                  </div>
                ))}
                {(cardDetail.interacoes ?? []).length === 0 && (
                  <div className="p-4 text-center text-xs font-medium text-[#475569]" style={{ color: '#475569' }}>Sem atividades.</div>
                )}
              </div>
              <form onSubmit={submitComment} className="p-3 border-t border-[#dfe1e6] flex space-x-2">
                <input
                  type="text"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Comentar..."
                  className="flex-1 rounded border border-[#dfe1e6] bg-white px-3 py-2 text-sm font-medium text-[#172b4d] focus:border-[#0079bf] focus:outline-none"
                  style={{ backgroundColor: '#ffffff', color: '#172b4d' }}
                />
                <button type="submit" className="rounded bg-[#0079bf] px-4 text-sm font-bold text-white hover:bg-[#026aa7]" style={{ backgroundColor: '#0079bf', color: '#ffffff' }}>Enviar</button>
              </form>
            </div>
          </div>
        </div>
      )}

      {moveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded bg-[#f4f5f7] p-5 text-[#172b4d] shadow-[0_18px_64px_rgba(9,30,66,0.38)]">
            <div className="flex justify-between items-center border-b border-[#dfe1e6] pb-3">
              <h3 className="text-base font-bold">Mover para {moveModal.column.nome}</h3>
              <button onClick={() => setMoveModal(null)} className="grid h-8 w-8 place-items-center rounded text-[#5e6c84] hover:bg-[#dfe1e6] hover:text-[#172b4d]"><X size={20} /></button>
            </div>
            <form onSubmit={confirmMoveCard} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-bold uppercase text-[#5e6c84]">Descrição do Defeito / Motivo</label>
                <textarea required value={mMotivo} onChange={(e) => setMMotivo(e.target.value)} rows={4} placeholder="Informe o defeito ou motivo da manutenção..." className="w-full rounded border border-[#dfe1e6] bg-white px-3 py-2 text-sm text-[#172b4d] shadow-inner focus:border-[#0079bf] focus:outline-none" />
              </div>
              <div className="flex justify-end space-x-3 pt-4 border-t border-[#dfe1e6]">
                <button type="button" onClick={() => setMoveModal(null)} className="rounded px-4 py-2 text-sm font-medium text-[#5e6c84] hover:bg-[#dfe1e6]">Cancelar</button>
                <button type="submit" className="rounded bg-[#0079bf] px-4 py-2 text-sm font-bold text-white hover:bg-[#026aa7]">Confirmar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
