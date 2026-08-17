import React, { useState, useEffect } from 'react';
import { procurementApi } from '../api/procurement';
import { suppliersApi } from '../api/suppliers';
import type {
  PurchaseRequest,
  PurchaseOrder,
  MaterialStock,
  PurchaseQuotation,
  ProcurementDashboard,
  CostCenter,
  PurchaseProduct,
} from '../types/procurement';
import { URGENCIES, requestStatusColor, orderStatusColor } from '../types/procurement';
import { useAuthStore } from '../stores/authStore';
import {
  Plus, X, ShieldAlert, Package, Gavel, CheckCircle2, Ban,
  ClipboardList, ArrowRightCircle,
} from 'lucide-react';

const canManage = ['admin', 'gerente_ti', 'gerente_infra', 'comprador'];

export const ProcurementPage: React.FC = () => {
  const user = useAuthStore().user;
  const manage = user ? canManage.includes(user.role) : false;

  const [tab, setTab] = useState<'dashboard' | 'solicitacoes' | 'ordens' | 'estoque' | 'cotacoes'>('dashboard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [dash, setDash] = useState<ProcurementDashboard | null>(null);
  const [requests, setRequests] = useState<PurchaseRequest[]>([]);
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [stock, setStock] = useState<MaterialStock[]>([]);
  const [quotations, setQuotations] = useState<PurchaseQuotation[]>([]);

  const [costCenters, setCostCenters] = useState<CostCenter[]>([]);
  const [products, setProducts] = useState<PurchaseProduct[]>([]);
  const [suppliers, setSuppliers] = useState<{ id: number; nome: string }[]>([]);

  // Request modal
  const [reqModal, setReqModal] = useState(false);
  const [rCC, setRCC] = useState<number | null>(null);
  const [rJust, setRJust] = useState('');
  const [rUrgencia, setRUrgencia] = useState('Média');
  const [rItens, setRItens] = useState<{ product_id: number; quantidade: number; valor_estimado: number }[]>([{ product_id: 0, quantidade: 1, valor_estimado: 0 }]);

  // Quotation modal
  const [quotModal, setQuotModal] = useState(false);
  const [qRequestId, setQRequestId] = useState<number | null>(null);
  const [qSuppliers, setQSuppliers] = useState<{ fornecedor_id: number; frete: number; prazo_entrega_dias: number; itens: { product_id: number; quantidade: number; valor_unitario: number }[] }[]>([]);

  // Order modal
  const [orderModal, setOrderModal] = useState(false);
  const [oSupplier, setOSupplier] = useState<number | null>(null);
  const [oCC, setOCC] = useState<number | null>(null);
  const [oItens, setOItens] = useState<{ product_id: number; quantidade: number; valor_unitario: number }[]>([{ product_id: 0, quantidade: 1, valor_unitario: 0 }]);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [d, r, o, s, q] = await Promise.all([
        procurementApi.dashboard(),
        procurementApi.listRequests(),
        procurementApi.listOrders(),
        procurementApi.listStock(),
        procurementApi.listQuotations(),
      ]);
      setDash(d);
      setRequests(r);
      setOrders(o);
      setStock(s);
      setQuotations(q);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
    procurementApi.listCostCenters().then(setCostCenters).catch(() => {});
    procurementApi.listProducts().then(setProducts).catch(() => {});
    suppliersApi.list(0, 200).then((s) => setSuppliers(s.map((x) => ({ id: x.id, nome: x.nome })))).catch(() => {});
  }, []);

  const showError = (err: any) => {
    setError(err.response?.data?.error || 'Erro na operação');
    setTimeout(() => setError(null), 5000);
  };

  // ---- Requests ----
  const submitRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rCC) { showError({ response: { data: { error: 'Selecione o centro de custo' } } }); return; }
    try {
      await procurementApi.createRequest({
        centro_custo_id: rCC,
        justificativa: rJust,
        urgencia: rUrgencia,
        itens: rItens.filter((i) => i.product_id && i.quantidade > 0),
      });
      setReqModal(false);
      setRCC(null); setRJust(''); setRUrgencia('Média');
      setRItens([{ product_id: 0, quantidade: 1, valor_estimado: 0 }]);
      fetchAll();
    } catch (err) {
      showError(err);
    }
  };

  const decideRequest = async (req: PurchaseRequest, decisao: 'Aprovado' | 'Reprovado') => {
    const nivel = window.prompt('Nível de aprovação (Gestor, Gerente, Financeiro, Diretoria, Compras):', 'Compras') ?? 'Compras';
    const obs = decisao === 'Reprovado' ? window.prompt('Motivo da reprovação:') ?? undefined : undefined;
    try {
      await procurementApi.decideRequest(req.id, nivel, decisao, obs);
      fetchAll();
    } catch (err) {
      showError(err);
    }
  };

  const releaseBudget = async (req: PurchaseRequest) => {
    if (!window.confirm(`Liberar orçamento da solicitação ${req.numero}?`)) return;
    try {
      await procurementApi.releaseBudget(req.id);
      fetchAll();
    } catch (err) {
      showError(err);
    }
  };

  // ---- Quotations ----
  const openQuotationModal = (req: PurchaseRequest) => {
    setQRequestId(req.id);
    setQSuppliers(req.itens.map((it) => ({
      fornecedor_id: it.fornecedor_sugerido_id ?? 0,
      frete: 0,
      prazo_entrega_dias: 0,
      itens: [{ product_id: it.product_id, quantidade: it.quantidade, valor_unitario: it.valor_estimado }],
    })));
    setQuotModal(true);
  };

  const submitQuotation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!qRequestId) return;
    try {
      await procurementApi.createQuotation(
        qRequestId,
        qSuppliers.filter((s) => s.fornecedor_id && s.itens.length > 0),
      );
      setQuotModal(false);
      setQRequestId(null);
      fetchAll();
    } catch (err) {
      showError(err);
    }
  };

  const selectWinner = async (quotationId: number, supplierId: number) => {
    if (!window.confirm('Confirmar este fornecedor como vencedor e emitir o Pedido de Compra?')) return;
    try {
      await procurementApi.selectWinner(quotationId, supplierId);
      fetchAll();
    } catch (err) {
      showError(err);
    }
  };

  // ---- Orders ----
  const submitOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!oSupplier || !oCC) { showError({ response: { data: { error: 'Selecione fornecedor e centro de custo' } } }); return; }
    try {
      await procurementApi.createOrder({
        fornecedor_id: oSupplier,
        centro_custo_id: oCC,
        itens: oItens.filter((i) => i.product_id && i.quantidade > 0),
      });
      setOrderModal(false);
      setOSupplier(null); setOCC(null);
      setOItens([{ product_id: 0, quantidade: 1, valor_unitario: 0 }]);
      fetchAll();
    } catch (err) {
      showError(err);
    }
  };

  const receiveOrder = async (order: PurchaseOrder) => {
    const itens = order.itens.map((it) => ({ product_id: it.product_id, quantidade_recebida: it.quantidade }));
    if (!window.confirm(`Registrar recebimento total do pedido ${order.numero}?`)) return;
    try {
      await procurementApi.receiveOrder(order.id, { itens, observacoes: 'Recebimento total' });
      fetchAll();
    } catch (err) {
      showError(err);
    }
  };

  const fmt = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0">Compras</h1>
          <p className="text-brand-muted text-sm mt-1">Solicitações, cotações, pedidos de compra e estoque.</p>
        </div>
      </div>

      {error && (
        <div className="p-3 border border-red-500/30 bg-red-500/5 text-red-400 text-xs font-mono flex items-center space-x-2">
          <ShieldAlert size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex space-x-1 border-b border-brand-border overflow-x-auto">
        {([
          ['dashboard', 'Dashboard'],
          ['solicitacoes', 'Solicitações'],
          ['cotacoes', 'Cotações'],
          ['ordens', 'Ordens de Compra'],
          ['estoque', 'Estoque'],
        ] as const).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2.5 font-mono text-xs uppercase tracking-wider border-b-2 transition-colors whitespace-nowrap ${
              tab === key ? 'border-brand-primary text-brand-primary' : 'border-transparent text-brand-muted hover:text-brand-text'
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border border-brand-border bg-brand-card p-4">
            <div className="text-3xl font-bold font-mono text-brand-primary">{dash.req_pending_count}</div>
            <div className="text-xs font-mono uppercase text-brand-muted mt-1">Solicitações pendentes</div>
          </div>
          <div className="border border-brand-border bg-brand-card p-4">
            <div className="text-3xl font-bold font-mono text-brand-primary">{dash.orders_active_count}</div>
            <div className="text-xs font-mono uppercase text-brand-muted mt-1">Pedidos em aberto</div>
          </div>
          <div className="border border-brand-border bg-brand-card p-4">
            <div className="text-3xl font-bold font-mono text-brand-primary">{dash.low_stock_count}</div>
            <div className="text-xs font-mono uppercase text-brand-muted mt-1">Itens com estoque baixo</div>
          </div>

          <div className="md:col-span-3 border border-brand-border bg-brand-card">
            <div className="p-3 border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">Solicitações recentes</div>
            <div className="divide-y divide-brand-border/60">
              {dash.requests_recent.map((r) => (
                <div key={r.id} className="p-3 flex justify-between items-center text-sm">
                  <span className="font-mono text-brand-primary text-xs">{r.numero}</span>
                  <span className="text-brand-text">{r.justificativa.slice(0, 60)}</span>
                  <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 border ${requestStatusColor[r.status] ?? 'border-brand-border'}`}>{r.status}</span>
                </div>
              ))}
              {dash.requests_recent.length === 0 && <div className="p-4 text-center text-brand-muted font-mono text-xs">Nenhuma solicitação.</div>}
            </div>
          </div>
        </div>
      )}

      {/* ---------- SOLICITAÇÕES ---------- */}
      {!loading && tab === 'solicitacoes' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button onClick={() => setReqModal(true)} className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs flex items-center space-x-1.5">
              <Plus size={16} /> <span>Nova Solicitação</span>
            </button>
          </div>
          <div className="border border-brand-border bg-brand-card overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">
                  <th className="p-4">Número</th>
                  <th className="p-4">Centro de Custo</th>
                  <th className="p-4">Justificativa</th>
                  <th className="p-4">Urgência</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border/60 text-sm">
                {requests.map((r) => (
                  <tr key={r.id} className="hover:bg-brand-dark/10">
                    <td className="p-4 font-mono text-xs text-brand-primary">{r.numero}</td>
                    <td className="p-4 text-brand-text">{r.centro_custo?.nome ?? `#${r.centro_custo_id}`}</td>
                    <td className="p-4 text-brand-text max-w-xs truncate">{r.justificativa}</td>
                    <td className="p-4 text-brand-text">{r.urgencia}</td>
                    <td className="p-4">
                      <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 border ${requestStatusColor[r.status] ?? 'border-brand-border'}`}>{r.status}</span>
                    </td>
                    <td className="p-4 text-right whitespace-nowrap">
                      {manage && r.status === 'Pendente' && (
                        <>
                          <button onClick={() => decideRequest(r, 'Aprovado')} className="text-green-400 border border-green-500/30 px-2.5 py-1.5 font-mono text-xs uppercase mr-2 hover:bg-green-500/10">
                            <CheckCircle2 size={12} className="inline mr-1" /> Aprovar
                          </button>
                          <button onClick={() => decideRequest(r, 'Reprovado')} className="text-red-400 border border-red-500/30 px-2.5 py-1.5 font-mono text-xs uppercase mr-2 hover:bg-red-500/10">
                            <Ban size={12} className="inline mr-1" /> Reprovar
                          </button>
                        </>
                      )}
                      {manage && r.status === 'Aguardando Liberação de Orçamento' && (
                        <button onClick={() => releaseBudget(r)} className="text-orange-400 border border-orange-500/30 px-2.5 py-1.5 font-mono text-xs uppercase mr-2 hover:bg-orange-500/10">
                          <ClipboardList size={12} className="inline mr-1" /> Liberar Orçamento
                        </button>
                      )}
                      {manage && ['Pendente', 'Em aprovação'].includes(r.status) && (
                        <button onClick={() => openQuotationModal(r)} className="text-brand-primary border border-brand-primary/30 px-2.5 py-1.5 font-mono text-xs uppercase hover:bg-brand-primary/10">
                          <Gavel size={12} className="inline mr-1" /> Cotar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {requests.length === 0 && (
                  <tr><td colSpan={6} className="p-12 text-center text-brand-muted font-mono text-sm">Nenhuma solicitação de compra.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ---------- COTAÇÕES ---------- */}
      {!loading && tab === 'cotacoes' && (
        <div className="border border-brand-border bg-brand-card overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">
                <th className="p-4">Número</th>
                <th className="p-4">Solicitação</th>
                <th className="p-4">Status</th>
                <th className="p-4">Fornecedores</th>
                <th className="p-4 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border/60 text-sm">
              {quotations.map((q) => (
                <tr key={q.id} className="hover:bg-brand-dark/10">
                  <td className="p-4 font-mono text-xs text-brand-primary">{q.numero}</td>
                  <td className="p-4 text-brand-text">{q.request?.numero ?? `#${q.request_id}`}</td>
                  <td className="p-4 text-brand-text">{q.status}</td>
                  <td className="p-4">
                    <div className="space-y-1">
                      {q.suppliers.map((s) => (
                        <div key={s.id} className="flex items-center space-x-2 text-xs">
                          <span className="text-brand-text">{s.fornecedor?.nome ?? `#${s.fornecedor_id}`}</span>
                          <span className="font-mono text-brand-muted">{fmt(s.valor_total)}</span>
                          {s.escolhido && <span className="text-green-400 font-mono uppercase">Vencedor</span>}
                        </div>
                      ))}
                    </div>
                  </td>
                  <td className="p-4 text-right whitespace-nowrap">
                    {manage && q.status === 'Em cotação' && q.suppliers.map((s) => (
                      <button key={s.id} onClick={() => selectWinner(q.id, s.id)} className="text-brand-primary border border-brand-primary/30 px-2.5 py-1.5 font-mono text-xs uppercase mr-2 hover:bg-brand-primary/10">
                        <ArrowRightCircle size={12} className="inline mr-1" /> Escolher
                      </button>
                    ))}
                  </td>
                </tr>
              ))}
              {quotations.length === 0 && (
                <tr><td colSpan={5} className="p-12 text-center text-brand-muted font-mono text-sm">Nenhuma cotação.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* ---------- ORDENS ---------- */}
      {!loading && tab === 'ordens' && (
        <div className="space-y-4">
          {manage && (
            <div className="flex justify-end">
              <button onClick={() => setOrderModal(true)} className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs flex items-center space-x-1.5">
                <Plus size={16} /> <span>Novo Pedido</span>
              </button>
            </div>
          )}
          <div className="border border-brand-border bg-brand-card overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">
                  <th className="p-4">Número</th>
                  <th className="p-4">Fornecedor</th>
                  <th className="p-4">Valor Total</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Emissão</th>
                  <th className="p-4 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border/60 text-sm">
                {orders.map((o) => (
                  <tr key={o.id} className="hover:bg-brand-dark/10">
                    <td className="p-4 font-mono text-xs text-brand-primary">{o.numero}</td>
                    <td className="p-4 text-brand-text">{o.fornecedor?.nome ?? `#${o.fornecedor_id}`}</td>
                    <td className="p-4 font-mono text-xs text-brand-text">{fmt(o.valor_total)}</td>
                    <td className="p-4">
                      <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 border ${orderStatusColor[o.status] ?? 'border-brand-border'}`}>{o.status}</span>
                    </td>
                    <td className="p-4 font-mono text-xs">{new Date(o.data_emissao).toLocaleDateString('pt-BR')}</td>
                    <td className="p-4 text-right whitespace-nowrap">
                      {manage && ['Aberto', 'Enviado', 'Aceito', 'Em transporte'].includes(o.status) && (
                        <button onClick={() => receiveOrder(o)} className="text-green-400 border border-green-500/30 px-2.5 py-1.5 font-mono text-xs uppercase hover:bg-green-500/10">
                          <Package size={12} className="inline mr-1" /> Receber
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {orders.length === 0 && (
                  <tr><td colSpan={6} className="p-12 text-center text-brand-muted font-mono text-sm">Nenhum pedido de compra.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ---------- ESTOQUE ---------- */}
      {!loading && tab === 'estoque' && (
        <div className="border border-brand-border bg-brand-card overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">
                <th className="p-4">Material</th>
                <th className="p-4">Categoria</th>
                <th className="p-4">Saldo</th>
                <th className="p-4">Localização</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border/60 text-sm">
              {stock.map((s) => (
                <tr key={s.id} className="hover:bg-brand-dark/10">
                  <td className="p-4 text-brand-text">{s.product?.nome ?? `#${s.product_id}`}</td>
                  <td className="p-4 text-brand-muted">{s.product?.categoria?.nome ?? '—'}</td>
                  <td className="p-4 font-mono text-xs">
                    <span className={s.quantidade_saldo < 5 ? 'text-red-400' : 'text-brand-primary'}>{s.quantidade_saldo}</span>
                  </td>
                  <td className="p-4 text-brand-muted">{s.localizacao_almoxarifado ?? '—'}</td>
                </tr>
              ))}
              {stock.length === 0 && (
                <tr><td colSpan={4} className="p-12 text-center text-brand-muted font-mono text-sm">Nenhum item em estoque.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* ---------- REQUEST MODAL ---------- */}
      {reqModal && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-2xl border border-brand-border bg-brand-card p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">Nova Solicitação de Compra</h3>
              <button onClick={() => setReqModal(false)} className="text-brand-muted hover:text-brand-text"><X size={20} /></button>
            </div>
            <form onSubmit={submitRequest} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Centro de Custo *</label>
                  <select required value={rCC ?? ''} onChange={(e) => setRCC(Number(e.target.value))} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                    <option value="">—</option>
                    {costCenters.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Urgência</label>
                  <select value={rUrgencia} onChange={(e) => setRUrgencia(e.target.value)} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                    {URGENCIES.map((u) => <option key={u} value={u}>{u}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Justificativa *</label>
                <textarea required value={rJust} onChange={(e) => setRJust(e.target.value)} rows={3} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-mono uppercase tracking-wider text-brand-muted">Itens</span>
                  <button type="button" onClick={() => setRItens([...rItens, { product_id: 0, quantidade: 1, valor_estimado: 0 }])} className="text-brand-primary border border-brand-primary/30 px-2 py-1 font-mono text-xs uppercase">+ Item</button>
                </div>
                {rItens.map((it, idx) => (
                  <div key={idx} className="grid grid-cols-4 gap-2">
                    <select value={it.product_id} onChange={(e) => { const n = [...rItens]; n[idx].product_id = Number(e.target.value); setRItens(n); }} className="col-span-2 bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                      <option value={0}>Produto...</option>
                      {products.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
                    </select>
                    <input type="number" step="0.01" placeholder="Qtd" value={it.quantidade} onChange={(e) => { const n = [...rItens]; n[idx].quantidade = Number(e.target.value); setRItens(n); }} className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" />
                    <input type="number" step="0.01" placeholder="Valor est." value={it.valor_estimado} onChange={(e) => { const n = [...rItens]; n[idx].valor_estimado = Number(e.target.value); setRItens(n); }} className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" />
                  </div>
                ))}
              </div>
              <div className="flex justify-end space-x-3 pt-4 border-t border-brand-border">
                <button type="button" onClick={() => setReqModal(false)} className="border border-brand-border hover:bg-brand-card px-4 py-2 font-mono text-xs uppercase">Cancelar</button>
                <button type="submit" className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs">Enviar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ---------- QUOTATION MODAL ---------- */}
      {quotModal && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-2xl border border-brand-border bg-brand-card p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">Nova Cotação</h3>
              <button onClick={() => setQuotModal(false)} className="text-brand-muted hover:text-brand-text"><X size={20} /></button>
            </div>
            <form onSubmit={submitQuotation} className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-mono uppercase tracking-wider text-brand-muted">Fornecedores cotados</span>
                  <button type="button" onClick={() => setQSuppliers([...qSuppliers, { fornecedor_id: 0, frete: 0, prazo_entrega_dias: 0, itens: [] }])} className="text-brand-primary border border-brand-primary/30 px-2 py-1 font-mono text-xs uppercase">+ Fornecedor</button>
                </div>
                {qSuppliers.map((s, idx) => (
                  <div key={idx} className="border border-brand-border p-3 space-y-2">
                    <div className="grid grid-cols-3 gap-2">
                      <select value={s.fornecedor_id} onChange={(e) => { const n = [...qSuppliers]; n[idx].fornecedor_id = Number(e.target.value); setQSuppliers(n); }} className="col-span-1 bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                        <option value={0}>Fornecedor...</option>
                        {suppliers.map((f) => <option key={f.id} value={f.id}>{f.nome}</option>)}
                      </select>
                      <input type="number" step="0.01" placeholder="Frete" value={s.frete} onChange={(e) => { const n = [...qSuppliers]; n[idx].frete = Number(e.target.value); setQSuppliers(n); }} className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" />
                      <input type="number" placeholder="Prazo (dias)" value={s.prazo_entrega_dias} onChange={(e) => { const n = [...qSuppliers]; n[idx].prazo_entrega_dias = Number(e.target.value); setQSuppliers(n); }} className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" />
                    </div>
                    <button type="button" onClick={() => { const n = [...qSuppliers]; n[idx].itens.push({ product_id: 0, quantidade: 1, valor_unitario: 0 }); setQSuppliers(n); }} className="text-brand-primary border border-brand-primary/30 px-2 py-1 font-mono text-xs uppercase">+ Item</button>
                    {s.itens.map((it, iIdx) => (
                      <div key={iIdx} className="grid grid-cols-3 gap-2">
                        <select value={it.product_id} onChange={(e) => { const n = [...qSuppliers]; n[idx].itens[iIdx].product_id = Number(e.target.value); setQSuppliers(n); }} className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                          <option value={0}>Produto...</option>
                          {products.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
                        </select>
                        <input type="number" step="0.01" placeholder="Qtd" value={it.quantidade} onChange={(e) => { const n = [...qSuppliers]; n[idx].itens[iIdx].quantidade = Number(e.target.value); setQSuppliers(n); }} className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" />
                        <input type="number" step="0.01" placeholder="Valor unit." value={it.valor_unitario} onChange={(e) => { const n = [...qSuppliers]; n[idx].itens[iIdx].valor_unitario = Number(e.target.value); setQSuppliers(n); }} className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" />
                      </div>
                    ))}
                  </div>
                ))}
              </div>
              <div className="flex justify-end space-x-3 pt-4 border-t border-brand-border">
                <button type="button" onClick={() => setQuotModal(false)} className="border border-brand-border hover:bg-brand-card px-4 py-2 font-mono text-xs uppercase">Cancelar</button>
                <button type="submit" className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs">Criar Cotação</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ---------- ORDER MODAL ---------- */}
      {orderModal && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-2xl border border-brand-border bg-brand-card p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">Novo Pedido de Compra</h3>
              <button onClick={() => setOrderModal(false)} className="text-brand-muted hover:text-brand-text"><X size={20} /></button>
            </div>
            <form onSubmit={submitOrder} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Fornecedor *</label>
                  <select required value={oSupplier ?? ''} onChange={(e) => setOSupplier(Number(e.target.value))} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                    <option value="">—</option>
                    {suppliers.map((f) => <option key={f.id} value={f.id}>{f.nome}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Centro de Custo *</label>
                  <select required value={oCC ?? ''} onChange={(e) => setOCC(Number(e.target.value))} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                    <option value="">—</option>
                    {costCenters.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
                  </select>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-mono uppercase tracking-wider text-brand-muted">Itens</span>
                  <button type="button" onClick={() => setOItens([...oItens, { product_id: 0, quantidade: 1, valor_unitario: 0 }])} className="text-brand-primary border border-brand-primary/30 px-2 py-1 font-mono text-xs uppercase">+ Item</button>
                </div>
                {oItens.map((it, idx) => (
                  <div key={idx} className="grid grid-cols-3 gap-2">
                    <select value={it.product_id} onChange={(e) => { const n = [...oItens]; n[idx].product_id = Number(e.target.value); setOItens(n); }} className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                      <option value={0}>Produto...</option>
                      {products.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
                    </select>
                    <input type="number" step="0.01" placeholder="Qtd" value={it.quantidade} onChange={(e) => { const n = [...oItens]; n[idx].quantidade = Number(e.target.value); setOItens(n); }} className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" />
                    <input type="number" step="0.01" placeholder="Valor unit." value={it.valor_unitario} onChange={(e) => { const n = [...oItens]; n[idx].valor_unitario = Number(e.target.value); setOItens(n); }} className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" />
                  </div>
                ))}
              </div>
              <div className="flex justify-end space-x-3 pt-4 border-t border-brand-border">
                <button type="button" onClick={() => setOrderModal(false)} className="border border-brand-border hover:bg-brand-card px-4 py-2 font-mono text-xs uppercase">Cancelar</button>
                <button type="submit" className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs">Emitir Pedido</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
