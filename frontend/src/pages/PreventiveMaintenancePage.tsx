import React, { useState, useEffect } from 'react';
import { preventiveApi } from '../api/preventive';
import { toApiFileUrl } from '../api/client';
import { usersApi } from '../api/users';
import { assetsApi } from '../api/assets';
import type {
  MaintenancePlan,
  MaintenanceOrder,
  MaintenanceChecklist,
  PMDashboard,
  PMNotification,
} from '../types/preventive';
import {
  PM_STATUSES,
  PM_TYPES,
  PM_PERIODICITIES,
  PM_PRIORITIES,
  PM_CRITICALITIES,
} from '../types/preventive';
import { useAuthStore } from '../stores/authStore';
import {
  Plus, Edit2, Trash2, X, ShieldAlert, Wrench, ClipboardList, Bell, Play, Pause,
  CheckCircle2, Ban, FileText, Camera,
} from 'lucide-react';

const structureRoles = ['admin', 'gerente_ti', 'gerente_infra'];
const workRoles = ['admin', 'gerente_ti', 'gerente_infra', 'tecnico'];

const statusColor: Record<string, string> = {
  'Aberta': 'text-blue-400 border-blue-500/30',
  'Agendada': 'text-cyan-400 border-cyan-500/30',
  'Em andamento': 'text-yellow-400 border-yellow-500/30',
  'Aguardando peça': 'text-orange-400 border-orange-500/30',
  'Pausada': 'text-purple-400 border-purple-500/30',
  'Concluída': 'text-green-400 border-green-500/30',
  'Cancelada': 'text-red-400 border-red-500/30',
};

type OrderChecklistDraft = {
  nome: string;
  items: {
    descricao: string;
    obrigatorio: boolean;
    requer_foto: boolean;
  }[];
};

const createEmptyChecklistItem = () => ({
  descricao: '',
  obrigatorio: true,
  requer_foto: false,
});

const createEmptyChecklistDraft = (): OrderChecklistDraft => ({
  nome: 'Checklist principal',
  items: [createEmptyChecklistItem()],
});

const formatMinutes = (totalMinutes: number) => {
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return `${hours}h ${String(minutes).padStart(2, '0')}min`;
};

