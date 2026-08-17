import React, { useState, useEffect } from 'react';
import { preventiveApi } from '../api/preventive';
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

const canManage = ['admin', 'gerente_ti', 'gerente_infra', 'tecnico', 'comprador'];

const statusColor: Record<string, string> = {
  'Aberta': 'text-blue-400 border-blue-500/30',
  'Agendada': 'text-cyan-400 border-cyan-500/30',
  'Em andamento': 'text-yellow-400 border-yellow-500/30',
  'Aguardando peça': 'text-orange-400 border-orange-500/30',
  'Pausada': 'text-purple-400 border-purple-500/30',
  'Concluída': 'text-green-400 border-green-500/30',
  'Cancelada': 'text-red-400 border-red-500/30',
};

export const PreventiveMaintenancePage: React.FC = () => {
  const user = useAuthStore().user;
  const manage = user ? canManage.includes(user.role) : false;

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
    setOrderModal(true);
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
      });
      setOrderModal(false);
      fetchAll();
    } catch (err) {
      showError(err);
    }
  };

  const openOrderDetail = async (orderId: number) => {
    try {
      setOrderDetail(await preventiveApi.getOrder(orderId));
    } catch (err) {
      showError(err);
    }
  };

  const orderAction = async (orderId: number, action: 'iniciar' | 'pausar' | 'concluir' | 'cancelar') => {
    try {
      if (action === 'iniciar') await preventiveApi.startOrder(orderId);
      else if (action === 'pausar') await preventiveApi.pauseOrder(orderId, window.prompt('Motivo da pausa (opcional):') ?? undefined);
      else if (action === 'cancelar') await preventiveApi.cancelOrder(orderId, window.prompt('Motivo do cancelamento (opcional):') ?? undefined);
      else {
        const solucao = window.prompt('Solução aplicada:') ?? '';
        const custo = window.prompt('Custo adicional (R$):') ?? '';
        await preventiveApi.completeOrder(orderId, solucao, custo);
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
        </div>
      )}

      {/* ---------- PLANOS ---------- */}
      {!loading && tab === 'planos' && (
        <div className="space-y-4">
          {manage && (
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
                      {manage && (
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
            {manage && (
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
                    <td className="p-4 font-mono text-xs">{new Date(o.data_abertura).toLocaleDateString('pt-BR')}</td>
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
                  {manage && (
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
                  <select value={oPlan ?? ''} onChange={(e) => setOPlan(e.target.value ? Number(e.target.value) : null)}
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
                </div>
              </div>
              <button onClick={() => setOrderDetail(null)} className="text-brand-muted hover:text-brand-text">
                <X size={20} />
              </button>
            </div>

            {/* Status actions */}
            <div className="flex flex-wrap gap-2">
              {(orderDetail.order.status === 'Aberta' || orderDetail.order.status === 'Agendada' || orderDetail.order.status === 'Pausada') && (
                <button onClick={() => orderAction(orderDetail.order.id, 'iniciar')}
                  className="bg-yellow-500/10 text-yellow-400 border border-yellow-500/30 px-3 py-2 font-mono text-xs uppercase hover:bg-yellow-500/20">
                  <Play size={12} className="inline mr-1" /> Iniciar
                </button>
              )}
              {orderDetail.order.status === 'Em andamento' && (
                <button onClick={() => orderAction(orderDetail.order.id, 'pausar')}
                  className="bg-purple-500/10 text-purple-400 border border-purple-500/30 px-3 py-2 font-mono text-xs uppercase hover:bg-purple-500/20">
                  <Pause size={12} className="inline mr-1" /> Pausar
                </button>
              )}
              {!['Concluída', 'Cancelada'].includes(orderDetail.order.status) && (
                <>
                  <button onClick={() => orderAction(orderDetail.order.id, 'concluir')}
                    className="bg-green-500/10 text-green-400 border border-green-500/30 px-3 py-2 font-mono text-xs uppercase hover:bg-green-500/20">
                    <CheckCircle2 size={12} className="inline mr-1" /> Concluir
                  </button>
                  {manage && (
                    <button onClick={() => orderAction(orderDetail.order.id, 'cancelar')}
                      className="bg-red-500/10 text-red-400 border border-red-500/30 px-3 py-2 font-mono text-xs uppercase hover:bg-red-500/20">
                      <Ban size={12} className="inline mr-1" /> Cancelar
                    </button>
                  )}
                </>
              )}
            </div>

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
                                  onChange={async (e) => {
                                    const checked = e.target.checked;
                                    let foto: File | undefined;
                                    if (checked && item.requer_foto) {
                                      const input = document.createElement('input');
                                      input.type = 'file';
                                      input.accept = 'image/*';
                                      input.onchange = () => { foto = input.files?.[0]; };
                                      input.click();
                                      await new Promise((res) => setTimeout(res, 1500));
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
              <div className="divide-y divide-brand-border/60">
                {orderDetail.order.materials.map((m) => (
                  <div key={m.id} className="p-3 flex justify-between items-center text-sm">
                    <div>
                      <div className="text-brand-text">{m.produto}</div>
                      <div className="text-xs font-mono text-brand-muted">x{m.quantidade} · R$ {m.valor_unitario.toFixed(2)}</div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs text-brand-primary">R$ {m.valor_total.toFixed(2)}</span>
                      {manage && (
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
              <div className="p-3 grid grid-cols-3 gap-3">
                {orderDetail.order.photos.map((p) => (
                  <div key={p.id} className="border border-brand-border p-2">
                    <img src={p.caminho_arquivo} alt={p.descricao ?? 'foto'} className="w-full h-28 object-cover" />
                    <div className="mt-1 text-xs font-mono text-brand-muted">{p.tipo}</div>
                    {manage && (
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
          </div>
        </div>
      )}
    </div>
  );
};
