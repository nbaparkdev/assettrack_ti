import { apiClient } from '../api/client';
import { offlineStorage } from './offlineStorage';

class OfflineSyncManager {
  private isSyncing = false;
  private listenersInitialized = false;

  public init() {
    if (this.listenersInitialized) return;
    this.listenersInitialized = true;

    window.addEventListener('online', () => {
      console.log('[OfflineSync] Restabelecida a conexão à internet. Sincronizando fila...');
      this.syncQueue();
    });

    // Check on startup
    if (navigator.onLine) {
      setTimeout(() => this.syncQueue(), 2500);
    }
  }

  public async syncQueue(): Promise<{ total: number; succeeded: number; failed: number }> {
    if (this.isSyncing || !navigator.onLine) {
      return { total: 0, succeeded: 0, failed: 0 };
    }

    const queue = offlineStorage.getQueue();
    const pendingItems = queue.filter(item => item.status === 'pending' || item.status === 'failed');
    if (pendingItems.length === 0) {
      return { total: 0, succeeded: 0, failed: 0 };
    }

    this.isSyncing = true;
    window.dispatchEvent(new CustomEvent('offline-sync-started', { detail: { count: pendingItems.length } }));

    let succeeded = 0;
    let failed = 0;

    for (const item of pendingItems) {
      offlineStorage.updateItem(item.id, { status: 'syncing' });

      try {
        await apiClient.request({
          url: item.endpoint,
          method: item.method,
          data: item.payload,
          headers: item.headers,
        });

        // Item successfully executed on backend -> remove from queue
        offlineStorage.removeItem(item.id);
        succeeded++;
      } catch (err: any) {
        console.error(`[OfflineSync] Erro ao sincronizar item ${item.id}:`, err);
        const errorMsg = err.response?.data?.detail || err.response?.data?.error || err.message || 'Erro de validação ao sincronizar.';
        offlineStorage.updateItem(item.id, {
          status: 'failed',
          error: errorMsg,
          retryCount: (item.retryCount || 0) + 1,
        });
        failed++;
      }
    }

    this.isSyncing = false;
    window.dispatchEvent(new CustomEvent('offline-sync-completed', {
      detail: {
        total: pendingItems.length,
        succeeded,
        failed,
      }
    }));

    return { total: pendingItems.length, succeeded, failed };
  }

  public retryItem(id: string) {
    offlineStorage.updateItem(id, { status: 'pending', error: undefined });
    this.syncQueue();
  }

  public removeItem(id: string) {
    offlineStorage.removeItem(id);
  }

  public isOnline(): boolean {
    return navigator.onLine;
  }
}

export const offlineSyncManager = new OfflineSyncManager();
