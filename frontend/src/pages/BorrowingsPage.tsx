import React, { useState, useEffect } from 'react';
import { transactionApi } from '../api/transaction';
import { assetsApi } from '../api/assets';
import { qrApi } from '../api/qr';
import { useAuthStore } from '../stores/authStore';
import type { Solicitacao, Asset } from '../types';
import { QRHandoverModal } from '../components/qr/QRHandoverModal';
import { 
  Plus, 
  Clock, 
  Check, 
  X, 
  AlertCircle, 
  Filter, 
  QrCode, 
  User,
  Calendar,
  Undo2
} from 'lucide-react';

export const BorrowingsPage: React.FC = () => {
  const { user: currentUser } = useAuthStore();
  const isManagerOrAbove = ['admin', 'gerente_ti', 'gerente_infra', 'tecnico'].includes(currentUser?.role?.toLowerCase() || '');

  const [solicitacoes, setSolicitacoes] = useState<Solicitacao[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter status state
  const [statusFilter, setStatusFilter] = useState<string>('');

  // Create request modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedAssetId, setSelectedAssetId] = useState<number | ''>('');
  const [motive, setMotive] = useState('');
  const [expectedDevolutionDate, setExpectedDevolutionDate] = useState('');

  // QR Handover modal integration
  const [showQRModal, setShowQRModal] = useState(false);

  useEffect(() => {
    fetchSolicitacoes();
    if (showCreateModal) {
      fetchAssets();
    }
  }, [showCreateModal]);

  const fetchSolicitacoes = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await transactionApi.listSolicitacoes();
      setSolicitacoes(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao carregar solicitações de empréstimo.');
    } finally {
      setLoading(false);
    }
  };

  const fetchAssets = async () => {
    try {
      const data = await assetsApi.list(0, 500);
      // Filter out assets that are locked, fixed, or already in use
      // Only display assets that are "Disponível" and not locked
      // For common users, we strictly enforce hiding blocked assets, for admins we show tooltips
      const available = data.filter(a => {
        if (isManagerOrAbove) {
          return a.status === 'Disponível';
        }
        return a.status === 'Disponível' && !a.bloqueado;
      });
      setAssets(available);
    } catch (err) {
      console.error('Error fetching assets:', err);
    }
  };

  const handleCreateSolicitacao = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssetId || !motive) {
      setError('Preencha todos os campos obrigatórios.');
      return;
    }

    try {
      await transactionApi.createSolicitacao({
        asset_id: Number(selectedAssetId),
        motivo: motive,
        data_prevista_devolucao: expectedDevolutionDate ? new Date(expectedDevolutionDate).toISOString() : undefined,
      });

      setShowCreateModal(false);
      setSelectedAssetId('');
      setMotive('');
      setExpectedDevolutionDate('');
      fetchSolicitacoes();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao criar solicitação de empréstimo.');
    }
  };

  const handleApprove = async (id: number) => {
    try {
      await transactionApi.approveSolicitacao(id);
      fetchSolicitacoes();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao aprovar solicitação.');
    }
  };

  const handleReject = async (id: number) => {
    try {
      await transactionApi.rejectSolicitacao(id);
      fetchSolicitacoes();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao rejeitar solicitação.');
    }
  };

  const handleDevolve = async (assetId: number) => {
    const sol = solicitacoes.find(s => s.asset_id === assetId && s.status === 'entregue');
    const isAssetBlocked = sol?.asset?.bloqueado;

    let confirmationMessage = 'Confirmar a devolução deste equipamento? Ele retornará ao inventário geral.';
    if (isAssetBlocked) {
      confirmationMessage = 'ATENÇÃO: Este equipamento é um Ativo Fixo (Bloqueado/Em uso corporativo). A devolução exige confirmação adicional da auditoria de TI. Confirma que a auditoria física foi concluída e o ativo deve retornar ao estado Bloqueado?';
    }

    if (!window.confirm(confirmationMessage)) return;
    
    try {
      await transactionApi.devolverAsset(assetId);
      fetchSolicitacoes();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao registrar devolução.');
    }
  };

  const handleManualDelivery = async (solicitacaoId: number) => {
    const obs = window.prompt("Observação para entrega manual (opcional):", "Entrega manual confirmada pelo administrador");
    if (obs === null) return; // User cancelled

    try {
      await qrApi.confirmDelivery({
        solicitacao_id: solicitacaoId,
        bypass_pin: true,
        observacao: obs
      });
      fetchSolicitacoes();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao registrar entrega manual.');
    }
  };

  // Filter list
  const filteredSolicitacoes = solicitacoes.filter(s => {
    if (statusFilter && s.status?.toLowerCase() !== statusFilter.toLowerCase()) return false;
    return true;
  });

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-brand-text">Solicitações de Empréstimo</h1>
          <p className="text-sm text-brand-muted">Gerencie o empréstimo temporário de ativos para colaboradores</p>
        </div>
        <div className="flex space-x-3">
          {isManagerOrAbove && (
            <button
              onClick={() => setShowQRModal(true)}
              className="flex items-center space-x-2 px-4 py-2.5 bg-brand-dark border border-brand-primary/30 hover:border-brand-primary text-brand-primary font-medium transition-all"
            >
              <QrCode size={18} />
              <span>Scanner QR</span>
            </button>
          )}
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center space-x-2 px-4 py-2.5 bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-medium transition-all"
          >
            <Plus size={18} />
            <span>Solicitar Equipamento</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-start space-x-3 p-4 border border-red-500/20 bg-red-500/5 text-red-400 text-sm">
          <AlertCircle size={18} className="shrink-0 mt-0.5" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto font-bold">×</button>
        </div>
      )}

      {/* Filters */}
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
          <option value="pendente">Pendente</option>
          <option value="aprovada">Aprovada</option>
          <option value="rejeitada">Rejeitada</option>
          <option value="entregue">Entregue / Em Uso</option>
          <option value="devolvida">Devolvida</option>
        </select>
      </div>

      {/* List */}
      {loading ? (
        <div className="p-12 text-center text-brand-muted font-mono text-sm">Carregando solicitações...</div>
      ) : filteredSolicitacoes.length === 0 ? (
        <div className="p-12 border border-brand-border bg-brand-card/20 text-center text-brand-muted text-sm">
          Nenhuma solicitação de empréstimo registrada.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredSolicitacoes.map((item) => {
            const st = item.status?.toLowerCase() || '';
            return (
              <div
                key={item.id}
                className="p-5 bg-brand-card border border-brand-border hover:border-brand-primary/20 transition-all flex flex-col justify-between space-y-4"
              >
                <div className="space-y-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold text-brand-text text-sm">{item.asset?.nome || 'Equipamento'}</h3>
                      <p className="text-xs text-brand-muted font-mono mt-0.5">EP: {item.asset?.e_patrimonio}</p>
                    </div>
                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 border ${
                      st === 'pendente'
                        ? 'text-blue-400 bg-blue-400/10 border-blue-400/20'
                        : st === 'aprovada'
                        ? 'text-amber-400 bg-amber-400/10 border-amber-400/20'
                        : st === 'entregue'
                        ? 'text-brand-primary bg-brand-primary/10 border-brand-primary/20'
                        : st === 'devolvida'
                        ? 'text-brand-muted bg-brand-muted/10 border-brand-border'
                        : 'text-red-400 bg-red-500/10 border-red-500/20'
                    }`}>
                      {item.status}
                    </span>
                  </div>

                  <div className="text-xs text-brand-muted bg-brand-dark/40 p-3 border border-brand-border/40 font-mono whitespace-pre-wrap">
                    Motivo: "{item.motivo}"
                  </div>

                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-brand-muted font-mono pt-1">
                    <div className="flex items-center space-x-1">
                      <User size={12} />
                      <span>Solicitante: {item.solicitante?.nome || 'Usuário'}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Calendar size={12} />
                      <span>Abertura: {new Date(item.data_solicitacao).toLocaleDateString('pt-BR')}</span>
                    </div>
                    {item.data_prevista_devolucao && (
                      <div className="flex items-center space-x-1 text-amber-500/80">
                        <Clock size={12} />
                        <span>Prev. Retorno: {new Date(item.data_prevista_devolucao).toLocaleDateString('pt-BR')}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Action buttons */}
                <div className="flex space-x-2 border-t border-brand-border/40 pt-3">
                  {isManagerOrAbove && st === 'pendente' && (
                    <>
                      <button
                        onClick={() => handleApprove(item.id)}
                        className="flex-1 py-1.5 bg-brand-primary hover:bg-brand-primary/95 text-brand-dark text-xs font-semibold flex items-center justify-center space-x-1"
                      >
                        <Check size={14} />
                        <span>Aprovar</span>
                      </button>
                      <button
                        onClick={() => handleReject(item.id)}
                        className="flex-1 py-1.5 bg-brand-muted/10 border border-brand-border hover:bg-red-500/10 hover:text-red-400 text-brand-text text-xs font-semibold flex items-center justify-center space-x-1"
                      >
                        <X size={14} />
                        <span>Rejeitar</span>
                      </button>
                    </>
                  )}

                  {isManagerOrAbove && st === 'aprovada' && (
                    <>
                      <button
                        onClick={() => handleManualDelivery(item.id)}
                        className="flex-1 py-1.5 bg-brand-primary hover:bg-brand-primary/95 text-brand-dark text-xs font-semibold flex items-center justify-center space-x-1"
                      >
                        <Check size={14} />
                        <span>Entregar (Manual)</span>
                      </button>
                      <button
                        onClick={() => setShowQRModal(true)}
                        className="flex-1 py-1.5 bg-brand-muted/10 border border-brand-border hover:bg-brand-primary hover:text-brand-dark text-brand-text text-xs font-semibold flex items-center justify-center space-x-1"
                      >
                        <QrCode size={14} />
                        <span>Entregar c/ QR</span>
                      </button>
                    </>
                  )}

                  {st === 'entregue' && item.asset_id && (
                    <button
                      onClick={() => handleDevolve(item.asset_id!)}
                      className="w-full py-1.5 bg-brand-muted/10 border border-brand-border hover:bg-brand-primary hover:text-brand-dark text-brand-text text-xs font-semibold flex items-center justify-center space-x-1 transition-all"
                    >
                      <Undo2 size={14} />
                      <span>Confirmar Devolução</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* QR Handover Modal */}
      <QRHandoverModal
        isOpen={showQRModal}
        onClose={() => setShowQRModal(false)}
        onSuccess={fetchSolicitacoes}
      />

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-dark/80 backdrop-blur-md">
          <div className="w-full max-w-md bg-brand-card border border-brand-border shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-brand-border bg-brand-dark/50">
              <h3 className="font-semibold text-lg text-brand-text">Solicitar Empréstimo</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-brand-muted hover:text-brand-text">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateSolicitacao} className="p-6 space-y-4">
              <div className="space-y-1">
                <label className="text-xs text-brand-muted">Equipamento Disponível</label>
                <select
                  required
                  value={selectedAssetId}
                  onChange={(e) => setSelectedAssetId(e.target.value === '' ? '' : Number(e.target.value))}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary"
                >
                  <option value="">Escolha um ativo...</option>
                  {assets.map(a => (
                    <option key={a.id} value={a.id} disabled={a.bloqueado}>
                      {a.nome} (EP: {a.e_patrimonio}){a.bloqueado ? ' - [BLOQUEADO / ATIVO FIXO]' : ''}
                    </option>
                  ))}
                </select>
                <p className="text-[10px] text-brand-muted">Apenas ativos em status 'Disponível' podem ser solicitados.</p>
              </div>

              <div className="space-y-1">
                <label className="text-xs text-brand-muted">Motivo do Empréstimo</label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Trabalho remoto temporário"
                  value={motive}
                  onChange={(e) => setMotive(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm focus:outline-none focus:border-brand-primary text-brand-text placeholder-brand-muted/30"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-brand-muted">Data Prevista para Devolução (Opcional)</label>
                <input
                  type="date"
                  value={expectedDevolutionDate}
                  min={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setExpectedDevolutionDate(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm focus:outline-none focus:border-brand-primary text-brand-text"
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
                  Enviar Solicitação
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
