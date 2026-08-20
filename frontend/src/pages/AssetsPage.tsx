import React, { useState, useEffect, useRef } from 'react';
import { assetsApi } from '../api/assets';
import { usersApi } from '../api/users';
import { maintenanceApi } from '../api/maintenance';
import type { 
  Asset, 
  AssetStatus, 
  AssetReferences,
  BulkCopySpec,
  AssetImportResponse,
  User
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
  Lock,
  MapPin,
  Layers3,
  Wrench,
  Download,
  ArrowRightLeft
} from 'lucide-react';

export const AssetsPage: React.FC = () => {
  const currentAuthUser = useAuthStore().user;
  const isManagerOrAbove = currentAuthUser?.role === 'admin' || 
                           currentAuthUser?.role === 'gerente_ti' || 
                           currentAuthUser?.role === 'gerente_infra' || 
                           currentAuthUser?.role === 'tecnico';

  const [activeTab, setActiveTab] = useState<'table' | 'kanban' | 'reports' | 'references'>('table');
  const [assets, setAssets] = useState<Asset[]>([]);
  const [references, setReferences] = useState<AssetReferences | null>(null);
  const [loading, setLoading] = useState(false);
  const [reportAssets, setReportAssets] = useState<Asset[]>([]);
  const [reportLoading, setReportLoading] = useState(false);

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
  const importInputRef = useRef<HTMLInputElement>(null);

  // CSV Import State
  const [showImportModal, setShowImportModal] = useState(false);
  const [importingCsv, setImportingCsv] = useState(false);
  const [selectedImportFile, setSelectedImportFile] = useState<File | null>(null);
  const [importSummary, setImportSummary] = useState<AssetImportResponse | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  // Reference management state
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newLocationName, setNewLocationName] = useState('');
  const [creatingCategory, setCreatingCategory] = useState(false);
  const [creatingLocation, setCreatingLocation] = useState(false);
  const [editingCategoryId, setEditingCategoryId] = useState<number | null>(null);
  const [editingCategoryName, setEditingCategoryName] = useState('');
  const [editingLocationId, setEditingLocationId] = useState<number | null>(null);
  const [editingLocationName, setEditingLocationName] = useState('');
  const [savingCategoryId, setSavingCategoryId] = useState<number | null>(null);
  const [savingLocationId, setSavingLocationId] = useState<number | null>(null);
  const [deletingCategoryId, setDeletingCategoryId] = useState<number | null>(null);
  const [deletingLocationId, setDeletingLocationId] = useState<number | null>(null);

  // Asset Details Modal State
  const [selectedAssetForDetail, setSelectedAssetForDetail] = useState<Asset | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showDetailMaintenanceForm, setShowDetailMaintenanceForm] = useState(false);
  const [showDetailTransferForm, setShowDetailTransferForm] = useState(false);
  
  // Maintenance request inside modal state
  const [detailMaintenanceDescription, setDetailMaintenanceDescription] = useState('');
  const [detailMaintenanceLoading, setDetailMaintenanceLoading] = useState(false);
  const [detailMaintenanceError, setDetailMaintenanceError] = useState<string | null>(null);

  // Transfer inside modal state
  const [detailTransferUserId, setDetailTransferUserId] = useState<number | ''>('');
  const [detailTransferLoading, setDetailTransferLoading] = useState(false);
  const [detailTransferError, setDetailTransferError] = useState<string | null>(null);

  // List of users for transferring
  const [usersList, setUsersList] = useState<User[]>([]);

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

  const fetchUsers = async () => {
    try {
      const data = await usersApi.list();
      setUsersList(data);
    } catch (err) {
      console.error('Falha ao buscar usuários:', err);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchReportAssets = async () => {
    setReportLoading(true);
    setGlobalError(null);
    try {
      const data = await assetsApi.list(0, 100, {
        data_inicio: reportStartDate,
        data_fim: reportEndDate,
        nome: reportName,
        categoria_id: reportCategory,
        localizacao_id: reportLocation,
        fornecedor_id: reportSupplier,
        nfe: reportInvoice,
        e_patrimonio: reportPatrimonio,
        status: reportStatus,
      });
      setReportAssets(data);
    } catch (_err) {
      setGlobalError('Falha ao buscar ativos para o painel de relatórios.');
    } finally {
      setReportLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
    fetchReferences();
  }, [searchEP, filterCategory, filterStatus]);

  useEffect(() => {
    if (activeTab === 'reports') {
      fetchReportAssets();
    }
  }, [
    activeTab,
    reportStartDate,
    reportEndDate,
    reportName,
    reportCategory,
    reportLocation,
    reportSupplier,
    reportInvoice,
    reportPatrimonio,
    reportStatus,
  ]);

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

  const handleOpenDetailModal = (asset: Asset) => {
    setSelectedAssetForDetail(asset);
    setShowDetailModal(true);
    setShowDetailMaintenanceForm(false);
    setShowDetailTransferForm(false);
    setDetailMaintenanceDescription('');
    setDetailMaintenanceError(null);
    setDetailTransferUserId('');
    setDetailTransferError(null);
  };

  const handleRequestMaintenanceFromDetail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssetForDetail || !detailMaintenanceDescription.trim()) return;

    setDetailMaintenanceLoading(true);
    setDetailMaintenanceError(null);
    try {
      await maintenanceApi.createRequest({
        asset_id: selectedAssetForDetail.id,
        descricao: detailMaintenanceDescription.trim(),
      });
      setGlobalSuccess('Solicitação de manutenção criada com sucesso.');
      fetchAssets();
      setShowDetailMaintenanceForm(false);
      setDetailMaintenanceDescription('');
      // Update selected asset state locally if needed
      const updatedData = await assetsApi.list(0, 100, { e_patrimonio: selectedAssetForDetail.e_patrimonio });
      if (updatedData.length > 0) {
        setSelectedAssetForDetail(updatedData[0]);
      }
    } catch (err: any) {
      setDetailMaintenanceError(err.response?.data?.detail || 'Erro ao criar solicitação de manutenção.');
    } finally {
      setDetailMaintenanceLoading(false);
    }
  };

  const handleTransferAssetFromDetail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssetForDetail || !detailTransferUserId) return;

    setDetailTransferLoading(true);
    setDetailTransferError(null);
    try {
      const selectedUser = usersList.find(u => u.id === Number(detailTransferUserId));
      
      const payload: Partial<Asset> = {
        current_user_id: Number(detailTransferUserId),
        em_posse_de: selectedUser ? selectedUser.nome : null,
        status: 'Em uso',
      };
      
      const updated = await assetsApi.update(selectedAssetForDetail.id, payload);
      
      setSelectedAssetForDetail(updated);
      setGlobalSuccess('Ativo transferido com sucesso.');
      
      fetchAssets();
      if (activeTab === 'reports') {
        fetchReportAssets();
      }
      
      setShowDetailTransferForm(false);
      setDetailTransferUserId('');
    } catch (err: any) {
      setDetailTransferError(err.response?.data?.error || 'Erro ao transferir o ativo.');
    } finally {
      setDetailTransferLoading(false);
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

  const handleOpenImportModal = () => {
    setShowImportModal(true);
    setSelectedImportFile(null);
    setImportSummary(null);
    setImportError(null);
    if (importInputRef.current) {
      importInputRef.current.value = '';
    }
  };

  const handleImportCsv = async () => {
    if (!selectedImportFile) {
      setImportError('Selecione um arquivo CSV para importar.');
      return;
    }

    setImportingCsv(true);
    setImportError(null);
    try {
      const summary = await assetsApi.importCsv(selectedImportFile);
      setImportSummary(summary);
      setGlobalSuccess(`Importação concluída: ${summary.criados} criado(s), ${summary.atualizados} atualizado(s) e ${summary.falhas} falha(s).`);
      fetchAssets();
      fetchReferences();
      if (activeTab === 'reports') {
        fetchReportAssets();
      }
    } catch (err: any) {
      setImportError(err.response?.data?.error || 'Não foi possível importar o CSV.');
    } finally {
      setImportingCsv(false);
    }
  };

  const getAssetLocationLabel = (asset: Asset) => {
    if (asset.current_local?.nome) return asset.current_local.nome;
    if (asset.status === 'Manutenção' && asset.prev_local?.nome) return `${asset.prev_local.nome} (origem)`;
    return '—';
  };

  const getAssetStorageLabel = (asset: Asset) => {
    if (asset.current_armazenamento?.nome) return asset.current_armazenamento.nome;
    if (asset.status === 'Manutenção' && asset.prev_armazenamento?.nome) return `${asset.prev_armazenamento.nome} (origem)`;
    return '';
  };

  const handleCreateCategoryInline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCategoryName.trim()) return;

    setCreatingCategory(true);
    try {
      await assetsApi.createCategoria(newCategoryName.trim());
      setNewCategoryName('');
      setGlobalSuccess('Categoria criada com sucesso.');
      fetchReferences();
    } catch (err: any) {
      setGlobalError(err.response?.data?.error || 'Não foi possível criar a categoria.');
    } finally {
      setCreatingCategory(false);
    }
  };

  const handleCreateLocationInline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLocationName.trim()) return;

    setCreatingLocation(true);
    try {
      await assetsApi.createLocalizacao(newLocationName.trim());
      setNewLocationName('');
      setGlobalSuccess('Localização criada com sucesso.');
      fetchReferences();
    } catch (err: any) {
      setGlobalError(err.response?.data?.error || 'Não foi possível criar a localização.');
    } finally {
      setCreatingLocation(false);
    }
  };

  const handleStartEditCategory = (id: number, nome: string) => {
    setEditingCategoryId(id);
    setEditingCategoryName(nome);
  };

  const handleSaveCategory = async (id: number) => {
    if (!editingCategoryName.trim()) return;
    setSavingCategoryId(id);
    try {
      await assetsApi.updateCategoria(id, editingCategoryName.trim());
      setEditingCategoryId(null);
      setEditingCategoryName('');
      setGlobalSuccess('Categoria atualizada com sucesso.');
      fetchReferences();
    } catch (err: any) {
      setGlobalError(err.response?.data?.error || 'Não foi possível atualizar a categoria.');
    } finally {
      setSavingCategoryId(null);
    }
  };

  const handleDeleteCategory = async (id: number, nome: string) => {
    if (!window.confirm(`Deseja excluir a categoria "${nome}"?`)) return;
    setDeletingCategoryId(id);
    try {
      await assetsApi.deleteCategoria(id);
      if (editingCategoryId === id) {
        setEditingCategoryId(null);
        setEditingCategoryName('');
      }
      setGlobalSuccess('Categoria excluída com sucesso.');
      fetchReferences();
    } catch (err: any) {
      setGlobalError(err.response?.data?.error || 'Não foi possível excluir a categoria.');
    } finally {
      setDeletingCategoryId(null);
    }
  };

  const handleStartEditLocation = (id: number, nome: string) => {
    setEditingLocationId(id);
    setEditingLocationName(nome);
  };

  const handleSaveLocation = async (id: number) => {
    if (!editingLocationName.trim()) return;
    setSavingLocationId(id);
    try {
      await assetsApi.updateLocalizacao(id, editingLocationName.trim());
      setEditingLocationId(null);
      setEditingLocationName('');
      setGlobalSuccess('Localização atualizada com sucesso.');
      fetchReferences();
    } catch (err: any) {
      setGlobalError(err.response?.data?.error || 'Não foi possível atualizar a localização.');
    } finally {
      setSavingLocationId(null);
    }
  };

  const handleDeleteLocation = async (id: number, nome: string) => {
    if (!window.confirm(`Deseja excluir a localização "${nome}"?`)) return;
    setDeletingLocationId(id);
    try {
      await assetsApi.deleteLocalizacao(id);
      if (editingLocationId === id) {
        setEditingLocationId(null);
        setEditingLocationName('');
      }
      setGlobalSuccess('Localização excluída com sucesso.');
      fetchReferences();
    } catch (err: any) {
      setGlobalError(err.response?.data?.error || 'Não foi possível excluir a localização.');
    } finally {
      setDeletingLocationId(null);
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
        <div className="app-notice--success p-4 border border-brand-primary/30 bg-brand-primary/5 text-brand-primary text-sm font-mono flex items-center justify-between">
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
            onClick={() => {
              assetsApi.exportCsv({
                e_patrimonio: searchEP,
                categoria_id: filterCategory,
                status: filterStatus,
              }).catch(() => {
                setGlobalError('Falha ao exportar os ativos.');
              });
            }}
            className="border border-brand-border hover:bg-brand-card text-brand-text font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs flex items-center space-x-1.5 transition-colors"
          >
            <FileText size={16} />
            <span>Exportar CSV</span>
          </button>

          {isManagerOrAbove && (
            <button
              onClick={handleOpenImportModal}
              className="border border-brand-border hover:bg-brand-card text-brand-text font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs flex items-center space-x-1.5 transition-colors"
            >
              <Upload size={16} />
              <span>Importar CSV</span>
            </button>
          )}

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
              ? 'border-brand-primary text-brand-primary bg-[#ededed] opacity-100'
              : 'border-transparent text-brand-text bg-[#e6e6e6] opacity-[0.75] hover:opacity-100'
          }`}
        >
          <TableIcon size={16} />
          <span>Tabela Geral</span>
        </button>

        <button
          onClick={() => setActiveTab('kanban')}
          className={`px-5 py-3 border-b-2 font-mono text-xs uppercase tracking-wider flex items-center space-x-2 transition-all ${
            activeTab === 'kanban'
              ? 'border-brand-primary text-brand-primary bg-[#ededed] opacity-100'
              : 'border-transparent text-brand-text bg-[#e6e6e6] opacity-[0.75] hover:opacity-100'
          }`}
        >
          <KanbanIcon size={16} />
          <span>Kanban Oficina</span>
        </button>

        <button
          onClick={() => setActiveTab('reports')}
          className={`px-5 py-3 border-b-2 font-mono text-xs uppercase tracking-wider flex items-center space-x-2 transition-all ${
            activeTab === 'reports'
              ? 'border-brand-primary text-brand-primary bg-[#ededed] opacity-100'
              : 'border-transparent text-brand-text bg-[#e6e6e6] opacity-[0.75] hover:opacity-100'
          }`}
        >
          <FileText size={16} />
          <span>Filtros & Relatórios</span>
        </button>

        {isManagerOrAbove && (
          <button
            onClick={() => setActiveTab('references')}
            className={`px-5 py-3 border-b-2 font-mono text-xs uppercase tracking-wider flex items-center space-x-2 transition-all ${
              activeTab === 'references'
                ? 'border-brand-primary text-brand-primary bg-[#ededed] opacity-100'
                : 'border-transparent text-brand-text bg-[#e6e6e6] opacity-[0.75] hover:opacity-100'
            }`}
          >
            <Layers3 size={16} />
            <span>Cadastros Base</span>
          </button>
        )}
      </div>

      {/* SEARCH AND QUICK FILTERS FOR TABLE & KANBAN */}
      {(activeTab === 'table' || activeTab === 'kanban') && (
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
                          <tr 
                            key={a.id} 
                            onClick={() => handleOpenDetailModal(a)}
                            className="hover:bg-brand-dark/15 cursor-pointer transition-colors"
                          >
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
                              <div className="text-brand-text">{getAssetLocationLabel(a)}</div>
                              <div className="text-brand-muted font-mono">{getAssetStorageLabel(a)}</div>
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
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleOpenDuplicate(a);
                                    }}
                                    className="border border-brand-border hover:border-brand-primary text-brand-text p-1.5 transition-colors"
                                    title="Duplicar ativo em lote"
                                  >
                                    <Copy size={13} />
                                  </button>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleOpenEdit(a);
                                    }}
                                    className="border border-brand-border hover:border-brand-primary text-brand-text p-1.5 transition-colors"
                                    title="Editar"
                                  >
                                    <Edit2 size={13} />
                                  </button>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleDeleteAsset(a.id);
                                    }}
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
                    <div 
                      key={a.id} 
                      onClick={() => handleOpenDetailModal(a)}
                      className="border border-brand-border bg-brand-card p-3 space-y-3 shadow-sm hover:border-brand-primary/50 transition-colors cursor-pointer"
                    >
                      <div>
                        <div className="font-medium text-xs text-brand-text flex items-center justify-between">
                          <span className="truncate pr-1">{a.nome}</span>
                          {a.bloqueado && <Lock size={10} className="text-purple-400 flex-shrink-0" />}
                        </div>
                        <div className="text-[10px] text-brand-muted font-mono">{a.e_patrimonio}</div>
                      </div>

                      {/* Dropdown status update */}
                      {isManagerOrAbove && (
                        <div onClick={(e) => e.stopPropagation()}>
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
                        <span className="truncate max-w-[100px]">{getAssetLocationLabel(a)}</span>
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

          <div className="bg-brand-card border border-brand-border p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-brand-border pb-3">
              <div>
                <h3 className="font-bold text-sm uppercase tracking-wider text-brand-text font-mono">
                  Ativos Encontrados
                </h3>
                <p className="text-[10px] font-mono uppercase tracking-wider text-brand-muted mt-1">
                  {reportLoading ? 'Atualizando resultados...' : `${reportAssets.length} registro(s) carregado(s)`}
                </p>
              </div>
            </div>

            {reportLoading ? (
              <div className="p-10 text-center flex flex-col items-center justify-center space-y-4">
                <RefreshCw className="animate-spin text-brand-primary" size={24} />
                <span className="font-mono text-xs text-brand-muted uppercase">Buscando ativos filtrados...</span>
              </div>
            ) : reportAssets.length === 0 ? (
              <div className="p-10 text-center text-brand-muted font-mono text-xs uppercase border border-brand-border/40 bg-brand-dark/20">
                Nenhum ativo encontrado com os filtros atuais.
              </div>
            ) : (
              <div className="overflow-x-auto border border-brand-border/40">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-brand-border/60 font-mono uppercase text-brand-muted text-[10px]">
                      <th className="py-3 px-3">Ativo</th>
                      <th className="py-3 px-3">Patrimônio</th>
                      <th className="py-3 px-3">Categoria</th>
                      <th className="py-3 px-3">Local</th>
                      <th className="py-3 px-3">Fornecedor</th>
                      <th className="py-3 px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-brand-border/30">
                    {reportAssets.map((asset) => (
                      <tr key={asset.id} className="hover:bg-brand-dark/20 transition-colors">
                        <td className="py-3 px-3">
                          <div className="font-semibold text-brand-text">{asset.nome}</div>
                          <div className="text-brand-muted text-[10px] mt-1">{asset.modelo || 'Sem modelo'}</div>
                        </td>
                        <td className="py-3 px-3 font-mono text-brand-text">{asset.e_patrimonio}</td>
                        <td className="py-3 px-3 text-brand-muted">{asset.categoria?.nome || 'Sem categoria'}</td>
                        <td className="py-3 px-3 text-brand-muted">{getAssetLocationLabel(asset)}</td>
                        <td className="py-3 px-3 text-brand-muted">{asset.fornecedor?.nome || '—'}</td>
                        <td className="py-3 px-3">
                          <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 border border-brand-primary/30 bg-brand-primary/5 text-brand-primary">
                            {asset.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB CONTENT: REFERENCE MANAGEMENT */}
      {activeTab === 'references' && isManagerOrAbove && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div className="bg-brand-card border border-brand-border p-6 space-y-5">
            <div className="flex items-center space-x-2 border-b border-brand-border pb-3">
              <Layers3 className="text-brand-primary" size={18} />
              <div>
                <h3 className="font-bold text-sm uppercase tracking-wider text-brand-text font-mono m-0">Categorias de Ativos</h3>
                <p className="text-[11px] text-brand-muted mt-1">Crie e organize os tipos de equipamentos do inventário.</p>
              </div>
            </div>

            <form onSubmit={handleCreateCategoryInline} className="space-y-3">
              <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted">Nova Categoria</label>
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  value={newCategoryName}
                  onChange={(e) => setNewCategoryName(e.target.value)}
                  placeholder="Ex.: Notebook, Monitor, Impressora"
                  className="flex-1 bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary"
                />
                <button
                  type="submit"
                  disabled={creatingCategory}
                  className="bg-brand-primary hover:bg-brand-primary/90 disabled:opacity-60 text-brand-dark font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs flex items-center justify-center gap-2"
                >
                  {creatingCategory && <RefreshCw size={14} className="animate-spin" />}
                  <span>{creatingCategory ? 'Criando...' : 'Criar Categoria'}</span>
                </button>
              </div>
            </form>

            <div className="border border-brand-border/50">
              <div className="px-4 py-3 border-b border-brand-border bg-brand-dark/20 flex items-center justify-between">
                <span className="font-mono text-xs uppercase tracking-wider text-brand-text">Categorias cadastradas</span>
                <span className="font-mono text-[10px] text-brand-muted">{references?.categorias.length ?? 0} itens</span>
              </div>
              <div className="max-h-[420px] overflow-y-auto divide-y divide-brand-border/30">
                {references?.categorias.length ? references.categorias.map((categoria) => (
                  <div key={categoria.id} className="px-4 py-3 flex items-center justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      {editingCategoryId === categoria.id ? (
                        <input
                          type="text"
                          value={editingCategoryName}
                          onChange={(e) => setEditingCategoryName(e.target.value)}
                          className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary"
                        />
                      ) : (
                        <div className="text-sm text-brand-text font-medium">{categoria.nome}</div>
                      )}
                      <div className="text-[10px] font-mono text-brand-muted mt-1">ID #{categoria.id}</div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {editingCategoryId === categoria.id ? (
                        <>
                          <button
                            type="button"
                            onClick={() => handleSaveCategory(categoria.id)}
                            disabled={savingCategoryId === categoria.id}
                            className="border border-brand-primary text-brand-primary hover:bg-brand-primary/5 px-3 py-1.5 font-mono text-[10px] uppercase"
                          >
                            {savingCategoryId === categoria.id ? 'Salvando...' : 'Salvar'}
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setEditingCategoryId(null);
                              setEditingCategoryName('');
                            }}
                            className="border border-brand-border text-brand-muted hover:bg-brand-card px-3 py-1.5 font-mono text-[10px] uppercase"
                          >
                            Cancelar
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            type="button"
                            onClick={() => handleStartEditCategory(categoria.id, categoria.nome)}
                            className="border border-brand-border hover:border-brand-primary text-brand-text p-2 transition-colors"
                            title="Editar categoria"
                          >
                            <Edit2 size={13} />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteCategory(categoria.id, categoria.nome)}
                            disabled={deletingCategoryId === categoria.id}
                            className="border border-brand-border hover:border-red-500 text-red-400 p-2 transition-colors disabled:opacity-60"
                            title="Excluir categoria"
                          >
                            <Trash2 size={13} />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                )) : (
                  <div className="px-4 py-8 text-center text-brand-muted font-mono text-xs uppercase">
                    Nenhuma categoria cadastrada.
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="bg-brand-card border border-brand-border p-6 space-y-5">
            <div className="flex items-center space-x-2 border-b border-brand-border pb-3">
              <MapPin className="text-brand-primary" size={18} />
              <div>
                <h3 className="font-bold text-sm uppercase tracking-wider text-brand-text font-mono m-0">Localizações</h3>
                <p className="text-[11px] text-brand-muted mt-1">Cadastre os locais físicos usados pelo estoque e pelos ativos em operação.</p>
              </div>
            </div>

            <form onSubmit={handleCreateLocationInline} className="space-y-3">
              <label className="block text-[10px] font-mono uppercase tracking-wider text-brand-muted">Nova Localização</label>
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  value={newLocationName}
                  onChange={(e) => setNewLocationName(e.target.value)}
                  placeholder="Ex.: Matriz, Filial Goiânia, Sala CPD"
                  className="flex-1 bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary"
                />
                <button
                  type="submit"
                  disabled={creatingLocation}
                  className="bg-brand-primary hover:bg-brand-primary/90 disabled:opacity-60 text-brand-dark font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs flex items-center justify-center gap-2"
                >
                  {creatingLocation && <RefreshCw size={14} className="animate-spin" />}
                  <span>{creatingLocation ? 'Criando...' : 'Criar Localização'}</span>
                </button>
              </div>
            </form>

            <div className="border border-brand-border/50">
              <div className="px-4 py-3 border-b border-brand-border bg-brand-dark/20 flex items-center justify-between">
                <span className="font-mono text-xs uppercase tracking-wider text-brand-text">Localizações cadastradas</span>
                <span className="font-mono text-[10px] text-brand-muted">{references?.localizacoes.length ?? 0} itens</span>
              </div>
              <div className="max-h-[420px] overflow-y-auto divide-y divide-brand-border/30">
                {references?.localizacoes.length ? references.localizacoes.map((localizacao) => (
                  <div key={localizacao.id} className="px-4 py-3 flex items-center justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      {editingLocationId === localizacao.id ? (
                        <input
                          type="text"
                          value={editingLocationName}
                          onChange={(e) => setEditingLocationName(e.target.value)}
                          className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary"
                        />
                      ) : (
                        <div className="text-sm text-brand-text font-medium">{localizacao.nome}</div>
                      )}
                      <div className="text-[10px] font-mono text-brand-muted mt-1">ID #{localizacao.id}</div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {editingLocationId === localizacao.id ? (
                        <>
                          <button
                            type="button"
                            onClick={() => handleSaveLocation(localizacao.id)}
                            disabled={savingLocationId === localizacao.id}
                            className="border border-brand-primary text-brand-primary hover:bg-brand-primary/5 px-3 py-1.5 font-mono text-[10px] uppercase"
                          >
                            {savingLocationId === localizacao.id ? 'Salvando...' : 'Salvar'}
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setEditingLocationId(null);
                              setEditingLocationName('');
                            }}
                            className="border border-brand-border text-brand-muted hover:bg-brand-card px-3 py-1.5 font-mono text-[10px] uppercase"
                          >
                            Cancelar
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            type="button"
                            onClick={() => handleStartEditLocation(localizacao.id, localizacao.nome)}
                            className="border border-brand-border hover:border-brand-primary text-brand-text p-2 transition-colors"
                            title="Editar localização"
                          >
                            <Edit2 size={13} />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteLocation(localizacao.id, localizacao.nome)}
                            disabled={deletingLocationId === localizacao.id}
                            className="border border-brand-border hover:border-red-500 text-red-400 p-2 transition-colors disabled:opacity-60"
                            title="Excluir localização"
                          >
                            <Trash2 size={13} />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                )) : (
                  <div className="px-4 py-8 text-center text-brand-muted font-mono text-xs uppercase">
                    Nenhuma localização cadastrada.
                  </div>
                )}
              </div>
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
                    <div><span className="text-brand-muted">Original Local:</span> <span className="text-brand-text">{getAssetLocationLabel(duplicateTemplate)}</span></div>
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
                    <div className="text-brand-muted">Local: {getAssetLocationLabel(scannedAsset)}</div>
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

      {/* DIALOG: CSV IMPORT */}
      {showImportModal && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-3xl border border-brand-border bg-brand-card p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <div>
                <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">Importar Ativos por CSV</h3>
                <p className="text-[11px] text-brand-muted mt-1">
                  Use o mesmo padrão do arquivo exportado pelo inventário. O sistema cria novos ativos e atualiza os já existentes pelo E-Patrimônio.
                </p>
              </div>
              <button onClick={() => setShowImportModal(false)} className="text-brand-muted hover:text-brand-text">
                <X size={20} />
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_.9fr] gap-6">
              <div className="space-y-4">
                <div
                  onClick={() => importInputRef.current?.click()}
                  className="border-2 border-dashed border-brand-border hover:border-brand-primary/50 bg-brand-dark/20 p-8 text-center cursor-pointer space-y-3 transition-colors"
                >
                  <Upload className="mx-auto text-brand-muted hover:text-brand-primary transition-colors" size={34} />
                  <div>
                    <span className="text-xs font-mono text-brand-text uppercase block font-semibold">Selecionar arquivo CSV</span>
                    <span className="text-[10px] text-brand-muted block mt-1">Separador `;` e colunas do inventário exportado</span>
                  </div>
                  <input
                    type="file"
                    ref={importInputRef}
                    accept=".csv,text/csv"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0] || null;
                      setSelectedImportFile(file);
                      setImportSummary(null);
                      setImportError(null);
                    }}
                  />
                </div>

                <div className="border border-brand-border/50 bg-brand-dark/20 p-4 text-xs space-y-2">
                  <div className="font-mono uppercase tracking-wider text-brand-primary">Como funciona</div>
                  <div className="text-brand-muted">Se o E-Patrimônio já existir, o ativo é atualizado.</div>
                  <div className="text-brand-muted">Se não existir, um novo ativo é criado.</div>
                  <div className="text-brand-muted">Categoria, localização, armazenamento, fornecedor e setor precisam já existir no sistema quando vierem preenchidos no CSV.</div>
                </div>

                <button
                  type="button"
                  onClick={() => assetsApi.downloadImportTemplate()}
                  className="border border-brand-border hover:bg-brand-card text-brand-text font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs flex items-center justify-center space-x-2 transition-colors w-full"
                >
                  <FileText size={14} />
                  <span>Baixar Modelo CSV</span>
                </button>

                {selectedImportFile && (
                  <div className="border border-brand-primary/30 bg-brand-primary/5 p-3 text-xs">
                    <div className="font-semibold text-brand-text">{selectedImportFile.name}</div>
                    <div className="text-brand-muted mt-1">{Math.max(1, Math.round(selectedImportFile.size / 1024))} KB</div>
                  </div>
                )}

                {importError && (
                  <div className="p-3 border border-red-500/30 bg-red-500/5 text-red-400 text-xs font-mono flex items-center space-x-2">
                    <ShieldAlert size={16} />
                    <span>{importError}</span>
                  </div>
                )}
              </div>

              <div className="space-y-4">
                <div className="border border-brand-border/50 bg-brand-dark/20 p-4 space-y-3">
                  <div className="font-mono uppercase tracking-wider text-brand-text text-xs">Colunas aceitas</div>
                  <div className="text-[11px] text-brand-muted leading-5">
                    E-Patrimônio, Nome, Modelo, Número de Série, Status, Categoria, Localização, Armazenamento, Fornecedor, Data de Aquisição, Valor, Ativo Fixo, Em Posse De, Setor e Requer Termo RH.
                  </div>
                </div>

                {importSummary && (
                  <div className="border border-brand-border bg-brand-dark/20 p-4 space-y-4">
                    <div className="grid grid-cols-3 gap-3 text-center">
                      <div className="border border-brand-border/50 p-3">
                        <div className="text-xl font-black font-mono text-brand-text">{importSummary.criados}</div>
                        <div className="text-[10px] uppercase font-mono text-brand-muted">Criados</div>
                      </div>
                      <div className="border border-brand-border/50 p-3">
                        <div className="text-xl font-black font-mono text-brand-text">{importSummary.atualizados}</div>
                        <div className="text-[10px] uppercase font-mono text-brand-muted">Atualizados</div>
                      </div>
                      <div className="border border-brand-border/50 p-3">
                        <div className="text-xl font-black font-mono text-red-400">{importSummary.falhas}</div>
                        <div className="text-[10px] uppercase font-mono text-brand-muted">Falhas</div>
                      </div>
                    </div>

                    <div className="max-h-64 overflow-y-auto border border-brand-border/50">
                      <table className="w-full text-left text-[11px]">
                        <thead className="border-b border-brand-border/50 font-mono uppercase text-[10px] text-brand-muted">
                          <tr>
                            <th className="px-3 py-2">Linha</th>
                            <th className="px-3 py-2">Ativo</th>
                            <th className="px-3 py-2">Resultado</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-brand-border/30">
                          {importSummary.resultados.map((item) => (
                            <tr key={`${item.linha}-${item.e_patrimonio}`}>
                              <td className="px-3 py-2 font-mono text-brand-muted">{item.linha}</td>
                              <td className="px-3 py-2">
                                <div className="text-brand-text">{item.nome || 'Sem nome'}</div>
                                <div className="text-brand-muted font-mono text-[10px]">{item.e_patrimonio || 'Sem patrimônio'}</div>
                              </td>
                              <td className="px-3 py-2">
                                {item.erro ? (
                                  <span className="text-red-400">{item.erro}</span>
                                ) : (
                                  <span className="text-brand-primary font-mono uppercase text-[10px]">{item.acao}</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-brand-border">
              <button
                type="button"
                onClick={() => setShowImportModal(false)}
                className="border border-brand-border hover:bg-brand-card px-4 py-2 font-mono text-xs uppercase"
              >
                Fechar
              </button>
              <button
                type="button"
                onClick={handleImportCsv}
                disabled={importingCsv}
                className="bg-brand-primary hover:bg-brand-primary/90 disabled:opacity-60 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs flex items-center gap-2"
              >
                {importingCsv && <RefreshCw size={14} className="animate-spin" />}
                <span>{importingCsv ? 'Importando...' : 'Importar Agora'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DETAIL MODAL */}
      {showDetailModal && selectedAssetForDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-dark/80 backdrop-blur-md">
          <div className="w-full max-w-4xl bg-brand-card border border-brand-border shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            {/* Header */}
            <div className="flex justify-between items-center px-6 py-4 border-b border-brand-border bg-brand-dark/50">
              <div>
                <span className="text-[10px] font-mono font-bold text-brand-primary uppercase tracking-widest bg-brand-primary/10 px-2 py-0.5 border border-brand-primary/20 mr-2.5">
                  {selectedAssetForDetail.e_patrimonio}
                </span>
                <h3 className="inline-block text-lg font-bold font-mono uppercase tracking-wider text-brand-text">
                  {selectedAssetForDetail.nome}
                </h3>
              </div>
              <button 
                onClick={() => setShowDetailModal(false)} 
                className="text-brand-muted hover:text-brand-text transition-colors p-1"
              >
                <X size={20} />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 lg:grid-cols-[1.3fr_0.7fr] gap-6">
              {/* Left Column: Full Registration Data */}
              <div className="space-y-6">
                {/* Status and Type alerts */}
                <div className="flex flex-wrap gap-2.5">
                  <span className={`text-[10px] font-mono uppercase px-2.5 py-1 border ${
                    selectedAssetForDetail.status === 'Manutenção' 
                      ? 'border-amber-500/30 bg-amber-500/5 text-amber-400' 
                      : selectedAssetForDetail.status === 'Disponível'
                      ? 'border-green-500/30 bg-green-500/5 text-green-400'
                      : 'border-brand-border bg-brand-dark/30 text-brand-text'
                  }`}>
                    Status: {selectedAssetForDetail.status}
                  </span>
                  
                  {selectedAssetForDetail.bloqueado && (
                    <span className="text-[10px] font-mono uppercase px-2.5 py-1 border border-purple-500/30 bg-purple-500/5 text-purple-400 flex items-center space-x-1.5">
                      <Lock size={12} />
                      <span>🔒 Ativo Fixo (Bloqueado)</span>
                    </span>
                  )}

                  {selectedAssetForDetail.requer_termo_rh && (
                    <span className="text-[10px] font-mono uppercase px-2.5 py-1 border border-blue-500/30 bg-blue-500/5 text-blue-400">
                      📋 Requer Termo RH
                    </span>
                  )}
                </div>

                {/* Section: Geral */}
                <div className="border border-brand-border/60 bg-brand-dark/10 p-4 space-y-3">
                  <h4 className="font-mono text-xs font-bold text-brand-primary uppercase tracking-widest border-b border-brand-border pb-1.5">
                    Informações Gerais
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-3 text-xs">
                    <div>
                      <span className="text-[10px] font-mono uppercase text-brand-muted block">Modelo</span>
                      <span className="text-brand-text font-semibold">{selectedAssetForDetail.modelo || '—'}</span>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase text-brand-muted block">Número de Série (S/N)</span>
                      <span className="text-brand-text font-mono">{selectedAssetForDetail.numero_serie || '—'}</span>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase text-brand-muted block">Categoria</span>
                      <span className="text-brand-text">{selectedAssetForDetail.categoria?.nome || 'Sem categoria'}</span>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase text-brand-muted block">Criado por</span>
                      <span className="text-brand-text">{selectedAssetForDetail.created_by?.nome || '—'}</span>
                    </div>
                    <div className="md:col-span-2">
                      <span className="text-[10px] font-mono uppercase text-brand-muted block">Descrição</span>
                      <p className="text-brand-text bg-brand-dark/40 p-2.5 border border-brand-border/40 rounded-sm font-mono mt-1 text-[11px] whitespace-pre-wrap">
                        {selectedAssetForDetail.descricao || 'Nenhuma descrição fornecida.'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Section: Localização e Responsabilidade */}
                <div className="border border-brand-border/60 bg-brand-dark/10 p-4 space-y-3">
                  <h4 className="font-mono text-xs font-bold text-brand-primary uppercase tracking-widest border-b border-brand-border pb-1.5">
                    Localização & Responsabilidade
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-3 text-xs">
                    <div>
                      <span className="text-[10px] font-mono uppercase text-brand-muted block">Localização Atual</span>
                      <span className="text-brand-text font-semibold">{getAssetLocationLabel(selectedAssetForDetail)}</span>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase text-brand-muted block">Armazenamento</span>
                      <span className="text-brand-text">{getAssetStorageLabel(selectedAssetForDetail) || '—'}</span>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase text-brand-muted block">Em Posse De</span>
                      <span className="text-brand-text font-semibold">{selectedAssetForDetail.em_posse_de || 'Ninguém (Disponível)'}</span>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase text-brand-muted block">Setor / Departamento</span>
                      <span className="text-brand-text">{selectedAssetForDetail.current_departamento?.nome || '—'}</span>
                    </div>
                  </div>
                </div>

                {/* Section: Financeiro & Aquisição */}
                <div className="border border-brand-border/60 bg-brand-dark/10 p-4 space-y-3">
                  <h4 className="font-mono text-xs font-bold text-brand-primary uppercase tracking-widest border-b border-brand-border pb-1.5">
                    Financeiro & Aquisição
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-3 text-xs">
                    <div>
                      <span className="text-[10px] font-mono uppercase text-brand-muted block">Valor de Aquisição</span>
                      <span className="text-brand-text font-mono font-semibold">
                        {selectedAssetForDetail.valor 
                          ? selectedAssetForDetail.valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) 
                          : '—'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase text-brand-muted block">Data de Aquisição</span>
                      <span className="text-brand-text font-mono">
                        {selectedAssetForDetail.data_aquisicao 
                          ? new Date(selectedAssetForDetail.data_aquisicao).toLocaleDateString('pt-BR') 
                          : '—'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase text-brand-muted block">Fornecedor</span>
                      <span className="text-brand-text">{selectedAssetForDetail.fornecedor?.nome || '—'}</span>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase text-brand-muted block">Nota Fiscal</span>
                      <span className="text-brand-text font-mono">{selectedAssetForDetail.nota_fiscal?.numero_nota || '—'}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column: QR Code & Quick Actions */}
              <div className="space-y-6 flex flex-col">
                {/* QR Code Container */}
                <div className="border border-brand-border bg-brand-dark/20 p-4 flex flex-col items-center justify-center text-center space-y-4">
                  <div className="font-mono text-xs font-bold text-brand-primary uppercase tracking-wider">
                    QR Code Patrimonial
                  </div>
                  <div className="bg-white p-2.5 border border-brand-border/60">
                    <img 
                      src={assetsApi.getQRCodeUrl(selectedAssetForDetail.id)} 
                      alt={`QR Code para ${selectedAssetForDetail.nome}`}
                      className="w-40 h-40 object-contain"
                    />
                  </div>
                  <button
                    onClick={() => assetsApi.downloadQRCode(selectedAssetForDetail.id, selectedAssetForDetail.e_patrimonio)}
                    className="flex items-center justify-center space-x-2 w-full py-2 bg-brand-dark hover:bg-brand-card border border-brand-border text-brand-text font-bold font-mono text-xs uppercase tracking-wider transition-colors"
                  >
                    <Download size={14} />
                    <span>Download QR Code</span>
                  </button>
                </div>

                {/* Actions Panel */}
                <div className="border border-brand-border bg-brand-dark/20 p-4 space-y-4 flex-1">
                  <div className="font-mono text-xs font-bold text-brand-primary uppercase tracking-wider">
                    Ações de Inventário
                  </div>

                  {!showDetailMaintenanceForm && !showDetailTransferForm && (
                    <div className="space-y-3">
                      <button
                        onClick={() => {
                          setShowDetailMaintenanceForm(true);
                          setShowDetailTransferForm(false);
                          setDetailMaintenanceDescription('');
                          setDetailMaintenanceError(null);
                        }}
                        className="flex items-center justify-center space-x-2 w-full py-2.5 bg-brand-primary text-brand-dark font-bold font-mono text-xs uppercase tracking-wider hover:bg-brand-primary/95 transition-all"
                      >
                        <Wrench size={14} />
                        <span>Solicitar Manutenção</span>
                      </button>

                      <button
                        onClick={() => {
                          setShowDetailTransferForm(true);
                          setShowDetailMaintenanceForm(false);
                          setDetailTransferUserId('');
                          setDetailTransferError(null);
                        }}
                        className="flex items-center justify-center space-x-2 w-full py-2.5 bg-brand-dark border border-brand-border text-brand-text font-bold font-mono text-xs uppercase tracking-wider hover:bg-brand-card transition-all"
                      >
                        <ArrowRightLeft size={14} />
                        <span>Transferir Ativo</span>
                      </button>
                    </div>
                  )}

                  {/* Request Maintenance Form */}
                  {showDetailMaintenanceForm && (
                    <form onSubmit={handleRequestMaintenanceFromDetail} className="space-y-3.5 pt-2">
                      <div className="font-semibold text-xs text-brand-text flex items-center space-x-2 border-b border-brand-border/60 pb-1.5">
                        <Wrench size={14} className="text-brand-primary" />
                        <span>Solicitação de Manutenção</span>
                      </div>
                      
                      {detailMaintenanceError && (
                        <div className="p-2.5 border border-red-500/20 bg-red-500/5 text-red-400 text-[11px] font-mono">
                          {detailMaintenanceError}
                        </div>
                      )}

                      <div className="space-y-1">
                        <label className="text-[10px] font-mono uppercase text-brand-muted block">
                          Motivo / Descrição do Problema
                        </label>
                        <textarea
                          required
                          rows={3}
                          value={detailMaintenanceDescription}
                          onChange={(e) => setDetailMaintenanceDescription(e.target.value)}
                          placeholder="Descreva detalhadamente o defeito ou motivo da manutenção..."
                          className="w-full bg-brand-dark border border-brand-border px-2.5 py-1.5 text-xs text-brand-text focus:outline-none focus:border-brand-primary placeholder-brand-muted/40"
                        />
                      </div>

                      <div className="flex space-x-2">
                        <button
                          type="button"
                          onClick={() => setShowDetailMaintenanceForm(false)}
                          className="w-1/3 py-1.5 bg-brand-dark border border-brand-border text-brand-muted text-xs font-semibold font-mono uppercase"
                        >
                          Voltar
                        </button>
                        <button
                          type="submit"
                          disabled={detailMaintenanceLoading || !detailMaintenanceDescription.trim()}
                          className="flex-1 py-1.5 bg-brand-primary text-brand-dark text-xs font-semibold font-mono uppercase flex items-center justify-center space-x-1.5 disabled:opacity-50"
                        >
                          {detailMaintenanceLoading && <RefreshCw size={12} className="animate-spin" />}
                          <span>Confirmar</span>
                        </button>
                      </div>
                    </form>
                  )}

                  {/* Transfer Asset Form */}
                  {showDetailTransferForm && (
                    <form onSubmit={handleTransferAssetFromDetail} className="space-y-3.5 pt-2">
                      <div className="font-semibold text-xs text-brand-text flex items-center space-x-2 border-b border-brand-border/60 pb-1.5">
                        <ArrowRightLeft size={14} className="text-brand-primary" />
                        <span>Transferir Equipamento</span>
                      </div>

                      {detailTransferError && (
                        <div className="p-2.5 border border-red-500/20 bg-red-500/5 text-red-400 text-[11px] font-mono">
                          {detailTransferError}
                        </div>
                      )}

                      <div className="space-y-1">
                        <label className="text-[10px] font-mono uppercase text-brand-muted block">
                          Selecione o Destinatário
                        </label>
                        <select
                          required
                          value={detailTransferUserId}
                          onChange={(e) => setDetailTransferUserId(e.target.value ? Number(e.target.value) : '')}
                          className="w-full bg-brand-dark border border-brand-border px-2.5 py-1.5 text-xs text-brand-text focus:outline-none focus:border-brand-primary font-mono"
                        >
                          <option value="">Selecione o usuário...</option>
                          {usersList.map((u) => (
                            <option key={u.id} value={u.id}>
                              {u.nome} ({u.role})
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="flex space-x-2">
                        <button
                          type="button"
                          onClick={() => setShowDetailTransferForm(false)}
                          className="w-1/3 py-1.5 bg-brand-dark border border-brand-border text-brand-muted text-xs font-semibold font-mono uppercase"
                        >
                          Voltar
                        </button>
                        <button
                          type="submit"
                          disabled={detailTransferLoading || !detailTransferUserId}
                          className="flex-1 py-1.5 bg-brand-primary text-brand-dark text-xs font-semibold font-mono uppercase flex items-center justify-center space-x-1.5 disabled:opacity-50"
                        >
                          {detailTransferLoading && <RefreshCw size={12} className="animate-spin" />}
                          <span>Transferir</span>
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 bg-brand-dark/30 border-t border-brand-border flex justify-end">
              <button
                type="button"
                onClick={() => setShowDetailModal(false)}
                className="border border-brand-border hover:bg-brand-card text-brand-text font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs transition-colors"
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
