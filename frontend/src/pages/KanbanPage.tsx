import React, { useEffect, useRef, useState } from 'react';
import { kanbanApi } from '../api/kanban';
import { preventiveApi } from '../api/preventive';
import { procurementApi } from '../api/procurement';
import { usersApi } from '../api/users';
import { assetsApi } from '../api/assets';
import { toApiFileUrl } from '../api/client';
import { useAuthStore } from '../stores/authStore';
import type {
  KanbanProject,
  KanbanCard,
  KanbanChecklistItem,
  KanbanColumn,
  KanbanNotification,
} from '../types/kanban';
import type { MaintenancePlan, PMDashboard } from '../types/preventive';
import { CARD_PRIORITIES } from '../types/kanban';
import {
  Bell,
  CalendarDays,
  Copy,
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
  ShoppingCart,
  RefreshCw,
  Link as LinkIcon,
  CheckCircle2,
  ExternalLink,
  Globe
} from 'lucide-react';

const columnPalette = ['#60A5FA', '#F59E0B', '#A78BFA', '#34D399', '#F87171', '#22D3EE'];
const boardBackgroundPalette = ['#212121', '#0F172A', '#12304A', '#14532D', '#5B2333', '#3B1D78', '#6B3F12', '#334155'];
const defaultBoardBackgroundColor = '#212121';
const boardPatternOptions = [
  { value: 'glow', label: 'Glow' },
  { value: 'grid', label: 'Grid' },
  { value: 'dots', label: 'Dots' },
  { value: 'clean', label: 'Clean' },
] as const;
const defaultBoardPattern = 'glow';
const preventiveOrderIntentStorageKey = 'assettrack:preventive-order-intent';
const preventiveOrderDetailIntentStorageKey = 'assettrack:preventive-order-detail-intent';
const kanbanReturnIntentStorageKey = 'assettrack:kanban-return-intent';
const boardThemePresets = [
  { id: 'ops', name: 'Operações', color: '#12304A', pattern: 'grid', accent: '#60A5FA' },
  { id: 'executivo', name: 'Executivo', color: '#0F172A', pattern: 'clean', accent: '#F59E0B' },
  { id: 'suporte', name: 'Suporte', color: '#14532D', pattern: 'glow', accent: '#34D399' },
  { id: 'criativo', name: 'Criativo', color: '#3B1D78', pattern: 'dots', accent: '#A78BFA' },
] as const;
const getDomainName = (url: string) => {
  try {
    const parsed = new URL(url);
    return parsed.hostname.replace(/^www\./, '');
  } catch {
    return 'Loja / Site';
  }
};

const priorityBadgeClass: Record<string, string> = {
  baixa: 'bg-[#61bd4f] text-white',
  media: 'bg-[#0079bf] text-white',
  alta: 'bg-[#ff9f1a] text-white',
  urgente: 'bg-[#eb5a46] text-white',
};

