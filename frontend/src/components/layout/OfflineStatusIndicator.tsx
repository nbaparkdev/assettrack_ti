import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Wifi, WifiOff, RefreshCw, AlertTriangle, CheckCircle2, Trash2, X, RotateCw } from 'lucide-react';
import { offlineStorage, type OfflineQueueItem } from '../../utils/offlineStorage';
import { offlineSyncManager } from '../../utils/offlineSyncManager';

export const OfflineStatusIndicator: React.FC = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [queue, setQueue] = useState<OfflineQueueItem[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    // Initialize offline sync listeners
    offlineSyncManager.init();

    const updateQueue = () => {
      setQueue(offlineStorage.getQueue());
    };

    updateQueue();

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    const handleQueueUpdated = () => updateQueue();
    const handleSyncStarted = () => setIsSyncing(true);
    const handleSyncCompleted = (e: any) => {
      setIsSyncing(false);
      updateQueue();
      const { succeeded, failed } = e.detail || {};
      if (succeeded > 0) {
        setToastMessage(`🎉 ${succeeded} ${succeeded === 1 ? 'ação sincronizada' : 'ações sincronizadas'} com sucesso!`);
        setTimeout(() => setToastMessage(null), 5000);
      }
      if (failed > 0) {
        setToastMessage(`⚠️ ${failed} ${failed === 1 ? 'item apresentou' : 'itens apresentaram'} erro de validação.`);
        setTimeout(() => setToastMessage(null), 6000);
      }
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('offline-queue-updated', handleQueueUpdated);
    window.addEventListener('offline-sync-started', handleSyncStarted);
    window.addEventListener('offline-sync-completed', handleSyncCompleted);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('offline-queue-updated', handleQueueUpdated);
      window.removeEventListener('offline-sync-started', handleSyncStarted);
      window.removeEventListener('offline-sync-completed', handleSyncCompleted);
    };
  }, []);

  const failedCount = queue.filter(q => q.status === 'failed').length;
  const totalQueue = queue.length;

  return (
    <>
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-20 right-4 md:bottom-6 md:right-6 z-50 max-w-sm bg-brand-card border border-brand-primary/50 text-brand-text p-3 shadow-2xl rounded-sm flex items-center space-x-2 animate-in fade-in slide-in-from-bottom-3">
          <CheckCircle2 size={18} className="text-brand-primary shrink-0" />
          <span className="text-xs font-medium">{toastMessage}</span>
          <button onClick={() => setToastMessage(null)} className="ml-auto text-brand-muted hover:text-brand-text">
            <X size={14} />
          </button>
        </div>
      )}

      {/* Connection / Sync Pill Indicator */}
      <div className="flex items-center space-x-1.5">
        {!isOnline ? (
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center space-x-1.5 px-2.5 py-1 bg-amber-500/15 border border-amber-500/40 text-amber-400 rounded text-xs font-medium hover:bg-amber-500/25 transition-all"
            title="Você está offline. As alterações serão salvas localmente."
          >
            <WifiOff size={14} className="animate-pulse" />
            <span className="hidden sm:inline">Modo Offline</span>
            {totalQueue > 0 && (
              <span className="px-1.5 py-0.2 bg-amber-500 text-brand-dark rounded-full font-bold text-[10px]">
                {totalQueue}
              </span>
            )}
          </button>
        ) : isSyncing ? (
          <div className="flex items-center space-x-1.5 px-2.5 py-1 bg-blue-500/15 border border-blue-500/40 text-blue-400 rounded text-xs font-medium">
            <RefreshCw size={13} className="animate-spin" />
            <span className="hidden sm:inline">Sincronizando...</span>
          </div>
        ) : failedCount > 0 ? (
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center space-x-1.5 px-2.5 py-1 bg-red-500/15 border border-red-500/40 text-red-400 rounded text-xs font-medium hover:bg-red-500/25 transition-all"
            title="Existem pendências de sincronização com erro."
          >
            <AlertTriangle size={14} />
            <span className="hidden sm:inline">Falha no Sync ({failedCount})</span>
          </button>
        ) : totalQueue > 0 ? (
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center space-x-1.5 px-2.5 py-1 bg-brand-primary/15 border border-brand-primary/40 text-brand-primary rounded text-xs font-medium hover:bg-brand-primary/25 transition-all"
            title="Itens na fila de sincronização."
          >
            <RotateCw size={13} />
            <span className="hidden sm:inline">Fila ({totalQueue})</span>
          </button>
        ) : (
          <div className="hidden lg:flex items-center space-x-1 px-2 py-0.5 text-[11px] text-emerald-400/80 font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block animate-pulse"></span>
            <span>Online</span>
          </div>
        )}
      </div>

      {/* Modal for viewing and managing offline queue */}
      {showModal && createPortal(
        <div className="fixed inset-0 z-[99999] bg-brand-dark/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-brand-card border border-brand-border shadow-2xl p-5 space-y-4 text-brand-text">
            <div className="flex items-center justify-between border-b border-brand-border pb-3">
              <div className="flex items-center space-x-2">
                {!isOnline ? <WifiOff size={18} className="text-amber-400" /> : <Wifi size={18} className="text-emerald-400" />}
                <h3 className="font-semibold text-sm text-brand-text">
                  Fila de Sincronização Offline ({queue.length})
                </h3>
              </div>
              <button onClick={() => setShowModal(false)} className="text-brand-muted hover:text-brand-text">
                <X size={18} />
              </button>
            </div>

            <div className="text-xs text-brand-muted">
              {!isOnline
                ? 'Você está sem conexão. As ações abaixo foram gravadas com segurança no seu aparelho e serão enviadas automaticamente assim que a internet voltar.'
                : 'Você está conectado. Caso haja itens pendentes ou com erro, você pode forçar a sincronização.'}
            </div>

            {/* Queue List */}
            <div className="max-h-60 overflow-y-auto space-y-2 divide-y divide-brand-border/40">
              {queue.map((item) => (
                <div key={item.id} className="pt-2 first:pt-0 flex items-start justify-between space-x-3 text-xs">
                  <div className="flex-1 space-y-0.5">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium text-brand-text">{item.description}</span>
                      <span className={`px-1.5 py-0.2 text-[10px] rounded font-mono uppercase ${
                        item.status === 'failed' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                        item.status === 'syncing' ? 'bg-blue-500/20 text-blue-400' :
                        'bg-amber-500/20 text-amber-400'
                      }`}>
                        {item.status === 'failed' ? 'Erro' : item.status === 'syncing' ? 'Enviando...' : 'Pendente'}
                      </span>
                    </div>
                    <div className="text-[11px] text-brand-muted font-mono">
                      {item.method} {item.endpoint} • {new Date(item.timestamp).toLocaleTimeString('pt-BR')}
                    </div>
                    {item.error && (
                      <div className="text-[11px] text-red-400 bg-red-500/5 p-1.5 border border-red-500/20 mt-1">
                        {item.error}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center space-x-1 shrink-0 pt-0.5">
                    {item.status === 'failed' && (
                      <button
                        onClick={() => offlineSyncManager.retryItem(item.id)}
                        className="p-1 text-brand-primary hover:bg-brand-primary/10 rounded"
                        title="Tentar novamente"
                      >
                        <RefreshCw size={13} />
                      </button>
                    )}
                    <button
                      onClick={() => offlineSyncManager.removeItem(item.id)}
                      className="p-1 text-red-400 hover:bg-red-500/10 rounded"
                      title="Descartar item"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              ))}

              {queue.length === 0 && (
                <div className="text-center py-6 text-brand-muted text-xs font-mono">
                  Nenhuma ação pendente na fila offline.
                </div>
              )}
            </div>

            {/* Modal Actions */}
            <div className="pt-3 border-t border-brand-border flex items-center justify-between">
              <button
                type="button"
                onClick={() => offlineStorage.clearQueue()}
                disabled={queue.length === 0}
                className="text-xs text-red-400 hover:underline disabled:opacity-40"
              >
                Limpar toda a fila
              </button>

              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3 py-1.5 border border-brand-border text-xs text-brand-muted hover:text-brand-text rounded"
                >
                  Fechar
                </button>
                {isOnline && queue.length > 0 && (
                  <button
                    type="button"
                    onClick={() => offlineSyncManager.syncQueue()}
                    disabled={isSyncing}
                    className="px-3 py-1.5 bg-brand-primary text-brand-dark font-bold text-xs rounded hover:bg-brand-primary/90 transition-all flex items-center space-x-1"
                  >
                    <RefreshCw size={12} className={isSyncing ? 'animate-spin' : ''} />
                    <span>{isSyncing ? 'Sincronizando...' : 'Sincronizar Agora'}</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
};
