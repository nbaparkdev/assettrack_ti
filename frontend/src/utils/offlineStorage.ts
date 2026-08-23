export interface OfflineQueueItem {
  id: string;
  endpoint: string;
  method: 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  payload: any;
  headers?: Record<string, string>;
  timestamp: number;
  description: string;
  category: 'chamado' | 'interacao' | 'ativo' | 'movimentacao' | 'geral';
  status: 'pending' | 'syncing' | 'failed';
  error?: string;
  retryCount: number;
}

const QUEUE_STORAGE_KEY = 'assettrack_offline_sync_queue';
const CACHE_PREFIX = 'assettrack_cache_';

export const offlineStorage = {
  getQueue(): OfflineQueueItem[] {
    try {
      const data = localStorage.getItem(QUEUE_STORAGE_KEY);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  },

  saveQueue(queue: OfflineQueueItem[]) {
    try {
      localStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(queue));
      window.dispatchEvent(new CustomEvent('offline-queue-updated', { detail: { count: queue.length } }));
    } catch (e) {
      console.error('Failed to save offline queue', e);
    }
  },

  enqueue(item: Omit<OfflineQueueItem, 'id' | 'timestamp' | 'status' | 'retryCount'>): OfflineQueueItem {
    const queue = this.getQueue();
    const newItem: OfflineQueueItem = {
      ...item,
      id: `offline_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      timestamp: Date.now(),
      status: 'pending',
      retryCount: 0,
    };
    queue.push(newItem);
    this.saveQueue(queue);
    return newItem;
  },

  updateItem(id: string, updates: Partial<OfflineQueueItem>) {
    const queue = this.getQueue();
    const index = queue.findIndex(q => q.id === id);
    if (index !== -1) {
      queue[index] = { ...queue[index], ...updates };
      this.saveQueue(queue);
    }
  },

  removeItem(id: string) {
    const queue = this.getQueue().filter(q => q.id !== id);
    this.saveQueue(queue);
  },

  clearQueue() {
    this.saveQueue([]);
  },

  // Cache helper for read-only offline navigation
  setCache<T>(key: string, data: T) {
    try {
      localStorage.setItem(CACHE_PREFIX + key, JSON.stringify({
        data,
        cachedAt: Date.now(),
      }));
    } catch (e) {
      console.warn('Cache quota exceeded', e);
    }
  },

  getCache<T>(key: string, maxAgeMs = 7 * 24 * 60 * 60 * 1000): T | null {
    try {
      const raw = localStorage.getItem(CACHE_PREFIX + key);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (Date.now() - parsed.cachedAt > maxAgeMs) {
        return null;
      }
      return parsed.data as T;
    } catch {
      return null;
    }
  }
};