export const KanbanPage: React.FC = () => {
  const currentUser = useAuthStore((state) => state.user);
  const userRole = currentUser?.role?.toLowerCase() || '';
  const isStaff = ['admin', 'gerente_ti', 'gerente_infra', 'tecnico'].includes(userRole);
  const [projects, setProjects] = useState<KanbanProject[]>([]);
  const [board, setBoard] = useState<{ project: KanbanProject; board_progress: number; total_cards: number } | null>(null);
  const [cardDetail, setCardDetail] = useState<KanbanCard | null>(null);
  const [notifs, setNotifs] = useState<KanbanNotification[]>([]);
  const [unread, setUnread] = useState(0);
  const [notifFilter, setNotifFilter] = useState<'todas' | 'nao_lidas'>('todas');
  const [notifStatusMessage, setNotifStatusMessage] = useState<string | null>(null);
  const [highlightedNotificationIds, setHighlightedNotificationIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [users, setUsers] = useState<{ id: number; nome: string }[]>([]);
  const [_assets, setAssets] = useState<{ id: number; nome: string }[]>([]);

  const [projModal, setProjModal] = useState(false);
  const [editingProject, setEditingProject] = useState<KanbanProject | null>(null);
  const [pTitle, setPTitle] = useState('');
  const [pDesc, setPDesc] = useState('');
  const [pParticipants, setPParticipants] = useState<number[]>([]);
  const [pBoardColor, setPBoardColor] = useState(defaultBoardBackgroundColor);
  const [pBoardPattern, setPBoardPattern] = useState<(typeof boardPatternOptions)[number]['value']>(defaultBoardPattern);
  const [pRelatedToMaintenance, setPRelatedToMaintenance] = useState(false);
  const [pRelatedToPreventive, setPRelatedToPreventive] = useState(false);
  const [pPreventivePlanId, setPPreventivePlanId] = useState<number | null>(null);
  const [boardInfoOpen, setBoardInfoOpen] = useState(false);
  const [boardSearchQuery, setBoardSearchQuery] = useState('');
  const [boardPriorityFilter, setBoardPriorityFilter] = useState<string>('todos');
  const [boardResponsibleFilter, setBoardResponsibleFilter] = useState<string>('todos');

  const [cardModal, setCardModal] = useState(false);
  const [cTitle, setCTitle] = useState('');
  const [cDesc, setCDesc] = useState('');
  const [cColumn, setCColumn] = useState<number | null>(null);
  const [cPriority, setCPriority] = useState('media');
  const [cResponsavel, setCResponsavel] = useState<number | null>(null);
  const [cDue, setCDue] = useState('');
  const [cParticipants, setCParticipants] = useState<number[]>([]);
  const [cAssets, setCAssets] = useState<number[]>([]);
  const [cChecklistItems, setCChecklistItems] = useState<KanbanChecklistItem[]>([]);

  const [comment, setComment] = useState('');
  const [moveModal, setMoveModal] = useState<{ card: KanbanCard; column: KanbanColumn; ordem: number } | null>(null);
  const [mMotivo, setMMotivo] = useState('');

  // Purchase request modal for Kanban cards (especially "Aguardando Compras")
  const [kanbanPurchaseModal, setKanbanPurchaseModal] = useState<{
    card: KanbanCard;
    column?: KanbanColumn;
    ordem?: number;
  } | null>(null);
  const [kProductName, setKProductName] = useState('');
  const [kProductLink, setKProductLink] = useState('');
  const [kProductQty, setKProductQty] = useState<number>(1);
  const [kProductEstimatedCost, setKProductEstimatedCost] = useState<string>('');
  const [kProductJustification, setKProductJustification] = useState('');
  const [kProductItemType, setKProductItemType] = useState('Consumo');
  const [kPurchaseSubmitting, setKPurchaseSubmitting] = useState(false);
  const [kPurchaseSuccess, setKPurchaseSuccess] = useState<string | null>(null);

  const [activeDragCardId, setActiveDragCardId] = useState<number | null>(null);
  const [dragOverTarget, setDragOverTarget] = useState<{ columnId: number; index: number } | null>(null);

  const [columnModalOpen, setColumnModalOpen] = useState(false);
  const [editingColumn, setEditingColumn] = useState<KanbanColumn | null>(null);
  const [columnName, setColumnName] = useState('');
  const [columnColor, setColumnColor] = useState(columnPalette[0]);
  const [preventiveSummary, setPreventiveSummary] = useState<PMDashboard | null>(null);
  const [preventivePlans, setPreventivePlans] = useState<MaintenancePlan[]>([]);

  const eventSourceRef = useRef<EventSource | null>(null);
  const notificationsRef = useRef<KanbanNotification[]>([]);
  const boardRef = useRef<{ project: KanbanProject; board_progress: number; total_cards: number } | null>(null);

  const showError = (err: any) => {
    setError(err.response?.data?.error || 'Erro na operação');
    setTimeout(() => setError(null), 5000);
  };

  const openPreventiveOrder = (context?: { planId?: number | null; assetId?: number | null; sourceCardId?: number | null }) => {
    const payload = {
      planId: context?.planId ?? null,
      assetId: context?.assetId ?? null,
      sourceProjectId: board?.project.id ?? null,
      sourceProjectTitle: board?.project.titulo ?? null,
      sourceCardId: context?.sourceCardId ?? null,
      sourceCardTitle: cardDetail?.titulo ?? null,
      createdAt: Date.now(),
    };

    sessionStorage.setItem(preventiveOrderIntentStorageKey, JSON.stringify(payload));

    const params = new URLSearchParams({ openOrder: '1' });
    if (payload.planId) params.set('planId', String(payload.planId));
    if (payload.assetId) params.set('assetId', String(payload.assetId));
    if (payload.sourceProjectId) params.set('sourceProjectId', String(payload.sourceProjectId));
    if (payload.sourceCardId) params.set('sourceCardId', String(payload.sourceCardId));

    window.location.assign(`/manutencao-preventiva?${params.toString()}`);
  };

  const openPreventiveOrderDetail = (orderId: number) => {
    const payload = {
      orderId,
      sourceProjectId: board?.project.id ?? null,
      sourceProjectTitle: board?.project.titulo ?? null,
      sourceCardId: cardDetail?.id ?? null,
      sourceCardTitle: cardDetail?.titulo ?? null,
      createdAt: Date.now(),
    };

    sessionStorage.setItem(preventiveOrderDetailIntentStorageKey, JSON.stringify(payload));

    const params = new URLSearchParams({
      openDetail: '1',
      orderId: String(orderId),
    });
    if (payload.sourceProjectId) params.set('sourceProjectId', String(payload.sourceProjectId));
    if (payload.sourceCardId) params.set('sourceCardId', String(payload.sourceCardId));

    window.location.assign(`/manutencao-preventiva?${params.toString()}`);
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

  const createChecklistItem = (titulo = ''): KanbanChecklistItem => ({
    id: `checklist-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    titulo,
    concluido: false,
  });

  const parseChecklistItems = (card?: Pick<KanbanCard, 'checklist_json'> | null): KanbanChecklistItem[] => {
    if (!card?.checklist_json) return [];
    try {
      const parsed = JSON.parse(card.checklist_json) as Array<Partial<KanbanChecklistItem>>;
      return parsed
        .map((item, index) => ({
          id: String(item.id || `checklist-${index + 1}`),
          titulo: String(item.titulo || '').trim(),
          concluido: Boolean(item.concluido),
        }))
        .filter((item) => item.titulo);
    } catch {
      return [];
    }
  };

  const normalizeBoardColor = (color?: string) => {
    const value = (color || '').trim();
    return /^#[0-9A-Fa-f]{6}$/.test(value) ? value.toUpperCase() : defaultBoardBackgroundColor;
  };

  const hexToRgba = (hex: string, alpha: number) => {
    const normalized = normalizeBoardColor(hex).replace('#', '');
    const r = parseInt(normalized.slice(0, 2), 16);
    const g = parseInt(normalized.slice(2, 4), 16);
    const b = parseInt(normalized.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  };

  const normalizeBoardPattern = (pattern?: string) => (
    boardPatternOptions.some((option) => option.value === pattern)
      ? pattern
      : defaultBoardPattern
  ) as (typeof boardPatternOptions)[number]['value'];

  const getBoardPatternStyle = (color?: string, pattern?: string): React.CSSProperties => {
    const normalizedColor = normalizeBoardColor(color);
    const selectedPattern = normalizeBoardPattern(pattern);

    if (selectedPattern === 'grid') {
      return {
        backgroundColor: normalizedColor,
        backgroundImage: `
          linear-gradient(${hexToRgba('#FFFFFF', 0.08)} 1px, transparent 1px),
          linear-gradient(90deg, ${hexToRgba('#FFFFFF', 0.08)} 1px, transparent 1px)
        `,
        backgroundSize: '28px 28px',
      };
    }

    if (selectedPattern === 'dots') {
      return {
        backgroundColor: normalizedColor,
        backgroundImage: `radial-gradient(${hexToRgba('#FFFFFF', 0.18)} 1.3px, transparent 1.3px)`,
        backgroundSize: '22px 22px',
      };
    }

    return { backgroundColor: normalizedColor };
  };

  const getBoardPreviewShellStyle = (color?: string, pattern?: string): React.CSSProperties => ({
    ...getBoardPatternStyle(color, pattern),
    boxShadow: `0 24px 48px ${hexToRgba(color || defaultBoardBackgroundColor, 0.28)}`,
  });

  const getNotificationTone = (type: string) => {
    if (type.includes('ATRIBUIDO')) return 'bg-[#e6f4ff] text-[#0052cc]';
    if (type.includes('MOVIMENTADO')) return 'bg-[#fff7ed] text-[#c2410c]';
    if (type.includes('ANEXO')) return 'bg-[#eef2ff] text-[#4338ca]';
    if (type.includes('PROJETO')) return 'bg-[#ecfdf5] text-[#047857]';
    return 'bg-[#f1f5f9] text-[#334155]';
  };

  const groupNotificationsByDate = (items: KanbanNotification[]) => {
    const now = new Date();
    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const startOfWeek = startOfToday - 6 * 24 * 60 * 60 * 1000;

    const groups: Array<{ label: string; items: KanbanNotification[] }> = [];
    const todayItems = items.filter((item) => new Date(item.created_at).getTime() >= startOfToday);
    const weekItems = items.filter((item) => {
      const timestamp = new Date(item.created_at).getTime();
      return timestamp < startOfToday && timestamp >= startOfWeek;
    });
    const olderItems = items.filter((item) => new Date(item.created_at).getTime() < startOfWeek);

    if (todayItems.length > 0) groups.push({ label: 'Hoje', items: todayItems });
    if (weekItems.length > 0) groups.push({ label: 'Esta semana', items: weekItems });
    if (olderItems.length > 0) groups.push({ label: 'Anteriores', items: olderItems });

    return groups;
  };

  const getBoardFiltersStorageKey = (projectId: number) => {
    const userId = currentUser?.id ?? 'anon';
    return `assettrack-kanban-filters:${userId}:${projectId}`;
  };

  const cardMatchesBoardFilters = (card: KanbanCard) => {
    const query = boardSearchQuery.trim().toLowerCase();
    const matchesQuery = !query
      || card.titulo.toLowerCase().includes(query)
      || card.descricao?.toLowerCase().includes(query);
    const matchesPriority = boardPriorityFilter === 'todos' || card.prioridade === boardPriorityFilter;
    const matchesResponsible = boardResponsibleFilter === 'todos'
      || String(card.responsavel?.id ?? card.responsavel_id ?? '') === boardResponsibleFilter;

    return matchesQuery && matchesPriority && matchesResponsible;
  };

  const resetProjectForm = () => {
    setEditingProject(null);
    setPTitle('');
    setPDesc('');
    setPParticipants([]);
    setPBoardColor(defaultBoardBackgroundColor);
    setPBoardPattern(defaultBoardPattern);
    setPRelatedToMaintenance(false);
    setPRelatedToPreventive(false);
    setPPreventivePlanId(null);
  };

  const applyBoardThemePreset = (preset: (typeof boardThemePresets)[number]) => {
    setPBoardColor(preset.color);
    setPBoardPattern(preset.pattern);
  };

  const openCreateProjectModal = () => {
    resetProjectForm();
    setProjModal(true);
  };

  const openEditProjectModal = (project: KanbanProject) => {
    setEditingProject(project);
    setPTitle(project.titulo || '');
    setPDesc(project.descricao || '');
    setPParticipants(project.participantes?.map((participant) => participant.id) ?? []);
    setPBoardColor(normalizeBoardColor(project.board_background_color));
    setPBoardPattern(normalizeBoardPattern(project.board_pattern));
    setPRelatedToMaintenance(Boolean(project.related_to_maintenance));
    setPRelatedToPreventive(Boolean(project.related_to_preventive));
    setPPreventivePlanId(project.preventive_plan_id ?? null);
    setProjModal(true);
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

  const refreshNotificationsState = async (options?: { highlightNew?: boolean; statusMessage?: string }) => {
    const [projectList, unreadCount, nextNotifications] = await Promise.all([
      kanbanApi.listProjects(),
      kanbanApi.unreadCount(),
      kanbanApi.listNotifications(),
    ]);

    setProjects(projectList);
    setUnread(unreadCount);
    setNotifs(nextNotifications);

    const previousIds = new Set(notificationsRef.current.map((item) => item.id));
    const newNotificationIds = nextNotifications
      .filter((item) => !previousIds.has(item.id))
      .map((item) => item.id);

    if (options?.highlightNew && newNotificationIds.length > 0) {
      setHighlightedNotificationIds((current) => Array.from(new Set([...newNotificationIds, ...current])));
      setNotifStatusMessage(
        options.statusMessage
        ?? `${newNotificationIds.length} nova${newNotificationIds.length > 1 ? 's' : ''} notifica${newNotificationIds.length > 1 ? 'ções' : 'ção'} recebida${newNotificationIds.length > 1 ? 's' : ''}.`,
      );
    }

    const activeBoardId = boardRef.current?.project.id;
    if (activeBoardId) {
      setBoard(await kanbanApi.getBoard(activeBoardId));
    }
  };

  useEffect(() => {
    fetchProjects();
    usersApi.list(0, 200).then((u) => setUsers(u.map((x) => ({ id: x.id, nome: x.nome })))).catch(() => {});
    assetsApi.list(0, 300).then((a) => setAssets(a.map((x) => ({ id: x.id, nome: x.nome })))).catch(() => {});
    preventiveApi.listPlans().then(setPreventivePlans).catch(() => {});
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  useEffect(() => {
    notificationsRef.current = notifs;
  }, [notifs]);

  useEffect(() => {
    boardRef.current = board;
  }, [board]);

  const connectSSE = () => {
    if (eventSourceRef.current) return;
    const token = localStorage.getItem('token');
    const es = new EventSource(`/api/v1/kanban/sse?token=${token}`);

    const handleRealtimeEvent = (e: MessageEvent<string>) => {
      try {
        const data = JSON.parse(e.data);
        if (data && data.tipo) {
          void refreshNotificationsState({
            highlightNew: true,
            statusMessage: data.mensagem ? `Atualização recebida: ${data.mensagem}` : undefined,
          });
        }
      } catch {
        // ping
      }
    };

    es.onmessage = handleRealtimeEvent;
    es.addEventListener('kanban_update', handleRealtimeEvent as EventListener);
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

  useEffect(() => {
    if (!notifStatusMessage) return;

    const timeout = window.setTimeout(() => setNotifStatusMessage(null), 2800);
    return () => window.clearTimeout(timeout);
  }, [notifStatusMessage]);

  useEffect(() => {
    if (highlightedNotificationIds.length === 0) return;

    const timeout = window.setTimeout(() => setHighlightedNotificationIds([]), 4200);
    return () => window.clearTimeout(timeout);
  }, [highlightedNotificationIds]);

  useEffect(() => {
    if (!board?.project?.id) return;

    const storageKey = getBoardFiltersStorageKey(board.project.id);
    const savedFilters = localStorage.getItem(storageKey);
    if (!savedFilters) {
      setBoardSearchQuery('');
      setBoardPriorityFilter('todos');
      setBoardResponsibleFilter('todos');
      return;
    }

    try {
      const parsed = JSON.parse(savedFilters) as {
        search?: string;
        priority?: string;
        responsible?: string;
      };
      setBoardSearchQuery(parsed.search ?? '');
      setBoardPriorityFilter(parsed.priority ?? 'todos');
      setBoardResponsibleFilter(parsed.responsible ?? 'todos');
    } catch {
      localStorage.removeItem(storageKey);
    }
  }, [board?.project?.id, currentUser?.id]);

  useEffect(() => {
    if (!board?.project?.id) return;

    localStorage.setItem(
      getBoardFiltersStorageKey(board.project.id),
      JSON.stringify({
        search: boardSearchQuery,
        priority: boardPriorityFilter,
        responsible: boardResponsibleFilter,
      }),
    );
  }, [board?.project?.id, boardSearchQuery, boardPriorityFilter, boardResponsibleFilter, currentUser?.id]);

  useEffect(() => {
    if (!board?.project?.related_to_preventive) {
      setPreventiveSummary(null);
      return;
    }

    preventiveApi.dashboard()
      .then(setPreventiveSummary)
      .catch(() => setPreventiveSummary(null));
  }, [board?.project?.id, board?.project?.related_to_preventive]);

  useEffect(() => {
    let cancelled = false;

    const restoreKanbanContext = async () => {
      const params = new URLSearchParams(window.location.search);
      const storedRaw = sessionStorage.getItem(kanbanReturnIntentStorageKey);

      let storedPayload: { projectId?: number | null; cardId?: number | null; createdAt?: number } | null = null;

      if (storedRaw) {
        try {
          const parsed = JSON.parse(storedRaw) as { projectId?: number | null; cardId?: number | null; createdAt?: number };
          if (parsed.createdAt && Date.now() - parsed.createdAt <= 120000) {
            storedPayload = parsed;
          } else {
            sessionStorage.removeItem(kanbanReturnIntentStorageKey);
          }
        } catch {
          sessionStorage.removeItem(kanbanReturnIntentStorageKey);
        }
      }

      const queryProjectId = Number(params.get('projectId') || '');
      const queryCardId = Number(params.get('cardId') || '');

      const projectId = storedPayload?.projectId ?? (Number.isFinite(queryProjectId) && queryProjectId > 0 ? queryProjectId : null);
      const cardId = storedPayload?.cardId ?? (Number.isFinite(queryCardId) && queryCardId > 0 ? queryCardId : null);

      if (!projectId && !cardId) return;

      try {
        if (projectId) {
          await openBoard(projectId);
        }

        if (!cancelled && cardId) {
          await openCard(cardId);
        }
      } finally {
        if (storedPayload) {
          window.setTimeout(() => {
            sessionStorage.removeItem(kanbanReturnIntentStorageKey);
          }, 2000);
        }

        if (params.has('projectId') || params.has('cardId')) {
          params.delete('projectId');
          params.delete('cardId');
          const cleaned = `${window.location.pathname}${params.toString() ? `?${params.toString()}` : ''}${window.location.hash}`;
          window.history.replaceState({}, '', cleaned);
        }
      }
    };

    void restoreKanbanContext();

    return () => {
      cancelled = true;
    };
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

  const openNotification = async (notification: KanbanNotification) => {
    try {
      if (!notification.lida) {
        await kanbanApi.markNotificationRead(notification.id);
        setNotifs((current) => current.map((item) => item.id === notification.id ? { ...item, lida: true } : item));
        setUnread((current) => Math.max(0, current - 1));
        setNotifStatusMessage('Notificação marcada como lida.');
      }

      if (notification.project_id) {
        await openBoard(notification.project_id);
      }

      if (notification.card_id) {
        await openCard(notification.card_id);
      }
    } catch (err) {
      showError(err);
    }
  };

  const markNotificationReadOnly = async (notification: KanbanNotification) => {
    if (notification.lida) return;

    try {
      await kanbanApi.markNotificationRead(notification.id);
      setNotifs((current) => current.map((item) => item.id === notification.id ? { ...item, lida: true } : item));
      setUnread((current) => Math.max(0, current - 1));
      setNotifStatusMessage('Notificação marcada como lida.');
    } catch (err) {
      showError(err);
    }
  };

  const submitProject = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        titulo: pTitle.trim(),
        descricao: pDesc.trim() || undefined,
        board_background_color: normalizeBoardColor(pBoardColor),
        board_pattern: normalizeBoardPattern(pBoardPattern),
        related_to_maintenance: pRelatedToMaintenance,
        related_to_preventive: pRelatedToPreventive,
        preventive_plan_id: pRelatedToPreventive ? (pPreventivePlanId ?? undefined) : undefined,
        participante_ids: pParticipants,
      };
      if (editingProject) {
        await kanbanApi.updateProject(editingProject.id, payload);
      } else {
        await kanbanApi.createProject(payload);
      }
      setProjModal(false);
      await fetchProjects();
      if (editingProject && board?.project.id === editingProject.id) {
        await openBoard(editingProject.id);
      }
      resetProjectForm();
    } catch (err) {
      showError(err);
    }
  };

  const duplicateProject = async (project: KanbanProject, openDuplicatedBoard = false) => {
    const incluirCartoes = window.confirm(
      `Deseja duplicar o projeto "${project.titulo}" com os cartões atuais?\n\n` +
      'Escolha "OK" para incluir os cartões ou "Cancelar" para copiar apenas a estrutura.',
    );

    try {
      const duplicated = await kanbanApi.duplicateProject(project.id, incluirCartoes);
      await fetchProjects();
      if (openDuplicatedBoard) {
        await openBoard(duplicated.id);
      }
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
    setCChecklistItems([]);
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
        checklist_items: cChecklistItems
          .map((item) => ({ ...item, titulo: item.titulo.trim() }))
          .filter((item) => item.titulo),
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

  const reorderBoardCards = (
    currentBoard: { project: KanbanProject; board_progress: number; total_cards: number },
    cardId: number,
    targetColumnId: number,
    targetIndex: number,
  ) => {
    const columns = currentBoard.project.colunas?.map((column) => ({
      ...column,
      cards: [...(column.cards ?? [])],
    })) ?? [];

    let draggedCard: KanbanCard | null = null;
    let sourceColumnId: number | null = null;
    let sourceIndex = -1;

    columns.forEach((column) => {
      const index = column.cards?.findIndex((card) => card.id === cardId) ?? -1;
      if (index >= 0 && column.cards) {
        draggedCard = column.cards[index];
        sourceColumnId = column.id;
        sourceIndex = index;
        column.cards.splice(index, 1);
      }
    });

    if (!draggedCard || sourceColumnId == null) {
      return currentBoard;
    }

    const destinationColumn = columns.find((column) => column.id === targetColumnId);
    if (!destinationColumn) {
      return currentBoard;
    }

    const normalizedIndex = Math.max(0, Math.min(targetIndex, destinationColumn.cards?.length ?? 0));
    const updatedCard: KanbanCard = {
      ...(draggedCard as KanbanCard),
      column_id: destinationColumn.id,
      ordem: normalizedIndex,
      column: destinationColumn,
    };

    if (sourceColumnId === targetColumnId && sourceIndex === normalizedIndex) {
      return currentBoard;
    }

    destinationColumn.cards?.splice(normalizedIndex, 0, updatedCard);

    const normalizedColumns = columns.map((column) => ({
      ...column,
      cards: (column.cards ?? []).map((card, index) => ({
        ...card,
        column_id: column.id,
        ordem: index,
      })),
    }));

    return {
      ...currentBoard,
      project: {
        ...currentBoard.project,
        colunas: normalizedColumns,
      },
    };
  };

  const moveCard = async (card: KanbanCard, column: KanbanColumn, ordem?: number) => {
    const targetOrder = ordem ?? (column.cards ? column.cards.length : 0);
    if (card.column_id === column.id && card.ordem === targetOrder) return;

    const colName = column.nome.toLowerCase();
    const projName = board?.project.titulo?.toLowerCase() || '';

    // Check if moving to "Aguardando Compras" or purchase-related column
    const isAguardandoCompras = colName.includes('compra') || colName.includes('aguardando compras') || colName.includes('suprimento');
    if (isAguardandoCompras) {
      setKProductName(card.titulo || '');
      setKProductLink('');
      setKProductQty(1);
      setKProductEstimatedCost('');
      setKProductJustification(`Solicitação de compra via Kanban Card #${card.id} - ${card.titulo}`);
      setKProductItemType('Consumo');
      setKPurchaseSuccess(null);
      setKanbanPurchaseModal({ card, column, ordem: targetOrder });
      return;
    }

    const isMaintenance = Boolean(board?.project.related_to_maintenance)
      || colName.includes('manuten') || colName.includes('oficina') || colName.includes('reparo')
      || projName.includes('oficina') || projName.includes('manuten');

    if (isMaintenance) {
      setMMotivo('');
      setMoveModal({ card, column, ordem: targetOrder });
      return;
    }

    const previousBoard = board;
    if (previousBoard) {
      setBoard(reorderBoardCards(previousBoard, card.id, column.id, targetOrder));
    }

    try {
      await kanbanApi.moveCard(card.id, column.id, targetOrder);
      if (board) openBoard(board.project.id);
      if (cardDetail?.id === card.id) openCard(card.id);
    } catch (err) {
      if (previousBoard) {
        setBoard(previousBoard);
      }
      showError(err);
    } finally {
      setActiveDragCardId(null);
      setDragOverTarget(null);
    }
  };

  const confirmKanbanPurchase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!kanbanPurchaseModal || !kProductName.trim()) return;

    try {
      setKPurchaseSubmitting(true);
      const estCost = kProductEstimatedCost ? Number(kProductEstimatedCost.replace(',', '.')) : 0;
      await procurementApi.kanbanPurchaseRequest(kanbanPurchaseModal.card.id, {
        nome_produto: kProductName.trim(),
        link_produto: kProductLink.trim() || undefined,
        quantidade: kProductQty > 0 ? kProductQty : 1,
        valor_estimado: isNaN(estCost) ? 0 : estCost,
        justificativa: kProductJustification.trim(),
        tipo_item: kProductItemType,
      });

      if (kanbanPurchaseModal.column) {
        await kanbanApi.moveCard(
          kanbanPurchaseModal.card.id,
          kanbanPurchaseModal.column.id,
          kanbanPurchaseModal.ordem ?? 0,
          `Movido para ${kanbanPurchaseModal.column.nome} - Solicitação de compra gerada: ${kProductName.trim()}`
        );
      }

      setKPurchaseSuccess('Solicitação de compra encaminhada com sucesso ao Comprador!');
      setTimeout(() => {
        setKanbanPurchaseModal(null);
        setKPurchaseSuccess(null);
        if (board) openBoard(board.project.id);
        if (cardDetail?.id === kanbanPurchaseModal.card.id) openCard(kanbanPurchaseModal.card.id);
      }, 1500);
    } catch (err: any) {
      showError(err);
    } finally {
      setKPurchaseSubmitting(false);
    }
  };

  const confirmMoveCard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!moveModal) return;
    try {
      await kanbanApi.moveCard(
        moveModal.card.id,
        moveModal.column.id,
        moveModal.ordem,
        mMotivo,
      );
      setMoveModal(null);
      if (board) openBoard(board.project.id);
      if (cardDetail?.id === moveModal.card.id) openCard(moveModal.card.id);
    } catch (err) {
      showError(err);
    }
  };

  const handleCardDragStart = (cardId: number) => {
    setActiveDragCardId(cardId);
  };

  const handleCardDragEnd = () => {
    setActiveDragCardId(null);
    setDragOverTarget(null);
  };

  const handleCardDrop = async (card: KanbanCard, column: KanbanColumn, index: number) => {
    await moveCard(card, column, index);
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

  const persistCardChecklist = async (card: KanbanCard, checklistItems: KanbanChecklistItem[]) => {
    try {
      await kanbanApi.updateCard(card.id, {
        titulo: card.titulo,
        descricao: card.descricao ?? '',
        checklist_items: checklistItems,
        column_id: card.column_id,
        responsavel_id: card.responsavel_id,
        prioridade: card.prioridade,
        data_entrega: card.data_entrega,
        participante_ids: card.participantes?.map((participant) => participant.id) ?? [],
        ativo_ids: card.ativos?.map((asset) => asset.id) ?? [],
      });
      await openCard(card.id);
      if (board) {
        await openBoard(board.project.id);
      }
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
  const boardColumnsCount = board?.project.colunas?.length ?? 0;
  const boardCardsCount = board?.project.colunas?.reduce((total, column) => total + (column.cards?.length ?? 0), 0) ?? 0;
  const boardParticipantsCount = board?.project.participantes?.length ?? 0;
  const boardThemeLabel = boardPatternOptions.find((option) => option.value === normalizeBoardPattern(board?.project.board_pattern))?.label ?? 'Glow';
  const boardRelatedToMaintenance = Boolean(board?.project.related_to_maintenance);
  const boardRelatedToPreventive = Boolean(board?.project.related_to_preventive);
  const boardFilteredCards = board?.project.colunas?.flatMap((column) => column.cards ?? []).filter(cardMatchesBoardFilters) ?? [];
  const isFilteringActive = Boolean(boardSearchQuery.trim()) || boardPriorityFilter !== 'todos' || boardResponsibleFilter !== 'todos';
  const visibleNotifications = notifs.filter((notification) => notifFilter === 'todas' || !notification.lida);
  const groupedNotifications = groupNotificationsByDate(visibleNotifications);
  const cardDetailChecklistItems = parseChecklistItems(cardDetail);
  const boardRecentActivity = [...(board?.project.colunas?.flatMap((column) => column.cards ?? []) ?? [])]
    .sort((a, b) => new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime())
    .slice(0, 6);

  return (
    <div className="min-h-[calc(100vh-12rem)] space-y-6">
      {notifStatusMessage && (
        <div className="pointer-events-none fixed right-5 top-20 z-[70] w-full max-w-sm">
          <div className="pointer-events-auto overflow-hidden rounded-2xl border border-[#bfdbfe] bg-white/95 shadow-[0_18px_48px_rgba(29,78,216,0.18)] backdrop-blur">
            <div className="flex items-start gap-3 px-4 py-3">
              <div className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[#dbeafe] text-[#1d4ed8]">
                <Bell size={16} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#1d4ed8]">
                  Notificações do kanban
                </div>
                <div className="mt-1 text-sm font-medium text-[#172b4d]">
                  {notifStatusMessage}
                </div>
                <div className="mt-2 text-xs text-[#64748b]">
                  {unread > 0 ? `${unread} pendente${unread > 1 ? 's' : ''} para revisar.` : 'Tudo sincronizado no momento.'}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setNotifStatusMessage(null)}
                className="grid h-8 w-8 shrink-0 place-items-center rounded-full text-[#64748b] transition hover:bg-[#eff6ff] hover:text-[#1d4ed8]"
                aria-label="Fechar aviso"
              >
                <X size={16} />
              </button>
            </div>
            <div className="h-1 w-full bg-[#dbeafe]">
              <div className="h-full w-full origin-left animate-[shrink-x_2.8s_linear_forwards] bg-[#2563eb]" />
            </div>
          </div>
        </div>
      )}

      {!board && (
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0">Kanban</h1>
          <p className="text-brand-muted text-sm mt-1">Projetos e cartões de tarefas.</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={openCreateProjectModal}
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
        <div
          className="relative -m-3 sm:-m-5 lg:-m-8 min-h-[calc(100dvh-4rem)] flex flex-col overflow-hidden text-[#172b4d]"
          style={getBoardPatternStyle(board.project.board_background_color, board.project.board_pattern)}
        >
          {normalizeBoardPattern(board.project.board_pattern) === 'glow' && (
            <>
              <div
                className="absolute inset-x-72 top-16 h-[560px] rounded-full blur-2xl"
                style={{ backgroundColor: hexToRgba(board.project.board_background_color || defaultBoardBackgroundColor, 0.24) }}
              />
              <div
                className="absolute bottom-[-160px] right-[-80px] h-[420px] w-[520px] rounded-full blur-xl"
                style={{ backgroundColor: hexToRgba(board.project.board_background_color || defaultBoardBackgroundColor, 0.32) }}
              />
            </>
          )}

          {/* Project Top Navigation Bar */}
          <div className="relative z-10 flex min-h-[44px] flex-wrap items-center justify-between bg-[#51627d]/90 px-3 sm:px-4 py-1 text-white backdrop-blur border-b border-white/15 gap-1.5">
            <div className="flex items-center gap-1.5 min-w-0">
              <button
                onClick={() => {
                  setBoard(null);
                  fetchProjects();
                }}
                className="grid h-8 w-8 place-items-center rounded bg-white/18 hover:bg-white/28 transition-colors shrink-0"
                title="Voltar aos Projetos"
              >
                <Home size={16} />
              </button>
              <button
                onClick={() => {
                  setBoard(null);
                  fetchProjects();
                }}
                className="inline-flex h-8 items-center gap-1.5 rounded bg-white/18 px-2.5 sm:px-3 text-xs sm:text-sm font-bold hover:bg-white/28 transition-colors shrink-0"
              >
                <Columns3 size={15} />
                <span>Projetos</span>
              </button>
              <label className="ml-1 hidden h-8 w-44 lg:w-56 items-center gap-2 rounded bg-white/18 px-3 md:flex">
                <Search size={14} />
                <input
                  value={boardSearchQuery}
                  onChange={(e) => setBoardSearchQuery(e.target.value)}
                  placeholder="Buscar cartões"
                  className="w-full bg-transparent text-xs sm:text-sm text-white placeholder:text-white/70 focus:outline-none"
                />
              </label>
              <span className="hidden rounded bg-white/12 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-white/80 md:inline-flex">
                {normalizeBoardPattern(board.project.board_pattern)}
              </span>
            </div>
            <div className="hidden items-center gap-1 text-sm lg:text-base font-semibold italic opacity-85 xl:flex">
              <Columns3 size={16} />
              <span>AssetTrack Board</span>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <button
                onClick={() => duplicateProject(board.project, true)}
                className="grid h-8 w-8 place-items-center rounded bg-white/18 hover:bg-white/28 transition-colors"
                title="Duplicar projeto"
              >
                <Copy size={15} />
              </button>
              <button onClick={openCreateColumnModal} className="grid h-8 w-8 place-items-center rounded bg-white/18 hover:bg-white/28 transition-colors" title="Nova coluna">
                <Plus size={17} />
              </button>
              <button
                onClick={() => setBoardInfoOpen(true)}
                className="grid h-8 w-8 place-items-center rounded bg-white/18 hover:bg-white/28 transition-colors"
                title="Informações"
              >
                <Info size={16} />
              </button>
              <button
                onClick={() => openEditProjectModal(board.project)}
                className="grid h-8 w-8 place-items-center rounded bg-white/18 hover:bg-white/28 transition-colors"
                title="Configurações"
              >
                <Settings size={16} />
              </button>
            </div>
          </div>

          {/* Project Title & Actions Bar */}
          <div className="relative z-10 flex min-h-[48px] flex-wrap items-center justify-between gap-2 bg-white/30 px-3 sm:px-5 py-1.5 text-[#172b4d] backdrop-blur border-b border-white/20">
            <div className="flex min-w-0 items-center gap-2">
              <h2 className="truncate text-base sm:text-lg font-bold">{board.project.titulo}</h2>
              <button className="grid h-7 w-7 place-items-center rounded bg-white/28 hover:bg-white/45 shrink-0" title="Favoritar">
                <Star size={14} />
              </button>
              <span className="hidden h-7 items-center rounded bg-white/28 px-2.5 text-xs font-medium md:inline-flex">
                {board.total_cards} cartões
              </span>
              <span className="hidden h-7 items-center rounded bg-white/28 px-2.5 text-xs font-medium md:inline-flex">
                {board.board_progress}% progresso
              </span>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <div className="hidden -space-x-2 md:flex">
                {board.project.participantes?.slice(0, 5).map((participant) => (
                  <div
                    key={participant.id}
                    title={participant.nome}
                    className="grid h-7 w-7 place-items-center rounded-full border-2 border-white bg-[#0079bf] text-[10px] font-bold text-white shadow"
                  >
                    {getInitials(participant.nome)}
                  </div>
                ))}
              </div>
              <button
                onClick={() => openEditProjectModal(board.project)}
                className="hidden h-7.5 rounded bg-white/28 px-2.5 text-xs font-medium hover:bg-white/45 md:block"
              >
                Personalizar
              </button>
              <button
                onClick={openCreateColumnModal}
                className="inline-flex h-7.5 items-center gap-1.5 rounded bg-white/28 px-2.5 text-xs font-medium hover:bg-white/45 transition-colors"
              >
                <Plus size={14} />
                <span>Coluna</span>
              </button>
            </div>
          </div>

          <div className="relative z-10 flex-1 h-[calc(100dvh-9.5rem)] overflow-x-auto overflow-y-hidden px-2 sm:px-3 py-2">
            <div
              className="flex h-full items-start gap-2.5 sm:gap-3 rounded-[8px] px-2 py-2"
              style={{ backgroundColor: hexToRgba(board.project.board_background_color || defaultBoardBackgroundColor, 0.18) }}
            >
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

                  <div
                    className="max-h-[calc(100vh-14rem)] space-y-2 overflow-y-auto px-2 pb-2"
                    onDragOver={(e) => {
                      e.preventDefault();
                      if (isFilteringActive) return;
                      setDragOverTarget({ columnId: col.id, index: col.cards?.length ?? 0 });
                    }}
                    onDrop={async (e) => {
                      e.preventDefault();
                      if (isFilteringActive) return;
                      if (!activeDragCardId) return;
                      const draggedCard = board.project.colunas?.flatMap((column) => column.cards ?? []).find((item) => item.id === activeDragCardId);
                      if (!draggedCard) return;
                      await handleCardDrop(draggedCard, col, dragOverTarget?.columnId === col.id ? dragOverTarget.index : (col.cards?.length ?? 0));
                    }}
                  >
                    {(!(col.cards?.filter(cardMatchesBoardFilters).length) && !isFilteringActive) && dragOverTarget?.columnId === col.id && dragOverTarget.index === 0 && (
                      <div className="rounded-[12px] border-2 border-dashed border-[#0079bf] bg-[#e6f4ff]/70 px-3 py-4 text-center text-sm font-semibold text-[#0052cc]">
                        Solte o cartão aqui
                      </div>
                    )}

                    {(col.cards ?? []).filter(cardMatchesBoardFilters).map((card, index, visibleCards) => {
                      const coverImage = card.anexos?.find((attachment) => attachment.tipo === 'imagem');
                      const linkAttachment = card.anexos?.find((attachment) => attachment.tipo === 'link' || attachment.url?.startsWith('http://') || attachment.url?.startsWith('https://'));
                      const descLinkMatch = (card.descricao || '').match(/https?:\/\/[^\s]+/i);
                      const productUrl = linkAttachment?.url || (descLinkMatch ? descLinkMatch[0] : null);

                      return (
                        <React.Fragment key={card.id}>
                          {dragOverTarget?.columnId === col.id && dragOverTarget.index === index && (
                            <div className="h-2 rounded-full bg-[#0079bf] shadow-[0_0_0_3px_rgba(0,121,191,0.18)]" />
                          )}
                          <article
                            draggable={!isFilteringActive}
                            onDragStart={(e) => {
                              if (isFilteringActive) return;
                              e.dataTransfer.effectAllowed = 'move';
                              e.dataTransfer.setData('text/plain', String(card.id));
                              handleCardDragStart(card.id);
                            }}
                            onDragEnd={handleCardDragEnd}
                            onDragOver={(e) => {
                              e.preventDefault();
                              if (isFilteringActive) return;
                              const rect = e.currentTarget.getBoundingClientRect();
                              const nextIndex = e.clientY > rect.top + rect.height / 2 ? index + 1 : index;
                              setDragOverTarget({ columnId: col.id, index: nextIndex });
                            }}
                            onDrop={async (e) => {
                              e.preventDefault();
                              if (isFilteringActive) return;
                              const draggedCardId = activeDragCardId ?? Number(e.dataTransfer.getData('text/plain'));
                              if (!draggedCardId) return;
                              const draggedCard = board.project.colunas?.flatMap((column) => column.cards ?? []).find((item) => item.id === draggedCardId);
                              if (!draggedCard) return;
                              const rect = e.currentTarget.getBoundingClientRect();
                              const nextIndex = e.clientY > rect.top + rect.height / 2 ? index + 1 : index;
                              await handleCardDrop(draggedCard, col, nextIndex);
                            }}
                            className={`cursor-pointer overflow-hidden rounded-[12px] border border-white/80 bg-white text-[#172b4d] shadow-[0_2px_8px_rgba(9,30,66,0.16)] transition hover:-translate-y-0.5 hover:shadow-[0_10px_18px_rgba(9,30,66,0.18)] ${
                              activeDragCardId === card.id ? 'rotate-[1deg] opacity-60 ring-2 ring-[#0079bf]/35' : ''
                            }`}
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

                            {/* Link / Product Preview on Kanban card */}
                            {productUrl && (
                              <div
                                onClick={(e) => {
                                  e.stopPropagation();
                                  window.open(productUrl, '_blank', 'noopener,noreferrer');
                                }}
                                className="mt-2.5 rounded-lg border border-amber-300/90 bg-gradient-to-r from-amber-50 to-orange-50/90 p-2 shadow-xs transition-all hover:border-amber-500 hover:shadow-md hover:from-amber-100 hover:to-orange-100 group cursor-pointer"
                                title="Abrir link do produto em nova aba"
                              >
                                <div className="flex items-center justify-between gap-1 text-[11px] font-bold text-amber-900 border-b border-amber-200/80 pb-1 mb-1">
                                  <div className="flex items-center space-x-1.5 truncate">
                                    <ShoppingCart size={12} className="text-amber-600 shrink-0" />
                                    <span className="truncate font-mono">{getDomainName(productUrl)}</span>
                                  </div>
                                  <span className="inline-flex items-center space-x-0.5 text-[10px] font-bold text-amber-800 bg-amber-200/80 px-1.5 py-0.5 rounded font-mono group-hover:bg-amber-600 group-hover:text-white transition-colors shrink-0">
                                    <span>Ver Loja</span>
                                    <ExternalLink size={9} />
                                  </span>
                                </div>
                                <div className="text-xs font-semibold text-[#172b4d] line-clamp-1">
                                  {linkAttachment?.nome ? linkAttachment.nome.replace(/^Link de Compra:\s*/i, '') : card.titulo}
                                </div>
                                <div className="mt-0.5 text-[10px] text-amber-700 truncate font-mono flex items-center space-x-1">
                                  <Globe size={10} className="shrink-0 text-amber-600" />
                                  <span className="truncate">{productUrl}</span>
                                </div>
                              </div>
                            )}

                            <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
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
                          {dragOverTarget?.columnId === col.id && dragOverTarget.index === index + 1 && index === visibleCards.length - 1 && (
                            <div className="h-2 rounded-full bg-[#0079bf] shadow-[0_0_0_3px_rgba(0,121,191,0.18)]" />
                          )}
                        </React.Fragment>
                      );
                    })}

                    {isFilteringActive && (col.cards ?? []).filter(cardMatchesBoardFilters).length === 0 && (
                      <div className="rounded-[12px] border border-dashed border-white/50 bg-white/30 px-3 py-4 text-center text-sm font-medium text-[#5e6c84]">
                        Nenhum cartão nesta lista com os filtros atuais.
                      </div>
                    )}

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
                <div className="flex items-center gap-3">
                  <span
                    className="h-3.5 w-3.5 rounded-full border border-white/40 shadow-[0_0_18px_rgba(255,255,255,0.25)]"
                    style={{ backgroundColor: normalizeBoardColor(p.board_background_color) }}
                  />
                  <div>
                    <h3 className="text-lg font-bold text-white m-0">{p.titulo}</h3>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {p.related_to_maintenance && (
                        <span className="inline-flex rounded-full border border-emerald-400/25 bg-emerald-500/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.12em] text-emerald-200">
                          Integrado a manutenções
                        </span>
                      )}
                      {p.related_to_preventive && (
                        <span className="inline-flex rounded-full border border-cyan-400/25 bg-cyan-500/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.12em] text-cyan-200">
                          Integrado a preventiva
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {p.is_archived && (
                    <span className="text-[10px] font-mono uppercase px-2 py-1 rounded-full border border-white/10 text-slate-300">Arquivado</span>
                  )}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      duplicateProject(p);
                    }}
                    className="grid h-9 w-9 place-items-center rounded-full border border-white/10 bg-white/5 text-slate-200 transition hover:bg-white/12 hover:text-white"
                    title="Duplicar projeto"
                  >
                    <Copy size={15} />
                  </button>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      openEditProjectModal(p);
                    }}
                    className="grid h-9 w-9 place-items-center rounded-full border border-white/10 bg-white/5 text-slate-200 transition hover:bg-white/12 hover:text-white"
                    title="Editar projeto"
                  >
                    <Settings size={16} />
                  </button>
                </div>
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
      <div className="min-h-[500px] border border-brand-border bg-brand-card rounded-2xl overflow-hidden">
        <div className="p-3 border-b border-brand-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono uppercase tracking-wider text-brand-muted flex items-center">
              <Bell size={14} className="mr-2" /> Notificações {unread > 0 && `(${unread} não lidas)`}
            </span>
            <div className="flex rounded-full border border-brand-border/70 bg-white/60 p-0.5">
              <button
                type="button"
                onClick={() => setNotifFilter('todas')}
                className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase transition ${notifFilter === 'todas' ? 'bg-brand-primary text-white' : 'text-brand-muted hover:text-brand-text'}`}
              >
                Todas
              </button>
              <button
                type="button"
                onClick={() => setNotifFilter('nao_lidas')}
                className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase transition ${notifFilter === 'nao_lidas' ? 'bg-brand-primary text-white' : 'text-brand-muted hover:text-brand-text'}`}
              >
                Não lidas
              </button>
            </div>
          </div>
          <button
            onClick={async () => {
              if (unread === 0) {
                await refreshNotificationsState();
                setNotifStatusMessage('Notificações atualizadas. Tudo continua lido.');
                return;
              }
              await kanbanApi.markAllNotificationsRead();
              setNotifs((current) => current.map((item) => ({ ...item, lida: true })));
              setUnread(0);
              setNotifStatusMessage('Todas as notificações foram marcadas como lidas.');
            }}
            className={`text-xs font-mono uppercase transition ${unread === 0 ? 'text-brand-muted hover:text-brand-text' : 'text-brand-primary hover:text-brand-primary/80'}`}
          >
            {unread === 0 ? 'Atualizar' : 'Marcar lidas'}
          </button>
        </div>
        <div className="max-h-[440px] min-h-[440px] divide-y divide-brand-border/60 overflow-y-auto">
          {groupedNotifications.map((group) => (
            <div key={group.label}>
              <div className="sticky top-0 z-10 bg-brand-card/95 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.14em] text-brand-muted backdrop-blur-sm">
                {group.label}
              </div>
              {group.items.map((n) => (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => openNotification(n)}
                  className={`w-full p-3 text-left text-sm transition hover:bg-brand-primary/5 ${
                    highlightedNotificationIds.includes(n.id)
                      ? 'animate-[pulse_1.3s_ease-out_2] bg-[#eff6ff] shadow-[inset_0_0_0_1px_rgba(29,78,216,0.18)]'
                      : n.lida
                        ? 'bg-transparent'
                        : 'bg-brand-primary/5'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs uppercase text-brand-primary">{n.titulo}</span>
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${getNotificationTone(n.tipo)}`}>
                          {n.tipo.replaceAll('_', ' ')}
                        </span>
                        {!n.lida && (
                          <span className="rounded-full bg-[#dbeafe] px-2 py-0.5 text-[10px] font-bold uppercase text-[#1d4ed8]">
                            Nova
                          </span>
                        )}
                        {highlightedNotificationIds.includes(n.id) && (
                          <span className="rounded-full bg-[#dcfce7] px-2 py-0.5 text-[10px] font-bold uppercase text-[#15803d]">
                            Agora
                          </span>
                        )}
                      </div>
                      <div className="text-brand-text mt-1">{n.mensagem}</div>
                      <div className="mt-2 text-[11px] font-medium text-brand-muted">
                        Clique para abrir o contexto desta notificação.
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {!n.lida && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              markNotificationReadOnly(n);
                            }}
                            className="rounded-full border border-[#bfdbfe] bg-[#eff6ff] px-2.5 py-1 text-[10px] font-bold uppercase text-[#1d4ed8] transition hover:bg-[#dbeafe]"
                          >
                            Ler
                          </button>
                        )}
                        {n.project_id && (
                          <button
                            type="button"
                            onClick={async (e) => {
                              e.stopPropagation();
                              await markNotificationReadOnly(n);
                              await openBoard(n.project_id!);
                            }}
                            className="rounded-full border border-brand-border bg-white px-2.5 py-1 text-[10px] font-bold uppercase text-brand-muted transition hover:border-brand-primary/30 hover:text-brand-primary"
                          >
                            Projeto
                          </button>
                        )}
                        {n.card_id && (
                          <button
                            type="button"
                            onClick={async (e) => {
                              e.stopPropagation();
                              await markNotificationReadOnly(n);
                              if (n.project_id) {
                                await openBoard(n.project_id);
                              }
                              await openCard(n.card_id!);
                            }}
                            className="rounded-full border border-brand-border bg-white px-2.5 py-1 text-[10px] font-bold uppercase text-brand-muted transition hover:border-brand-primary/30 hover:text-brand-primary"
                          >
                            Cartão
                          </button>
                        )}
                      </div>
                    </div>
                    <span className="shrink-0 text-xs font-mono text-brand-muted">{new Date(n.created_at).toLocaleString('pt-BR')}</span>
                  </div>
                </button>
              ))}
            </div>
          ))}
          {groupedNotifications.length === 0 && (
            <div className="p-6 text-center">
              <div className="text-brand-muted font-mono text-xs">
                {notifFilter === 'nao_lidas' ? 'Nenhuma notificação não lida.' : 'Nenhuma notificação.'}
              </div>
              <div className="mt-2 text-xs text-brand-muted/80">
                {notifFilter === 'nao_lidas'
                  ? 'Quando chegar algo novo no projeto, ele aparecerá aqui primeiro.'
                  : 'Novas movimentações do projeto, cartões atribuídos e anexos aparecerão aqui.'}
              </div>
            </div>
          )}
        </div>
      </div>
      )}

      {projModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4 backdrop-blur-sm">
          <div className="flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded bg-[#f4f5f7] text-[#172b4d] shadow-[0_18px_64px_rgba(9,30,66,0.38)]">
            <div className="flex items-center justify-between border-b border-[#dfe1e6] px-5 pb-3 pt-5">
              <div>
                <h3 className="text-base font-bold">{editingProject ? 'Editar projeto' : 'Novo projeto'}</h3>
                <p className="mt-1 text-sm text-[#5e6c84]">
                  Ajuste participantes e a identidade visual do board.
                </p>
              </div>
              <button
                onClick={() => {
                  setProjModal(false);
                  resetProjectForm();
                }}
                className="grid h-8 w-8 place-items-center rounded text-[#5e6c84] hover:bg-[#dfe1e6] hover:text-[#172b4d]"
              >
                <X size={20} />
              </button>
            </div>
            <form onSubmit={submitProject} className="flex min-h-0 flex-1 flex-col">
              <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
                <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
                <div className="space-y-4">
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
                      rows={4}
                      className="w-full rounded border border-[#dfe1e6] bg-white px-3 py-2 text-sm text-[#172b4d] shadow-inner focus:border-[#0079bf] focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-xs font-bold uppercase text-[#5e6c84]">Participantes</label>
                    <div className="flex max-h-56 flex-wrap gap-2 overflow-y-auto rounded border border-[#dfe1e6] bg-white p-3">
                      {users.map((u) => (
                        <label key={u.id} className="flex cursor-pointer items-center gap-1 rounded bg-[#f8fafc] px-2 py-1 text-xs text-[#5e6c84]">
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

                  {isStaff && (
                    <>
                      <div className="rounded-[16px] border border-[#dfe1e6] bg-[#f8fafc] p-4">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <div className="text-xs font-bold uppercase tracking-[0.12em] text-[#5e6c84]">Integração com manutenções</div>
                            <div className="mt-1 text-sm text-[#44546f]">
                              Ative para permitir que este projeto use o fluxo de manutenção ao mover cartões no board.
                            </div>
                          </div>
                          <label className="inline-flex cursor-pointer items-center gap-2 rounded-full bg-white px-3 py-2 shadow-sm">
                            <input
                              type="checkbox"
                              checked={pRelatedToMaintenance}
                              onChange={(e) => setPRelatedToMaintenance(e.target.checked)}
                              className="h-4 w-4 rounded border-[#b6c2cf] text-[#0079bf] focus:ring-[#0079bf]"
                            />
                            <span className="text-sm font-semibold text-[#172b4d]">Relacionar</span>
                          </label>
                        </div>
                      </div>

                      <div className="rounded-[16px] border border-[#dfe1e6] bg-[#f8fafc] p-4">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <div className="text-xs font-bold uppercase tracking-[0.12em] text-[#5e6c84]">Integração com manutenção preventiva</div>
                            <div className="mt-1 text-sm text-[#44546f]">
                              Ative para conectar este board ao panorama de planos e ordens de serviço preventivas.
                            </div>
                          </div>
                          <label className="inline-flex cursor-pointer items-center gap-2 rounded-full bg-white px-3 py-2 shadow-sm">
                            <input
                              type="checkbox"
                              checked={pRelatedToPreventive}
                              onChange={(e) => setPRelatedToPreventive(e.target.checked)}
                              className="h-4 w-4 rounded border-[#b6c2cf] text-[#0079bf] focus:ring-[#0079bf]"
                            />
                            <span className="text-sm font-semibold text-[#172b4d]">Relacionar</span>
                          </label>
                        </div>
                        {pRelatedToPreventive && (
                          <div className="mt-4">
                            <label className="mb-1.5 block text-xs font-bold uppercase tracking-[0.12em] text-[#5e6c84]">
                              Plano preventivo vinculado
                            </label>
                            <select
                              value={pPreventivePlanId ?? ''}
                              onChange={(e) => setPPreventivePlanId(e.target.value ? Number(e.target.value) : null)}
                              className="w-full rounded border border-[#dfe1e6] bg-white px-3 py-2 text-sm text-[#172b4d] focus:border-[#0079bf] focus:outline-none"
                            >
                              <option value="">Selecionar depois</option>
                              {preventivePlans.map((plan) => (
                                <option key={plan.id} value={plan.id}>
                                  {plan.nome} {plan.codigo ? `(${plan.codigo})` : ''}
                                </option>
                              ))}
                            </select>
                            <div className="mt-2 text-xs text-[#5e6c84]">
                              Esse plano será usado como base para abrir rapidamente uma nova OS preventiva a partir do board.
                            </div>
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="mb-1.5 block text-xs font-bold uppercase text-[#5e6c84]">Temas prontos</label>
                    <div className="grid grid-cols-2 gap-3">
                      {boardThemePresets.map((preset) => {
                        const active =
                          normalizeBoardColor(pBoardColor) === preset.color &&
                          normalizeBoardPattern(pBoardPattern) === preset.pattern;

                        return (
                          <button
                            key={preset.id}
                            type="button"
                            onClick={() => applyBoardThemePreset(preset)}
                            className={`overflow-hidden rounded-[16px] border text-left transition ${
                              active
                                ? 'border-[#0079bf] ring-2 ring-[#bfdbfe]'
                                : 'border-[#dfe1e6] hover:border-[#b6c2cf]'
                            }`}
                          >
                            <div
                              className="h-16 px-3 py-2 text-white"
                              style={getBoardPatternStyle(preset.color, preset.pattern)}
                            >
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-bold uppercase tracking-[0.14em] text-white/80">
                                  {preset.name}
                                </span>
                                <span
                                  className="h-2.5 w-2.5 rounded-full border border-white/60"
                                  style={{ backgroundColor: preset.accent }}
                                />
                              </div>
                              <div className="mt-4 text-[11px] font-semibold uppercase tracking-[0.12em] text-white/75">
                                {preset.pattern}
                              </div>
                            </div>
                            <div className="flex items-center justify-between bg-white px-3 py-2 text-xs font-semibold text-[#475569]">
                              <span>{preset.color}</span>
                              <span>{preset.pattern}</span>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div>
                    <label className="mb-1.5 block text-xs font-bold uppercase text-[#5e6c84]">Cor do fundo do board</label>
                    <div className="flex flex-wrap gap-3">
                      {boardBackgroundPalette.map((color) => (
                        <button
                          key={color}
                          type="button"
                          onClick={() => setPBoardColor(color)}
                          className={`h-11 w-11 rounded-[12px] border-2 shadow-sm transition ${normalizeBoardColor(pBoardColor) === color ? 'scale-105 border-[#172b4d]' : 'border-transparent opacity-90'}`}
                          style={{ backgroundColor: color }}
                          title={color}
                        />
                      ))}
                    </div>
                    <div className="mt-3 flex items-center gap-3 rounded border border-[#dfe1e6] bg-white px-3 py-2">
                      <input
                        type="color"
                        value={normalizeBoardColor(pBoardColor)}
                        onChange={(e) => setPBoardColor(e.target.value.toUpperCase())}
                        className="h-10 w-12 cursor-pointer rounded border border-[#dfe1e6] bg-white"
                      />
                      <div>
                        <div className="text-xs font-bold uppercase text-[#5e6c84]">Cor personalizada</div>
                        <div className="text-sm font-semibold text-[#172b4d]">{normalizeBoardColor(pBoardColor)}</div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="mb-1.5 block text-xs font-bold uppercase text-[#5e6c84]">Estilo do board</label>
                    <div className="grid grid-cols-2 gap-2">
                      {boardPatternOptions.map((option) => {
                        const active = pBoardPattern === option.value;
                        return (
                          <button
                            key={option.value}
                            type="button"
                            onClick={() => setPBoardPattern(option.value)}
                            className={`rounded border px-3 py-2 text-sm font-semibold transition ${
                              active
                                ? 'border-[#0079bf] bg-[#e6f4ff] text-[#0052cc]'
                                : 'border-[#dfe1e6] bg-white text-[#44546f] hover:border-[#b6c2cf] hover:bg-[#f7f8f9]'
                            }`}
                          >
                            {option.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div>
                    <label className="mb-1.5 block text-xs font-bold uppercase text-[#5e6c84]">Pré-visualização</label>
                    <div
                      className="overflow-hidden rounded-[20px] border border-white/20"
                      style={getBoardPreviewShellStyle(pBoardColor, pBoardPattern)}
                    >
                      <div className="flex items-center justify-between bg-white/12 px-4 py-3 text-white backdrop-blur-sm">
                        <div>
                          <div className="text-xs uppercase tracking-[0.16em] text-white/70">Board</div>
                          <div className="text-sm font-bold text-white">{pTitle.trim() || 'Nome do projeto'}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="rounded bg-white/12 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-white/75">
                            {pBoardPattern}
                          </span>
                          <Settings size={16} />
                        </div>
                      </div>
                      <div className="space-y-3 p-4">
                        <div className="rounded-[14px] border border-white/20 bg-white/74 p-3 backdrop-blur-sm">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="h-2.5 w-2.5 rounded-sm bg-[#60A5FA]" />
                              <span className="text-sm font-semibold text-[#172b4d]">Planejado</span>
                            </div>
                            <span className="text-xs text-[#5e6c84]">3</span>
                          </div>
                          <div className="mt-3 rounded-[12px] bg-white p-3 text-sm text-[#334155] shadow-[0_2px_10px_rgba(9,30,66,0.12)]">
                            {pDesc.trim() || 'A descrição do projeto aparece aqui para orientar o time.'}
                          </div>
                        </div>
                        <div className="rounded-[14px] border border-white/20 bg-white/12 p-3 text-white/90 backdrop-blur-sm">
                          <div className="text-[11px] font-bold uppercase tracking-[0.12em] text-white/70">
                            Fundo selecionado
                          </div>
                          <div className="mt-2 flex items-center gap-2">
                            <span
                              className="h-4 w-4 rounded-full border border-white/70"
                              style={{ backgroundColor: normalizeBoardColor(pBoardColor) }}
                            />
                            <span className="text-sm font-semibold">{normalizeBoardColor(pBoardColor)}</span>
                          </div>
                          <div className="mt-2 text-xs text-white/75">
                            O quadro final usará esta cor com o estilo <strong>{pBoardPattern}</strong>.
                          </div>
                          {isStaff && (
                            <>
                              <div className="mt-2 text-xs text-white/75">
                                Integração com manutenção: <strong>{pRelatedToMaintenance ? 'ativada' : 'desativada'}</strong>.
                              </div>
                              <div className="mt-2 text-xs text-white/75">
                                Integração com preventiva: <strong>{pRelatedToPreventive ? 'ativada' : 'desativada'}</strong>.
                              </div>
                              {pRelatedToPreventive && pPreventivePlanId && (
                                <div className="mt-2 text-xs text-white/75">
                                  Plano vinculado: <strong>{preventivePlans.find((plan) => plan.id === pPreventivePlanId)?.nome ?? 'Plano selecionado'}</strong>.
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              </div>
              <div className="flex justify-end space-x-3 border-t border-[#dfe1e6] bg-[#f4f5f7] px-5 py-4">
                <button
                  type="button"
                  onClick={() => {
                    setProjModal(false);
                    resetProjectForm();
                  }}
                  className="rounded px-4 py-2 text-sm font-medium text-[#5e6c84] hover:bg-[#dfe1e6]"
                >
                  Cancelar
                </button>
                <button type="submit" className="rounded bg-[#0079bf] px-4 py-2 text-sm font-bold text-white hover:bg-[#026aa7]">
                  {editingProject ? 'Salvar projeto' : 'Criar projeto'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {boardInfoOpen && board && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          <button
            type="button"
            aria-label="Fechar painel"
            onClick={() => setBoardInfoOpen(false)}
            className="absolute inset-0 bg-black/35 backdrop-blur-[2px]"
          />
          <div className="absolute inset-y-0 right-0 flex w-full max-w-[460px] animate-[slide-in-right_.22s_ease-out] flex-col border-l border-white/35 bg-[#f4f5f7] text-[#172b4d] shadow-[-18px_0_64px_rgba(9,30,66,0.22)]">
            <div className="flex items-start justify-between gap-4 border-b border-[#dfe1e6] bg-white px-5 py-4">
              <div className="min-w-0">
                <div className="text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Informações do board</div>
                <h3 className="mt-1 truncate text-xl font-bold text-[#172b4d]">{board.project.titulo}</h3>
                <p className="mt-2 text-sm text-[#5e6c84]">
                  {board.project.descricao?.trim() || 'Sem descrição cadastrada para este projeto.'}
                </p>
              </div>
              <button
                onClick={() => setBoardInfoOpen(false)}
                className="grid h-8 w-8 shrink-0 place-items-center rounded text-[#5e6c84] hover:bg-[#dfe1e6] hover:text-[#172b4d]"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4 overflow-y-auto px-5 py-4">
              <div className="grid gap-3 grid-cols-2">
                <div className="rounded-[16px] border border-[#dfe1e6] bg-white p-4 shadow-[0_1px_0_rgba(9,30,66,0.08)]">
                  <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Listas</div>
                  <div className="mt-2 text-2xl font-bold text-[#172b4d]">{boardColumnsCount}</div>
                </div>
                <div className="rounded-[16px] border border-[#dfe1e6] bg-white p-4 shadow-[0_1px_0_rgba(9,30,66,0.08)]">
                  <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Cartões</div>
                  <div className="mt-2 text-2xl font-bold text-[#172b4d]">{boardCardsCount}</div>
                </div>
                <div className="rounded-[16px] border border-[#dfe1e6] bg-white p-4 shadow-[0_1px_0_rgba(9,30,66,0.08)]">
                  <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Participantes</div>
                  <div className="mt-2 text-2xl font-bold text-[#172b4d]">{boardParticipantsCount}</div>
                </div>
                <div className="rounded-[16px] border border-[#dfe1e6] bg-white p-4 shadow-[0_1px_0_rgba(9,30,66,0.08)]">
                  <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Progresso</div>
                  <div className="mt-2 text-2xl font-bold text-[#172b4d]">{board.board_progress}%</div>
                </div>
              </div>

              {isStaff && (
                <>
                  <div className={`rounded-[16px] border p-4 shadow-[0_1px_0_rgba(9,30,66,0.08)] ${boardRelatedToMaintenance ? 'border-emerald-200 bg-emerald-50' : 'border-[#dfe1e6] bg-white'}`}>
                    <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Integração</div>
                    <div className="mt-2 text-sm font-semibold text-[#172b4d]">
                      {boardRelatedToMaintenance ? 'Projeto relacionado a manutenções' : 'Sem vínculo com manutenções'}
                    </div>
                    <div className="mt-1 text-sm text-[#5e6c84]">
                      {boardRelatedToMaintenance
                        ? 'Movimentações deste board podem abrir o fluxo de manutenção quando necessário.'
                        : 'Ative essa opção na edição do projeto para conectar o board ao módulo de manutenções.'}
                    </div>
                  </div>

                  <div className={`rounded-[16px] border p-4 shadow-[0_1px_0_rgba(9,30,66,0.08)] ${boardRelatedToPreventive ? 'border-cyan-200 bg-cyan-50' : 'border-[#dfe1e6] bg-white'}`}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Manutenção preventiva</div>
                        <div className="mt-2 text-sm font-semibold text-[#172b4d]">
                          {boardRelatedToPreventive ? 'Projeto conectado ao módulo preventivo' : 'Sem vínculo com manutenção preventiva'}
                        </div>
                        <div className="mt-1 text-sm text-[#5e6c84]">
                          {boardRelatedToPreventive
                            ? 'Este board pode acompanhar o panorama preventivo com planos ativos e ordens abertas.'
                            : 'Ative essa opção na edição do projeto para usar um board com contexto preventivo.'}
                        </div>
                        {board?.project.preventive_plan && (
                          <div className="mt-3 rounded-[14px] border border-cyan-100 bg-white px-3 py-3">
                            <div className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#5e6c84]">Plano vinculado</div>
                            <div className="mt-1 text-sm font-semibold text-[#172b4d]">{board.project.preventive_plan.nome}</div>
                            <div className="text-xs text-[#5e6c84]">{board.project.preventive_plan.codigo}</div>
                          </div>
                        )}
                      </div>
                      {boardRelatedToPreventive && (
                        <div className="flex flex-col gap-2">
                          <button
                            type="button"
                            onClick={() => window.location.assign('/manutencao-preventiva')}
                            className="rounded-full border border-cyan-200 bg-white px-3 py-2 text-xs font-bold uppercase tracking-[0.12em] text-cyan-700 hover:bg-cyan-100"
                          >
                            Abrir preventiva
                          </button>
                          {board?.project.preventive_plan_id && (
                            <button
                              type="button"
                              onClick={() => openPreventiveOrder({ planId: board.project.preventive_plan_id ?? null })}
                              className="rounded-full bg-cyan-600 px-3 py-2 text-xs font-bold uppercase tracking-[0.12em] text-white hover:bg-cyan-700"
                            >
                              Nova OS preventiva
                            </button>
                          )}
                        </div>
                      )}
                    </div>

                    {boardRelatedToPreventive && preventiveSummary && (
                      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                        <div className="rounded-[14px] border border-cyan-100 bg-white p-3">
                          <div className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#5e6c84]">Planos ativos</div>
                          <div className="mt-2 text-2xl font-bold text-[#172b4d]">{preventiveSummary.active_plans}</div>
                        </div>
                        <div className="rounded-[14px] border border-cyan-100 bg-white p-3">
                          <div className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#5e6c84]">Planos vencendo</div>
                          <div className="mt-2 text-2xl font-bold text-[#172b4d]">{preventiveSummary.plans_due}</div>
                        </div>
                        <div className="rounded-[14px] border border-cyan-100 bg-white p-3">
                          <div className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#5e6c84]">OS abertas</div>
                          <div className="mt-2 text-2xl font-bold text-[#172b4d]">{preventiveSummary.open_orders}</div>
                        </div>
                        <div className="rounded-[14px] border border-cyan-100 bg-white p-3">
                          <div className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#5e6c84]">Próximas em 7 dias</div>
                          <div className="mt-2 text-2xl font-bold text-[#172b4d]">{preventiveSummary.due_soon}</div>
                        </div>
                      </div>
                    )}
                  </div>
                </>
              )}

              <div className="rounded-[18px] border border-[#dfe1e6] bg-white p-4 shadow-[0_1px_0_rgba(9,30,66,0.08)]">
                <div className="text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Identidade visual</div>
                <div className="mt-3 overflow-hidden rounded-[18px] border border-white/20" style={getBoardPreviewShellStyle(board.project.board_background_color, board.project.board_pattern)}>
                  <div className="flex items-center justify-between bg-white/12 px-4 py-3 text-white backdrop-blur-sm">
                    <div>
                      <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-white/70">Tema do board</div>
                      <div className="text-sm font-semibold text-white">{boardThemeLabel}</div>
                    </div>
                    <span className="rounded bg-white/12 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-white/80">
                      {normalizeBoardColor(board.project.board_background_color)}
                    </span>
                  </div>
                  <div className="p-4">
                    <div className="rounded-[14px] border border-white/20 bg-white/74 p-3 backdrop-blur-sm">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="h-2.5 w-2.5 rounded-sm bg-[#60A5FA]" />
                          <span className="text-sm font-semibold text-[#172b4d]">Resumo visual</span>
                        </div>
                        <span className="text-xs font-semibold text-[#5e6c84]">{boardColumnsCount} listas</span>
                      </div>
                      <div className="mt-3 rounded-[12px] bg-white p-3 text-sm text-[#334155] shadow-[0_2px_10px_rgba(9,30,66,0.12)]">
                        Este board usa o estilo <strong>{boardThemeLabel}</strong> com fundo {normalizeBoardColor(board.project.board_background_color)}.
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="rounded-[18px] border border-[#dfe1e6] bg-white p-4 shadow-[0_1px_0_rgba(9,30,66,0.08)]">
                  <div className="text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Filtros rápidos</div>
                  <div className="mt-3 space-y-3">
                    <div>
                      <label className="mb-1.5 block text-[11px] font-bold uppercase tracking-[0.12em] text-[#5e6c84]">Buscar</label>
                      <input
                        value={boardSearchQuery}
                        onChange={(e) => setBoardSearchQuery(e.target.value)}
                        placeholder="Título ou descrição"
                        className="w-full rounded border border-[#dfe1e6] bg-[#f8fafc] px-3 py-2 text-sm text-[#172b4d] placeholder:text-[#8c9bab] focus:border-[#0079bf] focus:bg-white focus:outline-none"
                      />
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div>
                        <label className="mb-1.5 block text-[11px] font-bold uppercase tracking-[0.12em] text-[#5e6c84]">Prioridade</label>
                        <select
                          value={boardPriorityFilter}
                          onChange={(e) => setBoardPriorityFilter(e.target.value)}
                          className="w-full rounded border border-[#dfe1e6] bg-[#f8fafc] px-3 py-2 text-sm text-[#172b4d] focus:border-[#0079bf] focus:bg-white focus:outline-none"
                        >
                          <option value="todos">Todas</option>
                          {CARD_PRIORITIES.map((priority) => (
                            <option key={priority} value={priority}>{priority}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="mb-1.5 block text-[11px] font-bold uppercase tracking-[0.12em] text-[#5e6c84]">Responsável</label>
                        <select
                          value={boardResponsibleFilter}
                          onChange={(e) => setBoardResponsibleFilter(e.target.value)}
                          className="w-full rounded border border-[#dfe1e6] bg-[#f8fafc] px-3 py-2 text-sm text-[#172b4d] focus:border-[#0079bf] focus:bg-white focus:outline-none"
                        >
                          <option value="todos">Todos</option>
                          {users.map((user) => (
                            <option key={user.id} value={String(user.id)}>{user.nome}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <div className="flex items-center justify-between rounded-[12px] bg-[#f8fafc] px-3 py-2">
                      <span className="text-sm font-medium text-[#5e6c84]">Resultados visíveis</span>
                      <span className="text-sm font-bold text-[#172b4d]">{boardFilteredCards.length}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setBoardSearchQuery('');
                        setBoardPriorityFilter('todos');
                        setBoardResponsibleFilter('todos');
                      }}
                      className="w-full rounded border border-[#d0d7de] bg-white px-3 py-2 text-sm font-semibold text-[#334155] hover:bg-[#e2e8f0]"
                    >
                      Limpar filtros
                    </button>
                    {isFilteringActive && (
                      <div className="rounded-[12px] bg-[#fff7ed] px-3 py-2 text-xs font-medium text-[#9a3412]">
                        O arrastar e soltar fica pausado enquanto os filtros estão ativos, para evitar reordenação parcial.
                      </div>
                    )}
                  </div>
                </div>

                <div className="rounded-[18px] border border-[#dfe1e6] bg-white p-4 shadow-[0_1px_0_rgba(9,30,66,0.08)]">
                  <div className="text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Detalhes</div>
                  <div className="mt-3 space-y-3 text-sm text-[#334155]">
                    <div className="flex items-center justify-between gap-3 rounded-[12px] bg-[#f8fafc] px-3 py-2">
                      <span className="font-semibold text-[#5e6c84]">Criado em</span>
                      <span className="font-semibold text-[#172b4d]">{formatDate(board.project.created_at) || '—'}</span>
                    </div>
                    <div className="flex items-center justify-between gap-3 rounded-[12px] bg-[#f8fafc] px-3 py-2">
                      <span className="font-semibold text-[#5e6c84]">Atualizado em</span>
                      <span className="font-semibold text-[#172b4d]">{formatDate(board.project.updated_at) || '—'}</span>
                    </div>
                    <div className="flex items-center justify-between gap-3 rounded-[12px] bg-[#f8fafc] px-3 py-2">
                      <span className="font-semibold text-[#5e6c84]">Status</span>
                      <span className="font-semibold text-[#172b4d]">{board.project.is_active ? 'Ativo' : 'Inativo'}</span>
                    </div>
                  </div>
                </div>

                <div className="rounded-[18px] border border-[#dfe1e6] bg-white p-4 shadow-[0_1px_0_rgba(9,30,66,0.08)]">
                  <div className="text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Participantes</div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {(board.project.participantes ?? []).map((participant) => (
                      <div key={participant.id} className="inline-flex items-center gap-2 rounded-full bg-[#eff6ff] px-3 py-2 text-sm font-semibold text-[#1d4ed8]">
                        <span className="grid h-7 w-7 place-items-center rounded-full bg-[#0079bf] text-[10px] font-bold text-white">
                          {getInitials(participant.nome)}
                        </span>
                        <span>{participant.nome}</span>
                      </div>
                    ))}
                    {(board.project.participantes ?? []).length === 0 && (
                      <div className="rounded-[12px] bg-[#f8fafc] px-3 py-3 text-sm text-[#5e6c84]">
                        Nenhum participante além do criador foi adicionado.
                      </div>
                    )}
                  </div>
                </div>

                <div className="rounded-[18px] border border-[#dfe1e6] bg-white p-4 shadow-[0_1px_0_rgba(9,30,66,0.08)]">
                  <div className="text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Atividade recente</div>
                  <div className="mt-3 space-y-3">
                    {boardRecentActivity.map((card) => (
                      <button
                        key={card.id}
                        type="button"
                        onClick={() => {
                          setBoardInfoOpen(false);
                          openCard(card.id);
                        }}
                        className="w-full rounded-[14px] border border-[#dfe1e6] bg-[#f8fafc] px-3 py-3 text-left transition hover:border-[#b6c2cf] hover:bg-white"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <div className="truncate text-sm font-semibold text-[#172b4d]">{card.titulo}</div>
                            <div className="mt-1 text-xs text-[#5e6c84]">
                              {card.column?.nome ?? 'Sem lista'} · {card.responsavel?.nome ?? 'Sem responsável'}
                            </div>
                          </div>
                          <span className={`rounded px-2 py-0.5 text-[11px] font-bold ${priorityBadgeClass[card.prioridade] ?? 'bg-[#b3bac5] text-white'}`}>
                            {card.prioridade}
                          </span>
                        </div>
                        <div className="mt-2 text-[11px] font-medium text-[#64748b]">
                          Atualizado em {new Date(card.updated_at || card.created_at).toLocaleString('pt-BR')}
                        </div>
                      </button>
                    ))}
                    {boardRecentActivity.length === 0 && (
                      <div className="rounded-[12px] bg-[#f8fafc] px-3 py-3 text-sm text-[#5e6c84]">
                        Ainda não há atividade recente para este projeto.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 border-t border-[#dfe1e6] bg-[#f4f5f7] px-5 py-4">
              <button
                type="button"
                onClick={() => {
                  setBoardInfoOpen(false);
                  openEditProjectModal(board.project);
                }}
                className="rounded border border-[#d0d7de] bg-white px-4 py-2 text-sm font-semibold text-[#334155] hover:bg-[#e2e8f0]"
              >
                Personalizar board
              </button>
              <button
                type="button"
                onClick={() => {
                  setBoardInfoOpen(false);
                  openCreateColumnModal();
                }}
                className="rounded bg-[#0079bf] px-4 py-2 text-sm font-bold text-white hover:bg-[#026aa7]"
              >
                Nova lista
              </button>
            </div>
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

              <div className="rounded border border-[#dfe1e6] bg-white p-4 shadow-[0_1px_0_rgba(9,30,66,0.12)]" style={{ backgroundColor: '#ffffff' }}>
                <div className="mb-3 flex items-center justify-between gap-3">
                  <label className="block text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Checklist</label>
                  <button
                    type="button"
                    onClick={() => setCChecklistItems((current) => [...current, createChecklistItem()])}
                    className="rounded border border-[#bfdbfe] bg-[#eff6ff] px-2.5 py-1 text-[10px] font-bold uppercase text-[#1d4ed8] transition hover:bg-[#dbeafe]"
                  >
                    + Item
                  </button>
                </div>
                <div className="space-y-2">
                  {cChecklistItems.map((item, index) => (
                    <div key={item.id} className="flex items-center gap-2">
                      <input
                        type="text"
                        value={item.titulo}
                        onChange={(e) => setCChecklistItems((current) => current.map((entry) => entry.id === item.id ? { ...entry, titulo: e.target.value } : entry))}
                        placeholder={`Item ${index + 1} do checklist`}
                        className="w-full rounded border border-[#dfe1e6] bg-[#fafbfc] px-3 py-2.5 text-sm text-[#172b4d] placeholder:text-[#8c9bab] focus:border-[#0079bf] focus:bg-white focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => setCChecklistItems((current) => current.filter((entry) => entry.id !== item.id))}
                        className="grid h-10 w-10 shrink-0 place-items-center rounded border border-red-200 bg-red-50 text-red-500 transition hover:bg-red-100"
                        aria-label="Remover item do checklist"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                  {cChecklistItems.length === 0 && (
                    <div className="rounded border border-dashed border-[#d0d7de] bg-[#f8fafc] px-3 py-3 text-sm text-[#64748b]">
                      Adicione passos, validacoes ou subtarefas para este cartao.
                    </div>
                  )}
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

            {boardRelatedToPreventive && (
              <div className="rounded border border-[#dfe1e6] bg-white p-3 shadow-[0_1px_0_rgba(9,30,66,0.25)]">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-xs font-bold uppercase tracking-[0.14em] text-[#5e6c84]">Ação preventiva</div>
                    <div className="mt-1 text-sm text-[#334155]">
                      {cardDetail.ativos?.[0]
                        ? `Abrir OS preventiva com o ativo ${cardDetail.ativos[0].nome}.`
                        : 'Abrir OS preventiva a partir deste cartão.'}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      openPreventiveOrder({
                        planId: board.project.preventive_plan_id ?? null,
                        assetId: cardDetail.ativos?.[0]?.id ?? null,
                        sourceCardId: cardDetail.id,
                      });
                    }}
                    className="rounded bg-cyan-600 px-4 py-2 text-xs font-bold uppercase tracking-[0.12em] text-white hover:bg-cyan-700"
                  >
                    Nova OS preventiva
                  </button>
                </div>
              </div>
            )}

            {cardDetail.preventive_order && (
              <div className="rounded border border-cyan-200 bg-cyan-50 p-3 shadow-[0_1px_0_rgba(9,30,66,0.12)]">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="text-xs font-bold uppercase tracking-[0.14em] text-cyan-800">Acompanhamento da OS preventiva</div>
                    <div className="mt-1 text-sm font-semibold text-[#172b4d]">
                      {cardDetail.preventive_order.numero} · {cardDetail.preventive_order.status}
                    </div>
                    <div className="mt-1 text-sm text-[#334155]">
                      {cardDetail.preventive_order.plan?.nome ?? 'Sem plano'}{cardDetail.preventive_order.asset?.nome ? ` · ${cardDetail.preventive_order.asset.nome}` : ''}
                    </div>
                    <div className="mt-1 text-xs text-[#5e6c84]">
                      {cardDetail.preventive_order.tecnico?.nome ? `Técnico: ${cardDetail.preventive_order.tecnico.nome}` : 'Sem técnico definido'}
                      {cardDetail.preventive_order.data_agendada ? ` · Agendada para ${formatDate(cardDetail.preventive_order.data_agendada)}` : ''}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => openPreventiveOrderDetail(cardDetail.preventive_order!.id)}
                    className="rounded border border-cyan-200 bg-white px-3 py-2 text-xs font-bold uppercase tracking-[0.12em] text-cyan-700 hover:bg-cyan-100"
                  >
                    Abrir preventiva
                  </button>
                </div>
              </div>
            )}

            {/* Procurement / Purchase action on Card */}
            {(() => {
              const detailLinkAttachment = cardDetail.anexos?.find((attachment) => attachment.tipo === 'link' || attachment.url?.startsWith('http://') || attachment.url?.startsWith('https://'));
              const detailDescLinkMatch = (cardDetail.descricao || '').match(/https?:\/\/[^\s]+/i);
              const detailProductUrl = detailLinkAttachment?.url || (detailDescLinkMatch ? detailDescLinkMatch[0] : null);

              return (
                <>
                  {detailProductUrl && (
                    <div className="rounded-lg border border-amber-300 bg-gradient-to-br from-amber-50 to-orange-50/90 p-4 shadow-sm space-y-3">
                      <div className="flex items-center justify-between border-b border-amber-200/80 pb-2">
                        <div className="flex items-center space-x-2">
                          <ShoppingCart size={16} className="text-amber-600" />
                          <span className="text-xs font-bold uppercase tracking-wider text-amber-900 font-mono">
                            Preview do Link do Produto ({getDomainName(detailProductUrl)})
                          </span>
                        </div>
                        <span className="text-[10px] font-bold font-mono uppercase px-2 py-0.5 rounded bg-amber-200 text-amber-900">
                          Aguardando Compras
                        </span>
                      </div>

                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-3 rounded border border-amber-200 shadow-inner">
                        <div className="min-w-0 space-y-1">
                          <div className="text-sm font-bold text-[#172b4d] truncate">
                            {detailLinkAttachment?.nome ? detailLinkAttachment.nome.replace(/^Link de Compra:\s*/i, '') : cardDetail.titulo}
                          </div>
                          <div className="text-xs text-[#5e6c84] truncate font-mono flex items-center space-x-1.5">
                            <Globe size={13} className="text-amber-600 shrink-0" />
                            <span className="truncate">{detailProductUrl}</span>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2 shrink-0">
                          <a
                            href={detailProductUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="px-3.5 py-2 bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs font-mono uppercase rounded shadow-sm flex items-center space-x-1.5 transition-colors"
                          >
                            <span>Abrir no Site</span>
                            <ExternalLink size={13} />
                          </a>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="rounded border border-amber-200 bg-amber-50/80 p-3.5 shadow-[0_1px_0_rgba(9,30,66,0.12)]">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <div className="text-xs font-bold uppercase tracking-[0.14em] text-amber-800 flex items-center space-x-1.5">
                          <ShoppingCart size={14} className="text-amber-600" />
                          <span>Setor de Compras & Suprimentos</span>
                        </div>
                        <div className="mt-1 text-xs text-amber-900">
                          Solicitar aquisição de peça/produto com link do site para o Comprador no Kanban.
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setKProductName(cardDetail.titulo || '');
                          setKProductLink(detailProductUrl || '');
                          setKProductQty(1);
                          setKProductEstimatedCost('');
                          setKProductJustification(`Solicitação de compra via Kanban Card #${cardDetail.id} - ${cardDetail.titulo}`);
                          setKProductItemType('Consumo');
                          setKPurchaseSuccess(null);
                          setKanbanPurchaseModal({ card: cardDetail });
                        }}
                        className="rounded bg-amber-600 px-3.5 py-2 text-xs font-bold uppercase tracking-[0.12em] text-white hover:bg-amber-700 flex items-center space-x-1.5 shadow-sm transition-colors"
                      >
                        <ShoppingCart size={13} />
                        <span>Nova Solicitação de Compra</span>
                      </button>
                    </div>
                  </div>
                </>
              );
            })()}

            <div className="overflow-hidden rounded border border-[#dfe1e6] bg-white" style={{ backgroundColor: '#ffffff', color: '#172b4d' }}>
              <div className="flex items-center justify-between border-b border-[#dfe1e6] bg-[#ebecf0] p-3 text-xs font-bold uppercase text-[#475569]">
                <span>Checklist ({cardDetailChecklistItems.length})</span>
                {cardDetailChecklistItems.length > 0 && (
                  <span className="text-[11px] font-semibold normal-case text-[#64748b]">
                    {cardDetailChecklistItems.filter((item) => item.concluido).length}/{cardDetailChecklistItems.length} concluídos
                  </span>
                )}
              </div>
              <div className="space-y-2 p-3">
                {cardDetailChecklistItems.map((item) => (
                  <label
                    key={item.id}
                    className={`flex cursor-pointer items-center gap-3 rounded border px-3 py-2 text-sm transition ${
                      item.concluido
                        ? 'border-[#bbf7d0] bg-[#f0fdf4] text-[#166534]'
                        : 'border-[#dfe1e6] bg-[#fafbfc] text-[#334155]'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={item.concluido}
                      onChange={(e) => {
                        void persistCardChecklist(
                          cardDetail,
                          cardDetailChecklistItems.map((entry) => entry.id === item.id ? { ...entry, concluido: e.target.checked } : entry),
                        );
                      }}
                      className="accent-brand-primary"
                    />
                    <span className={item.concluido ? 'line-through opacity-75' : ''}>{item.titulo}</span>
                  </label>
                ))}
                {cardDetailChecklistItems.length === 0 && (
                  <div className="rounded border border-dashed border-[#d0d7de] bg-[#f8fafc] px-3 py-3 text-sm text-[#64748b]">
                    Este cartao ainda nao possui checklist.
                  </div>
                )}
              </div>
            </div>

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

      {/* KANBAN PURCHASE REQUEST MODAL (Aguardando Compras) */}
      {kanbanPurchaseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg rounded-lg bg-[#f4f5f7] p-5 text-[#172b4d] shadow-[0_20px_64px_rgba(0,0,0,0.5)] border border-amber-400">
            <div className="flex justify-between items-center border-b border-[#dfe1e6] pb-3">
              <div className="flex items-center space-x-2 text-amber-700">
                <ShoppingCart size={20} />
                <h3 className="text-base font-bold uppercase tracking-wider">
                  Nova Solicitação de Compra {kanbanPurchaseModal.column ? `(${kanbanPurchaseModal.column.nome})` : ''}
                </h3>
              </div>
              <button 
                onClick={() => setKanbanPurchaseModal(null)} 
                className="grid h-8 w-8 place-items-center rounded text-[#5e6c84] hover:bg-[#dfe1e6] hover:text-[#172b4d]"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={confirmKanbanPurchase} className="space-y-4 pt-3">
              <div className="bg-amber-50 p-3 rounded border border-amber-200 text-xs">
                <div className="font-bold text-amber-900">Cartão Kanban Vinculado:</div>
                <div className="text-sm font-semibold text-[#172b4d] mt-0.5">{kanbanPurchaseModal.card.titulo}</div>
                <div className="text-[11px] text-[#5e6c84]">ID #{kanbanPurchaseModal.card.id} · A solicitação será encaminhada para a lista do Comprador e adicionada como anexo a este cartão.</div>
              </div>

              {kPurchaseSuccess && (
                <div className="p-3 bg-green-100 border border-green-300 text-green-800 rounded text-xs flex items-center space-x-2">
                  <CheckCircle2 size={16} className="text-green-600 shrink-0" />
                  <span>{kPurchaseSuccess}</span>
                </div>
              )}

              <div>
                <label className="mb-1 block text-xs font-bold uppercase text-[#5e6c84]">
                  Qual produto / peça comprar? *
                </label>
                <input
                  type="text"
                  required
                  value={kProductName}
                  onChange={(e) => setKProductName(e.target.value)}
                  placeholder="Ex: Mouse sem fio Logitech MX, Cabo HDMI 4K 2m, Memória RAM 16GB..."
                  className="w-full rounded border border-[#dfe1e6] bg-white px-3 py-2 text-sm text-[#172b4d] shadow-inner focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="mb-1 flex items-center space-x-1 text-xs font-bold uppercase text-[#5e6c84]">
                  <LinkIcon size={12} className="text-amber-600" />
                  <span>Link do Site do Produto (URL da Loja/Fornecedor)</span>
                </label>
                <input
                  type="url"
                  value={kProductLink}
                  onChange={(e) => setKProductLink(e.target.value)}
                  placeholder="https://www.mercadolivre.com.br/... ou https://kabum.com.br/..."
                  className="w-full rounded border border-[#dfe1e6] bg-white px-3 py-2 text-sm text-[#172b4d] shadow-inner focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs font-bold uppercase text-[#5e6c84]">Quantidade *</label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={kProductQty}
                    onChange={(e) => setKProductQty(Number(e.target.value))}
                    className="w-full rounded border border-[#dfe1e6] bg-white px-3 py-2 text-sm text-[#172b4d] shadow-inner focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-bold uppercase text-[#5e6c84]">Valor Estimado (R$)</label>
                  <input
                    type="text"
                    value={kProductEstimatedCost}
                    onChange={(e) => setKProductEstimatedCost(e.target.value)}
                    placeholder="Ex: 199.90"
                    className="w-full rounded border border-[#dfe1e6] bg-white px-3 py-2 text-sm text-[#172b4d] shadow-inner focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block text-xs font-bold uppercase text-[#5e6c84]">Justificativa da Compra</label>
                <textarea
                  rows={2}
                  value={kProductJustification}
                  onChange={(e) => setKProductJustification(e.target.value)}
                  placeholder="Explique o motivo ou urgência..."
                  className="w-full rounded border border-[#dfe1e6] bg-white px-3 py-2 text-sm text-[#172b4d] shadow-inner focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3 border-t border-[#dfe1e6]">
                <button
                  type="button"
                  onClick={() => setKanbanPurchaseModal(null)}
                  className="rounded px-4 py-2 text-sm font-medium text-[#5e6c84] hover:bg-[#dfe1e6]"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={kPurchaseSubmitting || !kProductName.trim()}
                  className="rounded bg-amber-600 hover:bg-amber-700 px-4 py-2 text-sm font-bold text-white shadow flex items-center space-x-2 disabled:opacity-50"
                >
                  {kPurchaseSubmitting && <RefreshCw size={14} className="animate-spin" />}
                  <span>Confirmar & Encaminhar ao Comprador</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
