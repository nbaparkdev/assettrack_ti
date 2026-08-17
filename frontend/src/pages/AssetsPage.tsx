import React, { useState, useEffect, useRef } from 'react';
import { assetsApi } from '../api/assets';
import type { 
  Asset, 
  AssetStatus, 
  AssetReferences,
  BulkCopySpec
} from '../types';
import { useAuthStore } from '../stores/authStore';
import { 
  Plus, 
  Edit2, 
  Trash2, 
  QrCode, 
  FileText, 
  Search, 
  Filter, 
  ShieldAlert, 
  Check, 
  X, 
  Copy, 
  Kanban as KanbanIcon, 
  Table as TableIcon,
  Upload,
  RefreshCw,
  Lock
} from 'lucide-react';

export const AssetsPage: React.FC = () => {
  const currentAuthUser = useAuthStore().user;
  const isManagerOrAbove = currentAuthUser?.role === 'admin' || 
                           currentAuthUser?.role === 'gerente_ti' || 
                           currentAuthUser?.role === 'gerente_infra' || 
                           currentAuthUser?.role === 'tecnico';

  const [activeTab, setActiveTab] = useState<'table' | 'kanban' | 'reports'>('table');
  const [assets, setAssets] = useState<Asset[]>([]);
  const [references, setReferences] = useState<AssetReferences | null>(null);
  const [loading, setLoading] = useState(false);

  // Search & Filter State
  const [searchEP, setSearchEP] = useState('');
  const [filterCategory, setFilterCategory] = useState<number | ''>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  
  // Reports Filters
  const [reportStartDate, setReportStartDate] = useState('');
  const [reportEndDate, setReportEndDate] = useState('');
  const [reportName, setReportName] = useState('');
  const [reportCategory, setReportCategory] = useState<number | ''>('');
  const [reportLocation, setReportLocation] = useState<number | ''>('');
  const [reportSupplier, setReportSupplier] = useState<number | ''>('');
  const [reportInvoice, setReportInvoice] = useState('');
  const [reportPatrimonio, setReportPatrimonio] = useState('');
  const [reportStatus, setReportStatus] = useState('');

  // Asset Dialog State
  const [showFormModal, setShowFormModal] = useState(false);
  const [editAssetId, setEditAssetId] = useState<number | null>(null);
  const [assetName, setAssetName] = useState('');
  const [assetEP, setAssetEP] = useState('');
  const [assetModelo, setAssetModelo] = useState('');
  const [assetDescricao, setAssetDescricao] = useState('');
  const [assetValor, setAssetValor] = useState<number>(0);
  const [assetStatus, setAssetStatusValue] = useState<AssetStatus>('Disponível');
  const [assetSerie, setAssetSerie] = useState('');
  const [assetEmPosseDe, setAssetEmPosseDe] = useState('');
  const [assetBloqueado, setAssetBloqueado] = useState(false);
  const [assetRequerRH, setAssetRequerRH] = useState(false);
  const [assetCategoriaId, setAssetCategoriaId] = useState<number | ''>('');
  const [assetFornecedorId, setAssetFornecedorId] = useState<number | ''>('');
  const [assetLocalId, setAssetLocalId] = useState<number | ''>('');
  const [assetArmazenamentoId, setAssetArmazenamentoId] = useState<number | ''>('');
  const [assetDataAquisicao, setAssetDataAquisicao] = useState('');
  const [assetDepartamentoId, setAssetDepartamentoId] = useState<number | ''>('');

  // Duplication Wizard State
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [duplicateTemplate, setDuplicateTemplate] = useState<Asset | null>(null);
  const [duplicateStep, setDuplicateStep] = useState<'count' | 'specs' | 'results'>('count');
  const [duplicateCount, setDuplicateCount] = useState<number>(1);
  const [duplicateSpecs, setDuplicateSpecs] = useState<BulkCopySpec[]>([]);
  const [duplicateResults, setDuplicateResults] = useState<any[]>([]);
  const [duplicateSuccessCount, setDuplicateSuccessCount] = useState(0);
  const [duplicateFailedCount, setDuplicateFailedCount] = useState(0);

  // Scanner State
  const [showScannerModal, setShowScannerModal] = useState(false);
  const [scannerError, setScannerError] = useState<string | null>(null);
  const [scannedAsset, setScannedAsset] = useState<Asset | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Global UI states
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [globalSuccess, setGlobalSuccess] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchAssets = async () => {
    setLoading(true);
    setGlobalError(null);
    try {
      const data = await assetsApi.list(0, 100, {
        e_patrimonio: searchEP,
        categoria_id: filterCategory,
        status: filterStatus,
      });
      setAssets(data);
    } catch (err: any) {
      setGlobalError('Falha ao buscar ativos no servidor.');
    } finally {
      setLoading(false);
    }
  };

  const fetchReferences = async () => {
    try {
      const data = await assetsApi.getReferences();
      setReferences(data);
    } catch (err) {
      console.error('Falha ao buscar referências:', err);
    }
  };

  useEffect(() => {
    fetchAssets();
    fetchReferences();
  }, [searchEP, filterCategory, filterStatus]);

  // Asset crud triggers
  const handleOpenCreate = () => {
    setEditAssetId(null);
    setAssetName('');
    setAssetEP('');
    setAssetModelo('');
    setAssetDescricao('');
    setAssetValor(0);
    setAssetStatusValue('Disponível');
    setAssetSerie('');
    setAssetEmPosseDe('');
    setAssetBloqueado(false);
    setAssetRequerRH(false);
    setAssetCategoriaId('');
    setAssetFornecedorId('');
    setAssetLocalId('');
    setAssetArmazenamentoId('');
    setAssetDataAquisicao('');
    setAssetDepartamentoId('');
    setFormError(null);
    setShowFormModal(true);
  };

  const handleOpenEdit = (a: Asset) => {
    setEditAssetId(a.id);
    setAssetName(a.nome);
    setAssetEP(a.e_patrimonio);
    setAssetModelo(a.modelo || '');
    setAssetDescricao(a.descricao || '');
    setAssetValor(a.valor || 0);
    setAssetStatusValue(a.status);
    setAssetSerie(a.numero_serie || '');
    setAssetEmPosseDe(a.em_posse_de || '');
    setAssetBloqueado(a.bloqueado);
    setAssetRequerRH(a.requer_termo_rh);
    setAssetCategoriaId(a.categoria_id || '');
    setAssetFornecedorId(a.fornecedor_id || '');
    setAssetLocalId(a.current_local_id || '');
    setAssetArmazenamentoId(a.current_armazenamento_id || '');
    setAssetDataAquisicao(a.data_aquisicao ? a.data_aquisicao.split('T')[0] : '');
    setAssetDepartamentoId(a.current_departamento_id || '');
    setFormError(null);
    setShowFormModal(true);
  };

  const handleSaveAsset = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const payload: Partial<Asset> = {
      nome: assetName,
      e_patrimonio: assetEP,
      modelo: assetModelo || null,
      descricao: assetDescricao || null,
      valor: assetValor || null,
      status: assetStatus,
      numero_serie: assetSerie || null,
      em_posse_de: assetEmPosseDe || null,
      bloqueado: assetBloqueado,
      requer_termo_rh: assetRequerRH,
      categoria_id: assetCategoriaId ? Number(assetCategoriaId) : null,
      fornecedor_id: assetFornecedorId ? Number(assetFornecedorId) : null,
      current_local_id: assetLocalId ? Number(assetLocalId) : null,
      current_armazenamento_id: assetArmazenamentoId ? Number(assetArmazenamentoId) : null,
      current_departamento_id: assetDepartamentoId ? Number(assetDepartamentoId) : null,
      data_aquisicao: assetDataAquisicao ? new Date(assetDataAquisicao).toISOString() : null,
    };

    try {
      if (editAssetId) {
        await assetsApi.update(editAssetId, payload);
        setGlobalSuccess('Registro de ativo atualizado com sucesso.');
      } else {
        await assetsApi.create(payload);
        setGlobalSuccess('Novo ativo registrado com sucesso.');
      }
      setShowFormModal(false);
      fetchAssets();
    } catch (err: any) {
      setFormError(err.response?.data?.error || 'Erro ao salvar ativo.');
    }
  };

  const handleDeleteAsset = async (id: number) => {
    if (!window.confirm('Tem certeza que deseja excluir permanentemente este ativo?')) return;
    try {
      await assetsApi.delete(id);
      setGlobalSuccess('Ativo excluído com sucesso.');
      fetchAssets();
    } catch (err: any) {
      setGlobalError('Não foi possível excluir o ativo.');
    }
  };

  const handleCreateReference = async (type: 'categoria' | 'localizacao' | 'armazenamento' | 'departamento') => {
    const nome = window.prompt(`Digite o nome para o novo registro:`);
    if (!nome || !nome.trim()) return;

    try {
      if (type === 'categoria') {
        const res = await assetsApi.createCategoria(nome.trim());
        setAssetCategoriaId(res.id);
      } else if (type === 'localizacao') {
        const res = await assetsApi.createLocalizacao(nome.trim());
        setAssetLocalId(res.id);
      } else if (type === 'armazenamento') {
        const res = await assetsApi.createArmazenamento(nome.trim());
        setAssetArmazenamentoId(res.id);
      } else if (type === 'departamento') {
        const res = await assetsApi.createDepartamento(nome.trim());
        setAssetDepartamentoId(res.id);
      }
      fetchReferences(); // re-fetch references
    } catch (err: any) {
      alert(err.response?.data?.error || 'Erro ao criar referência.');
    }
  };

  // Status transitions
  const handleUpdateStatus = async (id: number, newStatus: AssetStatus) => {
    const originalAsset = assets.find(a => a.id === id);
    if (!originalAsset) return;

    try {
      await assetsApi.update(id, { ...originalAsset, status: newStatus });
      setGlobalSuccess(`Status do ativo alterado para "${newStatus}".`);
      fetchAssets();
    } catch (err: any) {
      setGlobalError(err.response?.data?.error || 'Falha ao atualizar status do ativo.');
    }
  };

  // Duplication wizard flow
  const handleOpenDuplicate = (a: Asset) => {
    setDuplicateTemplate(a);
    setDuplicateCount(1);
    setDuplicateStep('count');
    setDuplicateResults([]);
    setShowDuplicateModal(true);
  };

  const handleSetupSpecs = (e: React.FormEvent) => {
    e.preventDefault();
    const specs: BulkCopySpec[] = [];
    for (let i = 0; i < duplicateCount; i++) {
      specs.push({
        e_patrimonio: `${duplicateTemplate?.e_patrimonio}-${i + 1}`,
        numero_serie: '',
        current_local_id: duplicateTemplate?.current_local_id || null,
        current_armazenamento_id: duplicateTemplate?.current_armazenamento_id || null,
      });
    }
    setDuplicateSpecs(specs);
    setDuplicateStep('specs');
  };

  const handleSpecChange = (index: number, field: keyof BulkCopySpec, value: any) => {
    const updated = [...duplicateSpecs];
    updated[index] = { ...updated[index], [field]: value };
    setDuplicateSpecs(updated);
  };

  const handleExecuteDuplication = async () => {
    if (!duplicateTemplate) return;
    try {
      const response = await assetsApi.bulkDuplicate({
        template_id: duplicateTemplate.id,
        copies: duplicateSpecs
      });
      setDuplicateSuccessCount(response.success_count);
      setDuplicateFailedCount(response.failed_count);
      setDuplicateResults(response.results);
      setDuplicateStep('results');
      fetchAssets();
    } catch (err: any) {
      alert('Erro crítico ao duplicar ativos.');
    }
  };

  // Scanning simulation
  const handleScanFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setScannerError(null);
    setScannedAsset(null);
    try {
      const result = await assetsApi.scanQRCode(file);
      setScannedAsset(result);
    } catch (err: any) {
      setScannerError(err.response?.data?.error || 'QR Code inválido ou inacessível.');
    }
  };

  // Group assets by category name for list view
  const groupedAssets: Record<string, Asset[]> = {};
  assets.forEach(a => {
    const catName = a.categoria?.nome || 'Sem Categoria';
    if (!groupedAssets[catName]) {
      groupedAssets[catName] = [];
    }
    groupedAssets[catName].push(a);
  });

  // Kanban statuses list
  const statusesList: { name: AssetStatus; color: string; label: string }[] = [
    { name: 'Disponível', color: 'border-green-500/30 bg-green-500/5 text-green-400', label: 'Disponível' },
    { name: 'Em uso', color: 'border-blue-500/30 bg-blue-500/5 text-blue-400', label: 'Em Uso' },
    { name: 'Manutenção', color: 'border-amber-500/30 bg-amber-500/5 text-amber-400', label: 'Manutenção' },
    { name: 'Armazenado', color: 'border-purple-500/30 bg-purple-500/5 text-purple-400', label: 'Armazenado' },
    { name: 'Baixado', color: 'border-red-500/30 bg-red-500/5 text-red-400', label: 'Baixado' },
  ];

  return (
    <div className="space-y-8">
      {/* Notifications */}
      {globalError && (
        <div className="p-4 border border-red-500/30 bg-red-500/5 text-red-400 text-sm font-mono flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ShieldAlert size={18} />
            <span>{globalError}</span>
          </div>
          <button onClick={() => setGlobalError(null)} className="text-red-400/70 hover:text-red-400 font-bold">&times;</button>
        </div>
      )}

      {globalSuccess && (
        <div className="p-4 border border-brand-primary/30 bg-brand-primary/5 text-brand-primary text-sm font-mono flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Check size={18} />
            <span>{globalSuccess}</span>
          </div>
          <button onClick={() => setGlobalSuccess(null)} className="text-brand-primary/70 hover:text-brand-primary font-bold">&times;</button>
        </div>
      )}

      {/* Header section */}
      <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0">
            Ativos & Inventário
          </h1>
          <p className="text-brand-muted text-sm mt-1">
            Gestão de equipamentos, controle patrimonial, QR Codes e Kanban de oficina.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowScannerModal(true)}
            className="border border-brand-border hover:bg-brand-card text-brand-text font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs flex items-center space-x-1.5 transition-colors"
          >
            <QrCode size={16} />
            <span>Scanner QR</span>
          </button>

          {isManagerOrAbove && (
            <button
              onClick={handleOpenCreate}
              className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs flex items-center space-x-1.5 transition-colors"
            >
              <Plus size={16} />
              <span>Cadastrar Ativo</span>
            </button>
          )}
        </div>
      </div>

      {/* Tabs Menu */}
      <div className="flex border-b border-brand-border">
        <button
          onClick={() => setActiveTab('table')}
          className={`px-5 py-3 border-b-2 font-mono text-xs uppercase tracking-wider flex items-center space-x-2 transition-all ${
            activeTab === 'table'
              ? 'border-brand-primary text-brand-primary bg-brand-primary/5'
              : 'border-transparent text-brand-muted hover:text-brand-text'
          }`}
        >
          <TableIcon size={16} />
          <span>Tabela Geral</span>
        </button>

        <button
          onClick={() => setActiveTab('kanban')}
          className={`px-5 py-3 border-b-2 font-mono text-xs uppercase tracking-wider flex items-center space-x-2 transition-all ${
            activeTab === 'kanban'
              ? 'border-brand-primary text-brand-primary bg-brand-primary/5'
              : 'border-transparent text-brand-muted hover:text-brand-text'
          }`}
        >
          <KanbanIcon size={16} />
          <span>Kanban Oficina</span>
        </button>

        <button
          onClick={() => setActiveTab('reports')}
          className={`px-5 py-3 border-b-2 font-mono text-xs uppercase tracking-wider flex items-center space-x-2 transition-all ${
            activeTab === 'reports'
              ? 'border-brand-primary text-brand-primary bg-brand-primary/5'
              : 'border-transparent text-brand-muted hover:text-brand-text'
          }`}
        >
          <FileText size={16} />
          <span>Filtros & Relatórios</span>
        </button>
      </div>

      {/* SEARCH AND QUICK FILTERS FOR TABLE & KANBAN */}
      {activeTab !== 'reports' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-brand-card/25 border border-brand-border p-4">
          <div className="relative">
            <Search className="absolute left-3 top-3 text-brand-muted" size={16} />
            <input
              type="text"
              placeholder="Buscar por E-Patrimônio..."
              value={searchEP}
              onChange={(e) => setSearchEP(e.target.value)}
              className="w-full bg-brand-dark border border-brand-border pl-10 pr-4 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-mono transition-colors"
            />
          </div>

          <div>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value ? Number(e.target.value) : '')}
              className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono"
            >
              <option value="">Todas as Categorias</option>
              {references?.categorias.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.nome}</option>
              ))}
            </select>
          </div>

          <div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono"
            >
              <option value="">Todos os Status</option>
              <option value="Disponível">Disponível</option>
              <option value="Em uso">Em Uso</option>
              <option value="Manutenção">Manutenção</option>
              <option value="Armazenado">Armazenado</option>
              <option value="Baixado">Baixado</option>
              <option value="ativo_fixo">🔒 Ativo Fixo (Bloqueado)</option>
            </select>
          </div>
        </div>
      )}

      {/* TAB CONTENT: TABLE VIEW */}
      {activeTab === 'table' && (
        <div className="border border-brand-border bg-brand-card">
          {loading ? (
            <div className="p-12 text-center flex flex-col items-center justify-center space-y-4">
              <RefreshCw className="animate-spin text-brand-primary" size={24} />
              <span className="font-mono text-xs text-brand-muted uppercase">Sincronizando base de dados...</span>
            </div>
          ) : Object.keys(groupedAssets).length === 0 ? (
            <div className="p-12 text-center text-brand-muted font-mono text-xs uppercase">
              Nenhum ativo localizado na base de dados.
            </div>
          ) : (
            <div className="divide-y divide-brand-border">
              {Object.entries(groupedAssets).map(([categoryName, items]) => (
                <div key={categoryName} className="space-y-0.5">
                  <div className="bg-brand-dark/40 px-4 py-2 border-b border-brand-border flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-brand-primary uppercase tracking-widest">{categoryName}</span>
                    <span className="font-mono text-[10px] text-brand-muted">{items.length} itens</span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-brand-border/40 text-[10px] font-mono uppercase tracking-wider text-brand-muted">
                          <th className="p-4 w-1/4">Equipamento</th>
                          <th className="p-4">Patrimônio / S/N</th>
                          <th className="p-4">Local / Armaz.</th>
                          <th className="p-4">Status</th>
                          <th className="p-4">Posse / Setor</th>
                          {isManagerOrAbove && <th className="p-4 text-right">Ações</th>}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-brand-border/30 text-sm">
                        {items.map(a => (
                          <tr key={a.id} className="hover:bg-brand-dark/15">
                            <td className="p-4">
                              <div className="font-medium text-brand-text flex items-center space-x-1.5">
                                <span>{a.nome}</span>
                                {a.bloqueado && <span title="Ativo Fixo Bloqueado"><Lock size={12} className="text-purple-400" /></span>}
                              </div>
                              <div className="text-xs text-brand-muted">{a.modelo || 'Sem modelo'}</div>
                            </td>
                            <td className="p-4">
                              <div className="font-mono text-xs text-brand-text">{a.e_patrimonio}</div>
                              <div className="text-[10px] text-brand-muted font-mono">{a.numero_serie ? `S/N: ${a.numero_serie}` : 'S/N: —'}</div>
                            </td>
                            <td className="p-4 text-xs">
                              <div className="text-brand-text">{a.current_local?.nome || '—'}</div>
                              <div className="text-brand-muted font-mono">{a.current_armazenamento?.nome}</div>
                            </td>
                            <td className="p-4">
                              {a.status === 'Manutenção' ? (
                                <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 border border-amber-500/30 bg-amber-500/5 text-amber-400">
                                  Manutenção
                                </span>
                              ) : a.status === 'Disponível' ? (
                                <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 border border-green-500/30 bg-green-500/5 text-green-400">
                                  Disponível
                                </span>
                              ) : (
                                <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 border border-brand-border bg-brand-dark/30 text-brand-text">
                                  {a.status}
                                </span>
                              )}
                            </td>
                            <td className="p-4 text-xs">
                              <div className="text-brand-text">{a.current_user?.nome || '—'}</div>
                              <div className="text-brand-muted">{a.current_departamento?.nome}</div>
                            </td>
                            {isManagerOrAbove && (
                              <td className="p-4 text-right">
                                <div className="flex items-center justify-end space-x-2">
                                  <button
                                    onClick={() => handleOpenDuplicate(a)}
                                    className="border border-brand-border hover:border-brand-primary text-brand-text p-1.5 transition-colors"
                                    title="Duplicar ativo em lote"
                                  >
                                    <Copy size={13} />
                                  </button>
                                  <button
                                    onClick={() => handleOpenEdit(a)}
                                    className="border border-brand-border hover:border-brand-primary text-brand-text p-1.5 transition-colors"
                                    title="Editar"
                                  >
                                    <Edit2 size={13} />
                                  </button>
                                  <button
                                    onClick={() => handleDeleteAsset(a.id)}
                                    className="border border-brand-border hover:border-red-500 text-red-400 p-1.5 transition-colors"
                                    title="Excluir"
                                  >
                                    <Trash2 size={13} />
                                  </button>
                                </div>
                              </td>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB CONTENT: KANBAN BOARD */}
      {activeTab === 'kanban' && (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
          {statusesList.map(column => {
            const columnAssets = assets.filter(a => a.status === column.name);
            return (
              <div key={column.name} className="flex flex-col h-[70vh] border border-brand-border bg-brand-card">
                {/* Header */}
                <div className={`p-3 border-b border-brand-border flex items-center justify-between font-mono text-xs uppercase tracking-wider font-semibold ${column.color}`}>
                  <span>{column.label}</span>
                  <span>{columnAssets.length}</span>
                </div>

                {/* Cards Container */}
                <div className="flex-1 overflow-y-auto p-2 space-y-2 bg-brand-dark/10">
                  {columnAssets.map(a => (
                    <div key={a.id} className="border border-brand-border bg-brand-card p-3 space-y-3 shadow-sm hover:border-brand-primary/50 transition-colors">
                      <div>
                        <div className="font-medium text-xs text-brand-text flex items-center justify-between">
                          <span className="truncate pr-1">{a.nome}</span>
                          {a.bloqueado && <Lock size={10} className="text-purple-400 flex-shrink-0" />}
                        </div>
                        <div className="text-[10px] text-brand-muted font-mono">{a.e_patrimonio}</div>
                      </div>

                      {/* Dropdown status update */}
                      {isManagerOrAbove && (
                        <div>
                          <label className="text-[9px] font-mono uppercase text-brand-muted block mb-1">Mudar Status</label>
                          <select
                            value={a.status}
                            onChange={(e) => handleUpdateStatus(a.id, e.target.value as AssetStatus)}
                            className="w-full bg-brand-dark border border-brand-border px-1.5 py-1 text-[10px] text-brand-text focus:outline-none font-mono"
                          >
                            <option value="Disponível">Disponível</option>
                            <option value="Em uso">Em Uso</option>
                            <option value="Manutenção">Manutenção</option>
                            <option value="Armazenado">Armazenado</option>
                            <option value="Baixado">Baixado</option>
                          </select>
                        </div>
                      )}

                      <div className="flex justify-between items-center text-[9px] text-brand-muted border-t border-brand-border/30 pt-2 font-mono">
                        <span>{a.categoria?.nome || 'Sem Categoria'}</span>
                        <span className="truncate max-w-[80px]">{a.current_local?.nome || '—'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* TAB CONTENT: FILTERS & REPORTS */}
      {activeTab === 'reports' && (
        <div className="space-y-6">
          <div className="bg-brand-card border border-brand-border p-6 space-y-6">
            <div className="border-b border-brand-border pb-3 flex items-center space-x-2">
              <Filter className="text-brand-primary" size={18} />
              <h3 className="font-bold text-sm uppercase tracking-wider text-brand-text font-mono">Painel de Relatórios</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Data Aquisição (Início)</label>
                <input
                  type="date"
                  value={reportStartDate}
                  onChange={(e) => setReportStartDate(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-mono transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Data Aquisição (Fim)</label>
                <input
                  type="date"
                  value={reportEndDate}
                  onChange={(e) => setReportEndDate(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-mono transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Nome do Ativo</label>
                <input
                  type="text"
                  placeholder="Nome..."
                  value={reportName}
                  onChange={(e) => setReportName(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Categoria</label>
                <select
                  value={reportCategory}
                  onChange={(e) => setReportCategory(e.target.value ? Number(e.target.value) : '')}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono"
                >
                  <option value="">Todas</option>
                  {references?.categorias.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.nome}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Localização</label>
                <select
                  value={reportLocation}
                  onChange={(e) => setReportLocation(e.target.value ? Number(e.target.value) : '')}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono"
                >
                  <option value="">Todas</option>
                  {references?.localizacoes.map(loc => (
                    <option key={loc.id} value={loc.id}>{loc.nome}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Fornecedor</label>
                <select
                  value={reportSupplier}
                  onChange={(e) => setReportSupplier(e.target.value ? Number(e.target.value) : '')}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono"
                >
                  <option value="">Todos</option>
                  {references?.fornecedores.map(f => (
                    <option key={f.id} value={f.id}>{f.nome}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Nota Fiscal</label>
                <input
                  type="text"
                  placeholder="Número..."
                  value={reportInvoice}
                  onChange={(e) => setReportInvoice(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-mono transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">E-Patrimônio</label>
                <input
                  type="text"
                  placeholder="EP..."
                  value={reportPatrimonio}
                  onChange={(e) => setReportPatrimonio(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-mono transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">Status</label>
                <select
                  value={reportStatus}
                  onChange={(e) => setReportStatus(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono"
                >
                  <option value="">Todos</option>
                  <option value="Disponível">Disponível</option>
                  <option value="Em uso">Em Uso</option>
                  <option value="Manutenção">Manutenção</option>
                  <option value="Armazenado">Armazenado</option>
                  <option value="Baixado">Baixado</option>
                  <option value="ativo_fixo">🔒 Ativo Fixo (Bloqueado)</option>
                </select>
              </div>
            </div>

            <div className="flex space-x-3 pt-4 border-t border-brand-border">
              <button
                onClick={() => {
                  setReportStartDate('');
                  setReportEndDate('');
                  setReportName('');
                  setReportCategory('');
                  setReportLocation('');
                  setReportSupplier('');
                  setReportInvoice('');
                  setReportPatrimonio('');
                  setReportStatus('');
                }}
                className="border border-brand-border hover:bg-brand-card text-brand-muted px-4 py-2 font-mono text-xs uppercase"
              >
                Limpar Filtros
              </button>
              
              <button
                onClick={() => {
                  assetsApi.exportCsv({
                    data_inicio: reportStartDate,
                    data_fim: reportEndDate,
                    nome: reportName,
                    categoria_id: reportCategory,
                    localizacao_id: reportLocation,
                    fornecedor_id: reportSupplier,
                    nfe: reportInvoice,
                    e_patrimonio: reportPatrimonio,
                    status: reportStatus,
                  }).catch(() => {
                    setGlobalError('Falha ao exportar relatório de ativos.');
                  });
                }}
                className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-5 py-2 uppercase tracking-wider text-xs flex items-center space-x-1.5"
              >
                <FileText size={14} />
                <span>Exportar CSV</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DIALOG: CREATE / UPDATE ASSET */}
      {showFormModal && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-2xl border border-brand-border bg-brand-card p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">
                {editAssetId ? 'Editar Ativo' : 'Registrar Novo Ativo'}
              </h3>
              <button onClick={() => setShowFormModal(false)} className="text-brand-muted hover:text-brand-text">
                <X size={20} />
              </button>
            </div>

            {formError && (
              <div className="p-3 border border-red-500/30 bg-red-500/5 text-red-400 text-xs font-mono flex items-center space-x-2">
                <ShieldAlert size={16} />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleSaveAsset} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted mb-1.5">Nome do Ativo *</label>
                  <input
                    type="text"
                    required
                    value={assetName}
                    onChange={(e) => setAssetName(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted mb-1.5">E-Patrimônio *</label>
                  <input
                    type="text"
                    required
                    value={assetEP}
                    onChange={(e) => setAssetEP(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted mb-1.5">Modelo</label>
                  <input
                    type="text"
                    value={assetModelo}
                    onChange={(e) => setAssetModelo(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted mb-1.5">Número de Série</label>
                  <input
                    type="text"
                    value={assetSerie}
                    onChange={(e) => setAssetSerie(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted mb-1.5">Valor R$</label>
                  <input
                    type="number"
                    step="0.01"
                    value={assetValor}
                    onChange={(e) => setAssetValor(Number(e.target.value))}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-mono"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted mb-1.5">Data de Aquisição</label>
                  <input
                    type="date"
                    value={assetDataAquisicao}
                    onChange={(e) => setAssetDataAquisicao(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-mono"
                  />
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted">Categoria</label>
                    <button type="button" onClick={() => handleCreateReference('categoria')} className="text-brand-primary hover:text-brand-primary/80" title="Criar Nova Categoria">
                      <Plus size={14} />
                    </button>
                  </div>
                  <select
                    value={assetCategoriaId}
                    onChange={(e) => setAssetCategoriaId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-mono"
                  >
                    <option value="">Selecione...</option>
                    {references?.categorias.map(c => (
                      <option key={c.id} value={c.id}>{c.nome}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted mb-1.5">Fornecedor</label>
                  <select
                    value={assetFornecedorId}
                    onChange={(e) => setAssetFornecedorId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-mono"
                  >
                    <option value="">Selecione...</option>
                    {references?.fornecedores.map(f => (
                      <option key={f.id} value={f.id}>{f.nome}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted mb-1.5">Status Atual</label>
                  <select
                    value={assetStatus}
                    onChange={(e) => setAssetStatusValue(e.target.value as AssetStatus)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-mono"
                  >
                    <option value="Disponível">Disponível</option>
                    <option value="Em uso">Em Uso</option>
                    <option value="Manutenção">Manutenção</option>
                    <option value="Armazenado">Armazenado</option>
                    <option value="Baixado">Baixado</option>
                  </select>
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted">Localização Física</label>
                    <button type="button" onClick={() => handleCreateReference('localizacao')} className="text-brand-primary hover:text-brand-primary/80" title="Criar Nova Localização">
                      <Plus size={14} />
                    </button>
                  </div>
                  <select
                    value={assetLocalId}
                    onChange={(e) => setAssetLocalId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-mono"
                  >
                    <option value="">Selecione...</option>
                    {references?.localizacoes.map(loc => (
                      <option key={loc.id} value={loc.id}>{loc.nome}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted">Armazenamento (Rack/Escaninho)</label>
                    <button type="button" onClick={() => handleCreateReference('armazenamento')} className="text-brand-primary hover:text-brand-primary/80" title="Criar Novo Armazenamento">
                      <Plus size={14} />
                    </button>
                  </div>
                  <select
                    value={assetArmazenamentoId}
                    onChange={(e) => setAssetArmazenamentoId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-mono"
                  >
                    <option value="">Selecione...</option>
                    {references?.armazenamentos.map(arm => (
                      <option key={arm.id} value={arm.id}>{arm.nome}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted mb-1.5">Em Posse De (Pessoa / Usuário)</label>
                  <input
                    type="text"
                    value={assetEmPosseDe}
                    onChange={(e) => setAssetEmPosseDe(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-mono"
                  />
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted">Setor (Departamento)</label>
                    <button type="button" onClick={() => handleCreateReference('departamento')} className="text-brand-primary hover:text-brand-primary/80" title="Criar Novo Setor">
                      <Plus size={14} />
                    </button>
                  </div>
                  <select
                    value={assetDepartamentoId}
                    onChange={(e) => setAssetDepartamentoId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-mono"
                  >
                    <option value="">Selecione...</option>
                    {references?.setores.map(setor => (
                      <option key={setor.id} value={setor.id}>{setor.nome}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted mb-1.5">Descrição / Detalhes Adicionais</label>
                <textarea
                  value={assetDescricao}
                  onChange={(e) => setAssetDescricao(e.target.value)}
                  rows={3}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary font-sans"
                />
              </div>

              <div className="flex flex-col sm:flex-row gap-4 py-2 border-t border-b border-brand-border/30">
                <div className="flex items-center space-x-2 select-none cursor-pointer">
                  <input
                    id="assetBloqueado"
                    type="checkbox"
                    checked={assetBloqueado}
                    onChange={(e) => setAssetBloqueado(e.target.checked)}
                    className="rounded-none accent-brand-primary border-brand-border"
                  />
                  <label htmlFor="assetBloqueado" className="font-mono uppercase tracking-wider text-brand-text">
                    🔒 Ativo Fixo (Bloqueia alteração de local em manutenção)
                  </label>
                </div>

                <div className="flex items-center space-x-2 select-none cursor-pointer">
                  <input
                    id="assetRequerRH"
                    type="checkbox"
                    checked={assetRequerRH}
                    onChange={(e) => setAssetRequerRH(e.target.checked)}
                    className="rounded-none accent-brand-primary border-brand-border"
                  />
                  <label htmlFor="assetRequerRH" className="font-mono uppercase tracking-wider text-brand-text">
                    Requer Termo do RH
                  </label>
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowFormModal(false)}
                  className="border border-brand-border hover:bg-brand-card px-4 py-2 font-mono text-xs uppercase"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs"
                >
                  Confirmar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DIALOG: BULK DUPLICATE WIZARD */}
      {showDuplicateModal && duplicateTemplate && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-2xl border border-brand-border bg-brand-card p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <div>
                <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">Duplicar Ativo</h3>
                <p className="text-[10px] text-brand-muted font-mono mt-0.5">Origem: {duplicateTemplate.nome} ({duplicateTemplate.e_patrimonio})</p>
              </div>
              <button onClick={() => setShowDuplicateModal(false)} className="text-brand-muted hover:text-brand-text">
                <X size={20} />
              </button>
            </div>

            {/* STEP 1: QUANTIDADE */}
            {duplicateStep === 'count' && (
              <form onSubmit={handleSetupSpecs} className="space-y-6">
                <div className="bg-brand-dark/40 border border-brand-border p-4 space-y-3">
                  <h4 className="font-bold text-[10px] font-mono uppercase tracking-widest text-brand-primary">Dados herdados automaticamente</h4>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div><span className="text-brand-muted">Nome:</span> <span className="text-brand-text font-bold">{duplicateTemplate.nome}</span></div>
                    <div><span className="text-brand-muted">Modelo:</span> <span className="text-brand-text">{duplicateTemplate.modelo || '—'}</span></div>
                    <div><span className="text-brand-muted">Categoria:</span> <span className="text-brand-text">{duplicateTemplate.categoria?.nome || '—'}</span></div>
                    <div><span className="text-brand-muted">Fornecedor:</span> <span className="text-brand-text">{duplicateTemplate.fornecedor?.nome || '—'}</span></div>
                    {duplicateTemplate.valor && (
                      <div><span className="text-brand-muted">Valor:</span> <span className="text-brand-text font-mono font-bold">R$ {duplicateTemplate.valor.toFixed(2)}</span></div>
                    )}
                    <div><span className="text-brand-muted">Original Local:</span> <span className="text-brand-text">{duplicateTemplate.current_local?.nome || '—'}</span></div>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="font-mono text-xs font-bold text-brand-text uppercase tracking-widest block">Quantas cópias deseja gerar?</label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={duplicateCount}
                    onChange={(e) => setDuplicateCount(Math.min(50, Math.max(1, Number(e.target.value))))}
                    className="w-full bg-brand-dark border border-brand-border p-3 text-lg font-bold font-mono text-center text-brand-text focus:outline-none focus:border-brand-primary"
                  />
                  <p className="font-mono text-[9px] text-brand-muted">Limite operacional: 50 cópias por lote.</p>
                </div>

                <div className="flex justify-end space-x-3 pt-4 border-t border-brand-border">
                  <button
                    type="button"
                    onClick={() => setShowDuplicateModal(false)}
                    className="border border-brand-border hover:bg-brand-card px-4 py-2 font-mono text-xs uppercase"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs"
                  >
                    Prosseguir
                  </button>
                </div>
              </form>
            )}

            {/* STEP 2: CONFIGURE COPIES (E-Patrimonio, Serial, Locations) */}
            {duplicateStep === 'specs' && (
              <div className="space-y-4">
                <div className="p-3 border border-brand-primary/30 bg-brand-primary/5 text-brand-primary text-xs font-mono">
                  Defina os identificadores individuais de cada cópia.
                </div>

                <div className="space-y-3 max-h-[50vh] overflow-y-auto pr-2">
                  {duplicateSpecs.map((spec, i) => (
                    <div key={i} className="border border-brand-border bg-brand-dark/20 p-4 space-y-3">
                      <div className="flex items-center space-x-2 font-mono text-xs font-semibold text-brand-text">
                        <span className="w-5 h-5 bg-brand-primary text-brand-dark flex items-center justify-center font-bold text-[10px]">
                          {i + 1}
                        </span>
                        <span>Cópia #{i + 1}</span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                        <div>
                          <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted mb-1">E-Patrimônio *</label>
                          <input
                            type="text"
                            required
                            value={spec.e_patrimonio}
                            onChange={(e) => handleSpecChange(i, 'e_patrimonio', e.target.value)}
                            className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-xs text-brand-text focus:outline-none focus:border-brand-primary font-mono"
                          />
                        </div>

                        <div>
                          <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted mb-1">Número de Série (Opcional)</label>
                          <input
                            type="text"
                            value={spec.numero_serie || ''}
                            onChange={(e) => handleSpecChange(i, 'numero_serie', e.target.value || null)}
                            placeholder="S/N"
                            className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-xs text-brand-text focus:outline-none focus:border-brand-primary font-mono"
                          />
                        </div>

                        <div>
                          <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted mb-1">Localização</label>
                          <select
                            value={spec.current_local_id || ''}
                            onChange={(e) => handleSpecChange(i, 'current_local_id', e.target.value ? Number(e.target.value) : null)}
                            className="w-full bg-brand-dark border border-brand-border px-2 py-1.5 text-xs text-brand-text focus:outline-none font-mono"
                          >
                            <option value="">— Herdado do original —</option>
                            {references?.localizacoes.map(loc => (
                              <option key={loc.id} value={loc.id}>{loc.nome}</option>
                            ))}
                          </select>
                        </div>

                        <div>
                          <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted mb-1">Armazenamento</label>
                          <select
                            value={spec.current_armazenamento_id || ''}
                            onChange={(e) => handleSpecChange(i, 'current_armazenamento_id', e.target.value ? Number(e.target.value) : null)}
                            className="w-full bg-brand-dark border border-brand-border px-2 py-1.5 text-xs text-brand-text focus:outline-none font-mono"
                          >
                            <option value="">— Herdado do original —</option>
                            {references?.armazenamentos.map(arm => (
                              <option key={arm.id} value={arm.id}>{arm.nome}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex justify-end space-x-3 pt-4 border-t border-brand-border">
                  <button
                    onClick={() => setDuplicateStep('count')}
                    className="border border-brand-border hover:bg-brand-card text-brand-muted px-4 py-2 font-mono text-xs uppercase"
                  >
                    Voltar
                  </button>
                  <button
                    onClick={handleExecuteDuplication}
                    className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs"
                  >
                    Confirmar Duplicação
                  </button>
                </div>
              </div>
            )}

            {/* STEP 3: RESULTS (Success / Partial Success Report) */}
            {duplicateStep === 'results' && (
              <div className="space-y-4">
                <div className="border border-brand-border bg-brand-dark/30 p-4 space-y-2">
                  <h4 className="font-bold text-sm uppercase tracking-wider text-brand-text font-mono">Relatório de Duplicação</h4>
                  <p className="text-xs text-brand-muted">
                    Executado: <span className="text-brand-primary font-bold">{duplicateSuccessCount}</span> criados com sucesso / <span className="text-red-400 font-bold">{duplicateFailedCount}</span> falhas.
                  </p>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-brand-border/60 font-mono uppercase text-brand-muted text-[10px]">
                        <th className="py-2 px-3">E-Patrimônio</th>
                        <th className="py-2 px-3">Resultado</th>
                        <th className="py-2 px-3">Detalhes / Erro</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-brand-border/30">
                      {duplicateResults.map((res, idx) => (
                        <tr key={idx} className="hover:bg-brand-dark/10">
                          <td className="py-2 px-3 font-mono font-bold text-brand-text">{res.e_patrimonio}</td>
                          <td className="py-2 px-3">
                            {res.success ? (
                              <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 border border-green-500/30 bg-green-500/5 text-green-400">Criado</span>
                            ) : (
                              <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 border border-red-500/30 bg-red-500/5 text-red-400">Falhou</span>
                            )}
                          </td>
                          <td className="py-2 px-3 text-brand-muted font-mono">{res.error || 'Sucesso'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="flex justify-end pt-4 border-t border-brand-border">
                  <button
                    onClick={() => setShowDuplicateModal(false)}
                    className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs"
                  >
                    Fechar Relatório
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* DIALOG: QR SCANNER IMAGE UPLOADER */}
      {showScannerModal && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md border border-brand-border bg-brand-card p-6 space-y-6">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text flex items-center space-x-2">
                <QrCode size={18} className="text-brand-primary" />
                <span>Simular Scanner QR</span>
              </h3>
              <button onClick={() => setShowScannerModal(false)} className="text-brand-muted hover:text-brand-text">
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4">
              <p className="text-xs text-brand-muted">
                Envie uma imagem de QR Code para decodificar e carregar o ativo associado de forma instantânea.
              </p>

              {/* Upload trigger area */}
              <div 
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-brand-border hover:border-brand-primary/50 bg-brand-dark/30 p-8 text-center cursor-pointer space-y-3 transition-colors"
              >
                <Upload className="mx-auto text-brand-muted hover:text-brand-primary transition-colors" size={32} />
                <div>
                  <span className="text-xs font-mono text-brand-text uppercase block font-semibold">Selecionar Imagem</span>
                  <span className="text-[10px] text-brand-muted block mt-1">PNG, JPG ou GIF</span>
                </div>
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleScanFile} 
                  accept="image/*" 
                  className="hidden" 
                />
              </div>

              {/* Error block */}
              {scannerError && (
                <div className="p-3 border border-red-500/30 bg-red-500/5 text-red-400 text-xs font-mono flex items-center space-x-2">
                  <ShieldAlert size={16} />
                  <span>{scannerError}</span>
                </div>
              )}

              {/* Success Result */}
              {scannedAsset && (
                <div className="border border-brand-primary/30 bg-brand-primary/5 p-4 space-y-3">
                  <div className="flex items-center space-x-2 text-brand-primary">
                    <Check size={16} />
                    <span className="font-mono text-[10px] font-bold uppercase tracking-wider">Ativo Identificado</span>
                  </div>
                  
                  <div className="text-xs space-y-1">
                    <div className="font-bold text-brand-text">{scannedAsset.nome}</div>
                    <div className="font-mono text-brand-muted text-[10px]">{scannedAsset.e_patrimonio}</div>
                    <div className="text-brand-muted">Local: {scannedAsset.current_local?.nome || '—'}</div>
                    <div className="text-brand-muted">Status: {scannedAsset.status}</div>
                  </div>

                  <button
                    onClick={() => {
                      setShowScannerModal(false);
                      handleOpenEdit(scannedAsset);
                    }}
                    className="w-full bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono py-2 uppercase tracking-wider text-[10px]"
                  >
                    Abrir para Visualização / Edição
                  </button>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2 border-t border-brand-border">
              <button
                onClick={() => setShowScannerModal(false)}
                className="border border-brand-border hover:bg-brand-card text-brand-muted px-4 py-2 font-mono text-xs uppercase"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