export const PreventiveMaintenancePage: React.FC = () => {
  const user = useAuthStore().user;
  const canEditStructure = user ? structureRoles.includes(user.role) : false;
  const canWorkOrder = user ? workRoles.includes(user.role) : false;

  const [tab, setTab] = useState<'dashboard' | 'planos' | 'ordens' | 'notifs'>('dashboard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Dashboard
  const [dash, setDash] = useState<PMDashboard | null>(null);

  // Plans
  const [plans, setPlans] = useState<MaintenancePlan[]>([]);
  const [planModal, setPlanModal] = useState(false);
  const [editPlanId, setEditPlanId] = useState<number | null>(null);
  const [planDetail, setPlanDetail] = useState<{ plan: MaintenancePlan; orders: MaintenanceOrder[] } | null>(null);

  // Orders
  const [orders, setOrders] = useState<MaintenanceOrder[]>([]);
  const [orderStatusFilter, setOrderStatusFilter] = useState('');
  const [orderModal, setOrderModal] = useState(false);
  const [orderDetail, setOrderDetail] = useState<{ order: MaintenanceOrder; checklists: MaintenanceChecklist[] } | null>(null);

  // Notifications
  const [notifs, setNotifs] = useState<PMNotification[]>([]);

  // Lookups
  const [techs, setTechs] = useState<{ id: number; nome: string }[]>([]);
  const [assets, setAssets] = useState<{ id: number; nome: string }[]>([]);

  // Plan form
  const [pNome, setPNome] = useState('');
  const [pTipo, setPTipo] = useState('Preventiva');
  const [pPeriod, setPPeriod] = useState('Mensal');
  const [pCrit, setPCrit] = useState('Média');
  const [pPrio, setPPrio] = useState('Média');
  const [pDesc, setPDesc] = useState('');
  const [pResponsavel, setPResponsavel] = useState<number | null>(null);
  const [pDias, setPDias] = useState('');

  // Order form
  const [oTipo, setOTipo] = useState('Preventiva');
  const [oPrio, setOPrio] = useState('Média');
  const [oDesc, setODesc] = useState('');
  const [oAsset, setOAsset] = useState<number | null>(null);
  const [oInfra, setOInfra] = useState('');
  const [oTecnico, setOTecnico] = useState<number | null>(null);
  const [oPlan, setOPlan] = useState<number | null>(null);
  const [oAgendada, setOAgendada] = useState('');
  const [orderChecklistDrafts, setOrderChecklistDrafts] = useState<OrderChecklistDraft[]>([createEmptyChecklistDraft()]);
  const [mProduto, setMProduto] = useState('');
  const [mQuantidade, setMQuantidade] = useState('1');
  const [mValorUnitario, setMValorUnitario] = useState('');
  const [mObservacao, setMObservacao] = useState('');
  const [photoTipo, setPhotoTipo] = useState('Durante');
  const [photoDescricao, setPhotoDescricao] = useState('');
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [completeModal, setCompleteModal] = useState(false);
  const [completionDiagnosis, setCompletionDiagnosis] = useState('');
  const [completionSolution, setCompletionSolution] = useState('');
  const [completionRecommendations, setCompletionRecommendations] = useState('');
  const [completionAssetDestination, setCompletionAssetDestination] = useState('Disponível');
  const [completionExtraCost, setCompletionExtraCost] = useState('');
  const [timerNow, setTimerNow] = useState(Date.now());

  const normalizeOrderDetail = (detail: { order: MaintenanceOrder; checklists: MaintenanceChecklist[] | null }) => ({
    order: {
      ...detail.order,
      executions: detail.order.executions ?? [],
      materials: detail.order.materials ?? [],
      photos: detail.order.photos ?? [],
      history: detail.order.history ?? [],
    },
    checklists: detail.checklists ?? [],
  });

  const calculateElapsedMinutes = (order: MaintenanceOrder) => {
    let minutes = order.tempo_total_minutos ?? 0;
    if (order.status === 'Em andamento' && order.data_inicio) {
      minutes += Math.max(0, Math.floor((timerNow - new Date(order.data_inicio).getTime()) / 60000));
    }
    return minutes;
  };

  const pickChecklistPhoto = () =>
    new Promise<File | undefined>((resolve) => {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      let settled = false;

      const finish = (file?: File) => {
        if (settled) return;
        settled = true;
        resolve(file);
      };

      input.addEventListener('change', () => finish(input.files?.[0]), { once: true });
      window.setTimeout(() => finish(undefined), 30000);
      input.click();
    });

  const serializeChecklistDrafts = () =>
    orderChecklistDrafts
      .map((checklist, checklistIndex) => ({
        nome: checklist.nome.trim(),
        ordem: checklistIndex + 1,
        items: checklist.items
          .map((item, itemIndex) => ({
            descricao: item.descricao.trim(),
            obrigatorio: item.obrigatorio,
            requer_foto: item.requer_foto,
            ordem: itemIndex + 1,
          }))
          .filter((item) => item.descricao),
      }))
      .filter((checklist) => checklist.nome);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [d, p, o] = await Promise.all([
        preventiveApi.dashboard(),
        preventiveApi.listPlans(),
        preventiveApi.listOrders('', 0, 200),
      ]);
      setDash(d);
      setPlans(p);
      setOrders(o);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
    preventiveApi.myNotifications().then(setNotifs).catch(() => {});
    usersApi.list(0, 200).then((u) => setTechs(u.map((x) => ({ id: x.id, nome: x.nome })))).catch(() => {});
    assetsApi.list(0, 200).then((a) => setAssets(a.map((x) => ({ id: x.id, nome: x.nome })))).catch(() => {});
  }, []);

  useEffect(() => {
    const interval = window.setInterval(() => setTimerNow(Date.now()), 1000);
    return () => window.clearInterval(interval);
  }, []);

  const showError = (err: any) => {
    setError(err.response?.data?.error || 'Erro na operação');
    setTimeout(() => setError(null), 5000);
  };

  // ---- Plans ----
  const openPlanModal = (plan?: MaintenancePlan) => {
    setEditPlanId(plan?.id ?? null);
    setPNome(plan?.nome ?? '');
    setPTipo(plan?.tipo ?? 'Preventiva');
    setPPeriod(plan?.periodicidade ?? 'Mensal');
    setPCrit(plan?.criticidade ?? 'Média');
    setPPrio(plan?.prioridade ?? 'Média');
    setPDesc(plan?.descricao ?? '');
    setPResponsavel(plan?.responsavel_id ?? null);
    setPDias(plan?.dias_personalizado ? String(plan.dias_personalizado) : '');
    setPlanModal(true);
  };

  const submitPlan = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        nome: pNome,
        tipo: pTipo,
        periodicidade: pPeriod,
        criticidade: pCrit,
        prioridade: pPrio,
        descricao: pDesc,
        responsavel_id: pResponsavel ?? undefined,
        dias_personalizado: pPeriod === 'Personalizada' ? Number(pDias) || undefined : undefined,
      };
      if (editPlanId) await preventiveApi.updatePlan(editPlanId, payload);
      else await preventiveApi.createPlan(payload);
      setPlanModal(false);
      fetchAll();
    } catch (err) {
      showError(err);
    }
  };

  const deletePlan = async (plan: MaintenancePlan) => {
    if (!window.confirm(`Excluir plano "${plan.nome}"?`)) return;
    try {
      await preventiveApi.deletePlan(plan.id);
      fetchAll();
    } catch (err) {
      showError(err);
    }
  };

  const openPlanDetail = async (planId: number) => {
    try {
      setPlanDetail(await preventiveApi.getPlan(planId));
    } catch (err) {
      showError(err);
    }
  };

  // ---- Orders ----
  const openOrderModal = () => {
    setOTipo('Preventiva');
    setOPrio('Média');
    setODesc('');
    setOAsset(null);
    setOInfra('');
    setOTecnico(null);
    setOPlan(null);
    setOAgendada('');
    setOrderChecklistDrafts([createEmptyChecklistDraft()]);
    setOrderModal(true);
  };

  const loadChecklistDraftsFromPlan = async (planId: number | null) => {
    if (!planId) {
      setOrderChecklistDrafts([createEmptyChecklistDraft()]);
      return;
    }
    try {
      const detail = await preventiveApi.getPlan(planId);
      const drafts = (detail.plan.checklists ?? []).map((checklist) => ({
        nome: checklist.nome,
        items: checklist.items.length > 0
          ? checklist.items.map((item) => ({
              descricao: item.descricao,
              obrigatorio: item.obrigatorio,
              requer_foto: item.requer_foto,
            }))
          : [createEmptyChecklistItem()],
      }));
      setOrderChecklistDrafts(drafts.length > 0 ? drafts : [createEmptyChecklistDraft()]);
    } catch (err) {
      showError(err);
    }
  };

  const submitOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await preventiveApi.createOrder({
        tipo: oTipo,
        prioridade: oPrio,
        descricao: oDesc,
        asset_id: oAsset ?? undefined,
        infra_predial_servico: oInfra || undefined,
        tecnico_id: oTecnico ?? undefined,
        plan_id: oPlan ?? undefined,
        data_agendada: oAgendada ? new Date(oAgendada).toISOString() : undefined,
        checklists: serializeChecklistDrafts(),
      });
      setOrderModal(false);
      fetchAll();
    } catch (err) {
      showError(err);
    }
  };

  const openOrderDetail = async (orderId: number) => {
    try {
      const detail = await preventiveApi.getOrder(orderId);
      setOrderDetail(normalizeOrderDetail(detail));
      setMProduto('');
      setMQuantidade('1');
      setMValorUnitario('');
      setMObservacao('');
      setPhotoTipo('Durante');
      setPhotoDescricao('');
      setPhotoFile(null);
      setCompleteModal(false);
      setCompletionDiagnosis('');
      setCompletionSolution('');
      setCompletionRecommendations('');
      setCompletionAssetDestination('Disponível');
      setCompletionExtraCost('');
    } catch (err) {
      showError(err);
    }
  };

  const orderAction = async (orderId: number, action: 'iniciar' | 'pausar' | 'concluir' | 'cancelar') => {
    try {
      if (action === 'iniciar') await preventiveApi.startOrder(orderId);
      else if (action === 'pausar') await preventiveApi.pauseOrder(orderId);
      else if (action === 'cancelar') {
        if (!window.confirm('Cancelar esta ordem de serviço?')) return;
        await preventiveApi.cancelOrder(orderId);
      }
      else {
        setCompleteModal(true);
        return;
      }
      await openOrderDetail(orderId);
      fetchAll();
    } catch (err) {
      showError(err);
    }
  };

  const refreshOrderDetail = async () => {
    if (orderDetail) await openOrderDetail(orderDetail.order.id);
  };

  const submitMaterial = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orderDetail) return;
    try {
      await preventiveApi.addMaterial(orderDetail.order.id, {
        produto: mProduto,
        quantidade: Number(mQuantidade),
        valor_unitario: Number(mValorUnitario),
        observacao: mObservacao || undefined,
      });
      setMProduto('');
      setMQuantidade('1');
      setMValorUnitario('');
      setMObservacao('');
      await refreshOrderDetail();
    } catch (err) {
      showError(err);
    }
  };

  const deleteOrder = async (orderId: number) => {
    if (!window.confirm('Excluir esta ordem de serviço? Essa ação não poderá ser desfeita.')) return;
    try {
      await preventiveApi.deleteOrder(orderId);
      setOrderDetail(null);
      await fetchAll();
    } catch (err) {
      showError(err);
    }
  };

  const submitPhoto = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orderDetail || !photoFile) {
      setError('Selecione uma foto para anexar na OS.');
      setTimeout(() => setError(null), 5000);
      return;
    }
    try {
      await preventiveApi.uploadPhoto(orderDetail.order.id, photoFile, photoTipo, photoDescricao || undefined);
      setPhotoTipo('Durante');
      setPhotoDescricao('');
      setPhotoFile(null);
      await refreshOrderDetail();
    } catch (err) {
      showError(err);
    }
  };

  const submitCompletion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orderDetail) return;

    const requiredChecklistItems = orderDetail.checklists.flatMap((checklist) => checklist.items).filter((item) => item.obrigatorio);
    const completedRequired = requiredChecklistItems.filter((item) =>
      orderDetail.order.executions.some((execution) => execution.checklist_item_id === item.id && execution.concluido)
    );

    if (requiredChecklistItems.length > 0 && completedRequired.length !== requiredChecklistItems.length) {
      setError('Finalize todos os itens obrigatórios do checklist antes de concluir a OS.');
      setTimeout(() => setError(null), 5000);
      return;
    }

    if (orderDetail.order.photos.length === 0) {
      setError('Anexe pelo menos uma evidência fotográfica antes de concluir a OS.');
      setTimeout(() => setError(null), 5000);
      return;
    }

    try {
      await preventiveApi.completeOrder(orderDetail.order.id, {
        diagnostico: completionDiagnosis,
        solucao: completionSolution,
        recomendacoes: completionRecommendations || undefined,
        status_pos_manutencao: completionAssetDestination,
        custo_total: completionExtraCost || undefined,
      });
      setCompleteModal(false);
      setCompletionDiagnosis('');
      setCompletionSolution('');
      setCompletionRecommendations('');
      setCompletionAssetDestination('Disponível');
      setCompletionExtraCost('');
      await openOrderDetail(orderDetail.order.id);
      fetchAll();
    } catch (err) {
      showError(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0">
            Manutenção Preventiva
          </h1>
          <p className="text-brand-muted text-sm mt-1">
            Planos, ordens de serviço e checklists de manutenção.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-3 border border-red-500/30 bg-red-500/5 text-red-400 text-xs font-mono flex items-center space-x-2">
          <ShieldAlert size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex space-x-1 border-b border-brand-border">
        {([
          ['dashboard', 'Dashboard'],
          ['planos', 'Planos'],
          ['ordens', 'Ordens de Serviço'],
          ['notifs', 'Notificações'],
        ] as const).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2.5 font-mono text-xs uppercase tracking-wider border-b-2 transition-colors ${
              tab === key
                ? 'border-brand-primary text-brand-primary'
                : 'border-transparent text-brand-muted hover:text-brand-text'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {loading && (
        <div className="p-12 text-center flex flex-col items-center justify-center space-y-4">
          <div className="w-8 h-8 border-2 border-brand-primary border-t-transparent animate-spin" />
          <span className="font-mono text-xs text-brand-muted uppercase">Carregando...</span>
        </div>
      )}

      {/* ---------- DASHBOARD ---------- */}
      {!loading && tab === 'dashboard' && dash && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="border border-brand-border bg-brand-card p-4">
            <div className="text-3xl font-bold font-mono text-brand-primary">{dash.active_plans}</div>
            <div className="text-xs font-mono uppercase text-brand-muted mt-1">Planos ativos</div>
          </div>
          <div className="border border-brand-border bg-brand-card p-4">
            <div className="text-3xl font-bold font-mono text-brand-primary">{dash.plans_due}</div>
            <div className="text-xs font-mono uppercase text-brand-muted mt-1">Planos a vencer (7d)</div>
          </div>
          <div className="border border-brand-border bg-brand-card p-4">
            <div className="text-3xl font-bold font-mono text-brand-primary">{dash.open_orders}</div>
            <div className="text-xs font-mono uppercase text-brand-muted mt-1">OS abertas</div>
          </div>
          <div className="border border-brand-border bg-brand-card p-4">
            <div className="text-3xl font-bold font-mono text-brand-primary">{dash.due_soon}</div>
            <div className="text-xs font-mono uppercase text-brand-muted mt-1">OS agendadas (7d)</div>
          </div>
          <div className="border border-brand-border bg-brand-card p-4">
            <div className="text-3xl font-bold font-mono text-brand-primary">{dash.total_orders}</div>
            <div className="text-xs font-mono uppercase text-brand-muted mt-1">Total de OS</div>
          </div>
          <div className="border border-brand-border bg-brand-card p-4">
            <div className="text-3xl font-bold font-mono text-brand-primary">{dash.total_plans}</div>
            <div className="text-xs font-mono uppercase text-brand-muted mt-1">Total de planos</div>
          </div>

          <div className="col-span-2 md:col-span-3 lg:col-span-6 border border-brand-border bg-brand-card p-4">
            <div className="text-xs font-mono uppercase text-brand-muted mb-3">OS por status</div>
            <div className="flex flex-wrap gap-2">
              {Object.entries(dash.orders_by_status).map(([status, count]) => (
                <span key={status} className={`text-xs font-mono uppercase px-2 py-1 border ${statusColor[status] ?? 'border-brand-border'}`}>
                  {status}: {count}
                </span>
              ))}
            </div>
          </div>

          <div className="col-span-2 md:col-span-3 lg:col-span-6 border border-brand-border bg-brand-card p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs font-mono uppercase text-brand-muted">Desempenho dos técnicos</div>
              <div className="text-xs text-brand-muted">Tempo médio e aderência aos itens obrigatórios</div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-brand-border text-[11px] font-mono uppercase tracking-wider text-brand-muted">
                    <th className="py-2 pr-4">Responsável</th>
                    <th className="py-2 pr-4">OS atribuídas</th>
                    <th className="py-2 pr-4">Em andamento</th>
                    <th className="py-2 pr-4">Concluídas</th>
                    <th className="py-2 pr-4">Obrigatórias</th>
                    <th className="py-2">Tempo médio</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-brand-border/50 text-sm">
                  {dash.technician_performance.map((tech) => (
                    <tr key={tech.user_id}>
                      <td className="py-3 pr-4 text-brand-text">{tech.nome}</td>
                      <td className="py-3 pr-4 font-mono text-brand-text">{tech.assigned_orders}</td>
                      <td className="py-3 pr-4 font-mono text-brand-text">{tech.in_progress_orders}</td>
                      <td className="py-3 pr-4 font-mono text-brand-text">{tech.completed_orders}</td>
                      <td className="py-3 pr-4 font-mono text-brand-text">{tech.required_completion_rate.toFixed(0)}%</td>
                      <td className="py-3 font-mono text-brand-primary">{formatMinutes(tech.avg_resolution_minutes)}</td>
                    </tr>
                  ))}
                  {dash.technician_performance.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-brand-muted font-mono text-xs">
                        Ainda não há indicadores suficientes para exibir desempenho técnico.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ---------- PLANOS ---------- */}
      {!loading && tab === 'planos' && (
        <div className="space-y-4">
          {canEditStructure && (
            <div className="flex justify-end">
              <button
                onClick={() => openPlanModal()}
                className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs flex items-center space-x-1.5"
              >
                <Plus size={16} />
                <span>Novo Plano</span>
              </button>
            </div>
          )}

          <div className="border border-brand-border bg-brand-card overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">
                  <th className="p-4">Código</th>
                  <th className="p-4">Nome</th>
                  <th className="p-4">Tipo / Period.</th>
                  <th className="p-4">Prioridade</th>
                  <th className="p-4">Próx. execução</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border/60 text-sm">
                {plans.map((p) => (
                  <tr key={p.id} className="hover:bg-brand-dark/10">
                    <td className="p-4 font-mono text-xs text-brand-primary">{p.codigo}</td>
                    <td className="p-4 font-medium text-brand-text">{p.nome}</td>
                    <td className="p-4">
                      <div className="text-brand-text">{p.tipo}</div>
                      <div className="text-xs text-brand-muted">{p.periodicidade}</div>
                    </td>
                    <td className="p-4 text-brand-text">{p.prioridade}</td>
                    <td className="p-4 font-mono text-xs">
                      {new Date(p.proxima_execucao).toLocaleDateString('pt-BR')}
                    </td>
                    <td className="p-4">
                      <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 border ${p.ativo ? 'border-green-500/30 text-green-400' : 'border-brand-border text-brand-muted'}`}>
                        {p.ativo ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="p-4 text-right whitespace-nowrap">
                      <button onClick={() => openPlanDetail(p.id)} className="text-brand-primary border border-brand-primary/30 px-2.5 py-1.5 font-mono text-xs uppercase mr-2 hover:bg-brand-primary/10">
                        <ClipboardList size={12} className="inline mr-1" /> Detalhes
                      </button>
                      {canEditStructure && (
                        <>
                          <button onClick={() => openPlanModal(p)} className="text-brand-primary border border-brand-primary/30 px-2.5 py-1.5 font-mono text-xs uppercase mr-2 hover:bg-brand-primary/10">
                            <Edit2 size={12} className="inline mr-1" /> Editar
                          </button>
                          <button onClick={() => deletePlan(p)} className="text-red-400 border border-red-500/30 px-2.5 py-1.5 font-mono text-xs uppercase hover:bg-red-500/10">
                            <Trash2 size={12} className="inline mr-1" /> Excluir
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
                {plans.length === 0 && (
                  <tr>
                    <td colSpan={7} className="p-12 text-center text-brand-muted font-mono text-sm">
                      Nenhum plano cadastrado.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ---------- ORDENS ---------- */}
      {!loading && tab === 'ordens' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <select
              value={orderStatusFilter}
              onChange={(e) => setOrderStatusFilter(e.target.value)}
              className="bg-brand-dark border border-brand-border px-3 py-2 text-sm font-mono text-brand-text focus:outline-none focus:border-brand-primary"
            >
              <option value="">Todos os status</option>
              {PM_STATUSES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            {canEditStructure && (
              <button
                onClick={openOrderModal}
                className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs flex items-center space-x-1.5"
              >
                <Plus size={16} />
                <span>Nova OS</span>
              </button>
            )}
          </div>

          <div className="border border-brand-border bg-brand-card overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">
                  <th className="p-4">OS</th>
                  <th className="p-4">Ativo</th>
                  <th className="p-4">Tipo</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Prioridade</th>
                  <th className="p-4">Abertura</th>
                  <th className="p-4 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border/60 text-sm">
                {orders.filter((o) => !orderStatusFilter || o.status === orderStatusFilter).map((o) => (
                  <tr key={o.id} className="hover:bg-brand-dark/10">
                    <td className="p-4 font-mono text-xs text-brand-primary">{o.numero}</td>
                    <td className="p-4">
                      <div className="text-brand-text">{o.asset?.nome ?? o.infra_predial_servico ?? '—'}</div>
                      {o.asset?.e_patrimonio && <div className="text-xs text-brand-muted font-mono">{o.asset.e_patrimonio}</div>}
                    </td>
                    <td className="p-4 text-brand-text">{o.tipo}</td>
                    <td className="p-4">
                      <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 border ${statusColor[o.status] ?? 'border-brand-border'}`}>
                        {o.status}
                      </span>
                    </td>
                    <td className="p-4 text-brand-text">{o.prioridade}</td>
                    <td className="p-4">
                      <div className="font-mono text-xs">{new Date(o.data_abertura).toLocaleDateString('pt-BR')}</div>
                      <div className="font-mono text-[11px] text-brand-primary mt-1">
                        {formatMinutes(calculateElapsedMinutes(o))}
                      </div>
                    </td>
                    <td className="p-4 text-right">
                      <button onClick={() => openOrderDetail(o.id)} className="text-brand-primary border border-brand-primary/30 px-2.5 py-1.5 font-mono text-xs uppercase hover:bg-brand-primary/10">
                        <FileText size={12} className="inline mr-1" /> Abrir
                      </button>
                    </td>
                  </tr>
                ))}
                {orders.length === 0 && (
                  <tr>
                    <td colSpan={7} className="p-12 text-center text-brand-muted font-mono text-sm">
                      Nenhuma ordem de serviço.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ---------- NOTIFICAÇÕES ---------- */}
      {!loading && tab === 'notifs' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={async () => {
                await preventiveApi.markNotificationsRead();
                setNotifs(await preventiveApi.myNotifications());
              }}
              className="border border-brand-border px-3 py-2 font-mono text-xs uppercase hover:bg-brand-card"
            >
              Marcar todas como lidas
            </button>
          </div>
          <div className="space-y-2">
            {notifs.map((n) => (
              <div key={n.id} className={`border p-4 ${n.lida ? 'border-brand-border bg-brand-card/50' : 'border-brand-primary/40 bg-brand-card'}`}>
                <div className="flex items-center justify-between">
                  <span className={`text-xs font-mono uppercase ${n.lida ? 'text-brand-muted' : 'text-brand-primary'}`}>
                    <Bell size={12} className="inline mr-1" />
                    {n.tipo}
                  </span>
                  <span className="text-xs font-mono text-brand-muted">
                    {new Date(n.data_criacao).toLocaleString('pt-BR')}
                  </span>
                </div>
                <pre className="mt-2 text-sm text-brand-text font-sans whitespace-pre-wrap m-0">{n.mensagem}</pre>
              </div>
            ))}
            {notifs.length === 0 && (
              <div className="p-12 text-center text-brand-muted font-mono text-sm">
                Nenhuma notificação.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ---------- PLAN MODAL ---------- */}
      {planModal && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-2xl border border-brand-border bg-brand-card p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">
                {editPlanId ? 'Editar Plano' : 'Novo Plano'}
              </h3>
              <button onClick={() => setPlanModal(false)} className="text-brand-muted hover:text-brand-text">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={submitPlan} className="space-y-4">
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Nome do Plano *</label>
                <input type="text" required value={pNome} onChange={(e) => setPNome(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary" />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Tipo</label>
                  <select value={pTipo} onChange={(e) => setPTipo(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                    {PM_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Periodicidade</label>
                  <select value={pPeriod} onChange={(e) => setPPeriod(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                    {PM_PERIODICITIES.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
              </div>

              {pPeriod === 'Personalizada' && (
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Dias personalizados</label>
                  <input type="number" value={pDias} onChange={(e) => setPDias(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" />
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Criticidade</label>
                  <select value={pCrit} onChange={(e) => setPCrit(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                    {PM_CRITICALITIES.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Prioridade</label>
                  <select value={pPrio} onChange={(e) => setPPrio(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                    {PM_PRIORITIES.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Responsável</label>
                <select value={pResponsavel ?? ''} onChange={(e) => setPResponsavel(e.target.value ? Number(e.target.value) : null)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                  <option value="">—</option>
                  {techs.map((t) => <option key={t.id} value={t.id}>{t.nome}</option>)}
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Descrição</label>
                <textarea value={pDesc} onChange={(e) => setPDesc(e.target.value)} rows={3}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" />
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-brand-border">
                <button type="button" onClick={() => setPlanModal(false)}
                  className="border border-brand-border hover:bg-brand-card px-4 py-2 font-mono text-xs uppercase">Cancelar</button>
                <button type="submit"
                  className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs">Confirmar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ---------- PLAN DETAIL MODAL ---------- */}
      {planDetail && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-3xl border border-brand-border bg-brand-card p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <div>
                <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">{planDetail.plan.nome}</h3>
                <span className="text-xs font-mono text-brand-primary">{planDetail.plan.codigo}</span>
              </div>
              <button onClick={() => setPlanDetail(null)} className="text-brand-muted hover:text-brand-text">
                <X size={20} />
              </button>
            </div>

            {planDetail.plan.checklists?.map((cl) => (
              <div key={cl.id} className="border border-brand-border">
                <div className="p-3 border-b border-brand-border bg-brand-dark/20 flex justify-between items-center">
                  <span className="text-xs font-mono uppercase tracking-wider text-brand-text">{cl.nome}</span>
                  {canEditStructure && (
                    <button
                      onClick={async () => {
                        if (!window.confirm('Excluir checklist?')) return;
                        await preventiveApi.deleteChecklist(planDetail.plan.id, cl.id);
                        await openPlanDetail(planDetail.plan.id);
                      }}
                      className="text-red-400 border border-red-500/30 px-2 py-1"
                    >
                      <Trash2 size={12} />
                    </button>
                  )}
                </div>
                <div className="divide-y divide-brand-border/60">
                  {cl.items.map((item) => (
                    <div key={item.id} className="p-3 flex justify-between items-center text-sm">
                      <span className="text-brand-text">{item.descricao}</span>
                      <span className="text-xs font-mono text-brand-muted">
                        {item.obrigatorio && 'OBRIGATÓRIO'} {item.requer_foto && '· FOTO'}
                      </span>
                    </div>
                  ))}
                  {cl.items.length === 0 && (
                    <div className="p-4 text-center text-brand-muted font-mono text-xs">Sem itens.</div>
                  )}
                </div>
              </div>
            ))}

            <div className="grid grid-cols-2 gap-4">
              <div className="border border-brand-border bg-brand-dark/20 p-4">
                <div className="text-xs font-mono uppercase text-brand-muted mb-2">OS do plano</div>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {planDetail.orders.map((o) => (
                    <div key={o.id} className="text-xs font-mono text-brand-text">
                      {o.numero} — <span className="text-brand-muted">{o.status}</span>
                    </div>
                  ))}
                  {planDetail.orders.length === 0 && (
                    <div className="text-xs text-brand-muted font-mono">Nenhuma OS gerada.</div>
                  )}
                </div>
              </div>
              <div className="border border-brand-border bg-brand-dark/20 p-4">
                <div className="text-xs font-mono uppercase text-brand-muted mb-2">Ativos vinculados</div>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {planDetail.plan.assets?.map((pa) => (
                    <div key={pa.id} className="text-xs font-mono text-brand-text">
                      {pa.asset?.nome ?? '—'} {pa.asset?.e_patrimonio ? `(${pa.asset.e_patrimonio})` : ''}
                    </div>
                  ))}
                  {(!planDetail.plan.assets || planDetail.plan.assets.length === 0) && (
                    <div className="text-xs text-brand-muted font-mono">Sem ativos vinculados.</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ---------- ORDER MODAL ---------- */}
      {orderModal && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-2xl border border-brand-border bg-brand-card p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">Nova Ordem de Serviço</h3>
              <button onClick={() => setOrderModal(false)} className="text-brand-muted hover:text-brand-text">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={submitOrder} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Tipo</label>
                  <select value={oTipo} onChange={(e) => setOTipo(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                    {PM_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Prioridade</label>
                  <select value={oPrio} onChange={(e) => setOPrio(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                    {PM_PRIORITIES.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Ativo</label>
                  <select value={oAsset ?? ''} onChange={(e) => setOAsset(e.target.value ? Number(e.target.value) : null)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                    <option value="">—</option>
                    {assets.map((a) => <option key={a.id} value={a.id}>{a.nome}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Técnico</label>
                  <select value={oTecnico ?? ''} onChange={(e) => setOTecnico(e.target.value ? Number(e.target.value) : null)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                    <option value="">—</option>
                    {techs.map((t) => <option key={t.id} value={t.id}>{t.nome}</option>)}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Plano (opcional)</label>
                  <select value={oPlan ?? ''} onChange={async (e) => {
                    const planId = e.target.value ? Number(e.target.value) : null;
                    setOPlan(planId);
                    await loadChecklistDraftsFromPlan(planId);
                  }}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                    <option value="">—</option>
                    {plans.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Data agendada</label>
                  <input type="datetime-local" value={oAgendada} onChange={(e) => setOAgendada(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Serviço de Infra Predial (se não houver ativo)</label>
                <input type="text" value={oInfra} onChange={(e) => setOInfra(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Descrição *</label>
                <textarea required value={oDesc} onChange={(e) => setODesc(e.target.value)} rows={3}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" />
              </div>

              <div className="border border-brand-border bg-brand-dark/20 p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs font-mono uppercase tracking-wider text-brand-muted">Checklist da OS</div>
                    <div className="text-xs text-brand-muted mt-1">
                      Administradores e gerentes podem ajustar o procedimento desta ordem antes de abrir o atendimento.
                    </div>
                  </div>
                  {canEditStructure && (
                    <button
                      type="button"
                      onClick={() => setOrderChecklistDrafts((current) => [...current, createEmptyChecklistDraft()])}
                      className="border border-brand-primary/30 text-brand-primary px-3 py-2 font-mono text-xs uppercase hover:bg-brand-primary/10"
                    >
                      <Plus size={12} className="inline mr-1" /> Checklist
                    </button>
                  )}
                </div>

                <div className="space-y-3">
                  {orderChecklistDrafts.map((checklist, checklistIndex) => (
                    <div key={checklistIndex} className="border border-brand-border bg-brand-card/40 p-3 space-y-3">
                      <div className="flex items-center gap-3">
                        <input
                          type="text"
                          value={checklist.nome}
                          onChange={(e) => setOrderChecklistDrafts((current) => current.map((item, index) => index === checklistIndex ? { ...item, nome: e.target.value } : item))}
                          disabled={!canEditStructure}
                          className="flex-1 bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none"
                          placeholder="Nome do checklist"
                        />
                        {canEditStructure && orderChecklistDrafts.length > 1 && (
                          <button
                            type="button"
                            onClick={() => setOrderChecklistDrafts((current) => current.filter((_, index) => index !== checklistIndex))}
                            className="text-red-400 border border-red-500/30 px-2 py-2"
                          >
                            <Trash2 size={12} />
                          </button>
                        )}
                      </div>

                      <div className="space-y-2">
                        {checklist.items.map((item, itemIndex) => (
                          <div key={itemIndex} className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto_auto] gap-2 items-center">
                            <input
                              type="text"
                              value={item.descricao}
                              onChange={(e) => setOrderChecklistDrafts((current) => current.map((currentChecklist, currentChecklistIndex) => currentChecklistIndex === checklistIndex ? {
                                ...currentChecklist,
                                items: currentChecklist.items.map((currentItem, currentItemIndex) => currentItemIndex === itemIndex ? { ...currentItem, descricao: e.target.value } : currentItem),
                              } : currentChecklist))}
                              disabled={!canEditStructure}
                              className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none"
                              placeholder="Descreva a atividade obrigatória ou opcional"
                            />
                            <label className="flex items-center gap-2 text-xs font-mono text-brand-muted uppercase">
                              <input
                                type="checkbox"
                                checked={item.obrigatorio}
                                disabled={!canEditStructure}
                                onChange={(e) => setOrderChecklistDrafts((current) => current.map((currentChecklist, currentChecklistIndex) => currentChecklistIndex === checklistIndex ? {
                                  ...currentChecklist,
                                  items: currentChecklist.items.map((currentItem, currentItemIndex) => currentItemIndex === itemIndex ? { ...currentItem, obrigatorio: e.target.checked } : currentItem),
                                } : currentChecklist))}
                                className="accent-brand-primary"
                              />
                              Obrigatório
                            </label>
                            <label className="flex items-center gap-2 text-xs font-mono text-brand-muted uppercase">
                              <input
                                type="checkbox"
                                checked={item.requer_foto}
                                disabled={!canEditStructure}
                                onChange={(e) => setOrderChecklistDrafts((current) => current.map((currentChecklist, currentChecklistIndex) => currentChecklistIndex === checklistIndex ? {
                                  ...currentChecklist,
                                  items: currentChecklist.items.map((currentItem, currentItemIndex) => currentItemIndex === itemIndex ? { ...currentItem, requer_foto: e.target.checked } : currentItem),
                                } : currentChecklist))}
                                className="accent-brand-primary"
                              />
                              Foto
                            </label>
                            {canEditStructure && (
                              <button
                                type="button"
                                onClick={() => setOrderChecklistDrafts((current) => current.map((currentChecklist, currentChecklistIndex) => currentChecklistIndex === checklistIndex ? {
                                  ...currentChecklist,
                                  items: currentChecklist.items.filter((_, currentItemIndex) => currentItemIndex !== itemIndex),
                                } : currentChecklist))}
                                className="text-red-400 border border-red-500/30 px-2 py-2"
                              >
                                <Trash2 size={12} />
                              </button>
                            )}
                          </div>
                        ))}
                      </div>

                      {canEditStructure && (
                        <button
                          type="button"
                          onClick={() => setOrderChecklistDrafts((current) => current.map((item, index) => index === checklistIndex ? { ...item, items: [...item.items, createEmptyChecklistItem()] } : item))}
                          className="border border-brand-border px-3 py-2 font-mono text-xs uppercase hover:bg-brand-card"
                        >
                          <Plus size={12} className="inline mr-1" /> Item
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-brand-border">
                <button type="button" onClick={() => setOrderModal(false)}
                  className="border border-brand-border hover:bg-brand-card px-4 py-2 font-mono text-xs uppercase">Cancelar</button>
                <button type="submit"
                  className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs">Criar OS</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ---------- ORDER DETAIL MODAL ---------- */}
      {orderDetail && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-4xl border border-brand-border bg-brand-card p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <div>
                <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">
                  OS {orderDetail.order.numero}
                </h3>
                <div className="flex items-center space-x-2 mt-1">
                  <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 border ${statusColor[orderDetail.order.status] ?? 'border-brand-border'}`}>
                    {orderDetail.order.status}
                  </span>
                  <span className="text-xs font-mono text-brand-muted">
                    {orderDetail.order.asset?.nome ?? orderDetail.order.infra_predial_servico ?? '—'}
                  </span>
                  <span className="text-xs font-mono text-brand-primary">
                    {formatMinutes(calculateElapsedMinutes(orderDetail.order))}
                  </span>
                </div>
              </div>
              <button onClick={() => setOrderDetail(null)} className="text-brand-muted hover:text-brand-text">
                <X size={20} />
              </button>
            </div>

            {/* Status actions */}
            <div className="flex flex-wrap gap-2">
              {canWorkOrder && (orderDetail.order.status === 'Aberta' || orderDetail.order.status === 'Agendada' || orderDetail.order.status === 'Pausada') && (
                <button onClick={() => orderAction(orderDetail.order.id, 'iniciar')}
                  className="bg-yellow-500/10 text-yellow-400 border border-yellow-500/30 px-3 py-2 font-mono text-xs uppercase hover:bg-yellow-500/20">
                  <Play size={12} className="inline mr-1" /> Iniciar
                </button>
              )}
              {canWorkOrder && orderDetail.order.status === 'Em andamento' && (
                <button onClick={() => orderAction(orderDetail.order.id, 'pausar')}
                  className="bg-purple-500/10 text-purple-400 border border-purple-500/30 px-3 py-2 font-mono text-xs uppercase hover:bg-purple-500/20">
                  <Pause size={12} className="inline mr-1" /> Pausar
                </button>
              )}
              {canWorkOrder && !['Concluída', 'Cancelada'].includes(orderDetail.order.status) && (
                <>
                  <button onClick={() => orderAction(orderDetail.order.id, 'concluir')}
                    className="bg-green-500/10 text-green-400 border border-green-500/30 px-3 py-2 font-mono text-xs uppercase hover:bg-green-500/20">
                    <CheckCircle2 size={12} className="inline mr-1" /> Concluir
                  </button>
                  {canEditStructure && (
                    <button onClick={() => orderAction(orderDetail.order.id, 'cancelar')}
                      className="bg-red-500/10 text-red-400 border border-red-500/30 px-3 py-2 font-mono text-xs uppercase hover:bg-red-500/20">
                      <Ban size={12} className="inline mr-1" /> Cancelar
                    </button>
                  )}
                  {canEditStructure && orderDetail.order.status !== 'Concluída' && (
                    <button
                      onClick={() => deleteOrder(orderDetail.order.id)}
                      className="bg-red-950/40 text-red-300 border border-red-700/40 px-3 py-2 font-mono text-xs uppercase hover:bg-red-950/60"
                    >
                      <Trash2 size={12} className="inline mr-1" /> Excluir OS
                    </button>
                  )}
                </>
              )}
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="border border-brand-border bg-brand-dark/20 p-3">
                <div className="text-xs font-mono uppercase text-brand-muted mb-1">Técnico</div>
                <div className="text-sm text-brand-text">{orderDetail.order.tecnico?.nome ?? 'Não definido'}</div>
              </div>
              <div className="border border-brand-border bg-brand-dark/20 p-3">
                <div className="text-xs font-mono uppercase text-brand-muted mb-1">Materiais</div>
                <div className="text-sm text-brand-text">{orderDetail.order.materials.length} item(ns)</div>
              </div>
              <div className="border border-brand-border bg-brand-dark/20 p-3">
                <div className="text-xs font-mono uppercase text-brand-muted mb-1">Fotos</div>
                <div className="text-sm text-brand-text">{orderDetail.order.photos.length} evidência(s)</div>
              </div>
              <div className="border border-brand-border bg-brand-dark/20 p-3">
                <div className="text-xs font-mono uppercase text-brand-muted mb-1">Custo acumulado</div>
                <div className="text-sm text-brand-text">
                  R$ {orderDetail.order.materials.reduce((sum, item) => sum + item.valor_total, 0).toFixed(2)}
                </div>
              </div>
              <div className="border border-brand-border bg-brand-dark/20 p-3">
                <div className="text-xs font-mono uppercase text-brand-muted mb-1">Validador final</div>
                <div className="text-sm text-brand-text">{orderDetail.order.validado_por?.nome ?? 'Pendente'}</div>
              </div>
              <div className="border border-brand-border bg-brand-dark/20 p-3">
                <div className="text-xs font-mono uppercase text-brand-muted mb-1">Tempo da OS</div>
                <div className="text-sm text-brand-primary">{formatMinutes(calculateElapsedMinutes(orderDetail.order))}</div>
              </div>
            </div>

            {orderDetail.order.observacoes && (
              <div className="border border-brand-border bg-brand-dark/20 p-4">
                <div className="text-xs font-mono uppercase text-brand-muted mb-2">Escopo da manutenção</div>
                <div className="text-sm text-brand-text whitespace-pre-wrap">{orderDetail.order.observacoes}</div>
              </div>
            )}

            {/* Checklist execution */}
            {orderDetail.checklists.length > 0 && (
              <div className="border border-brand-border">
                <div className="p-3 border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted flex items-center">
                  <ClipboardList size={14} className="mr-2" /> Checklists
                </div>
                <div className="divide-y divide-brand-border/60">
                  {orderDetail.checklists.map((cl) => (
                    <div key={cl.id}>
                      <div className="p-3 text-sm font-bold text-brand-text font-mono">{cl.nome}</div>
                      {cl.items.map((item) => {
                        const exec = orderDetail.order.executions.find((e) => e.checklist_item_id === item.id);
                        return (
                          <div key={item.id} className="p-3 flex items-center justify-between border-t border-brand-border/40">
                            <div className="flex-1">
                              <span className={`text-sm ${exec?.concluido ? 'text-brand-muted line-through' : 'text-brand-text'}`}>
                                {item.descricao}
                              </span>
                              <div className="text-xs font-mono text-brand-muted">
                                {item.obrigatorio && 'OBRIGATÓRIO'} {item.requer_foto && '· REQUER FOTO'}
                                {exec?.executado_por && ` · ${exec.executado_por.nome}`}
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              {exec?.concluido && (
                                <span className="text-green-400 text-xs font-mono uppercase">Executado</span>
                              )}
                              <label className="flex items-center space-x-1 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={!!exec?.concluido}
                                  disabled={!canWorkOrder || ['Concluída', 'Cancelada'].includes(orderDetail.order.status)}
                                  onChange={async (e) => {
                                    const checked = e.target.checked;
                                    let foto: File | undefined;
                                    if (checked && item.requer_foto) {
                                      foto = await pickChecklistPhoto();
                                      if (!foto) {
                                        setError(`Selecione uma foto para concluir o item obrigatório "${item.descricao}".`);
                                        setTimeout(() => setError(null), 5000);
                                        return;
                                      }
                                    }
                                    try {
                                      await preventiveApi.executeChecklistItem(orderDetail.order.id, item.id, checked, undefined, foto);
                                      await refreshOrderDetail();
                                    } catch (err) {
                                      showError(err);
                                    }
                                  }}
                                  className="accent-brand-primary"
                                />
                                <Camera size={12} className="text-brand-muted" />
                              </label>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Materials */}
            <div className="border border-brand-border">
              <div className="p-3 border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted flex items-center">
                <Wrench size={14} className="mr-2" /> Materiais aplicados
              </div>
              {canWorkOrder && !['Concluída', 'Cancelada'].includes(orderDetail.order.status) && (
                <form onSubmit={submitMaterial} className="p-3 border-b border-brand-border/60 bg-brand-card/40 space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                    <input
                      type="text"
                      placeholder="Produto ou peça"
                      value={mProduto}
                      onChange={(e) => setMProduto(e.target.value)}
                      className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none"
                      required
                    />
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      placeholder="Quantidade"
                      value={mQuantidade}
                      onChange={(e) => setMQuantidade(e.target.value)}
                      className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none"
                      required
                    />
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      placeholder="Valor unitário"
                      value={mValorUnitario}
                      onChange={(e) => setMValorUnitario(e.target.value)}
                      className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none"
                      required
                    />
                    <button
                      type="submit"
                      className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs"
                    >
                      Adicionar material
                    </button>
                  </div>
                  <input
                    type="text"
                    placeholder="Observação do material aplicado (opcional)"
                    value={mObservacao}
                    onChange={(e) => setMObservacao(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none"
                  />
                </form>
              )}
              <div className="divide-y divide-brand-border/60">
                {orderDetail.order.materials.map((m) => (
                  <div key={m.id} className="p-3 flex justify-between items-center text-sm">
                    <div>
                      <div className="text-brand-text">{m.produto}</div>
                      <div className="text-xs font-mono text-brand-muted">x{m.quantidade} · R$ {m.valor_unitario.toFixed(2)}</div>
                      {m.observacao && <div className="text-xs text-brand-muted mt-1">{m.observacao}</div>}
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs text-brand-primary">R$ {m.valor_total.toFixed(2)}</span>
                      {canWorkOrder && (
                        <button
                          onClick={async () => {
                            if (!window.confirm('Remover material?')) return;
                            await preventiveApi.removeMaterial(orderDetail.order.id, m.id);
                            await refreshOrderDetail();
                          }}
                          className="text-red-400 border border-red-500/30 px-2 py-1"
                        >
                          <Trash2 size={12} />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
                {orderDetail.order.materials.length === 0 && (
                  <div className="p-4 text-center text-brand-muted font-mono text-xs">Nenhum material aplicado.</div>
                )}
              </div>
            </div>

            {/* Photos */}
            <div className="border border-brand-border">
              <div className="p-3 border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted flex items-center">
                <Camera size={14} className="mr-2" /> Fotos ({orderDetail.order.photos.length})
              </div>
              {canWorkOrder && !['Concluída', 'Cancelada'].includes(orderDetail.order.status) && (
                <form onSubmit={submitPhoto} className="p-3 border-b border-brand-border/60 bg-brand-card/40 space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                    <select
                      value={photoTipo}
                      onChange={(e) => setPhotoTipo(e.target.value)}
                      className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none"
                    >
                      <option value="Antes">Antes</option>
                      <option value="Durante">Durante</option>
                      <option value="Depois">Depois</option>
                    </select>
                    <input
                      type="text"
                      placeholder="Descrição da evidência"
                      value={photoDescricao}
                      onChange={(e) => setPhotoDescricao(e.target.value)}
                      className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none md:col-span-2"
                    />
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => setPhotoFile(e.target.files?.[0] ?? null)}
                      className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none"
                    />
                  </div>
                  <div className="flex justify-end">
                    <button
                      type="submit"
                      className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs"
                    >
                      Anexar foto
                    </button>
                  </div>
                </form>
              )}
              <div className="p-3 grid grid-cols-3 gap-3">
                {orderDetail.order.photos.map((p) => (
                  <div key={p.id} className="border border-brand-border p-2">
                    <img src={toApiFileUrl(p.caminho_arquivo)} alt={p.descricao ?? 'foto'} className="w-full h-28 object-cover" />
                    <div className="mt-1 text-xs font-mono text-brand-muted">{p.tipo}</div>
                    {p.descricao && <div className="text-xs text-brand-text mt-1">{p.descricao}</div>}
                    {canWorkOrder && (
                      <button
                        onClick={async () => {
                          if (!window.confirm('Excluir foto?')) return;
                          await preventiveApi.deletePhoto(orderDetail.order.id, p.id);
                          await refreshOrderDetail();
                        }}
                        className="text-red-400 text-xs font-mono uppercase mt-1"
                      >
                        Excluir
                      </button>
                    )}
                  </div>
                ))}
                {orderDetail.order.photos.length === 0 && (
                  <div className="col-span-3 p-4 text-center text-brand-muted font-mono text-xs">Nenhuma evidência fotográfica anexada.</div>
                )}
              </div>
            </div>

            {/* History */}
            <div className="border border-brand-border">
              <div className="p-3 border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">
                Histórico
              </div>
              <div className="divide-y divide-brand-border/60 max-h-56 overflow-y-auto">
                {orderDetail.order.history.map((h) => (
                  <div key={h.id} className="p-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-brand-primary font-mono text-xs uppercase">{h.acao}</span>
                      <span className="text-xs font-mono text-brand-muted">{new Date(h.data_hora).toLocaleString('pt-BR')}</span>
                    </div>
                    <div className="text-brand-text mt-1">{h.descricao}</div>
                    {h.usuario && <div className="text-xs font-mono text-brand-muted">por {h.usuario.nome}</div>}
                  </div>
                ))}
                {orderDetail.order.history.length === 0 && (
                  <div className="p-4 text-center text-brand-muted font-mono text-xs">Sem histórico.</div>
                )}
              </div>
            </div>

            {completeModal && (
              <div className="border border-green-500/30 bg-green-500/5 p-4 space-y-4">
                <div>
                  <div className="text-xs font-mono uppercase tracking-wider text-green-400">Encerramento assistido da OS</div>
                  <div className="text-sm text-brand-muted mt-1">
                    Registre o diagnóstico, a solução aplicada e as recomendações finais antes de concluir a ordem.
                  </div>
                </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="border border-brand-border bg-brand-dark/20 p-3">
                    <div className="text-xs font-mono uppercase text-brand-muted mb-1">Checklist obrigatório</div>
                    <div className="text-sm text-brand-text">
                      {orderDetail.checklists.flatMap((checklist) => checklist.items).filter((item) => item.obrigatorio).length === 0
                        ? 'Sem itens obrigatórios'
                        : `${orderDetail.checklists.flatMap((checklist) => checklist.items).filter((item) => item.obrigatorio && orderDetail.order.executions.some((execution) => execution.checklist_item_id === item.id && execution.concluido)).length}/${orderDetail.checklists.flatMap((checklist) => checklist.items).filter((item) => item.obrigatorio).length} concluídos`}
                    </div>
                  </div>
                  <div className="border border-brand-border bg-brand-dark/20 p-3">
                    <div className="text-xs font-mono uppercase text-brand-muted mb-1">Evidências fotográficas</div>
                    <div className="text-sm text-brand-text">{orderDetail.order.photos.length} anexo(s)</div>
                  </div>
                  <div className="border border-brand-border bg-brand-dark/20 p-3">
                    <div className="text-xs font-mono uppercase text-brand-muted mb-1">Custo de materiais</div>
                    <div className="text-sm text-brand-text">
                      R$ {orderDetail.order.materials.reduce((sum, item) => sum + item.valor_total, 0).toFixed(2)}
                    </div>
                  </div>
                </div>

                <form onSubmit={submitCompletion} className="space-y-3">
                  <div>
                    <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Diagnóstico final *</label>
                    <textarea
                      required
                      value={completionDiagnosis}
                      onChange={(e) => setCompletionDiagnosis(e.target.value)}
                      rows={3}
                      className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none"
                      placeholder="Descreva a causa encontrada e o estado do ativo no momento do atendimento."
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Solução aplicada *</label>
                    <textarea
                      required
                      value={completionSolution}
                      onChange={(e) => setCompletionSolution(e.target.value)}
                      rows={3}
                      className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none"
                      placeholder="Informe o procedimento executado, troca de peças, ajustes, limpeza ou atualização realizada."
                    />
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Recomendações finais</label>
                      <textarea
                        value={completionRecommendations}
                        onChange={(e) => setCompletionRecommendations(e.target.value)}
                        rows={3}
                        className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none"
                        placeholder="Ex.: monitorar temperatura, trocar bateria no próximo ciclo, orientar usuário..."
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Destino final do ativo *</label>
                      <select
                        value={completionAssetDestination}
                        onChange={(e) => setCompletionAssetDestination(e.target.value)}
                        className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none mb-3"
                      >
                        <option value="Disponível">Liberado para uso / Disponível</option>
                        <option value="Armazenado">Armazenado após manutenção</option>
                        <option value="Manutenção">Manter em manutenção / nova intervenção</option>
                      </select>
                      <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Custo adicional extra (R$)</label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={completionExtraCost}
                        onChange={(e) => setCompletionExtraCost(e.target.value)}
                        className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none"
                        placeholder="0,00"
                      />
                      <p className="text-xs text-brand-muted mt-2">
                        O sistema soma esse valor ao custo já registrado em materiais e atualiza o status do ativo no encerramento.
                      </p>
                    </div>
                  </div>

                  <div className="flex justify-end space-x-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setCompleteModal(false)}
                      className="border border-brand-border hover:bg-brand-card px-4 py-2 font-mono text-xs uppercase"
                    >
                      Voltar
                    </button>
                    <button
                      type="submit"
                      className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs"
                    >
                      Confirmar encerramento
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
