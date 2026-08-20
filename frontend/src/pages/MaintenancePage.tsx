import React, { useState, useEffect } from 'react';
import { maintenanceApi } from '../api/maintenance';
import { assetsApi } from '../api/assets';
import { useAuthStore } from '../stores/authStore';
import type { SolicitacaoManutencao, Asset } from '../types';
import { QRHandoverModal } from '../components/qr/QRHandoverModal';
import { 
  Plus, 
  Clock, 
  Check, 
  X, 
  AlertCircle, 
  Filter, 
  QrCode, 
  DollarSign,
  User,
  ExternalLink
} from 'lucide-react';

export const MaintenancePage: React.FC = () => {
  const { user: currentUser } = useAuthStore();
  const isTechnicianOrAbove = currentUser?.role === 'admin' || currentUser?.role === 'gerente_ti' || currentUser?.role === 'tecnico';

  const [requests, setRequests] = useState<SolicitacaoManutencao[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Tabs: 'requests' | 'active' | 'history'
  const [activeTab, setActiveTab] = useState<'requests' | 'active' | 'history'>('requests');

  // Filter state
  const [statusFilter, setStatusFilter] = useState<string>('');

  // Request creation modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedAssetId, setSelectedAssetId] = useState<number | ''>('');
  const [newDescription, setNewDescription] = useState('');

  // Rejection modal
  const [rejectingRequestId, setRejectingRequestId] = useState<number | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');

  // Conclusion modal
  const [concludingRequestId, setConcludingRequestId] = useState<number | null>(null);
  const [conclusionNotes, setConclusionNotes] = useState('');
  const [conclusionCost, setConclusionCost] = useState<string>('');

  // QR Handover modal integration
  const [showQRModal, setShowQRModal] = useState(false);

  useEffect(() => {
    fetchRequests();
    if (showCreateModal) {
      fetchAssets();
    }
  }, [showCreateModal]);

  const fetchRequests = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await maintenanceApi.listRequests();
      setRequests(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao buscar solicitações de manutenção.');
    } finally {
      setLoading(false);
    }
  };

  const fetchAssets = async () => {
    try {
      const data = await assetsApi.list(0, 500);
      // For common users, filter out locked assets. For admins, show everything.
      if (isTechnicianOrAbove) {
        setAssets(data);
      } else {
        // filter out blocked/in maintenance assets
        setAssets(data.filter(a => !a.bloqueado && a.status === 'Disponível'));
      }
    } catch (err) {
      console.error('Error fetching assets:', err);
    }
  };

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssetId || !newDescription) {
      setError('Preencha os campos obrigatórios.');
      return;
    }

    try {
      const request = await maintenanceApi.createRequest({
        asset_id: Number(selectedAssetId),
        descricao: newDescription,
      });

      setRequests([request, ...requests]);
      setShowCreateModal(false);
      setSelectedAssetId('');
      setNewDescription('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao abrir solicitação.');
    }
  };

  const handleAcceptRequest = async (id: number) => {
    try {
      await maintenanceApi.acceptRequest(id);
      fetchRequests();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao aceitar manutenção.');
    }
  };

  const handleRejectRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectingRequestId || !rejectionReason) return;

    try {
      await maintenanceApi.rejectRequest(rejectingRequestId, rejectionReason);
      setRejectingRequestId(null);
      setRejectionReason('');
      fetchRequests();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao rejeitar manutenção.');
    }
  };

  const handleConcludeRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!concludingRequestId || !conclusionNotes) return;

    try {
      const cost = conclusionCost ? Number(conclusionCost) : undefined;
      await maintenanceApi.concludeRequest(concludingRequestId, conclusionNotes, cost);
      setConcludingRequestId(null);
      setConclusionNotes('');
      setConclusionCost('');
      fetchRequests();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao registrar conclusão.');
    }
  };

  const handleConfirmReceiptDirect = async (id: number) => {
    try {
      await maintenanceApi.confirmReceipt(id);
      fetchRequests();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao confirmar recebimento do ativo.');
    }
  };

  const getMaintenanceAssetLocation = (asset?: Asset) => {
    if (!asset) return '—';
    if (asset.current_local?.nome) return asset.current_local.nome;
    if (asset.status === 'Manutenção' && asset.prev_local?.nome) return `${asset.prev_local.nome} (origem)`;
    return '—';
  };

  const getMaintenanceAssetStorage = (asset?: Asset) => {
    if (!asset) return '';
    if (asset.current_armazenamento?.nome) return asset.current_armazenamento.nome;
    if (asset.status === 'Manutenção' && asset.prev_armazenamento?.nome) return `${asset.prev_armazenamento.nome} (origem)`;
    return '';
  };

  // Filter requests based on tab and filters
  const filteredRequests = requests.filter(r => {
    if (activeTab === 'requests') {
      // Show pending requests
      if (r.status !== 'pendente' && r.status !== 'rejeitada') return false;
    } else if (activeTab === 'active') {
      // Show active maintenance entries (accepted/awaiting handover)
      if (r.status === 'pendente' || r.status === 'rejeitada' || r.status === 'concluida' || r.status === 'entregue') return false;
    } else {
      // Show finished maintenance history
      if (r.status !== 'concluida' && r.status !== 'entregue') return false;
    }

    if (statusFilter && r.status !== statusFilter) return false;
    return true;
  });


  // Workshop Metrics calculations
  const totalInWorkshop = requests.filter(r => r.status === 'aceita' || r.status === 'aguardando_entrega' || r.status === 'em_andamento').length;
  const totalConcluded = requests.filter(r => r.status === 'concluida' || r.status === 'entregue').length;
  const totalPending = requests.filter(r => r.status === 'pendente').length;
  const totalSpent = requests.reduce((sum, r) => sum + (r.manutencao?.custo || 0), 0);

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-brand-text">Gestão de Oficina & Manutenção</h1>
          <p className="text-sm text-brand-muted">Acompanhe solicitações corretivas, preventivas e relatórios técnicos</p>
        </div>
        <div className="flex space-x-3">
          {isTechnicianOrAbove && (
            <button
              onClick={() => setShowQRModal(true)}
              className="flex items-center space-x-2 px-4 py-2.5 bg-brand-dark border border-brand-primary/30 hover:border-brand-primary text-brand-primary font-medium transition-all"
            >
              <QrCode size={18} />
              <span>Scanner de Handover</span>
            </button>
          )}
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center space-x-2 px-4 py-2.5 bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-medium transition-all"
          >
            <Plus size={18} />
            <span>Solicitar Manutenção</span>
          </button>
        </div>
      </div>

      {/* Workshop Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 bg-brand-card border border-brand-border flex flex-col justify-between">
          <span className="text-[10px] uppercase font-bold text-brand-muted tracking-wider">Fila de Espera</span>
          <span className="text-2xl font-bold text-blue-400 mt-2">{totalPending}</span>
          <span className="text-[10px] text-brand-muted mt-1">Solicitações aguardando triagem</span>
        </div>
        <div className="p-4 bg-brand-card border border-brand-border flex flex-col justify-between">
          <span className="text-[10px] uppercase font-bold text-brand-muted tracking-wider">Na Bancada (Oficina)</span>
          <span className="text-2xl font-bold text-amber-500 mt-2">{totalInWorkshop}</span>
          <span className="text-[10px] text-brand-muted mt-1">Equipamentos sendo consertados</span>
        </div>
        <div className="p-4 bg-brand-card border border-brand-border flex flex-col justify-between">
          <span className="text-[10px] uppercase font-bold text-brand-muted tracking-wider">Total Concluído</span>
          <span className="text-2xl font-bold text-brand-primary mt-2">{totalConcluded}</span>
          <span className="text-[10px] text-brand-muted mt-1">Reparos finalizados com sucesso</span>
        </div>
        <div className="p-4 bg-brand-card border border-brand-border flex flex-col justify-between">
          <span className="text-[10px] uppercase font-bold text-brand-muted tracking-wider">Custo de Oficina</span>
          <span className="text-2xl font-bold text-emerald-400 mt-2">{formatCurrency(totalSpent)}</span>
          <span className="text-[10px] text-brand-muted mt-1">Investimento total em reparação</span>
        </div>
      </div>

      {error && (
        <div className="flex items-start space-x-3 p-4 border border-red-500/20 bg-red-500/5 text-red-400 text-sm">
          <AlertCircle size={18} className="shrink-0 mt-0.5" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto font-bold">×</button>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-brand-border flex space-x-6">
        <button
          onClick={() => { setActiveTab('requests'); setStatusFilter(''); }}
          className={`py-3 text-sm font-semibold border-b-2 transition-all ${
            activeTab === 'requests'
              ? 'border-brand-primary text-brand-primary opacity-100'
              : 'border-transparent text-brand-text opacity-[0.55] hover:opacity-75'
          }`}
        >
          Triagem e Solicitações ({totalPending})
        </button>
        <button
          onClick={() => { setActiveTab('active'); setStatusFilter(''); }}
          className={`py-3 text-sm font-semibold border-b-2 transition-all ${
            activeTab === 'active'
              ? 'border-brand-primary text-brand-primary opacity-100'
              : 'border-transparent text-brand-text opacity-[0.55] hover:opacity-75'
          }`}
        >
          Oficina Ativa ({totalInWorkshop})
        </button>
        <button
          onClick={() => { setActiveTab('history'); setStatusFilter(''); }}
          className={`py-3 text-sm font-semibold border-b-2 transition-all ${
            activeTab === 'history'
              ? 'border-brand-primary text-brand-primary opacity-100'
              : 'border-transparent text-brand-text opacity-[0.55] hover:opacity-75'
          }`}
        >
          Histórico de Reparos ({totalConcluded})
        </button>
      </div>

      {/* Filters (Conditional based on active tab) */}
      <div className="p-4 bg-brand-card border border-brand-border flex items-center space-x-4">
        <div className="flex items-center space-x-2 text-brand-muted text-xs">
          <Filter size={14} />
          <span>Status:</span>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-brand-dark border border-brand-border px-3 py-1.5 text-xs text-brand-text focus:outline-none focus:border-brand-primary"
        >
          <option value="">Todos</option>
          {activeTab === 'requests' ? (
            <>
              <option value="pendente">Pendente</option>
              <option value="rejeitada">Rejeitada</option>
            </>
          ) : activeTab === 'active' ? (
            <>
              <option value="aceita">Aceita / Iniciada</option>
              <option value="aguardando_entrega">Aguardando Entrega</option>
            </>
          ) : (
            <>
              <option value="concluida">Concluída</option>
              <option value="entregue">Entregue ao Solicitante</option>
            </>
          )}
        </select>
      </div>


      {/* Grid List */}
      {loading ? (
        <div className="p-12 text-center text-brand-muted font-mono text-sm">Buscando registros...</div>
      ) : filteredRequests.length === 0 ? (
        <div className="p-12 border border-brand-border bg-brand-card/20 text-center text-brand-muted text-sm">
          Nenhuma solicitação encontrada.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredRequests.map((request) => (
            <div
              key={request.id}
              className="p-5 bg-brand-card border border-brand-border hover:border-brand-primary/20 transition-all flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-brand-text text-sm">{request.asset?.nome}</h3>
                    <p className="text-xs text-brand-muted font-mono mt-0.5">EP: {request.asset?.e_patrimonio}</p>
                  </div>
                  <span className={`text-[10px] uppercase font-bold px-2 py-0.5 border ${
                    request.status === 'pendente'
                      ? 'text-blue-400 bg-blue-400/10 border-blue-400/20'
                      : request.status === 'aceita'
                      ? 'text-amber-400 bg-amber-400/10 border-amber-400/20'
                      : request.status === 'aguardando_entrega'
                      ? 'text-purple-400 bg-purple-400/10 border-purple-400/20'
                      : request.status === 'concluida'
                      ? 'text-brand-primary bg-brand-primary/10 border-brand-primary/20'
                      : 'text-red-400 bg-red-500/10 border-red-500/20'
                  }`}>
                    {request.status.replace('_', ' ')}
                  </span>
                </div>

                <div className="text-xs text-brand-muted bg-brand-dark/40 p-3 border border-brand-border/40 font-mono whitespace-pre-wrap">
                  {request.descricao}
                </div>

                {request.observacao_resposta && (
                  <div className="text-xs text-red-400/90 italic">
                    Rejeitado por: "{request.observacao_resposta}"
                  </div>
                )}

                <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-brand-muted font-mono pt-1">
                  <div className="flex items-center space-x-1">
                    <User size={12} />
                    <span>Solicitante: {request.solicitante?.nome || 'Usuário'}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <span>Local: {getMaintenanceAssetLocation(request.asset)}</span>
                  </div>
                  {getMaintenanceAssetStorage(request.asset) && (
                    <div className="flex items-center space-x-1">
                      <span>Armaz.: {getMaintenanceAssetStorage(request.asset)}</span>
                    </div>
                  )}
                  <div className="flex items-center space-x-1">
                    <Clock size={12} />
                    <span>Abertura: {new Date(request.data_solicitacao).toLocaleDateString('pt-BR')}</span>
                  </div>
                </div>

                {/* If the request status is concluded/delivered, or has associated maintenance information */}
                {(request.status === 'concluida' || request.status === 'entregue' || request.manutencao) && (
                  <div className="mt-3 p-3 bg-brand-dark/30 border border-emerald-500/10 rounded space-y-2">
                    <div className="flex justify-between items-center text-xs font-semibold text-emerald-400">
                      <span>Relatório de Conclusão Técnica</span>
                      {request.manutencao?.custo !== undefined && (
                        <span className="font-mono">{formatCurrency(request.manutencao.custo)}</span>
                      )}
                    </div>
                    
                    {request.manutencao?.observacao_conclusao && (
                      <p className="text-xs text-brand-text bg-brand-dark/50 p-2 border border-brand-border/40 font-mono whitespace-pre-wrap">
                        Resolução: "{request.manutencao.observacao_conclusao}"
                      </p>
                    )}

                    <div className="grid grid-cols-2 gap-2 text-[10px] text-brand-muted font-mono pt-1">
                      <div>
                        <span className="font-bold text-brand-muted">Responsável:</span> {request.manutencao?.responsavel?.nome || request.responsavel?.nome || 'Técnico'}
                      </div>
                      <div>
                        <span className="font-bold text-brand-muted">Tipo:</span> <span className="uppercase">{request.manutencao?.tipo || 'corretiva'}</span>
                      </div>
                      {request.data_conclusao_tecnico && (
                        <div>
                          <span className="font-bold text-brand-muted">Conserto:</span> {new Date(request.data_conclusao_tecnico).toLocaleDateString('pt-BR')}
                        </div>
                      )}
                      {request.data_entrega && (
                        <div>
                          <span className="font-bold text-brand-muted">Entregue em:</span> {new Date(request.data_entrega).toLocaleDateString('pt-BR')}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons for Technicians */}
              {isTechnicianOrAbove && (
                <div className="flex space-x-2 border-t border-brand-border/40 pt-3">
                  {request.status === 'pendente' && (
                    <>
                      <button
                        onClick={() => handleAcceptRequest(request.id)}
                        className="flex-1 py-1.5 bg-brand-primary hover:bg-brand-primary/95 text-brand-dark text-xs font-semibold flex items-center justify-center space-x-1"
                      >
                        <Check size={14} />
                        <span>Aceitar</span>
                      </button>
                      <button
                        onClick={() => setRejectingRequestId(request.id)}
                        className="flex-1 py-1.5 bg-brand-muted/10 border border-brand-border hover:bg-red-500/10 hover:text-red-400 text-brand-text text-xs font-semibold flex items-center justify-center space-x-1"
                      >
                        <X size={14} />
                        <span>Rejeitar</span>
                      </button>
                    </>
                  )}

                  {request.status === 'aceita' && (
                    <button
                      onClick={() => setConcludingRequestId(request.id)}
                      className="w-full py-1.5 bg-brand-primary hover:bg-brand-primary/95 text-brand-dark text-xs font-semibold flex items-center justify-center space-x-1"
                    >
                      <Check size={14} />
                      <span>Concluir Reparo</span>
                    </button>
                  )}

                  {request.status === 'aguardando_entrega' && (
                    <>
                      <button
                        onClick={() => setShowQRModal(true)}
                        className="flex-1 py-1.5 bg-brand-dark border border-brand-primary/40 hover:border-brand-primary text-brand-primary text-xs font-semibold flex items-center justify-center space-x-1"
                      >
                        <QrCode size={14} />
                        <span>Entrega QR (PIN)</span>
                      </button>
                      <button
                        onClick={() => handleConfirmReceiptDirect(request.id)}
                        className="flex-1 py-1.5 bg-brand-muted/10 border border-brand-border hover:bg-brand-card text-brand-text text-xs font-semibold flex items-center justify-center space-x-1"
                      >
                        <ExternalLink size={14} />
                        <span>Entrega Direta</span>
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* QR Handover Modal */}
      <QRHandoverModal
        isOpen={showQRModal}
        onClose={() => setShowQRModal(false)}
        onSuccess={() => {
          fetchRequests();
        }}
      />

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-dark/80 backdrop-blur-md">
          <div className="w-full max-w-md bg-brand-card border border-brand-border shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-brand-border bg-brand-dark/50">
              <h3 className="font-semibold text-lg text-brand-text">Solicitar Manutenção</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-brand-muted hover:text-brand-text">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateRequest} className="p-6 space-y-4">
              <div className="space-y-1">
                <label className="text-xs text-brand-muted">Selecione o Equipamento</label>
                <select
                  required
                  value={selectedAssetId}
                  onChange={(e) => setSelectedAssetId(e.target.value === '' ? '' : Number(e.target.value))}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary"
                >
                  <option value="">Escolha um ativo...</option>
                  {assets.map(a => (
                    <option key={a.id} value={a.id}>
                      {a.nome} (EP: {a.e_patrimonio})
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs text-brand-muted">Descrição do Defeito / Motivo</label>
                <textarea
                  required
                  rows={4}
                  placeholder="Informe detalhadamente qual o problema apresentado no equipamento..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm focus:outline-none focus:border-brand-primary text-brand-text placeholder-brand-muted/30"
                />
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="w-1/3 py-2 bg-brand-dark border border-brand-border hover:bg-brand-card text-brand-muted text-sm transition-all"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-brand-primary hover:bg-brand-primary/95 text-brand-dark font-semibold text-sm transition-all"
                >
                  Confirmar Abertura
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {rejectingRequestId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-dark/80 backdrop-blur-md">
          <div className="w-full max-w-md bg-brand-card border border-brand-border shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-brand-border">
              <h3 className="font-semibold text-brand-text text-sm">Rejeitar Solicitação de Manutenção</h3>
              <button onClick={() => setRejectingRequestId(null)} className="text-brand-muted hover:text-brand-text">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleRejectRequest} className="p-6 space-y-4">
              <div className="space-y-1">
                <label className="text-xs text-brand-muted">Motivo da Rejeição</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Escreva a justificativa para recusar este reparo..."
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-xs focus:outline-none focus:border-brand-primary text-brand-text"
                />
              </div>
              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={() => setRejectingRequestId(null)}
                  className="w-1/3 py-1.5 bg-brand-dark border border-brand-border text-xs text-brand-muted"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="flex-1 py-1.5 bg-red-500 hover:bg-red-600 text-white text-xs font-semibold"
                >
                  Rejeitar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Conclude Modal */}
      {concludingRequestId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-dark/80 backdrop-blur-md">
          <div className="w-full max-w-md bg-brand-card border border-brand-border shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-brand-border">
              <h3 className="font-semibold text-brand-text text-sm">Registrar Conclusão de Reparo</h3>
              <button onClick={() => setConcludingRequestId(null)} className="text-brand-muted hover:text-brand-text">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleConcludeRequest} className="p-6 space-y-4">
              <div className="space-y-1">
                <label className="text-xs text-brand-muted">Notas Técnicas do Reparo</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Detalhe o que foi feito (ex: troca de pasta térmica, limpeza, formatação)..."
                  value={conclusionNotes}
                  onChange={(e) => setConclusionNotes(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-xs focus:outline-none focus:border-brand-primary text-brand-text"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-brand-muted flex items-center space-x-1">
                  <DollarSign size={12} />
                  <span>Custo Adicional de Reparo (Opcional)</span>
                </label>
                <input
                  type="number"
                  placeholder="0.00"
                  step="0.01"
                  value={conclusionCost}
                  onChange={(e) => setConclusionCost(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-1.5 text-xs focus:outline-none focus:border-brand-primary text-brand-text"
                />
              </div>

              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={() => setConcludingRequestId(null)}
                  className="w-1/3 py-1.5 bg-brand-dark border border-brand-border text-xs text-brand-muted"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="flex-1 py-1.5 bg-brand-primary text-brand-dark text-xs font-semibold"
                >
                  Confirmar Conclusão
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
