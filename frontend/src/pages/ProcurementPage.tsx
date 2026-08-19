import React, { useState, useEffect } from 'react';
import { procurementApi } from '../api/procurement';
import { suppliersApi } from '../api/suppliers';
import { assetsApi } from '../api/assets';
import { usersApi } from '../api/users';
import { getSettings, updateSettings } from '../api/settings';
import type {
  PurchaseRequest,
  PurchaseOrder,
  MaterialStock,
  MaterialStockTransaction,
  PurchaseQuotation,
  ProcurementDashboard,
  CostCenter,
  PurchaseProduct,
  PurchaseCategory,
} from '../types/procurement';
import { URGENCIES, requestStatusColor, orderStatusColor } from '../types/procurement';
import { useAuthStore } from '../stores/authStore';
import {
  Plus, X, ShieldAlert, Package, Gavel, CheckCircle2, Ban,
  ClipboardList, ArrowRightCircle,
  Building2, Pencil, Trash2, Save, Boxes,
} from 'lucide-react';

const canManage = ['admin', 'gerente_ti', 'gerente_infra', 'comprador'];

export const ProcurementPage: React.FC = () => {
  const user = useAuthStore().user;
  const manage = user ? canManage.includes(user.role) : false;

  const [tab, setTab] = useState<'dashboard' | 'solicitacoes' | 'ordens' | 'estoque' | 'cotacoes' | 'cadastros'>('dashboard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [dash, setDash] = useState<ProcurementDashboard | null>(null);
  const [requests, setRequests] = useState<PurchaseRequest[]>([]);
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [stock, setStock] = useState<MaterialStock[]>([]);
  const [stockTransactions, setStockTransactions] = useState<MaterialStockTransaction[]>([]);
  const [quotations, setQuotations] = useState<PurchaseQuotation[]>([]);

  const [costCenters, setCostCenters] = useState<CostCenter[]>([]);
  const [products, setProducts] = useState<PurchaseProduct[]>([]);
  const [categories, setCategories] = useState<PurchaseCategory[]>([]);
  const [suppliers, setSuppliers] = useState<{ id: number; nome: string }[]>([]);
  const [departments, setDepartments] = useState<{ id: number; nome: string }[]>([]);
  const [users, setUsers] = useState<{ id: number; nome: string }[]>([]);
  const [requestCostCenterFilter, setRequestCostCenterFilter] = useState<number | 'all'>('all');
  const [approvalLimitGestor, setApprovalLimitGestor] = useState<number>(5000);
  const [approvalLimitGerente, setApprovalLimitGerente] = useState<number>(15000);
  const [approvalLimitFinanceiro, setApprovalLimitFinanceiro] = useState<number>(50000);
  const [savingApprovalConfig, setSavingApprovalConfig] = useState(false);
  const [stockConsumeModal, setStockConsumeModal] = useState(false);
  const [consumeStockId, setConsumeStockId] = useState<number | ''>('');
  const [consumeQty, setConsumeQty] = useState<number>(1);
  const [consumeJustification, setConsumeJustification] = useState('');
  const [consumeCCId, setConsumeCCId] = useState<number | ''>('');
  const [savingConsume, setSavingConsume] = useState(false);

  // Cost center management
  const [ccCodigo, setCCCodigo] = useState('');
  const [ccNome, setCCNome] = useState('');
  const [ccDepartamentoId, setCCDepartamentoId] = useState<number | ''>('');
  const [ccResponsavelId, setCCResponsavelId] = useState<number | ''>('');
  const [ccOrcamentoMensal, setCCOrcamentoMensal] = useState<number>(0);
  const [ccOrcamentoAnual, setCCOrcamentoAnual] = useState<number>(0);
  const [ccAlertaLimite, setCCAlertaLimite] = useState(true);
  const [ccBloquearLimite, setCCBloquearLimite] = useState(false);
  const [editingCCId, setEditingCCId] = useState<number | null>(null);
  const [savingCC, setSavingCC] = useState(false);
  const [deletingCCId, setDeletingCCId] = useState<number | null>(null);

  // Category quick-create
  const [categoryNome, setCategoryNome] = useState('');
  const [editingCategoryId, setEditingCategoryId] = useState<number | null>(null);
  const [savingCategory, setSavingCategory] = useState(false);

  // Product quick-create
  const [productCodigo, setProductCodigo] = useState('');
  const [productNome, setProductNome] = useState('');
  const [productCategoriaId, setProductCategoriaId] = useState<number | ''>('');
  const [productUnidade, setProductUnidade] = useState('UN');
  const [productTipo, setProductTipo] = useState('Produto');
  const [editingProductId, setEditingProductId] = useState<number | null>(null);
  const [savingProduct, setSavingProduct] = useState(false);
  const [deletingCategoryId, setDeletingCategoryId] = useState<number | null>(null);
  const [deletingProductId, setDeletingProductId] = useState<number | null>(null);

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
      const [d, r, o, s, tx, q] = await Promise.all([
        procurementApi.dashboard(),
        procurementApi.listRequests(),
        procurementApi.listOrders(),
        procurementApi.listStock(),
        procurementApi.listStockTransactions(undefined, 20),
        procurementApi.listQuotations(),
      ]);
      setDash(d);
      setRequests(r);
      setOrders(o);
      setStock(s);
      setStockTransactions(tx);
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
    procurementApi.listCategories().then(setCategories).catch(() => {});
    procurementApi.listProducts().then(setProducts).catch(() => {});
    suppliersApi.list(0, 200).then((s) => setSuppliers(s.map((x) => ({ id: x.id, nome: x.nome })))).catch(() => {});
    assetsApi.getReferences().then((refs) => setDepartments(refs.setores.map((x) => ({ id: x.id, nome: x.nome })))).catch(() => {});
    usersApi.list().then((list) => setUsers(list.map((x) => ({ id: x.id, nome: x.nome })))).catch(() => {});
    getSettings().then((settings) => {
      setApprovalLimitGestor(Number(settings.procurement_approval_limit_gestor || 5000));
      setApprovalLimitGerente(Number(settings.procurement_approval_limit_gerente || 15000));
      setApprovalLimitFinanceiro(Number(settings.procurement_approval_limit_financeiro || 50000));
    }).catch(() => {});
  }, []);

  const showError = (err: any) => {
    setError(err.response?.data?.error || 'Erro na operação');
    setTimeout(() => setError(null), 5000);
  };

  const refreshMasterData = async () => {
    try {
      const [ccs, cats, prods] = await Promise.all([
        procurementApi.listCostCenters(),
        procurementApi.listCategories(),
        procurementApi.listProducts(),
      ]);
      setCostCenters(ccs);
      setCategories(cats);
      setProducts(prods);
    } catch (_err) {
      // keep current UI state
    }
  };

  const resetCostCenterForm = () => {
    setEditingCCId(null);
    setCCCodigo('');
    setCCNome('');
    setCCDepartamentoId('');
    setCCResponsavelId('');
    setCCOrcamentoMensal(0);
    setCCOrcamentoAnual(0);
    setCCAlertaLimite(true);
    setCCBloquearLimite(false);
  };

  const openEditCostCenter = (cc: CostCenter) => {
    setEditingCCId(cc.id);
    setCCCodigo(cc.codigo);
    setCCNome(cc.nome);
    setCCDepartamentoId(cc.departamento_id ?? '');
    setCCResponsavelId(cc.responsavel_id ?? '');
    setCCOrcamentoMensal(cc.orcamento_mensal);
    setCCOrcamentoAnual(cc.orcamento_anual);
    setCCAlertaLimite(cc.alerta_limite);
    setCCBloquearLimite(cc.bloquear_limite);
    setTab('cadastros');
  };

  const submitCostCenter = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ccCodigo.trim() || !ccNome.trim()) {
      showError({ response: { data: { error: 'Código e nome do centro de custo são obrigatórios' } } });
      return;
    }

    setSavingCC(true);
    try {
      const payload = {
        codigo: ccCodigo.trim(),
        nome: ccNome.trim(),
        departamento_id: ccDepartamentoId ? Number(ccDepartamentoId) : undefined,
        responsavel_id: ccResponsavelId ? Number(ccResponsavelId) : undefined,
        orcamento_mensal: Number(ccOrcamentoMensal) || 0,
        orcamento_anual: Number(ccOrcamentoAnual) || 0,
        alerta_limite: ccAlertaLimite,
        bloquear_limite: ccBloquearLimite,
      };
      if (editingCCId) {
        await procurementApi.updateCostCenter(editingCCId, payload);
      } else {
        await procurementApi.createCostCenter(payload);
      }
      resetCostCenterForm();
      await refreshMasterData();
      setGlobalMessage(editingCCId ? 'Centro de custo atualizado com sucesso.' : 'Centro de custo criado com sucesso.');
    } catch (err) {
      showError(err);
    } finally {
      setSavingCC(false);
    }
  };

  const deleteCostCenter = async (cc: CostCenter) => {
    if (!window.confirm(`Excluir o centro de custo ${cc.codigo} - ${cc.nome}?`)) return;
    setDeletingCCId(cc.id);
    try {
      await procurementApi.deleteCostCenter(cc.id);
      if (editingCCId === cc.id) resetCostCenterForm();
      await refreshMasterData();
      setGlobalMessage('Centro de custo excluído com sucesso.');
    } catch (err) {
      showError(err);
    } finally {
      setDeletingCCId(null);
    }
  };

  const createCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!categoryNome.trim()) return;
    setSavingCategory(true);
    try {
      if (editingCategoryId) {
        await procurementApi.updateCategory(editingCategoryId, { nome: categoryNome.trim(), ativo: true });
      } else {
        await procurementApi.createCategory({ nome: categoryNome.trim(), ativo: true });
      }
      setCategoryNome('');
      setEditingCategoryId(null);
      await refreshMasterData();
      setGlobalMessage(editingCategoryId ? 'Categoria de compra atualizada com sucesso.' : 'Categoria de compra criada com sucesso.');
    } catch (err) {
      showError(err);
    } finally {
      setSavingCategory(false);
    }
  };

  const createProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productCodigo.trim() || !productNome.trim() || !productCategoriaId) {
      showError({ response: { data: { error: 'Código, nome e categoria do produto são obrigatórios' } } });
      return;
    }
    setSavingProduct(true);
    try {
      const payload = {
        codigo: productCodigo.trim(),
        nome: productNome.trim(),
        categoria_id: Number(productCategoriaId),
        unidade: productUnidade.trim() || 'UN',
        tipo: productTipo,
        ativo: true,
      };
      if (editingProductId) {
        await procurementApi.updateProduct(editingProductId, payload);
      } else {
        await procurementApi.createProduct(payload);
      }
      setProductCodigo('');
      setProductNome('');
      setProductCategoriaId('');
      setProductUnidade('UN');
      setProductTipo('Produto');
      setEditingProductId(null);
      await refreshMasterData();
      setGlobalMessage(editingProductId ? 'Produto de compras atualizado com sucesso.' : 'Produto de compras criado com sucesso.');
    } catch (err) {
      showError(err);
    } finally {
      setSavingProduct(false);
    }
  };

  const [globalMessage, setGlobalMessage] = useState<string | null>(null);

  const editCategory = (category: PurchaseCategory) => {
    setEditingCategoryId(category.id);
    setCategoryNome(category.nome);
    setTab('cadastros');
  };

  const deleteCategory = async (category: PurchaseCategory) => {
    if (!window.confirm(`Excluir a categoria ${category.nome}?`)) return;
    setDeletingCategoryId(category.id);
    try {
      await procurementApi.deleteCategory(category.id);
      if (editingCategoryId === category.id) {
        setEditingCategoryId(null);
        setCategoryNome('');
      }
      await refreshMasterData();
      setGlobalMessage('Categoria de compra excluída com sucesso.');
    } catch (err) {
      showError(err);
    } finally {
      setDeletingCategoryId(null);
    }
  };

  const editProduct = (product: PurchaseProduct) => {
    setEditingProductId(product.id);
    setProductCodigo(product.codigo);
    setProductNome(product.nome);
    setProductCategoriaId(product.categoria_id);
    setProductUnidade(product.unidade || 'UN');
    setProductTipo(product.tipo || 'Produto');
    setTab('cadastros');
  };

  const deleteProduct = async (product: PurchaseProduct) => {
    if (!window.confirm(`Excluir o produto ${product.codigo} - ${product.nome}?`)) return;
    setDeletingProductId(product.id);
    try {
      await procurementApi.deleteProduct(product.id);
      if (editingProductId === product.id) {
        setEditingProductId(null);
        setProductCodigo('');
        setProductNome('');
        setProductCategoriaId('');
        setProductUnidade('UN');
        setProductTipo('Produto');
      }
      await refreshMasterData();
      setGlobalMessage('Produto de compras excluído com sucesso.');
    } catch (err) {
      showError(err);
    } finally {
      setDeletingProductId(null);
    }
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
    const obs = decisao === 'Reprovado' ? window.prompt('Motivo da reprovação:') ?? undefined : undefined;
    try {
      await procurementApi.decideRequestAuto(req.id, decisao, obs);
      setGlobalMessage(
        decisao === 'Aprovado'
          ? `Solicitação ${req.numero} aprovada usando a alçada automática sugerida para este caso.`
          : `Solicitação ${req.numero} reprovada com sucesso.`,
      );
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

  const updateOrderStatus = async (order: PurchaseOrder, status: string) => {
    try {
      await procurementApi.updateOrderStatus(order.id, status);
      setGlobalMessage(`Pedido ${order.numero} atualizado para ${status}.`);
      fetchAll();
    } catch (err) {
      showError(err);
    }
  };

  const submitStockConsume = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!consumeStockId || consumeQty <= 0) {
      showError({ response: { data: { error: 'Selecione um item de estoque e informe uma quantidade válida' } } });
      return;
    }
    setSavingConsume(true);
    try {
      await procurementApi.consumeStock({
        stock_id: Number(consumeStockId),
        quantidade_usar: consumeQty,
        justificativa: consumeJustification.trim() || undefined,
        centro_custo_id: consumeCCId ? Number(consumeCCId) : undefined,
      });
      setStockConsumeModal(false);
      setConsumeStockId('');
      setConsumeQty(1);
      setConsumeJustification('');
      setConsumeCCId('');
      setGlobalMessage('Consumo de estoque registrado com sucesso.');
      fetchAll();
    } catch (err) {
      showError(err);
    } finally {
      setSavingConsume(false);
    }
  };

  const saveApprovalConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (approvalLimitGestor <= 0 || approvalLimitGerente < approvalLimitGestor || approvalLimitFinanceiro < approvalLimitGerente) {
      showError({ response: { data: { error: 'Configure limites crescentes e maiores que zero para as alçadas' } } });
      return;
    }
    setSavingApprovalConfig(true);
    try {
      await updateSettings({
        procurement_approval_limit_gestor: String(approvalLimitGestor),
        procurement_approval_limit_gerente: String(approvalLimitGerente),
        procurement_approval_limit_financeiro: String(approvalLimitFinanceiro),
      });
      setGlobalMessage('Faixas de aprovação do compras salvas com sucesso.');
      fetchAll();
    } catch (err) {
      showError(err);
    } finally {
      setSavingApprovalConfig(false);
    }
  };

  const fmt = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const filteredRequests = requests.filter((r) => requestCostCenterFilter === 'all' || r.centro_custo_id === requestCostCenterFilter);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0">Compras</h1>
          <p className="text-brand-muted text-sm mt-1">Solicitações, cotações, pedidos de compra e estoque.</p>
        </div>
        <div className="hidden xl:flex items-center gap-2">
          <button onClick={() => procurementApi.exportCsv('dashboard')} className="border border-brand-border hover:bg-brand-card px-3 py-2 font-mono text-xs uppercase">
            Exportar Resumo
          </button>
          <button onClick={() => procurementApi.exportCsv('solicitacoes')} className="border border-brand-border hover:bg-brand-card px-3 py-2 font-mono text-xs uppercase">
            Exportar Solicitações
          </button>
          <button onClick={() => procurementApi.exportCsv('pedidos')} className="border border-brand-border hover:bg-brand-card px-3 py-2 font-mono text-xs uppercase">
            Exportar Pedidos
          </button>
          <button onClick={() => procurementApi.exportCsv('estoque')} className="border border-brand-border hover:bg-brand-card px-3 py-2 font-mono text-xs uppercase">
            Exportar Estoque
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 border border-red-500/30 bg-red-500/5 text-red-400 text-xs font-mono flex items-center space-x-2">
          <ShieldAlert size={16} />
          <span>{error}</span>
        </div>
      )}

      {globalMessage && (
        <div className="app-notice--success p-3 border border-brand-primary/30 bg-brand-primary/5 text-brand-primary text-xs font-mono flex items-center justify-between">
          <span>{globalMessage}</span>
          <button onClick={() => setGlobalMessage(null)} className="text-brand-primary/70 hover:text-brand-primary font-bold">&times;</button>
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
          ['cadastros', 'Cadastros'],
        ] as const).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2.5 font-mono text-xs uppercase tracking-wider border-b-2 transition-colors whitespace-nowrap bg-white text-[#000205] opacity-[0.38] hover:opacity-60 ${
              tab === key ? 'border-brand-primary' : 'border-transparent'
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
        <div className="grid grid-cols-1 md:grid-cols-4 xl:grid-cols-6 gap-4">
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
          <div className="border border-brand-border bg-brand-card p-4">
            <div className="text-3xl font-bold font-mono text-brand-primary">{fmt(dash.monthly_budget_used || 0)}</div>
            <div className="text-xs font-mono uppercase text-brand-muted mt-1">Uso do orçamento mensal</div>
            <div className="text-[11px] text-brand-muted mt-2">Base: {fmt(dash.monthly_budget_total || 0)}</div>
          </div>
          <div className="border border-brand-border bg-brand-card p-4">
            <div className="text-3xl font-bold font-mono text-brand-primary">{fmt(dash.requested_total || 0)}</div>
            <div className="text-xs font-mono uppercase text-brand-muted mt-1">Total solicitado</div>
          </div>
          <div className="border border-brand-border bg-brand-card p-4">
            <div className="text-3xl font-bold font-mono text-brand-primary">{fmt(dash.estimated_savings_total || 0)}</div>
            <div className="text-xs font-mono uppercase text-brand-muted mt-1">Economia estimada</div>
            <div className="text-[11px] text-brand-muted mt-2">Comprado: {fmt(dash.ordered_total || 0)}</div>
          </div>

          <div className="md:col-span-4 grid grid-cols-1 xl:grid-cols-[1.2fr_.8fr] gap-4">
            <div className="border border-brand-border bg-brand-card">
              <div className="p-3 border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">Solicitações recentes</div>
              <div className="divide-y divide-brand-border/60">
                {dash.requests_recent.map((r) => (
                  <div key={r.id} className="p-3 flex flex-col md:flex-row md:items-center md:justify-between gap-2 text-sm">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-brand-primary text-xs">{r.numero}</span>
                      <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 border ${requestStatusColor[r.status] ?? 'border-brand-border'}`}>{r.status}</span>
                    </div>
                    <span className="text-brand-text">{r.justificativa.slice(0, 60)}</span>
                    <div className="text-right">
                      <div className="font-mono text-xs text-brand-text">{fmt(r.valor_estimado_total || 0)}</div>
                      <div className="text-[11px] text-brand-muted mt-1">{r.nivel_aprovacao_sugerido}</div>
                    </div>
                  </div>
                ))}
                {dash.requests_recent.length === 0 && <div className="p-4 text-center text-brand-muted font-mono text-xs">Nenhuma solicitação.</div>}
              </div>
            </div>

            <div className="border border-brand-border bg-brand-card">
              <div className="p-3 border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">Saúde dos centros de custo</div>
              <div className="p-4 grid grid-cols-2 gap-3 border-b border-brand-border">
                <div className="border border-brand-border bg-brand-dark/10 p-3">
                  <div className="text-2xl font-bold font-mono text-orange-400">{dash.cost_centers_alert || 0}</div>
                  <div className="text-[11px] uppercase font-mono text-brand-muted mt-1">Em alerta</div>
                </div>
                <div className="border border-brand-border bg-brand-dark/10 p-3">
                  <div className="text-2xl font-bold font-mono text-red-400">{dash.cost_centers_over_limit || 0}</div>
                  <div className="text-[11px] uppercase font-mono text-brand-muted mt-1">Acima do limite</div>
                </div>
              </div>
              <div className="divide-y divide-brand-border/60">
                {(dash.cost_centers_summary || []).slice(0, 5).map((cc) => (
                  <div key={cc.id} className="p-3">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="font-mono text-xs text-brand-primary">{cc.codigo}</div>
                        <div className="text-sm text-brand-text mt-1">{cc.nome}</div>
                      </div>
                      <div className={`text-[10px] uppercase font-mono px-1.5 py-0.5 border ${
                        cc.status === 'over_limit' ? 'text-red-400 border-red-500/30' :
                        cc.status === 'alert' ? 'text-orange-400 border-orange-500/30' :
                        cc.status === 'no_budget' ? 'text-gray-400 border-gray-500/30' :
                        'text-green-400 border-green-500/30'
                      }`}>
                        {cc.status === 'over_limit' ? 'Acima do limite' : cc.status === 'alert' ? 'Alerta' : cc.status === 'no_budget' ? 'Sem orçamento' : 'Ok'}
                      </div>
                    </div>
                    <div className="mt-3 h-2 bg-brand-dark/20 border border-brand-border overflow-hidden">
                      <div
                        className={`h-full ${
                          cc.status === 'over_limit' ? 'bg-red-400' :
                          cc.status === 'alert' ? 'bg-orange-400' :
                          'bg-brand-primary'
                        }`}
                        style={{ width: `${Math.min(cc.uso_percentual || 0, 100)}%` }}
                      />
                    </div>
                    <div className="mt-2 flex items-center justify-between text-[11px] text-brand-muted">
                      <span>{fmt(cc.orcamento_mensal_usado || 0)}</span>
                      <span>{(cc.uso_percentual || 0).toFixed(1)}%</span>
                      <span>{fmt(cc.orcamento_mensal || 0)}</span>
                    </div>
                  </div>
                ))}
                {(dash.cost_centers_summary || []).length === 0 && <div className="p-4 text-center text-brand-muted font-mono text-xs">Nenhum centro de custo cadastrado.</div>}
              </div>
            </div>

            <div className="border border-brand-border bg-brand-card">
              <div className="p-3 border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">Fornecedores com maior volume</div>
              <div className="divide-y divide-brand-border/60">
                {(dash.top_suppliers || []).map((supplier) => (
                  <div key={supplier.id} className="p-3 flex items-center justify-between gap-3">
                    <div>
                      <div className="text-sm text-brand-text">{supplier.nome}</div>
                      <div className="text-[11px] text-brand-muted mt-1">{supplier.total_pedidos} pedido(s)</div>
                    </div>
                    <div className="text-right font-mono text-xs text-brand-primary">{fmt(supplier.valor_total || 0)}</div>
                  </div>
                ))}
                {(dash.top_suppliers || []).length === 0 && <div className="p-4 text-center text-brand-muted font-mono text-xs">Nenhum fornecedor com pedidos ainda.</div>}
              </div>
            </div>
          </div>

          <div className="md:col-span-4 xl:col-span-6 grid grid-cols-1 xl:grid-cols-2 gap-4">
            <div className="border border-brand-border bg-brand-card overflow-x-auto">
              <div className="p-3 border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">Relatório por centro de custo</div>
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-brand-border bg-brand-dark/10 text-xs font-mono uppercase tracking-wider text-brand-muted">
                    <th className="p-4">Centro</th>
                    <th className="p-4">Pendente</th>
                    <th className="p-4">Aprovado</th>
                    <th className="p-4">Comprado</th>
                    <th className="p-4">Economia</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-brand-border/60 text-sm">
                  {(dash.cost_center_reports || []).map((cc) => (
                    <tr key={cc.id} className="hover:bg-brand-dark/10">
                      <td className="p-4">
                        <div className="font-mono text-xs text-brand-primary">{cc.codigo}</div>
                        <div className="text-brand-text mt-1">{cc.nome}</div>
                      </td>
                      <td className="p-4 font-mono text-xs text-brand-text">{fmt(cc.solicitado_pendente || 0)}</td>
                      <td className="p-4 font-mono text-xs text-brand-text">{fmt(cc.solicitado_aprovado || 0)}</td>
                      <td className="p-4 font-mono text-xs text-brand-text">{fmt(cc.comprado_total || 0)}</td>
                      <td className="p-4 font-mono text-xs text-green-400">{fmt(cc.economia_total || 0)}</td>
                    </tr>
                  ))}
                  {(dash.cost_center_reports || []).length === 0 && (
                    <tr><td colSpan={5} className="p-10 text-center text-brand-muted font-mono text-sm">Nenhum dado de centro de custo ainda.</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="border border-brand-border bg-brand-card overflow-x-auto">
              <div className="p-3 border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">Performance de fornecedores</div>
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-brand-border bg-brand-dark/10 text-xs font-mono uppercase tracking-wider text-brand-muted">
                    <th className="p-4">Fornecedor</th>
                    <th className="p-4">Pedidos</th>
                    <th className="p-4">Ativos</th>
                    <th className="p-4">Recebidos</th>
                    <th className="p-4">SLA</th>
                    <th className="p-4">Ticket Médio</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-brand-border/60 text-sm">
                  {(dash.supplier_performance || []).map((supplier) => (
                    <tr key={supplier.id} className="hover:bg-brand-dark/10">
                      <td className="p-4 text-brand-text">{supplier.nome}</td>
                      <td className="p-4 font-mono text-xs text-brand-text">{supplier.total_pedidos}</td>
                      <td className="p-4 font-mono text-xs text-orange-400">{supplier.pedidos_ativos}</td>
                      <td className="p-4 font-mono text-xs text-green-400">{supplier.pedidos_recebidos}</td>
                      <td className="p-4 text-xs">
                        <div className="font-mono text-brand-text">{(supplier.sla_percentual || 0).toFixed(1)}%</div>
                        <div className="text-[11px] text-brand-muted mt-1">{supplier.pedidos_no_prazo} no prazo · {supplier.pedidos_em_atraso} atrasado(s)</div>
                      </td>
                      <td className="p-4 font-mono text-xs text-brand-text">{fmt(supplier.ticket_medio || 0)}</td>
                    </tr>
                  ))}
                  {(dash.supplier_performance || []).length === 0 && (
                    <tr><td colSpan={6} className="p-10 text-center text-brand-muted font-mono text-sm">Nenhum fornecedor com histórico ainda.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ---------- SOLICITAÇÕES ---------- */}
      {!loading && tab === 'solicitacoes' && (
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div className="flex items-center gap-3">
              <select value={requestCostCenterFilter} onChange={(e) => setRequestCostCenterFilter(e.target.value === 'all' ? 'all' : Number(e.target.value))} className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                <option value="all">Todos os centros de custo</option>
                {costCenters.map((c) => <option key={c.id} value={c.id}>{c.codigo} · {c.nome}</option>)}
              </select>
            </div>
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
                  <th className="p-4">Valor Estimado</th>
                  <th className="p-4">Alçada Sugerida</th>
                  <th className="p-4">Urgência</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Orçamento</th>
                  <th className="p-4 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border/60 text-sm">
                {filteredRequests.map((r) => (
                  <tr key={r.id} className="hover:bg-brand-dark/10">
                    <td className="p-4 font-mono text-xs text-brand-primary">{r.numero}</td>
                    <td className="p-4 text-brand-text">{r.centro_custo?.nome ?? `#${r.centro_custo_id}`}</td>
                    <td className="p-4 text-brand-text max-w-xs truncate">{r.justificativa}</td>
                    <td className="p-4 font-mono text-xs text-brand-text">{fmt(r.valor_estimado_total || 0)}</td>
                    <td className="p-4 text-brand-muted">{r.nivel_aprovacao_sugerido || '—'}</td>
                    <td className="p-4 text-brand-text">{r.urgencia}</td>
                    <td className="p-4">
                      <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 border ${requestStatusColor[r.status] ?? 'border-brand-border'}`}>{r.status}</span>
                    </td>
                    <td className="p-4">
                      <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 border ${
                        r.situacao_orcamento_centro === 'Bloqueio por orçamento' || r.situacao_orcamento_centro === 'Acima do orçamento'
                          ? 'text-red-400 border-red-500/30'
                          : r.situacao_orcamento_centro === 'Em alerta'
                            ? 'text-orange-400 border-orange-500/30'
                            : 'text-green-400 border-green-500/30'
                      }`}>
                        {r.situacao_orcamento_centro || '—'}
                      </span>
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
                {filteredRequests.length === 0 && (
                  <tr><td colSpan={9} className="p-12 text-center text-brand-muted font-mono text-sm">Nenhuma solicitação de compra.</td></tr>
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
                  <th className="p-4">Comparativo</th>
                  <th className="p-4">Prazo / SLA</th>
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
                    <td className="p-4 text-xs">
                      <div className="font-mono text-brand-text">Solicitado: {fmt(o.request_valor_estimado_total || 0)}</div>
                      <div className={`font-mono mt-1 ${(o.economia_estimada || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {(o.economia_estimada || 0) >= 0 ? 'Economia' : 'Acima do estimado'}: {fmt(Math.abs(o.economia_estimada || 0))}
                      </div>
                    </td>
                    <td className="p-4 text-xs">
                      <div className="font-mono text-brand-text">
                        {o.data_prevista_entrega ? `Previsto: ${new Date(o.data_prevista_entrega).toLocaleDateString('pt-BR')}` : 'Sem prazo previsto'}
                      </div>
                      <div className={`font-mono mt-1 ${
                        o.sla_status?.includes('atraso') || o.sla_status === 'Em atraso'
                          ? 'text-red-400'
                          : o.sla_status?.includes('prazo')
                            ? 'text-green-400'
                            : 'text-brand-muted'
                      }`}>
                        {o.sla_status || 'Sem SLA'}
                      </div>
                    </td>
                    <td className="p-4">
                      <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 border ${orderStatusColor[o.status] ?? 'border-brand-border'}`}>{o.status}</span>
                    </td>
                    <td className="p-4 font-mono text-xs">{new Date(o.data_emissao).toLocaleDateString('pt-BR')}</td>
                    <td className="p-4 text-right whitespace-nowrap">
                      {manage && o.status === 'Aberto' && (
                        <button onClick={() => updateOrderStatus(o, 'Enviado')} className="text-cyan-400 border border-cyan-500/30 px-2.5 py-1.5 font-mono text-xs uppercase mr-2 hover:bg-cyan-500/10">
                          Enviar
                        </button>
                      )}
                      {manage && o.status === 'Enviado' && (
                        <button onClick={() => updateOrderStatus(o, 'Aceito')} className="text-yellow-400 border border-yellow-500/30 px-2.5 py-1.5 font-mono text-xs uppercase mr-2 hover:bg-yellow-500/10">
                          Aceitar
                        </button>
                      )}
                      {manage && ['Aceito', 'Recebido parcialmente'].includes(o.status) && (
                        <button onClick={() => updateOrderStatus(o, 'Em transporte')} className="text-purple-400 border border-purple-500/30 px-2.5 py-1.5 font-mono text-xs uppercase mr-2 hover:bg-purple-500/10">
                          Em Transporte
                        </button>
                      )}
                      {manage && ['Aberto', 'Enviado', 'Aceito', 'Em transporte'].includes(o.status) && (
                        <button onClick={() => receiveOrder(o)} className="text-green-400 border border-green-500/30 px-2.5 py-1.5 font-mono text-xs uppercase hover:bg-green-500/10">
                          <Package size={12} className="inline mr-1" /> Receber
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {orders.length === 0 && (
                  <tr><td colSpan={8} className="p-12 text-center text-brand-muted font-mono text-sm">Nenhum pedido de compra.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ---------- ESTOQUE ---------- */}
      {!loading && tab === 'estoque' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            {manage && (
              <button onClick={() => setStockConsumeModal(true)} className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs flex items-center space-x-1.5">
                <Package size={16} /> <span>Registrar Consumo</span>
              </button>
            )}
          </div>

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

          <div className="border border-brand-border bg-brand-card overflow-x-auto">
            <div className="p-4 border-b border-brand-border bg-brand-dark/20">
              <div className="text-xs font-mono uppercase tracking-wider text-brand-muted">Movimentações recentes de estoque</div>
            </div>
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-brand-border bg-brand-dark/10 text-xs font-mono uppercase tracking-wider text-brand-muted">
                  <th className="p-4">Data</th>
                  <th className="p-4">Tipo</th>
                  <th className="p-4">Quantidade</th>
                  <th className="p-4">Responsável</th>
                  <th className="p-4">Justificativa</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border/60 text-sm">
                {stockTransactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-brand-dark/10">
                    <td className="p-4 font-mono text-xs text-brand-text">{new Date(tx.data_transacao).toLocaleString('pt-BR')}</td>
                    <td className="p-4">
                      <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 border ${tx.tipo_movimentacao === 'Saída' ? 'text-red-400 border-red-500/30' : 'text-green-400 border-green-500/30'}`}>
                        {tx.tipo_movimentacao}
                      </span>
                    </td>
                    <td className="p-4 font-mono text-xs text-brand-text">{tx.quantidade}</td>
                    <td className="p-4 text-brand-muted">{tx.user?.nome ?? `#${tx.user_id}`}</td>
                    <td className="p-4 text-brand-text">{tx.justificativa ?? '—'}</td>
                  </tr>
                ))}
                {stockTransactions.length === 0 && (
                  <tr><td colSpan={5} className="p-12 text-center text-brand-muted font-mono text-sm">Nenhuma movimentação registrada.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {stockConsumeModal && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-xl border border-brand-border bg-brand-card p-6 space-y-6">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">Registrar Consumo de Estoque</h3>
              <button onClick={() => setStockConsumeModal(false)} className="text-brand-muted hover:text-brand-text"><X size={20} /></button>
            </div>
            <form onSubmit={submitStockConsume} className="space-y-4">
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Item de estoque</label>
                <select value={consumeStockId} onChange={(e) => setConsumeStockId(e.target.value ? Number(e.target.value) : '')} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                  <option value="">Selecione...</option>
                  {stock.map((s) => <option key={s.id} value={s.id}>{s.product?.nome ?? `#${s.product_id}`} · saldo {s.quantidade_saldo}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Quantidade</label>
                  <input type="number" min="0.01" step="0.01" value={consumeQty} onChange={(e) => setConsumeQty(Number(e.target.value))} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" />
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Centro de custo</label>
                  <select value={consumeCCId} onChange={(e) => setConsumeCCId(e.target.value ? Number(e.target.value) : '')} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                    <option value="">Opcional...</option>
                    {costCenters.map((c) => <option key={c.id} value={c.id}>{c.codigo} · {c.nome}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Justificativa</label>
                <textarea value={consumeJustification} onChange={(e) => setConsumeJustification(e.target.value)} rows={3} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" placeholder="Ex.: uso interno do suporte, reposição de campo, atendimento emergencial..." />
              </div>
              <div className="flex justify-end space-x-3 pt-4 border-t border-brand-border">
                <button type="button" onClick={() => setStockConsumeModal(false)} className="border border-brand-border hover:bg-brand-card px-4 py-2 font-mono text-xs uppercase">Cancelar</button>
                <button type="submit" disabled={savingConsume} className="bg-brand-primary hover:bg-brand-primary/90 disabled:opacity-60 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs">
                  {savingConsume ? 'Salvando...' : 'Registrar Consumo'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {!loading && tab === 'cadastros' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 xl:grid-cols-[1.15fr_.85fr] gap-6">
            <div className="border border-brand-border bg-brand-card p-6 space-y-5">
              <div className="flex items-center space-x-2 border-b border-brand-border pb-3">
                <Building2 size={18} className="text-brand-primary" />
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-brand-text">Centros de Custo</h3>
                  <p className="text-[11px] text-brand-muted mt-1">Base orçamentária do processo de compras. Sem isso, solicitação e pedido ficam sem governança.</p>
                </div>
              </div>

              <form onSubmit={submitCostCenter} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Código *</label>
                    <input value={ccCodigo} onChange={(e) => setCCCodigo(e.target.value)} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" placeholder="Ex.: CC-TI-01" />
                  </div>
                  <div>
                    <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Nome *</label>
                    <input value={ccNome} onChange={(e) => setCCNome(e.target.value)} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" placeholder="Ex.: TI / Operações" />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Departamento</label>
                    <select value={ccDepartamentoId} onChange={(e) => setCCDepartamentoId(e.target.value ? Number(e.target.value) : '')} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                      <option value="">—</option>
                      {departments.map((d) => <option key={d.id} value={d.id}>{d.nome}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Responsável</label>
                    <select value={ccResponsavelId} onChange={(e) => setCCResponsavelId(e.target.value ? Number(e.target.value) : '')} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                      <option value="">—</option>
                      {users.map((u) => <option key={u.id} value={u.id}>{u.nome}</option>)}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Orçamento Mensal</label>
                    <input type="number" step="0.01" value={ccOrcamentoMensal} onChange={(e) => setCCOrcamentoMensal(Number(e.target.value))} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" />
                  </div>
                  <div>
                    <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Orçamento Anual</label>
                    <input type="number" step="0.01" value={ccOrcamentoAnual} onChange={(e) => setCCOrcamentoAnual(Number(e.target.value))} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" />
                  </div>
                </div>

                <div className="flex flex-col md:flex-row gap-4 py-2 border-t border-b border-brand-border/40">
                  <label className="flex items-center gap-2 text-sm text-brand-text">
                    <input type="checkbox" checked={ccAlertaLimite} onChange={(e) => setCCAlertaLimite(e.target.checked)} />
                    Alertar ao atingir limite
                  </label>
                  <label className="flex items-center gap-2 text-sm text-brand-text">
                    <input type="checkbox" checked={ccBloquearLimite} onChange={(e) => setCCBloquearLimite(e.target.checked)} />
                    Bloquear ao ultrapassar orçamento
                  </label>
                </div>

                <div className="flex justify-end gap-3">
                  {editingCCId && (
                    <button type="button" onClick={resetCostCenterForm} className="border border-brand-border hover:bg-brand-card px-4 py-2 font-mono text-xs uppercase">
                      Cancelar edição
                    </button>
                  )}
                  <button type="submit" disabled={savingCC} className="bg-brand-primary hover:bg-brand-primary/90 disabled:opacity-60 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs flex items-center gap-2">
                    <Save size={14} />
                    <span>{savingCC ? 'Salvando...' : editingCCId ? 'Atualizar Centro de Custo' : 'Cadastrar Centro de Custo'}</span>
                  </button>
                </div>
              </form>
            </div>

            <div className="space-y-6">
              <div className="border border-brand-border bg-brand-card p-6 space-y-4">
                <div className="flex items-center space-x-2 border-b border-brand-border pb-3">
                  <ShieldAlert size={18} className="text-brand-primary" />
                  <div>
                    <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-brand-text">Alçadas de aprovação</h3>
                    <p className="text-[11px] text-brand-muted mt-1">Defina até onde cada faixa de valor pode ser aprovada automaticamente no fluxo de compras.</p>
                  </div>
                </div>

                <form onSubmit={saveApprovalConfig} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Até Gestor</label>
                      <input type="number" min="0" step="0.01" value={approvalLimitGestor} onChange={(e) => setApprovalLimitGestor(Number(e.target.value))} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" />
                    </div>
                    <div>
                      <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Até Gerente</label>
                      <input type="number" min="0" step="0.01" value={approvalLimitGerente} onChange={(e) => setApprovalLimitGerente(Number(e.target.value))} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" />
                    </div>
                    <div>
                      <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Até Financeiro</label>
                      <input type="number" min="0" step="0.01" value={approvalLimitFinanceiro} onChange={(e) => setApprovalLimitFinanceiro(Number(e.target.value))} className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" />
                    </div>
                  </div>
                  <div className="text-[11px] text-brand-muted">
                    Acima do limite do Financeiro, a aprovação sugerida passa automaticamente para Diretoria.
                  </div>
                  <div className="flex justify-end">
                    <button type="submit" disabled={savingApprovalConfig} className="bg-brand-primary hover:bg-brand-primary/90 disabled:opacity-60 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs">
                      {savingApprovalConfig ? 'Salvando...' : 'Salvar Alçadas'}
                    </button>
                  </div>
                </form>
              </div>

              <div className="border border-brand-border bg-brand-card p-6 space-y-4">
                <div className="flex items-center space-x-2 border-b border-brand-border pb-3">
                  <Boxes size={18} className="text-brand-primary" />
                  <div>
                    <h3 className="text-sm font-bold uppercase tracking-wider font-mono text-brand-text">Cadastros rápidos</h3>
                    <p className="text-[11px] text-brand-muted mt-1">Base mínima para sustentar solicitações, cotações, pedidos e estoque.</p>
                  </div>
                </div>

                <form onSubmit={createCategory} className="space-y-3">
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted">Categoria de compra</label>
                  <div className="flex gap-3">
                    <input value={categoryNome} onChange={(e) => setCategoryNome(e.target.value)} className="flex-1 bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" placeholder="Ex.: Infraestrutura, Licenças, Periféricos" />
                    <button type="submit" disabled={savingCategory} className="bg-brand-primary hover:bg-brand-primary/90 disabled:opacity-60 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs">
                      {savingCategory ? 'Salvando...' : editingCategoryId ? 'Atualizar' : 'Criar'}
                    </button>
                  </div>
                  {editingCategoryId && (
                    <button type="button" onClick={() => { setEditingCategoryId(null); setCategoryNome(''); }} className="border border-brand-border hover:bg-brand-card px-3 py-2 font-mono text-xs uppercase">
                      Cancelar edição
                    </button>
                  )}
                </form>

                <form onSubmit={createProduct} className="space-y-3 border-t border-brand-border pt-4">
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted">Produto de compra</label>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <input value={productCodigo} onChange={(e) => setProductCodigo(e.target.value)} className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" placeholder="Código" />
                    <input value={productNome} onChange={(e) => setProductNome(e.target.value)} className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none" placeholder="Nome do produto" />
                    <select value={productCategoriaId} onChange={(e) => setProductCategoriaId(e.target.value ? Number(e.target.value) : '')} className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none">
                      <option value="">Categoria...</option>
                      {categories.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
                    </select>
                    <input value={productUnidade} onChange={(e) => setProductUnidade(e.target.value)} className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none font-mono" placeholder="UN" />
                    <select value={productTipo} onChange={(e) => setProductTipo(e.target.value)} className="bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none md:col-span-2">
                      {['Produto', 'Serviço', 'Licença', 'Assinatura', 'Equipamento', 'Material de Consumo'].map((t) => <option key={t} value={t}>{t}</option>)}
                    </select>
                  </div>
                  <button type="submit" disabled={savingProduct} className="bg-brand-primary hover:bg-brand-primary/90 disabled:opacity-60 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs">
                    {savingProduct ? 'Salvando...' : editingProductId ? 'Atualizar Produto' : 'Cadastrar Produto'}
                  </button>
                  {editingProductId && (
                    <button type="button" onClick={() => { setEditingProductId(null); setProductCodigo(''); setProductNome(''); setProductCategoriaId(''); setProductUnidade('UN'); setProductTipo('Produto'); }} className="ml-3 border border-brand-border hover:bg-brand-card px-3 py-2 font-mono text-xs uppercase">
                      Cancelar edição
                    </button>
                  )}
                </form>
              </div>
            </div>
          </div>

          <div className="border border-brand-border bg-brand-card overflow-x-auto">
            <div className="p-4 border-b border-brand-border bg-brand-dark/20 flex items-center justify-between">
              <div>
                <div className="text-xs font-mono uppercase tracking-wider text-brand-muted">Centros de custo cadastrados</div>
                <div className="text-[11px] text-brand-muted mt-1">{costCenters.length} registro(s) ativos na governança de compras.</div>
              </div>
            </div>
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-brand-border bg-brand-dark/10 text-xs font-mono uppercase tracking-wider text-brand-muted">
                  <th className="p-4">Código</th>
                  <th className="p-4">Nome</th>
                  <th className="p-4">Departamento</th>
                  <th className="p-4">Responsável</th>
                  <th className="p-4">Orçamento</th>
                  <th className="p-4">Uso</th>
                  <th className="p-4 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border/60 text-sm">
                {costCenters.map((cc) => (
                  <tr key={cc.id} className="hover:bg-brand-dark/10">
                    <td className="p-4 font-mono text-xs text-brand-primary">{cc.codigo}</td>
                    <td className="p-4 text-brand-text">{cc.nome}</td>
                    <td className="p-4 text-brand-muted">{cc.departamento?.nome || '—'}</td>
                    <td className="p-4 text-brand-muted">{cc.responsavel?.nome || '—'}</td>
                    <td className="p-4 text-xs">
                      <div className="font-mono text-brand-text">Mensal: {fmt(cc.orcamento_mensal || 0)}</div>
                      <div className="font-mono text-brand-muted mt-1">Anual: {fmt(cc.orcamento_anual || 0)}</div>
                    </td>
                    <td className="p-4 text-xs">
                      <div className="font-mono text-brand-text">Mensal: {fmt(cc.orcamento_mensal_usado || 0)}</div>
                      <div className="font-mono text-brand-muted mt-1">Anual: {fmt(cc.orcamento_anual_usado || 0)}</div>
                    </td>
                    <td className="p-4 text-right whitespace-nowrap">
                      <button onClick={() => openEditCostCenter(cc)} className="text-brand-primary border border-brand-primary/30 px-2.5 py-1.5 font-mono text-xs uppercase mr-2 hover:bg-brand-primary/10">
                        <Pencil size={12} className="inline mr-1" /> Editar
                      </button>
                      <button onClick={() => deleteCostCenter(cc)} disabled={deletingCCId === cc.id} className="text-red-400 border border-red-500/30 px-2.5 py-1.5 font-mono text-xs uppercase hover:bg-red-500/10 disabled:opacity-60">
                        <Trash2 size={12} className="inline mr-1" /> Excluir
                      </button>
                    </td>
                  </tr>
                ))}
                {costCenters.length === 0 && (
                  <tr><td colSpan={7} className="p-12 text-center text-brand-muted font-mono text-sm">Nenhum centro de custo cadastrado. Cadastre ao menos um para operar o ERP de compras.</td></tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div className="border border-brand-border bg-brand-card overflow-x-auto">
              <div className="p-4 border-b border-brand-border bg-brand-dark/20">
                <div className="text-xs font-mono uppercase tracking-wider text-brand-muted">Categorias de compra</div>
              </div>
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-brand-border bg-brand-dark/10 text-xs font-mono uppercase tracking-wider text-brand-muted">
                    <th className="p-4">Nome</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-brand-border/60 text-sm">
                  {categories.map((category) => (
                    <tr key={category.id} className="hover:bg-brand-dark/10">
                      <td className="p-4 text-brand-text">{category.nome}</td>
                      <td className="p-4 text-brand-muted">{category.ativo ? 'Ativa' : 'Inativa'}</td>
                      <td className="p-4 text-right whitespace-nowrap">
                        <button onClick={() => editCategory(category)} className="text-brand-primary border border-brand-primary/30 px-2.5 py-1.5 font-mono text-xs uppercase mr-2 hover:bg-brand-primary/10">
                          <Pencil size={12} className="inline mr-1" /> Editar
                        </button>
                        <button onClick={() => deleteCategory(category)} disabled={deletingCategoryId === category.id} className="text-red-400 border border-red-500/30 px-2.5 py-1.5 font-mono text-xs uppercase hover:bg-red-500/10 disabled:opacity-60">
                          <Trash2 size={12} className="inline mr-1" /> Excluir
                        </button>
                      </td>
                    </tr>
                  ))}
                  {categories.length === 0 && (
                    <tr><td colSpan={3} className="p-10 text-center text-brand-muted font-mono text-sm">Nenhuma categoria cadastrada.</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="border border-brand-border bg-brand-card overflow-x-auto">
              <div className="p-4 border-b border-brand-border bg-brand-dark/20">
                <div className="text-xs font-mono uppercase tracking-wider text-brand-muted">Produtos de compras</div>
              </div>
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-brand-border bg-brand-dark/10 text-xs font-mono uppercase tracking-wider text-brand-muted">
                    <th className="p-4">Código</th>
                    <th className="p-4">Produto</th>
                    <th className="p-4">Categoria</th>
                    <th className="p-4 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-brand-border/60 text-sm">
                  {products.map((product) => (
                    <tr key={product.id} className="hover:bg-brand-dark/10">
                      <td className="p-4 font-mono text-xs text-brand-primary">{product.codigo}</td>
                      <td className="p-4 text-brand-text">
                        <div>{product.nome}</div>
                        <div className="text-[11px] text-brand-muted mt-1">{product.tipo} · {product.unidade}</div>
                      </td>
                      <td className="p-4 text-brand-muted">{product.categoria?.nome ?? '—'}</td>
                      <td className="p-4 text-right whitespace-nowrap">
                        <button onClick={() => editProduct(product)} className="text-brand-primary border border-brand-primary/30 px-2.5 py-1.5 font-mono text-xs uppercase mr-2 hover:bg-brand-primary/10">
                          <Pencil size={12} className="inline mr-1" /> Editar
                        </button>
                        <button onClick={() => deleteProduct(product)} disabled={deletingProductId === product.id} className="text-red-400 border border-red-500/30 px-2.5 py-1.5 font-mono text-xs uppercase hover:bg-red-500/10 disabled:opacity-60">
                          <Trash2 size={12} className="inline mr-1" /> Excluir
                        </button>
                      </td>
                    </tr>
                  ))}
                  {products.length === 0 && (
                    <tr><td colSpan={4} className="p-10 text-center text-brand-muted font-mono text-sm">Nenhum produto de compra cadastrado.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
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
